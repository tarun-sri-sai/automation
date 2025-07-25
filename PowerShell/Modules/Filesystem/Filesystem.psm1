function Join-Paths {
    param (
        [Parameter(Mandatory = $true)]
        [string[]] $Paths
    )

    $joinedPaths = $Paths[0]
    for ($i = 1; $i -lt $Paths.Length; $i++) {
        $joinedPaths = Join-Path -Path $joinedPaths -ChildPath $Paths[$i]
    }

    return $joinedPaths
}

function Get-FilesToRemove {
    param (
        [string]$PathFilter,

        [int]$Versions = 5,

        [switch]$AsDays = $false
    )

    $files = Get-ChildItem $PathFilter | Sort-Object @{Expression = { $_.LastWriteTime.ToString("yyyyMMdd") }; }

    $totalFilesToRemove = @();

    if ($AsDays) {
        $groupedByDate = $files | Group-Object { $_.LastWriteTime.ToString("yyyyMMdd") } | Sort-Object @{Expression = { $_.Group[0].LastWriteTime.ToString("yyyyMMdd") }; Descending = $true }

        if ($groupedByDate.Count -gt $Versions) {
            $count = $groupedByDate.Count - $Versions
            $filesToRemove = $groupedByDate | Select-Object -Last $count | ForEach-Object { $_.Group } | Select-Object -ExpandProperty FullName
            foreach ($file in $filesToRemove) {
                $totalFilesToRemove += $file
            }
        }
    }
    else {
        if ($files.Count -gt $Versions) {
            $totalFilesToRemove = $files | Select-Object -First ($files.Count - $Versions) | Select-Object -ExpandProperty FullName
        }
    }

    return $totalFilesToRemove
}

Export-ModuleMember -Function Join-Paths, Get-FilesToRemove
