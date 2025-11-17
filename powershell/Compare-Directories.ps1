param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Path1,

    [Parameter(Mandatory = $true, Position = 1)]
    [string]$Path2,

    [switch]$FollowSymlink = $false,

    [int]$ThrottleLimit = 10
)

function Get-AllItems() {
    if ($FollowSymlink) {
        return Get-ChildItem -Recurse -File -FollowSymlink
    } else {
        return Get-ChildItem -Recurse -File
    }
}

$cwd = (Get-Location).Path

Set-Location $Path1
$files1 = Get-AllItems | ForEach-Object { 
    Resolve-Path -Relative -Path $_.FullName
}
Set-Location $cwd

Set-Location $Path2
$files2 = Get-AllItems | ForEach-Object { 
    Resolve-Path -Relative -Path $_.FullName
}
Set-Location $cwd

$files2Set = [System.Collections.Generic.HashSet[string]]::new()
foreach ($file in $files2) {
    $files2Set.Add($file) | Out-Null
}

$commonFiles = [System.Collections.Generic.HashSet[string]]::new()
foreach ($file in $files1) {
    if ($file -in $files2Set) {
        $commonFiles.Add($file) | Out-Null
    }
}

$minusFiles = @($files1 | Where-Object { $_ -notin $commonFiles })
$plusFiles = @($files2 | Where-Object { $_ -notin $commonFiles })

$differentContent = New-Object 'System.Collections.Concurrent.ConcurrentBag[string]'

$runspacePool = [runspacefactory]::CreateRunspacePool(1, $ThrottleLimit)
$runspacePool.Open()
$runspaces = New-Object System.Collections.ArrayList

$scriptBlock = {
    param($file, $Path1, $Path2, $differentContent)

    $file1 = Join-Path -Path (Get-Item $Path1).FullName -ChildPath $file
    $file2 = Join-Path -Path (Get-Item $Path2).FullName -ChildPath $file

    if ((Test-Path $file1) -and (Test-Path $file2)) {
        $hash1 = Get-FileHash -Path $file1 -Algorithm MD5
        $hash2 = Get-FileHash -Path $file2 -Algorithm MD5
        if ($hash1.Hash -ne $hash2.Hash) {
            $differentContent.Add($file)
        }
    }
}

foreach ($file in $commonFiles) {
    $ps = [powershell]::Create().AddScript($scriptBlock).
        AddArgument($file).
        AddArgument($Path1).
        AddArgument($Path2).
        AddArgument($differentContent)
    $ps.RunspacePool = $runspacePool
    $handle = $ps.BeginInvoke()
    $runspace = [PSCustomObject]@{
        PowerShell = $ps
        Handle     = $handle
        File       = $file
    }
    [void]$runspaces.Add($runspace)
}

while ($runspaces.Count -gt 0) {
    $completed = $runspaces | Where-Object { $_.Handle.IsCompleted }
    foreach ($r in $completed) {
        $r.PowerShell.EndInvoke($r.Handle)
        $r.PowerShell.Dispose()
        $runspaces.Remove($r)
    }
    if ($runspaces.Count -gt 0) {
        Start-Sleep -Milliseconds 100
    }
}

$runspacePool.Close()
$runspacePool.Dispose()

if ($differentContent.Count -gt 0) {
    $differentContent.ToArray() | ForEach-Object { 
        $minusFiles += $_
        $plusFiles += $_
    }
}

return @($minusFiles | Sort-Object | ForEach-Object { "- $_" }) + @($plusFiles | Sort-Object | ForEach-Object { "+ $_" }) 
