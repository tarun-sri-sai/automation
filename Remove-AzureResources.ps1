param(
    [Parameter(Mandatory = $true)]
    [string]$AzureApp,

    [Parameter(Mandatory = $true)]
    [string]$Tenant,

    [Parameter(Mandatory = $true)]
    [string]$Subscription,

    [string]$TagName = "toBeDeleted",

    [string]$TagValue = "true",

    [switch]$Force = $false
)

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Encryption.psm1")
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Filesystem.psm1")
Import-Module (Join-Path (Join-Path "$thisDirectory" "lib") "Logging.psm1")

$fileBaseName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Definition)
$logPath = Join-Path (Join-Path $thisDirectory "logs") "$fileBaseName.log"

$passwordFile = Join-Paths $env:USERPROFILE, $AzureApp, 'password.txt'                                      # Assume password file is stored in %USERPROFILE%\<AzureApp>\password.txt
$password = Get-PasswordFromFile -LogPath $logPath -PassFile $passwordFile

$cred = New-Object System.Management.Automation.PSCredential(
    $AzureApp,
    (ConvertTo-SecureString -AsPlainText -Force $password)
)

Write-LogMessage -LogPath $logPath -Message "Connecting to Azure for tenant $Tenant with app $AzureApp."
Connect-AzAccount -ServicePrincipal -Credential $cred -Tenant $Tenant

Write-LogMessage -LogPath $logPath -Message "Setting Azure context to subscription $Subscription."
Set-AzContext -Subscription $Subscription

$resourceGroupIds = New-Object 'System.Collections.Generic.HashSet[string]'

foreach ($group in @(Get-AzResourceGroup)) {
    if (-not ($group.Tags -and ($group.Tags[$TagName] -eq $TagValue))) {
        continue
    }

    $resourceGroupIds.Add($group.ResourceId) | Out-Null

    $ToDelete = $Force
    if (-not $ToDelete) {
        while ($true) {
            $answer = Read-Host "Removing $($group.ResourceGroupName). Proceed? (y/N)"

            if ($answer.ToLower() -eq "y") {
                $ToDelete = $true
                break
            }
            elseif ($answer.ToLower() -eq "n" -or $answer -eq "") {
                break
            }
            else {
                Write-Host "Please answer 'y' or 'n'. Leaving blank will default to 'n'."
            }
        }
    }

    if ($ToDelete) {
        Write-LogMessage -LogPath $logPath -Message "Removing $($group.ResourceGroupName)..."
        Remove-AzResourceGroup -Name $group.ResourceGroupName -Force -AsJob
    }
}

# No need to prompt for individual resources that are tagged
foreach ($resource in @(Get-AzResource)) {
    if ($resource.ResourceId -in $resourceGroupIds) {
        continue
    }

    if (-not ($resource.Tags -and ($resource.Tags[$TagName] -eq $TagValue))) {
        continue
    }

    Write-LogMessage -LogPath $logPath -Message "Removing resource $($resource.Name) in RG $($resource.ResourceGroupName)..."
    Remove-AzResource -ResourceId $resource.ResourceId -Force -AsJob
}
