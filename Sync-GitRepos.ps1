param (
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$thisDirectory = Split-Path -Parent $MyInvocation.MyCommand.Definition
$loggingModulePath = (Join-Path "$thisDirectory" "lib" "Logging.psm1")

Get-ChildItem -Directory $Path | ForEach-Object -Parallel {
    Import-Module $using:loggingModulePath

    $repo = $_.FullName
    $repoName = $_.Name

    & git -C $repo stash
    $originalBranch = & git -C $repo branch --show-current

    & git -C $repo branch --format='%(refname:short)' | ForEach-Object {
        $record = [pscustomobject]@{
            repo   = $repoName
            branch = $_
            switch = Get-CommandOutput { & git -C $repo switch $_ }
            pull   = Get-CommandOutput { & git -C $repo pull --rebase origin $_ }
            push   = Get-CommandOutput { & git -C $repo push origin $_ }
            status = Get-CommandOutput { & git -C $repo status }
        }
        $record | ConvertTo-Json -Compress -Depth 10
    }

    & git -C $repo switch $originalBranch
    & git -C $repo stash pop
}
