$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
Import-Module (Join-Path "$thisDirectory" "Logging.psm1")

function Add-Patch {
    param (
        [Parameter(Mandatory = $true)]
        [string] $LogPath,
        
        [Parameter(Mandatory = $true)]
        [string]$PatchFilePath,

        [Parameter(Mandatory = $true)]
        [string]$RepoPath
    )

    $prevLocation = Get-Location
    try {
        Write-LogMessage -LogPath $logPath -Message "Adding patch file: $PatchFilePath to the repository."

        if (-Not (Test-Path $PatchFilePath)) {
            Write-LogMessage -LogPath $logPath -Message "Patch file does not exist: $PatchFilePath." -Level 2
            Exit 1
        }

        $PatchFileBasename = [System.IO.Path]::GetFileName($PatchFilePath)

        Write-LogMessage -LogPath $logPath -Message "Setting location to $((Get-Item $RepoPath).Fullname)."
        Set-Location $RepoPath

        Invoke-LoggedExpression -LogPath $LogPath -Command "git stash"
        Invoke-LoggedExpression -LogPath $logPath -Command "git apply --ignore-whitespace `"$PatchFilePath`""
        Invoke-LoggedExpression -LogPath $logPath -Command "git add -A"
        Invoke-LoggedExpression -LogPath $logPath -Command "git commit -m `"Apply patch $PatchFileBasename`""
        Invoke-LoggedExpression -LogPath $LogPath -Command "git stash pop"

        Write-LogMessage -LogPath $logPath -Message "Patch file added successfully."
    }
    catch {
        Write-LogMessage -LogPath $logPath -Message "An error occurred while adding the patch file: $_." -Level 1
        Write-LogException -LogPath $LogPath -Exception $_
        exit 1
    }
    finally {
        Set-Location $prevLocation
    }
}

Export-ModuleMember -Function Add-Patch
