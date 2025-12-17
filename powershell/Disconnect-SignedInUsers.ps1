$lines = quser.exe | Select-Object -Skip 1
foreach ($line in $lines) {
    if ($line -match '^>') {                # Ignore my session
        continue
    }
    $words = ($line -split '\s+')
    $session = $words[$words.Length - 6]    # Get the session ID, which is 6th from the end
    Write-Output "logging off session ID $session"
    logoff $session
}
