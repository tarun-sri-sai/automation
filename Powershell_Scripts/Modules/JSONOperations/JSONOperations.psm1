function Invoke-JQUpdate {
    param (
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $true)]
        [string]$Operation
    )

    $inputContent = jq "$Operation" "$FilePath"
    Set-Content -Path $FilePath -Value $inputContent
}

Export-ModuleMember -Function Invoke-JQUpdate
