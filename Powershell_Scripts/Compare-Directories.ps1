param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Path1,

    [Parameter(Mandatory = $true, Position = 1)]
    [string]$Path2
)

$cwd = (Get-Location).Path

Set-Location $Path1
$files1 = Get-ChildItem -Recurse -File | ForEach-Object { 
    [PSCustomObject]@{
        AbsolutePath = $_.FullName;
        RelativePath = Resolve-Path -Relative -Path $_.FullName
    }
}
Set-Location $cwd

Set-Location $Path2
$files2 = Get-ChildItem -Recurse -File | ForEach-Object { 
    [PSCustomObject]@{
        AbsolutePath = $_.FullName;
        RelativePath = Resolve-Path -Relative -Path $_.FullName
    }
}
Set-Location $cwd

$commonFiles = $files1 | Where-Object { $_.RelativePath -in $files2.RelativePath }

$diff1 = $files1 | Where-Object { $_.RelativePath -notin $commonFiles.RelativePath }
$diff2 = $files2 | Where-Object { $_.RelativePath -notin $commonFiles.RelativePath }

if ($diff1) {
    Write-Output "Files only in ${Path1}:"
    $diff1 | ForEach-Object { Write-Output $_.RelativePath }
    Write-Output ""
}

if ($diff2) {
    Write-Output "Files only in ${Path2}:"
    $diff2 | ForEach-Object { Write-Output $_.RelativePath }
    Write-Output ""
}

$differentContent = @()
foreach ($file in $commonFiles) {
    $file1 = $file.AbsolutePath
    $file2 = ($files2 | Where-Object { $_.RelativePath -eq $file.RelativePath }).AbsolutePath

    $hash1 = Get-FileHash -Path $file1 -Algorithm SHA256
    $hash2 = Get-FileHash -Path $file2 -Algorithm SHA256

    if ($hash1.Hash -ne $hash2.Hash) {
        $differentContent += $file.RelativePath
    }
}

if ($differentContent) {
    Write-Output "Files with different content:"
    $differentContent | ForEach-Object { Write-Output $_ }
    Write-Output ""
}
