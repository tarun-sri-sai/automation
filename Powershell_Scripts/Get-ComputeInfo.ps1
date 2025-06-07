param (
    [int]$SampleCount = 3
)

$cpuTotal = 0
$ramTotal = 0

$os = Get-WmiObject -Class Win32_OperatingSystem

for ($i = 0; $i -lt $SampleCount; $i++) {
    $cpuSample = Get-Counter '\Processor(_Total)\% Processor Time'
    $cpuUsage = $cpuSample.CounterSamples.CookedValue
    $cpuTotal += $cpuUsage

    $totalRAM = [float]$os.TotalVisibleMemorySize / 1024  # in MB
    $freeRAM = [float]$os.FreePhysicalMemory / 1024       # in MB
    $usedRAM = $totalRAM - $freeRAM
    $ramTotal += $usedRAM

    Start-Sleep -Seconds 1
}

$avgCPU = [math]::Round($cpuTotal / $SampleCount, 2)
$avgRAM = [math]::Round($ramTotal / $SampleCount, 2)

@{
    CPU = "$avgCPU%"
    RAM = "$avgRAM MB"
}
