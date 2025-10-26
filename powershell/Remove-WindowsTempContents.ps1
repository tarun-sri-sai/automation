$windowsTemp = "C:\Windows\Temp"
Write-Host "Cleaning up contents of '$windowsTemp'"
Remove-Item -Recurse -Force "$windowsTemp\*"

$userDirectories = Get-ChildItem C:\Users | ForEach-Object { $_.FullName }

foreach($userDir in $userDirectories) {
    $tempDirectory = (Get-Item -ErrorAction SilentlyContinue "$userDir\AppData\Local\Temp")

    if (($null -ne $tempDirectory) -and (Test-Path -PathType Container $tempDirectory)) {
        Write-Host "Cleaning up contents of '$tempDirectory'"
        Remove-Item -Recurse -Force "$tempDirectory\*"
    } else {
        Write-Host "'$userDir' does not have a temp directory"
    }
}
