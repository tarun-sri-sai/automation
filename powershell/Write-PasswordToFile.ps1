param (
    [parameter(Mandatory=$true)]
    [string]$FolderPath
)

Import-Module Encryption

$password = Read-PasswordFromInput
$password | ConvertFrom-SecureString | Out-File (Join-Path "$FolderPath" "password.txt")
