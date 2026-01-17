param (
    [parameter(Mandatory=$true)]
    [string]$FolderPath
)

Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Encryption.psm1")

$password = Read-PasswordFromInput
$password | ConvertFrom-SecureString | Out-File (Join-Path "$FolderPath" "password.txt")
