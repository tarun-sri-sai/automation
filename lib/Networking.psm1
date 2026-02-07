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
        StartIP    = $startIP
        IPCount    = $ipCount
        SkipFirst  = $skipFirst
        SkipLast   = $skipLast
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

function Get-NaturalSortKey {
    param($s)
    
    return (
        $s -split '(\d+)' | ForEach-Object {
            if ($_ -match '^\d+$') { '{0:D10}' -f [int]$_ } else { $_ }
        }
    ) -join ''
}

function Get-Subnet {
    param (
        [Parameter(Mandatory = $false)]
        [string]$Subnet = "192.168.0.0/24",
    
        [Parameter(Mandatory = $false)]
        [int]$ThrottleLimit = 100,

        [Parameter(Mandatory = $false)]
        [int]$Count = 1,

        [Parameter(Mandatory = $false)]
        [switch]$Unreachable,

        [Parameter(Mandatory = $false)]
        [switch]$All,

        [int]$Port = 0,

        [switch]$Hostnames = $false
    )

    $result = @()

    if (($Port -lt 0) -or ($Port -gt 0xFFFF)) {
        Write-Error "Invalid port provided: $Port"
        return $result
    }

    if ($Subnet -notmatch "/\d{1,2}$") {
        $Subnet = "$Subnet/24"
    }

    try {
        $range = ConvertTo-IPRange -CIDR $Subnet
        $totalIPs = $range.IPCount
        $startIP = $range.StartIP

        $allIPs = New-Object System.Collections.Generic.List[string]
        for ($i = $range.SkipFirst; $i -lt ($totalIPs + 1 - $range.SkipLast); $i++) {
            $allIPs.Add((ConvertTo-DottedDecimalIP -StartIP $startIP -Offset $i)) | Out-Null
        }

        if ($All) {
            $result = $allIPs | Sort-Object { Get-NaturalSortKey $_ }
        }
        else {
            Write-Host "Scanning subnet $Subnet ($totalIPs addresses)..."
    
            $reachableIPs = New-Object 'System.Collections.Concurrent.ConcurrentBag[string]'
            $progress = 0

            $scriptBlock = {
                param($ip, $count, $port, $reachableIPs)
        
                if ($port -gt 0) {
                    $tcp = New-Object System.Net.Sockets.TcpClient

                    try {
                        $connect = $tcp.ConnectAsync($ip, $port)

                        if ($connect.Wait(2000) -and $tcp.Connected) {
                            $reachableIPs.Add($ip)
                        }
                    }
                    catch {
                        Write-Error "port scan failed for [${ip}:$port]: $_"
                    }
                    finally {
                        $tcp.Dispose()
                    }
                }
                elseif (Test-Connection -ComputerName $ip -Count $count -Quiet) {
                    $reachableIPs.Add($ip)
                }
            }
    
            $runspacePool = [runspacefactory]::CreateRunspacePool(1, $ThrottleLimit)
            $runspacePool.Open()
    
            $runspaces = New-Object System.Collections.ArrayList
    
            for ($i = $range.SkipFirst; $i -lt ($totalIPs + 1 - $range.SkipLast); $i++) {
                $currentIP = ConvertTo-DottedDecimalIP -StartIP $startIP -Offset $i
        
                $completed = $runspaces | Where-Object { $_.Handle.IsCompleted -eq $true }
                while (($runspaces.Count -ge $ThrottleLimit) -and ($completed.Count -eq 0)) {
                    Start-Sleep -Milliseconds 100
                    $completed = $runspaces | Where-Object { $_.Handle.IsCompleted -eq $true }
                }

                foreach ($runspace in $completed) {
                    $runspace.PowerShell.EndInvoke($runspace.Handle)
                    $runspace.PowerShell.Dispose()
                    $runspaces.Remove($runspace)
            
                    $progress++
                    $percentComplete = [math]::Min(100, ($progress / $totalIPs) * 100)
                    Write-Progress -Activity "Scanning IP addresses" -Status "Checked $progress of $totalIPs IPs" -PercentComplete $percentComplete
                }

                $powerShell = [powershell]::Create().AddScript($scriptBlock).AddArgument($currentIP).AddArgument($Count).AddArgument($Port).AddArgument($reachableIPs)
                $powerShell.RunspacePool = $runspacePool
        
                $handle = $powerShell.BeginInvoke()
                $runspace = [PSCustomObject]@{
                    PowerShell = $powerShell
                    Handle     = $handle
                    IP         = $currentIP
                }
                [void]$runspaces.Add($runspace)
            }
    
            while ($runspaces.Count -gt 0) {
                $completed = $runspaces | Where-Object { $_.Handle.IsCompleted -eq $true }
                foreach ($runspace in $completed) {
                    $runspace.PowerShell.EndInvoke($runspace.Handle)
                    $runspace.PowerShell.Dispose()
                    $runspaces.Remove($runspace)
            
                    $progress++
                    $percentComplete = [math]::Min(100, ($progress / $totalIPs) * 100)
                    Write-Progress -Activity "Scanning IP addresses" -Status "Checked $progress of $totalIPs IPs" -PercentComplete $percentComplete
                }
        
                if ($runspaces.Count -gt 0) {
                    Start-Sleep -Milliseconds 100
                }
            }
    
            $runspacePool.Close()
            $runspacePool.Dispose()
    
            Write-Progress -Activity "Scanning IP addresses" -Completed

            if ($Unreachable) {
                $reachableSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
                foreach ($rip in $reachableIPs) { [void]$reachableSet.Add($rip) }

                $unreachableIPs = New-Object System.Collections.Generic.List[string]
                foreach ($ip in $allIPs) {
                    if (-not $reachableSet.Contains($ip)) { $unreachableIPs.Add($ip) | Out-Null }
                }

                Write-Host "Found $($unreachableIPs.Count) unreachable IP addresses."
                $result = $unreachableIPs | Sort-Object { Get-NaturalSortKey $_ }
            }
            else {
                Write-Host "Found $($reachableIPs.Count) reachable IP addresses."
                $result = $reachableIPs.ToArray() | Sort-Object { Get-NaturalSortKey $_ }
            }
        }

        if ($Hostnames) {
            Write-Host "Resolving hostnames for $($result.Count) IPs..."
            
            $dnsScriptBlock = {
                param($ip)
                try {
                    return [System.Net.Dns]::GetHostEntry($ip).HostName
                }
                catch {
                    return $ip
                }
            }

            $dnsRunspacePool = [runspacefactory]::CreateRunspacePool(1, $ThrottleLimit)
            $dnsRunspacePool.Open()
            $dnsRunspaces = New-Object System.Collections.ArrayList
            $lookupResults = @{}
            
            $processedCount = 0
            $totalCount = $result.Count
            
            foreach ($ip in $result) {
                $completed = $dnsRunspaces | Where-Object { $_.Handle.IsCompleted -eq $true }
                while (($dnsRunspaces.Count -ge $ThrottleLimit) -and ($completed.Count -eq 0)) {
                    Start-Sleep -Milliseconds 100
                    $completed = $dnsRunspaces | Where-Object { $_.Handle.IsCompleted -eq $true }
                }
                
                foreach ($runspace in $completed) {
                    $output = $runspace.PowerShell.EndInvoke($runspace.Handle)
                    $runspace.PowerShell.Dispose()
                    $dnsRunspaces.Remove($runspace)
                    
                    $lookupResults[$runspace.IP] = $output[0].ToString()
                    $processedCount++
                    
                    $percentComplete = [math]::Min(100, ($processedCount / $totalCount) * 100)
                    Write-Progress -Activity "Resolving Hostnames" -Status "Resolved $processedCount of $totalCount" -PercentComplete $percentComplete
                }

                $powerShell = [powershell]::Create().AddScript($dnsScriptBlock).AddArgument($ip)
                $powerShell.RunspacePool = $dnsRunspacePool
                $handle = $powerShell.BeginInvoke()
                
                $runspace = [PSCustomObject]@{
                    PowerShell = $powerShell
                    Handle     = $handle
                    IP         = $ip
                }
                [void]$dnsRunspaces.Add($runspace)
            }

            while ($dnsRunspaces.Count -gt 0) {
                $completed = $dnsRunspaces | Where-Object { $_.Handle.IsCompleted -eq $true }
                foreach ($runspace in $completed) {
                    $output = $runspace.PowerShell.EndInvoke($runspace.Handle)
                    $runspace.PowerShell.Dispose()
                    $dnsRunspaces.Remove($runspace)
                    
                    $lookupResults[$runspace.IP] = $output[0].ToString()
                    $processedCount++
                    
                    $percentComplete = [math]::Min(100, ($processedCount / $totalCount) * 100)
                    Write-Progress -Activity "Resolving Hostnames" -Status "Resolved $processedCount of $totalCount" -PercentComplete $percentComplete
                }
                
                if ($dnsRunspaces.Count -gt 0) {
                    Start-Sleep -Milliseconds 100
                }
            }
            
            $dnsRunspacePool.Close()
            $dnsRunspacePool.Dispose()
            Write-Progress -Activity "Resolving Hostnames" -Completed

            $resultHostnames = @()
            foreach ($ip in $result) {
                if ($lookupResults.ContainsKey($ip)) {
                    $resultHostnames += $lookupResults[$ip]
                } else {
                    $resultHostnames += $ip
                }
            }
            return $resultHostnames
        }

        return $result
    } 
    catch {
        Write-Error "Error scanning subnet: $_"
    }
}

Export-ModuleMember -Function Get-Subnet
