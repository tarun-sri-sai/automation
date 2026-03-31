param (
    [Parameter(Mandatory = $true)]
    [string]$RepoDirectory,

    [Parameter(Mandatory = $true)]
    [string]$Destination,

    [Parameter(Mandatory = $false)]
    [int]$ThrottleLimit = 100
)

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Filesystem.psm1")
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Logging.psm1")

$fileBaseName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Definition)
$logPath = Join-Path (Join-Path $thisDirectory "logs") "$fileBaseName.log"

try {
    Push-Location $RepoDirectory
}
catch {
    Write-LogMessage -LogPath $logPath -Message "$RepoDirectory is an invalid repo directory" -Level 2
    continue
}

try {
    Write-LogMessage -LogPath $logPath -Message "getting git tracked files"
    $files = @(& git ls-files)
    
    $files = $files | Where-Object { $_ }
    
    if ($files.Count -eq 0) {
        Write-LogMessage -LogPath $logPath -Message "no files found in $dir" -Level 3
        continue
    }

    $copyScriptBlock = {
        param($repoDir, $relativePath, $repoBaseName, $destinationPath, $logPath)

        $result = @{
            File     = $relativePath
            Status   = "unknown"
            Message  = ""
        }

        try {
            $fullPath = Join-Path $repoDir $relativePath
            $fileItem = Get-Item $fullPath
            $fileRelativeDir = Split-Path $relativePath
            
            if ($fileRelativeDir) {
                $newFolder = Join-Path $destinationPath $repoBaseName $fileRelativeDir
            }
            else {
                $newFolder = Join-Path $destinationPath $repoBaseName
            }
            
            $destFilePath = Join-Path $newFolder $fileItem.Name

            $null = New-Item -Type Directory -ErrorAction SilentlyContinue $newFolder

            $copyRequired = $true

            if (Test-Path $destFilePath) {
                $destFile = Get-Item $destFilePath

                if (
                    ($fileItem.Length -eq $destFile.Length) -and
                    ($fileItem.LastWriteTimeUtc -le $destFile.LastWriteTimeUtc)
                ) {
                    $copyRequired = $false
                }
            }

            if ($copyRequired) {
                Copy-Item -Force $fileItem.FullName $destFilePath
                $result.Status = "copied"
                $result.Message = "copied $relativePath to $destFilePath"
            }
            else {
                $result.Status = "skipped"
                $result.Message = "skipped unmodified file $relativePath"
            }
        }
        catch {
            $result.Status = "failed"
            $result.Message = "error copying $relativePath`: $_"
        }

        return $result
    }

    $runspacePool = [runspacefactory]::CreateRunspacePool(1, $ThrottleLimit)
    $runspacePool.Open()

    $runspaces = New-Object System.Collections.ArrayList
    $copyResults = New-Object 'System.Collections.Concurrent.ConcurrentBag[PSObject]'
    $progress = 0
    $progressLock = New-Object 'System.Threading.Mutex'
    $totalFiles = $files.Count
    $repoName = (Get-Item $pwd).BaseName

    foreach ($file in $files) {
        $completed = $runspaces | Where-Object { $_.Handle.IsCompleted -eq $true }
        while (($runspaces.Count -ge $ThrottleLimit) -and ($completed.Count -eq 0)) {
            Start-Sleep -Milliseconds 100
            $completed = $runspaces | Where-Object { $_.Handle.IsCompleted -eq $true }
        }

        foreach ($runspace in $completed) {
            $output = $runspace.PowerShell.EndInvoke($runspace.Handle)
            $runspace.PowerShell.Dispose()
            $runspaces.Remove($runspace)

            $copyResults.Add($output) | Out-Null

            $progressLock.WaitOne() | Out-Null
            $progress++
            $percentComplete = [math]::Min(100, ($progress / $totalFiles) * 100)
            Write-Progress -Activity "copying files in $repoName" -Status "processed $progress of $totalFiles files" -PercentComplete $percentComplete
            $progressLock.ReleaseMutex()
        }

        $repoPath = (Resolve-Path $pwd).Path
        $powerShell = [powershell]::Create().AddScript($copyScriptBlock).AddArgument($repoPath).AddArgument($file).AddArgument($repoName).AddArgument($Destination).AddArgument($logPath)
        $powerShell.RunspacePool = $runspacePool

        $handle = $powerShell.BeginInvoke()
        $runspace = [PSCustomObject]@{
            PowerShell = $powerShell
            Handle     = $handle
            File       = $file
        }
        [void]$runspaces.Add($runspace)
    }

    while ($runspaces.Count -gt 0) {
        $completed = $runspaces | Where-Object { $_.Handle.IsCompleted -eq $true }
        foreach ($runspace in $completed) {
            $output = $runspace.PowerShell.EndInvoke($runspace.Handle)
            $runspace.PowerShell.Dispose()
            $runspaces.Remove($runspace)

            $copyResults.Add($output) | Out-Null

            $progressLock.WaitOne() | Out-Null
            $progress++
            $percentComplete = [math]::Min(100, ($progress / $totalFiles) * 100)
            Write-Progress -Activity "copying files in $repoName" -Status "processed $progress of $totalFiles files" -PercentComplete $percentComplete
            $progressLock.ReleaseMutex()
        }

        if ($runspaces.Count -gt 0) {
            Start-Sleep -Milliseconds 100
        }
    }

    Write-Progress -Activity "copying files in $repoName" -Completed

    $runspacePool.Close()
    $runspacePool.Dispose()

    $copiedCount = ($copyResults | Where-Object { $_.Status -eq "copied" }).Count
    $skippedCount = ($copyResults | Where-Object { $_.Status -eq "skipped" }).Count
    $failedCount = ($copyResults | Where-Object { $_.Status -eq "failed" }).Count

    foreach($result in $copyResults | Where-Object { $_.Status -eq "skipped" }) {
        Write-LogMessage -LogPath $logPath -Message $result.Message
    }

    foreach ($result in $copyResults | Where-Object { $_.Status -ne "skipped" }) {
        $level = if ($result.Status -eq "failed") { 2 } else { 5 }
        Write-LogMessage -LogPath $logPath -Message $result.Message -Level $level
    }

    Write-LogMessage -LogPath $logPath -Message "completed ${repoName}: $copiedCount copied, $skippedCount skipped, $failedCount failed"
}
finally {
    Pop-Location
}
