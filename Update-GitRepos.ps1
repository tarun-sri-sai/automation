param (
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$result = @{}
Get-ChildItem -Directory $Path | ForEach-Object -Parallel {
    function Get-CommandOutput {
        param (
            [Parameter(Mandatory = $true)]
            [ScriptBlock]$ScriptBlock
        )

        $output = @(& $ScriptBlock 2>&1)
        foreach ($item in $output) {
            if ($item -is [System.Management.Automation.ErrorRecord]) {
                $item.Exception.Message
            } else { 
                $item
            }
        }
    }

    $repo = $_.FullName
    $repoName = $_.Name
    $repoResult = @{}

    & git -C $repo branch --format='%(refname:short)' | ForEach-Object {
        $repoResult[$_] = @{
            switch = Get-CommandOutput { & git -C $repo switch $_ }
            pull   = Get-CommandOutput { & git -C $repo pull --rebase origin $_ }
            push   = Get-CommandOutput { & git -C $repo push origin $_ }
            status = Get-CommandOutput { & git -C $repo status }
        }
    }

    @{ $repoName = $repoResult }
} | ForEach-Object { $result += $_ }

$result | ConvertTo-Json -Depth 10
