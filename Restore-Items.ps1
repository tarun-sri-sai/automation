param (
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,

    [Parameter(Mandatory = $true)]
    [string]$GpgRecipient,

    [Parameter(Mandatory = $true)]
    [string]$Destination
)

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path (Join-Path $thisDirectory "lib") "Logging.psm1")

$fileBaseName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Definition)
$logPath = Join-Path (Join-Path $thisDirectory "logs") "$fileBaseName.log"

try {
    Write-LogMessage -LogPath $logPath -Message "Starting restore from $BackupPath."

    $encryptedFile = Get-Item -Path $BackupPath
    if (-not $encryptedFile) {
        throw "No encrypted backup found at $BackupPath."
    }

    Write-LogMessage -LogPath $logPath -Message "Found encrypted file: $($encryptedFile.FullName)."

    $decryptedArchive = (Join-Path $encryptedFile.Directory $encryptedFile.BaseName)

    Write-LogMessage -LogPath $logPath -Message "Decrypting archive using certificate and private key."
    & gpg -r $GpgRecipient --decrypt --output $decryptedArchive $encryptedFile.FullName

    if (-not (Test-Path $decryptedArchive)) {
        throw "Decryption failed. Output file not created."
    }

    Write-LogMessage -LogPath $logPath -Message "Decryption successful: $decryptedArchive."

    if (-not (Test-Path $Destination)) {
        New-Item -ItemType Directory -Path $Destination | Out-Null
    }

    Write-LogMessage -LogPath $logPath -Message "Extracting archive to $Destination."
    & 7z x $decryptedArchive -y "-o$Destination"

    Write-LogMessage -LogPath $logPath -Message "Extraction completed."

    Write-LogMessage -LogPath $logPath -Message "Removing decrypted archive."
    Remove-Item -Force $decryptedArchive

    Write-LogMessage -LogPath $logPath -Message "Restore completed successfully."
} catch {
    Write-LogMessage -LogPath $logPath -Message "Restore failed: $_" -Level 1
    Write-LogException -LogPath $logPath -Exception $_
    exit 1
}
