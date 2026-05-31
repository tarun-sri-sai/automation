function Write-LogMessage {
    param (
        [Parameter(Mandatory = $true)]
        [string] $LogPath,

        [Parameter(Mandatory = $true)]
        [string] $Message,

        [int] $Level = 4
    )

    $levels = @{
        1 = 'CRITICAL'
        2 = 'ERROR'
        3 = 'WARN'
        4 = 'INFO'
        5 = 'DEBUG'
    }
    if (-not $levels.ContainsKey($Level)) {
        $Level = 4
    }

    $logDir = Split-Path $LogPath -Parent
    if ($logDir -and -not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }

    $maxSize = 5MB
    try {
        if (Test-Path $LogPath) {
            $item = Get-Item $LogPath

            if ($item.Length -ge $maxSize) {
                Move-Item $LogPath "$LogPath.1" -Force
            }
        }
    } catch {
        Write-Warning "Log rotation failed: $_"
    }

    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logLine = '{0} - {1} - {2}' -f $timestamp, $levels[$Level], $Message

    switch ($Level) {
        1 { Write-Error $logLine }
        2 { Write-Error $logLine }
        3 { Write-Warning $logLine }
        4 { Write-Information $logLine -InformationAction Continue }
        5 { Write-Verbose $logLine }
    }

    $fs = [System.IO.FileStream]::new(
        $LogPath,
        [System.IO.FileMode]::Append,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::Read
    )
    try {
        $sw = [System.IO.StreamWriter]::new(
            $fs,
            [System.Text.UTF8Encoding]::new($false)
        )
        try {
            $sw.WriteLine($logLine)
        } finally {
            $sw.Dispose()
        }
    } finally {
        $fs.Dispose()
    }
}

function Get-CommandOutput {
    param (
        [Parameter(Mandatory = $true)]
        [ScriptBlock]$ScriptBlock
    )

    $output = @(& $ScriptBlock 2>&1)

    $result = @()
    foreach ($item in $output) {
        if ($item -is [System.Management.Automation.ErrorRecord]) {
            $result += $item.Exception.Message
        } else {
            $result += $item
        }
    }

    return $result -join "`n"
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
        $output = (Get-CommandOutput -ScriptBlock $ScriptBlock) -join "`n"
        Write-LogMessage -LogPath $LogPath -Message "$($ScriptBlock.ToString().Trim()): $output" -Level $Level
    } catch {
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

Export-ModuleMember -Function Write-LogMessage, Invoke-LoggedScriptBlock, Write-LogException, Get-CommandOutput
