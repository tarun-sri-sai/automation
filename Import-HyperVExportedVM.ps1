<#
.SYNOPSIS
    Imports a Hyper-V virtual machine from an exported .vmcx file, assigns a new ID, renames the VM and its VHDX file to match the new VM name.

.PARAMETER ExportPath
    Full path to the exported VM's .vmcx file.
    Example: "C:\Exported VMs\MyVM\Virtual Machines\{GUID}.vmcx"

.PARAMETER NewName
    Desired display name for the imported VM. Also used as the new name for the VHDX file.

.PARAMETER DestPath
    Root destination folder where the VM files will be placed.
    Subfolders "Virtual Machines" and "Virtual Hard Disks" will be created under this path.

.EXAMPLE
    .\Import-HyperVExportedVM.ps1 -ExportPath "C:\Exported VMs\MyVM\Virtual Machines\{GUID}.vmcx" -NewName "NewVM01" -DestPath "C:\HyperV"
#>
param (
    [Parameter(Mandatory = $true)]
    [string]$ExportPath,

    [Parameter(Mandatory = $true)]
    [string]$NewName,

    [Parameter(Mandatory = $true)]
    [string]$DestPath
)

try {
    Write-Host "Starting VM import process..."
    $vmPath = Join-Path $DestPath "Virtual Machines"
    $vhdxPath = Join-Path $DestPath "Virtual Hard Disks"
    $newVhdName = "$NewName.vhdx"
    $newVhdPath = Join-Path $vhdxPath $newVhdName

    Write-Host "Importing VM from: $ExportPath"
    $vm = Import-VM -Path $ExportPath -Copy -GenerateNewId -VirtualMachinePath $vmPath -VhdDestinationPath $vhdxPath

    Write-Host "Renaming VM to: $NewName"
    Rename-VM -VM $vm -NewName $NewName

    Write-Host "Getting VHD information..."
    $vhd = Get-VMHardDiskDrive -VMName $NewName
    $oldVhdPath = $vhd.Path

    Write-Host "Renaming VHDX from '$oldVhdPath' to '$newVhdName'"
    Rename-Item -Path $oldVhdPath -NewName $newVhdName

    Write-Host "Updating VM to use renamed VHDX..."
    Set-VMHardDiskDrive -VMName $NewName -ControllerType $vhd.ControllerType -ControllerNumber $vhd.ControllerNumber -ControllerLocation $vhd.ControllerLocation -Path $newVhdPath

    Write-Host "VM import and configuration completed successfully."
}
catch {
    Write-Error $_
}
