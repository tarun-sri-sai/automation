Write-Output "--- CPU ---"

$cpu = Get-CimInstance Win32_Processor |
    Measure-Object -Property LoadPercentage -Average |
    Select-Object -ExpandProperty Average

Write-Output ("Usage: {0}%" -f $cpu)

Write-Output "--- Memory ---"

$os = Get-CimInstance Win32_OperatingSystem

$totalGB = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
$freeGB  = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
$usedGB  = [math]::Round($totalGB - $freeGB, 2)

Write-Output ("Total: {0} GB  Used: {1} GB  Free: {2} GB" -f $totalGB, $usedGB, $freeGB)
