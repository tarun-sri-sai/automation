param (
    [parameter(Mandatory=$true)]
    [string]$FolderPath
)

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Encryption.psm1")

$password = Read-PasswordFromInput
$password | ConvertFrom-SecureString | Out-File (Join-Path "$FolderPath" "password.txt")
