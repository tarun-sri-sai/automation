param (
    [Parameter(Mandatory=$false)]
    [string]$Subnet = "192.168.0.0/24",
    
    [Parameter(Mandatory=$false)]
    [int]$ThrottleLimit = 100,

    [Parameter(Mandatory=$false)]
    [int]$Count = 1
)

function ConvertTo-IPRange {
    param (
        [string]$CIDR
    )
    
    if ($CIDR -notmatch "^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$") {
        throw "Invalid CIDR format. Expected format: xxx.xxx.xxx.xxx/xx"
    }
    
    $ipPart = $CIDR.Split('/')[0]
    $maskLength = [int]$CIDR.Split('/')[1]
    
    if ($maskLength -lt 0 -or $maskLength -gt 32) {
        throw "Invalid subnet mask length. It must be between 0 and 32."
    }
    
    $ipBytes = $ipPart.Split('.') | ForEach-Object { [byte]$_ }
    $ip = ([byte[]]$ipBytes[0..3] | ForEach-Object { [Convert]::ToString($_, 2).PadLeft(8, '0') }) -join ''
    
    $networkBits = $ip.Substring(0, $maskLength)
    $hostBits = '0' * (32 - $maskLength)
    
    $hostBitsCount = 32 - $maskLength
    $ipCount = [Math]::Pow(2, $hostBitsCount) - 2
    
    if ($ipCount -le 0) {
        $ipCount = [Math]::Pow(2, $hostBitsCount)
    }
    
    $startIP = ConvertFrom-BinaryIP ($networkBits + $hostBits)
    
    $skipFirst = 0
    $skipLast = 0
    
    if ($maskLength -lt 31) {
        $skipFirst = 1
        $skipLast = 1
    }
    
    return @{
        StartIP = $startIP
        IPCount = $ipCount
        SkipFirst = $skipFirst
        SkipLast = $skipLast
        MaskLength = $maskLength
    }
}

function ConvertFrom-BinaryIP {
    param (
        [string]$BinaryIP
    )
    
    $octets = @(
        [Convert]::ToInt32($BinaryIP.Substring(0, 8), 2),
        [Convert]::ToInt32($BinaryIP.Substring(8, 8), 2),
        [Convert]::ToInt32($BinaryIP.Substring(16, 8), 2),
        [Convert]::ToInt32($BinaryIP.Substring(24, 8), 2)
    )
    
    return $octets -join '.'
}

function ConvertTo-DottedDecimalIP {
    param (
        [string]$StartIP,
        [int]$Offset
    )
    
    $octets = $StartIP.Split('.')
    $ipValue = ([int]$octets[0] * 16777216) + ([int]$octets[1] * 65536) + ([int]$octets[2] * 256) + [int]$octets[3]
    $ipValue += $Offset
    
    $o1 = [Math]::Floor($ipValue / 16777216) % 256
    $o2 = [Math]::Floor($ipValue / 65536) % 256
    $o3 = [Math]::Floor($ipValue / 256) % 256
    $o4 = $ipValue % 256
    
    return "$o1.$o2.$o3.$o4"
}

if ($Subnet -notmatch "/\d{1,2}$") {
    $Subnet = "$Subnet/24"
}

try {
    $range = ConvertTo-IPRange -CIDR $Subnet
    $totalIPs = $range.IPCount
    $startIP = $range.StartIP
    
    Write-Host "Scanning subnet $Subnet ($totalIPs addresses)..."
    
    $reachableIPs = New-Object 'System.Collections.Concurrent.ConcurrentBag[string]'
    $progress = 0
    $progressLock = New-Object 'System.Threading.Mutex'
    
    $scriptBlock = {
        param($ip, $count, $reachableIPs)
        
        if (Test-Connection -ComputerName $ip -Count $count -Quiet) {
            $reachableIPs.Add($ip)
        }
    }
    
    $runspacePool = [runspacefactory]::CreateRunspacePool(1, $ThrottleLimit)
    $runspacePool.Open()
    
    $runspaces = New-Object System.Collections.ArrayList
    
    for ($i = $range.SkipFirst; $i -lt ($totalIPs + 1 - $range.SkipLast); $i++) {
        $currentIP = ConvertTo-DottedDecimalIP -StartIP $startIP -Offset $i
        
        $powerShell = [powershell]::Create().AddScript($scriptBlock).AddArgument($currentIP).AddArgument($Count).AddArgument($reachableIPs)
        $powerShell.RunspacePool = $runspacePool
        
        $handle = $powerShell.BeginInvoke()
        $runspace = [PSCustomObject]@{
            PowerShell = $powerShell
            Handle = $handle
            IP = $currentIP
        }
        [void]$runspaces.Add($runspace)
        
        $completed = $runspaces | Where-Object { $_.Handle.IsCompleted -eq $true }
        foreach ($runspace in $completed) {
            $runspace.PowerShell.EndInvoke($runspace.Handle)
            $runspace.PowerShell.Dispose()
            $runspaces.Remove($runspace)
            
            $progressLock.WaitOne() | Out-Null
            $progress++
            $percentComplete = [math]::Min(100, ($progress / $totalIPs) * 100)
            Write-Progress -Activity "Scanning IP addresses" -Status "Checked $progress of $totalIPs IPs" -PercentComplete $percentComplete
            $progressLock.ReleaseMutex()
        }
    }
    
    while ($runspaces.Count -gt 0) {
        $completed = $runspaces | Where-Object { $_.Handle.IsCompleted -eq $true }
        foreach ($runspace in $completed) {
            $runspace.PowerShell.EndInvoke($runspace.Handle)
            $runspace.PowerShell.Dispose()
            $runspaces.Remove($runspace)
            
            $progressLock.WaitOne() | Out-Null
            $progress++
            $percentComplete = [math]::Min(100, ($progress / $totalIPs) * 100)
            Write-Progress -Activity "Scanning IP addresses" -Status "Checked $progress of $totalIPs IPs" -PercentComplete $percentComplete
            $progressLock.ReleaseMutex()
        }
        
        if ($runspaces.Count -gt 0) {
            Start-Sleep -Milliseconds 100
        }
    }
    
    $runspacePool.Close()
    $runspacePool.Dispose()
    
    Write-Progress -Activity "Scanning IP addresses" -Completed
    
    Write-Host "Found $($reachableIPs.Count) reachable IP addresses."
    return $reachableIPs.ToArray() | Sort-Object
} 
catch {
    Write-Error "Error scanning subnet: $_"
}
