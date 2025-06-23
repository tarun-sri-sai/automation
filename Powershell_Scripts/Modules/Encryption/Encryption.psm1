function Get-PasswordFromFile {
    param (
        [String]$PassFile = "password.txt"
    )

    if (-Not (Test-Path -Type Leaf $PassFile)) {
        Write-Host "$PassFile password file does not exist."
        return $null
    }

    if ((Get-Item $PassFile).Length -gt 0) {
        $SecurePassword = (Get-Content -Path $PassFile | ConvertTo-SecureString)
        return [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword))
    
    }

    Write-Host "Password file is empty."
    return $null
}

function Read-PasswordFromInput {
    $password = Read-Host "Enter a password" -AsSecureString
    $confirmPassword = Read-Host "Confirm your password" -AsSecureString

    $passwordText = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))
    $confirmPasswordText = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($confirmPassword))

    $result = $passwordText -eq $confirmPasswordText
    $exitWithFailure = $false
    if (-Not $result) {
        Write-Error "Passwords don't match. Try again"
        $exitWithFailure = $true
    }

    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($confirmPassword))

    if ($exitWithFailure) {
        Exit 1
    }

    if ($result) { return $password }
    return $null
}

Export-ModuleMember -Function Get-PasswordFromFile, Read-PasswordFromInput
