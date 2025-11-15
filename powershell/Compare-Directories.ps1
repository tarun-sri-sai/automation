param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Path1,

    [Parameter(Mandatory = $true, Position = 1)]
    [string]$Path2
)

$cwd = (Get-Location).Path

Set-Location $Path1
$files1 = Get-ChildItem -Recurse -File -FollowSymlink | ForEach-Object { 
    Resolve-Path -Relative -Path $_.FullName
}
Set-Location $cwd

Set-Location $Path2
$files2 = Get-ChildItem -Recurse -File -FollowSymlink | ForEach-Object { 
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

$differentContent = @()
foreach ($file in $commonFiles) {
    $file1 = Join-Path -Path (Get-Item $Path1).FullName -ChildPath $file
    $hash1 = Get-FileHash -Path $file1 -Algorithm MD5

    $file2 = Join-Path -Path (Get-Item $Path2).FullName -ChildPath $file
    $hash2 = Get-FileHash -Path $file2 -Algorithm MD5

    if ($hash1.Hash -ne $hash2.Hash) {
        $differentContent += $file
    }
}

if ($differentContent.Count -gt 0) {
    $differentContent | ForEach-Object { 
        $minusFiles += $_
        $plusFiles += $_
    }
}

return @($minusFiles | Sort-Object | ForEach-Object { "- $_" }) + @($plusFiles | Sort-Object | ForEach-Object { "+ $_" }) 
