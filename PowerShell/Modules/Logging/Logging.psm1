function Write-LogMessage {
    param (
        [Parameter(Mandatory = $true)]
        [string] $LogPath,

        [Parameter(Mandatory = $true)]
        [string] $Message,
        
        [int]$Level = 4
    )

    $LoggingLevels = @("CRITICAL", "ERROR", "WARN", "INFO", "DEBUG")
    if (($Level -lt 1) -or ($Level -gt $LoggingLevels.Length)) {
        $Level = 4  # Default to INFO if wrong level is provided
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $prefix = "${timestamp} - $($LoggingLevels[$Level - 1])"

    $logLine = "${prefix}`t${Message}"

    Write-Host $logLine

    $fs = [System.IO.File]::Open($LogPath, 'Append', 'Write', 'ReadWrite')
    $sw = New-Object System.IO.StreamWriter($fs)
    try {
        $sw.WriteLine($logLine)
    }
    catch {}
    finally {
        $sw.Close()
        $fs.Close()
    }
}

function Invoke-LoggedExpression {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Command,

        [Parameter(Mandatory = $true)]
        [string]$LogPath,

        [int]$Level = 5
    )

    try {
        $output = Invoke-Expression "$Command 2>&1"
        Write-LogMessage -LogPath $LogPath -Message "${Command}: $output" -Level $Level
    }
    catch {
        Write-LogMessage -LogPath $LogPath -Message "${Command}: ERROR - $($_.Exception.Message)" -Level 2
        throw $_
    }
}

function Write-LogException {
    param (
        [Parameter(Mandatory = $true)]
        [string]$LogPath,

        [Parameter(Mandatory = $true)]
        [System.Management.Automation.ErrorRecord]$Exception
    )

    Write-LogMessage -LogPath $LogPath -Message "Error Type: $($Exception.GetType().FullName)"
    Write-LogMessage -LogPath $LogPath -Message "Error Message: $($Exception.Exception.Message)"
    Write-LogMessage -LogPath $LogPath -Message "Exception .NET StackTrace:`n$($Exception.Exception.StackTrace)"
    Write-LogMessage -LogPath $LogPath -Message "PowerShell ScriptStackTrace:`n$($Exception.ScriptStackTrace)"
}

Export-ModuleMember -Function Write-LogMessage, Invoke-LoggedExpression, Write-LogException
