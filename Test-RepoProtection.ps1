foreach ($repo in (gh repo list --limit 1000 --json name,owner | ConvertFrom-Json)) {
     $name = $repo.name
     $owner = $repo.owner.login

     $defaultBranch = (gh repo view "$owner/$name" --json defaultBranchRef 2>$1 | ConvertFrom-Json).defaultBranchRef.name

     try {
         $protection = gh api "repos/$owner/$name/branches/$defaultBranch/protection" 2>$1 | ConvertFrom-Json
     }
     catch {
         Write-Host "$name → NO protection"
         continue
     }

     $force = $protection.allow_force_pushes.enabled
     $delete = $protection.allow_deletions.enabled

     if (($force -ne $false) -or ($delete -ne $false)) {
         Write-Host "$name → force=$force, delete=$delete"
     }
 }
