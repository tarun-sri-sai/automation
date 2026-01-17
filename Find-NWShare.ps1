param (
    [Parameter(Mandatory = $true)]
    [string]$FolderName,

    [Parameter(Mandatory = $true)]
    [pscredential]$Credential,

    [Parameter(Mandatory = $false)]
    [string]$Subnet = "192.168.0.0/24",

    [Parameter(Mandatory = $false)]
    [int]$ThrottleLimit = 50,

    [Parameter(Mandatory = $false)]
    [int]$Count = 1
)

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Networking.psm1")

$reachableIPs = Get-Subnet -Subnet $Subnet -Count $Count -ThrottleLimit $ThrottleLimit

$results = New-Object 'System.Collections.Concurrent.ConcurrentBag[string]'

$scriptBlock = {
    param (
        [Parameter(Mandatory = $true)]
        [string]$ip,
        
        [Parameter(Mandatory = $true)]
        [pscredential]$credential, 
        
        [Parameter(Mandatory = $true)]
        [string]$folderName, 
        
        [Parameter(Mandatory = $true)]
        [System.Collections.ArrayList] $resultBag
    )

    function Test-SWLibraryShare {
        param (
            [Parameter(Mandatory = $true)]
            [string]$IPAddress,

            [Parameter(Mandatory = $true)]
            [pscredential]$Credential,

            [Parameter(Mandatory = $true)]
            [string]$FolderName
        )

        # First check if SMB port (445) is open
        if (-not (Test-NetConnection -ComputerName $IPAddress -Port 445 -InformationLevel Quiet)) {
            return $false
        }

        $sharePath = "\\$IPAddress\$FolderName"
        $driveName = "Z$([Guid]::NewGuid().ToString('N').Substring(0,6))"

        try {
            New-PSDrive -Name $driveName `
                -PSProvider FileSystem `
                -Root $sharePath `
                -Credential $Credential `
                -ErrorAction Stop | Out-Null

            Test-Path "${driveName}:\"
        }
        catch {
            $false
        }
        finally {
            if (Get-PSDrive -Name $driveName -ErrorAction SilentlyContinue) {
                Remove-PSDrive -Name $driveName -Force
            }
        }
    }

    if (Test-SWLibraryShare -IPAddress $ip -Credential $credential -FolderName $folderName) {
        Write-Host "IP found with ${folderName}: $ip"
        $resultBag.Add($ip)
    }
}

$pool = [runspacefactory]::CreateRunspacePool(1, $ThrottleLimit)
$pool.Open()

$runspaces = New-Object System.Collections.ArrayList

$total = $reachableIPs.Count
$completedCount = 0

foreach ($ip in $reachableIPs) {
    $ps = [powershell]::Create().
    AddScript($scriptBlock).
    AddArgument($ip).
    AddArgument($Credential).
    AddArgument($FolderName).
    AddArgument($results)

    $ps.RunspacePool = $pool

    $handle = $ps.BeginInvoke()
    [void]$runspaces.Add([pscustomobject]@{
            PowerShell = $ps
            Handle     = $handle
        })
}

Write-Progress `
    -Activity "Scanning network shares" `
    -Status "Checked $completedCount of $total IPs" `
    -PercentComplete (($completedCount / $total) * 100)

while ($runspaces.Count -gt 0) {
    $completed = $runspaces | Where-Object { $_.Handle.IsCompleted }

    foreach ($r in $completed) {
        $r.PowerShell.EndInvoke($r.Handle)
        $r.PowerShell.Dispose()
        $runspaces.Remove($r)

        $completedCount++
        Write-Progress `
            -Activity "Scanning network shares" `
            -Status "Checked $completedCount of $total IPs" `
            -PercentComplete (($completedCount / $total) * 100)
    }

    if ($runspaces.Count -gt 0) {
        Start-Sleep -Milliseconds 100
    }
}

Write-Progress -Activity "Scanning network shares" -Completed

$pool.Close()
$pool.Dispose()

$results.ToArray() | Sort-Object { Get-NaturalSortKey $_ }
