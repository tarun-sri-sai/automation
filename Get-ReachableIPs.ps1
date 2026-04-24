param (
    [Parameter(Mandatory = $false)]
    [string]$Subnet = "192.168.0.0/24",
    
    [Parameter(Mandatory = $false)]
    [int]$ThrottleLimit = 100,

    [Parameter(Mandatory = $false)]
    [int]$Count = 1,

    [Parameter(Mandatory = $false)]
    [switch]$Unreachable,

    [int]$Port = 0,

    [switch]$Hostnames = $false
)

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Networking.psm1")

Get-Subnet -Subnet $Subnet -ThrottleLimit $ThrottleLimit -Count $Count -Unreachable:$Unreachable -Port $Port -Hostnames:$Hostnames
