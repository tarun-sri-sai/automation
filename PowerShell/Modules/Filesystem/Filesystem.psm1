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

Export-ModuleMember -Function Join-Paths
