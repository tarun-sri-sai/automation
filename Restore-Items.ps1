param (
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,

    [Parameter(Mandatory = $true)]
    [string]$CertPath,

    [Parameter(Mandatory = $true)]
    [string]$KeyPath,

    [Parameter(Mandatory = $true)]
    [string]$Destination
)

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path (Join-Path $thisDirectory "lib") "Logging.psm1")

$fileBaseName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Definition)
$logPath = Join-Path (Join-Path $thisDirectory "logs") "$fileBaseName.log"

try {
    Write-LogMessage -LogPath $logPath -Message "Starting restore from $BackupPath."

    $encryptedFile = Get-ChildItem -Path $BackupPath -Filter "*.7z.enc" |
    Sort-Object LastWriteTime |
    Select-Object -Last 1

    if (-not $encryptedFile) {
        throw "No encrypted backup (*.7z.enc) found in $BackupPath."
    }

    Write-LogMessage -LogPath $logPath -Message "Found encrypted file: $($encryptedFile.FullName)."

    $decryptedZip = $encryptedFile.FullName -replace ".enc", ""

    Write-LogMessage -LogPath $logPath -Message "Decrypting archive using certificate and private key."
    & openssl cms -decrypt -binary -inform DER -in $encryptedFile.FullName -out $decryptedZip -recip $CertPath -inkey $KeyPath

    if (-not (Test-Path $decryptedZip)) {
        throw "Decryption failed. Output file not created."
    }

    Write-LogMessage -LogPath $logPath -Message "Decryption successful: $decryptedZip."

    if (-not (Test-Path $Destination)) {
        New-Item -ItemType Directory -Path $Destination | Out-Null
    }

    Write-LogMessage -LogPath $logPath -Message "Extracting archive to $Destination."
    & 7z x $decryptedZip -y "-o$Destination"

    Write-LogMessage -LogPath $logPath -Message "Extraction completed."

    Write-LogMessage -LogPath $logPath -Message "Removing decrypted archive."
    Remove-Item -Force $decryptedZip

    Write-LogMessage -LogPath $logPath -Message "Restore completed successfully."
}
catch {
    Write-LogMessage -LogPath $logPath -Message "Restore failed: $_" -Level 1
    Write-LogException -LogPath $logPath -Exception $_
    exit 1
}
