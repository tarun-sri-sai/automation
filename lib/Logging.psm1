function Write-LogMessage {
    param (
        [Parameter(Mandatory = $true)]
        [string] $LogPath,

        [Parameter(Mandatory = $true)]
        [string] $Message,
        
        [int]$Level = 4
    )

    $maxSize = 5MB
    if (Test-Path $LogPath) {
        $size = (Get-Item $LogPath).Length
        if ($size -ge $maxSize) {
            Move-Item $LogPath "$LogPath.1" -Force # keep only one version for now
            Remove-Item $LogPath -Force
        }
    }

    $loggingLevels = @("CRITICAL", "ERROR", "WARN", "INFO", "DEBUG")
    if (($Level -lt 1) -or ($Level -gt $loggingLevels.Length)) {
        $Level = 4  # Default to INFO if wrong level is provided
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $prefix = "${timestamp} - $($loggingLevels[$Level - 1])"

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

function Invoke-LoggedScriptBlock {
    param (
        [Parameter(Mandatory = $true)]
        [ScriptBlock]$ScriptBlock,

        [Parameter(Mandatory = $true)]
        [string]$LogPath,

        [int]$Level = 5
    )

    try {
        $output = & $ScriptBlock 2>&1
        Write-LogMessage -LogPath $LogPath -Message "$($ScriptBlock.ToString().Trim()): $output" -Level $Level
    }
    catch {
        Write-LogMessage -LogPath $LogPath -Message "$($ScriptBlock.ToString().Trim()): ERROR - $($_.Exception.Message)" -Level 2
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

Export-ModuleMember -Function Write-LogMessage, Invoke-LoggedScriptBlock, Write-LogException
