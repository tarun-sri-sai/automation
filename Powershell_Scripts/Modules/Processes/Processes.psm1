$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path "$thisDirectory" "Logging.psm1")

function Stop-Processes {
    param (
        [Parameter(Mandatory = $true)]
        [string] $LogPath,
    
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    try {
        $processes = Get-Process -Name "$Name" -ErrorAction SilentlyContinue
        if ($processes) {
            $processes | ForEach-Object {
                Stop-Process -Id $_.Id -Force -ErrorAction Stop
            }
     
            Write-LogMessage -LogPath $logPath -Message "$(${processes}.Length) $Name processes have been killed."
        }
        else {
            Write-LogMessage -LogPath $logPath -Message "No $Name processes found."
        }
    }
    catch {
        Write-LogMessage -LogPath $logPath -Message "An error occurred while stopping ${name}: $_." -Level 1
        exit 1
    }
}

Export-ModuleMember -Function Stop-Processes
