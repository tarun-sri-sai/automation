param (
    [Parameter(Mandatory = $true)]
    [string[]]$Paths,

    [Parameter(Mandatory = $true)]
    [string]$MountPath,

    [Parameter(Mandatory = $true)]
    [string]$CertPath,

    [int]$Versions = 5,

    [switch]$AsDays = $false,

    [int]$CompressionLevel = 5,

    [string]$ZipFileName = "",

    [string[]]$Exclude = @()
)

$ZipFileName = $ZipFileName.Trim()
if ($ZipFileName.Length -eq 0) {
    $ZipFileName = $(hostname)
}

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Logging.psm1")
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Filesystem.psm1")

$fileBaseName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Definition)
$logPath = Join-Path (Join-Path $thisDirectory "logs") "$fileBaseName.log"

try {
    $ext = "7z"
    $encExt = "enc"
    $date = Get-Date -Format "yyyyMMddHHmmss"
    $zipFile = "${ZipFileName}_${date}.${ext}"
    $encryptedFile = "$zipFile.${encExt}"

    if (Test-Path $encryptedFile) {
        Write-LogMessage -LogPath $logPath -Message "Removing existing zip file: ${encryptedFile}."
        Remove-Item -Force $zipFile
    }
    else {
        Write-LogMessage -LogPath $logPath -Message "Zip file: ${encryptedFile} does not exist."
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

    $itemList = $Paths -join ' '

    Write-LogMessage -LogPath $logPath -Message "Creating archive $zipFile."

    $scriptArgs = @("a", "-mx=$CompressionLevel", $zipFile, $excludeOptions, $itemList) | Where-Object { $_ -and $_.Trim() }
    Invoke-LoggedScriptBlock -LogPath $logPath -ScriptBlock {
        & 7z @scriptArgs
    }

    Write-LogMessage -LogPath $logPath -Message "Encrypting archive using certificate: $CertPath."
    Invoke-LoggedScriptBlock -LogPath $logPath -ScriptBlock {
        & openssl cms -encrypt -binary -aes256 -out $encryptedFile -outform DER -in $zipFile $CertPath
    }

    Write-LogMessage -LogPath $logPath -Message "Removing unencrypted archive."
    Remove-Item -Force $zipFile

    Write-LogMessage -LogPath $logPath -Message "Moving encrypted archive to $MountPath."
    Move-Item -Force $encryptedFile $MountPath

    $filesToRemove = Get-FilesToRemove -PathFilter (Join-Path $MountPath "${ZipFileName}*.${ext}.${encExt}") -Versions $Versions -AsDays:$AsDays
    Write-LogMessage -LogPath $logPath -Message "Matched files with filter ${ZipFileName}: $($filesToRemove.Count)"

    foreach ($file in $filesToRemove) {
        Write-LogMessage -LogPath $logPath -Message "Removing old backup: $file" -Level 5
        Remove-Item -Force $file
    }

    Write-LogMessage -LogPath $logPath -Message "Back up finished for $($Paths -join ', ') to $MountPath."
}
catch {
    Write-LogMessage -LogPath $logPath -Message "Backup failed: $_." -Level 1
    Write-LogException -LogPath $logPath -Exception $_
    exit 1
}
