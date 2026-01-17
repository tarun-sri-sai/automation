param (
    [int]$ValidityDays = 24 * 30
)

$password = Read-Host -AsSecureString "Enter password to protect your certificate"
$subjectName = Read-Host "Enter certificate subject name (e.g., CN=YourAppName)"

$certOutputPath = "$PWD\AzureCertificates"
$publicKeyPath = "$certOutputPath\PublicKeys"
$privateKeyPath = "$certOutputPath\PrivateKeys"
foreach ($path in @($certOutputPath, $publicKeyPath, $privateKeyPath)) {
    if (!(Test-Path $path)) { New-Item -ItemType Directory -Path $path -Force | Out-Null }
}

$cert = New-SelfSignedCertificate -Subject $subjectName -CertStoreLocation "Cert:\CurrentUser\My" `
    -KeyExportPolicy Exportable -KeySpec Signature -KeyLength 2048 -KeyAlgorithm RSA `
    -HashAlgorithm SHA256 -NotAfter (Get-Date).AddDays([int]$ValidityDays)

$thumbprint = $cert.Thumbprint
$publicKeyFile = "$publicKeyPath\$thumbprint.cer"
$pfxFilePath = "$privateKeyPath\$thumbprint.pfx"
Export-Certificate -Cert $cert -FilePath $publicKeyFile -Type CERT | Out-Null
Export-PfxCertificate -Cert $cert -FilePath $pfxFilePath -Password $password -Force | Out-Null
Remove-Item -Path "Cert:\CurrentUser\My\$thumbprint" -Force

Write-Host "Certificate created with thumbprint: $thumbprint" -ForegroundColor Green
Write-Host "Public key: $publicKeyFile" -ForegroundColor Green
Write-Host "Private key: $pfxFilePath" -ForegroundColor Green

return @{ Thumbprint = $thumbprint; PublicKeyPath = $publicKeyFile; PrivateKeyPath = $pfxFilePath }
