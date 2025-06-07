param (
    [Parameter(Mandatory = $true)]
    [string]$ZipFileName,

    [string[]]$Exclude,

    [Parameter(Mandatory = $true)]
    [string[]]$Directories,

    [Parameter(Mandatory = $true)]
    [string]$MountPath,

    [int]$Versions = 5,

    [int]$CompressionLevel = 5
)

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path (Join-Path "$thisDirectory" "helpers") "Logging.psm1")
Import-Module (Join-Path (Join-Path "$thisDirectory" "helpers") "Encryption.psm1")

$logPath = Join-Path (Join-Path "$thisDirectory" "logs") "Backup-Directories.log"

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

foreach ($dir in $Directories) {
    Write-LogMessage -LogPath $logPath -Message "Backing up directory: ${dir}."
}

if ($Exclude) {
    $excludeOptions = $Exclude | ForEach-Object { "-xr!`"$_`"" }
    $excludeOptions = $excludeOptions -join " "
    Write-LogMessage -LogPath $logPath -Message "Parsed exclude options: $excludeOptions."
}
else {
    $excludeOptions = ""
}

Write-LogMessage -LogPath $logPath "Reading password securely."
$password = Get-PasswordFromFile (Join-Path (Join-Path $thisDirectory "inputs") "password.txt")

$directoryList = $Directories -join ' '
Write-LogMessage -LogPath $logPath -Message "Compressing to file: $zipFile."
Invoke-Expression "7z a -mx=$CompressionLevel -p`"$password`" '$zipFile' $excludeOptions $directoryList" | Out-Null

Write-LogMessage -LogPath $logPath -Message "Moving zip file to $MountPath."
Move-Item -Force $zipFile "$MountPath"

$files = Get-ChildItem -Path $MountPath -Filter "${ZipFileName}_*.${ext}" | Sort-Object LastWriteTime
$filesCount = $files.Count

if (($Versions -gt 0) -and ($filesCount -gt $Versions)) {
    Write-LogMessage -LogPath $logPath -Message "Deleting last $($filesCount - $Versions) versions."
    $filesToRemove = $files | Select-Object -First ($filesCount - $Versions)
    foreach ($file in $filesToRemove) {
        Write-LogMessage -LogPath $logPath -Message "Removing old backup: $($file.FullName)."
        Remove-Item -Force $file.FullName
    }
}

Write-LogMessage -LogPath $logPath -Message "Back up finished for $($Directories -join ', ') to $MountPath."
