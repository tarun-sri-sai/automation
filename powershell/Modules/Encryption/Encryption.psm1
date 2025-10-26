Import-Module Logging

function Get-PasswordFromFile {
    param (
        [Parameter(Mandatory = $true)]
        [string] $LogPath,

        [String]$PassFile = "password.txt"
    )

    $passwordPtr = $null 

    try {
        if (-Not (Test-Path -Type Leaf $PassFile)) {
            Write-LogMessage -LogPath $LogPath -Message "$PassFile password file does not exist." -Level 3
            return $null
        }

        if ((Get-Item $PassFile).Length -gt 0) {
            $password = (Get-Content -Path $PassFile | ConvertTo-SecureString)
            $passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
            return [Runtime.InteropServices.Marshal]::PtrToStringAuto($passwordPtr)
        }

        Write-LogMessage -LogPath $LogPath -Message "Password file is empty." -Level 3
        return $null
    }
    catch {
        Write-LogMessage -LogPath $LogPath -Message "Error while decoding password from ${PassFile}:" -Level 1
        Write-LogException -LogPath $LogPath -Exception $_
    }
    finally {
        if ($null -ne $passwordPtr) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
        }
    }
}

function Read-PasswordFromInput {
    $passwordPtr = $null
    $confirmPasswordPtr = $null

    try {
        $password = Read-Host "Enter a password" -AsSecureString
        $confirmPassword = Read-Host "Confirm your password" -AsSecureString

        $passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($password)
        $confirmPasswordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($confirmPassword)

        $passwordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto($passwordPtr)
        $confirmPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto($confirmPasswordPtr)

        $result = $passwordPlain -eq $confirmPasswordPlain
        if (-Not $result) {
            Write-Error "Passwords don't match. Try again"
            return $null
        }

        return $password
    }
    finally {
        if ($null -ne $passwordPtr) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
        }

        if ($null -ne $passwordPtr) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
        }
    }
}

Export-ModuleMember -Function Get-PasswordFromFile, Read-PasswordFromInput
