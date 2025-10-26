param (
    [Parameter(Mandatory = $true)]
    [string[]]$Paths,

    [Parameter(Mandatory = $true)]
    [string]$MountPath,

    [Parameter(Mandatory = $true)]
    [string]$PassFile,

    [int]$Versions = 5,

    [switch]$AsDays = $false,

    [int]$CompressionLevel = 5,

    [string]$ZipFileName = "",

    [string[]]$Exclude = @()
)

$ZipFileName = $ZipFileName.Trim()
if (0 -eq $ZipFileName.Length) {
    $ZipFileName = $(hostname)
}

Import-Module Logging
Import-Module Encryption
Import-Module Filesystem

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
$fileBaseName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Definition)
$logPath = Join-Path (Join-Path $thisDirectory "logs") "$fileBaseName.log"

try {
    $ext = "7z"
    $date = Get-Date -Format "yyyyMMddHHmmss"
    $zipFile = "${ZipFileName}_${date}.${ext}"
    if (Test-Path $zipFile) {
        Write-LogMessage -LogPath $logPath -Message "Removing existing zip file: ${zipFile}."
        Remove-Item -Force $zipFile
    }
    else {
        Write-LogMessage -LogPath $logPath -Message "Zip file: ${zipFile} does not exist."
    }

    foreach ($item in $Paths) {
        Write-LogMessage -LogPath $logPath -Message "Backing up item: ${item}." -Level 5
    }

    if ($Exclude) {
        $excludeOptions = $Exclude | ForEach-Object { "-xr!`"$_`"" }
        $excludeOptions = $excludeOptions -join " "
        Write-LogMessage -LogPath $logPath -Message "Parsed exclude options: $excludeOptions." -Level 5
    }
    else {
        $excludeOptions = ""
    }

    Write-LogMessage -LogPath $logPath "Reading password securely."
    $password = Get-PasswordFromFile -LogPath $logPath -PassFile $PassFile

    $itemList = $Paths -join ' '
    Write-LogMessage -LogPath $logPath -Message "Compressing to file: $zipFile."
    Invoke-Expression "7z a -mx=$CompressionLevel -p`"$password`" '$zipFile' $excludeOptions $itemList"

    Write-LogMessage -LogPath $logPath -Message "Moving zip file to $MountPath."
    Move-Item -Force $zipFile "$MountPath"

    $filesToRemove = Get-FilesToRemove -PathFilter (Join-Path $MountPath "${ZipFileName}*" ) -Versions $Versions -AsDays:$AsDays
    Write-LogMessage -LogPath $logPath -Message "Matched files with filter ${ZipFileName}: $($filesToRemove.Count)"

    foreach ($file in $filesToRemove) {
        Write-LogMessage -LogPath $logPath -Message "Removing old backup: $file." -Level 5        
        Remove-Item -Force $file
    }

    Write-LogMessage -LogPath $logPath -Message "Back up finished for $($Paths -join ', ') to $MountPath."
}
catch {
    Write-LogMessage -LogPath $logPath -Message "An error occurred while backing up items: $_." -Level 1
    Write-LogException -LogPath $LogPath -Exception $_
    exit 1
}
