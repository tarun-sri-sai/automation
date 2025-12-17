param(
    [Parameter(Mandatory=$true)]
    [string]$IsoDate,

    [Parameter(Mandatory=$true)]
    [string]$TimeZoneId
)

$dt = [datetimeoffset]::Parse($IsoDate)
$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById($TimeZoneId)
$converted = [System.TimeZoneInfo]::ConvertTime($dt, $tz)
return $converted.ToString("o")
