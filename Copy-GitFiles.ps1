param (
    [Parameter(Mandatory = $true)]
    [string[]]$RepoDirectories,

    [Parameter(Mandatory = $true)]
    [string[]]$Destination
)

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Filesystem.psm1")
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Logging.psm1")

$fileBaseName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Definition)
$logPath = Join-Path (Join-Path $thisDirectory "logs") "$fileBaseName.log"

foreach ($dir in $RepoDirectories) {
    try {
        Set-Location $dir
    }
    catch {
        Write-LogMessage -LogPath $logPath -Message "$dir is an invalid repo directory" -Level 2
        continue
    }

    try {
        Write-LogMessage -LogPath $logPath -Message "getting git tracked files"
        $files = & git ls-files

        foreach ($f in ($files -Split "`n")) {
            if (-not $f) {
                continue
            }

            $file = (Get-Item $f)

            $folder = Resolve-Path -Relative $file.Directory
            $newFolder = Join-Paths $Destination, $((Get-Item $pwd).BaseName), $folder
            New-Item -Type Directory -ErrorAction SilentlyContinue $newFolder | Out-Null

            $destFilePath = Join-Path $newFolder $file.Name

            $copyRequired = $true

            if (Test-Path $destFilePath) {
                $destFile = Get-Item $destFilePath

                if (
                    ($file.Length -eq $destFile.Length) -and
                    ($file.LastWriteTimeUtc -le $destFile.LastWriteTimeUtc)
                ) {
                    $copyRequired = $false
                }
            }

            if ($copyRequired) {
                Write-LogMessage -LogPath $logPath -Message "copying $file to $destFilePath" -Level 5
                Copy-Item -Force $file.FullName $destFilePath
            }
            else {
                Write-LogMessage -LogPath $logPath -Message "skipping unmodified file $file" -Level 5
            }
        }
    }
    finally {
        Set-Location ..
    }
}
