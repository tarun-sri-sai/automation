param (
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$result = @{}
Get-ChildItem -Directory $Path | ForEach-Object -Parallel {
    $repo = $_.FullName
    $repoName = $_.Name
    $repoResult = @{}

    git -C $repo branch --format='%(refname:short)' | ForEach-Object {
        $repoResult[$_] = @{
            switch = @(git -C $repo switch $_ 2>&1)
            pull   = @(git -C $repo pull --rebase origin $_ 2>&1)
            push   = @(git -C $repo push origin $_ 2>&1)
            status = @(git -C $repo status 2>&1)
        }
    }

    @{ $repoName = $repoResult }
} | ForEach-Object { $result += $_ }

$result | ConvertTo-Json -Depth 10
