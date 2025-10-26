param(
    [Parameter(Mandatory = $true)]
    [string] $LogFolder,

    [Parameter(Mandatory = $true)]
    [datetime] $StartTime,

    [Parameter(Mandatory = $true)]
    [datetime] $EndTime,

    [string] $OutputFile = "filtered.log",

    [string] $DateTimeFormat = 'yyyy-MM-dd HH:mm:ss',

    [string] $FileFilter = '*.log',

    [System.Globalization.CultureInfo] $Culture = $null,

    [switch]$Boundaries = $false
)

Write-Host "Getting logs between $StartTime and $EndTime"

$pattern = $DateTimeFormat -replace '([A-Za-z]+)', {
    "\d{$($_.Value.Length)}"
}
if ($Boundaries) {
    $pattern = "\b$pattern\b"
}
Write-Host "Pattern: $pattern"

foreach($file in (Get-ChildItem -Path $LogFolder -Recurse -Filter $FileFilter)) {
    $matchedLines = @()
    foreach($line in (Get-Content $file.FullName)) {
        if ($line -match $pattern) {
            $ts = [datetime]::ParseExact(
                "$($Matches[0])",
                $DateTimeFormat,
                $Culture
            )
            if ($ts -ge $StartTime -and $ts -le $EndTime) {
                $matchedLines += $line
            }
        }
    }
    if ($matchedLines) {
        Write-Host "Found matches in: $($file.FullName)"
        $separator = "*" * 32
        Add-Content -Encoding utf8 -Path $OutputFile -Value "$separator`n$($file.Name)`n$separator"
        Add-Content -Encoding utf8 -Path $OutputFile -Value $matchedLines
    }
}
