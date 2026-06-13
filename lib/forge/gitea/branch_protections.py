import logging
from lib.forge.branch_protections import BranchProtections


class GiteaBranchProtections(BranchProtections):
    def __init__(self, client, repos):
        self._client = client
        self._repos = repos

    def _get(self, repo):
        url = f"/api/v1/repos/{repo}/branch_protections"
        response = self._client.make_request("GET", url)
        return response.json()

    def _verify_repo(self, repo):
        check_lists = {
            "**": {
                "priority": 1,
                "enable_push": True,
                "enable_push_whitelist": False,
                "push_whitelist_usernames": [],
                "push_whitelist_teams": [],
                "push_whitelist_deploy_keys": False,
                "enable_force_push": False,
                "enable_force_push_allowlist": False,
                "force_push_allowlist_usernames": [],
                "force_push_allowlist_teams": [],
                "force_push_allowlist_deploy_keys": False,
                "enable_merge_whitelist": False,
                "merge_whitelist_usernames": [],
                "merge_whitelist_teams": [],
                "enable_status_check": False,
                "status_check_contexts": None,
                "required_approvals": 0,
                "enable_approvals_whitelist": False,
                "approvals_whitelist_username": [],
                "approvals_whitelist_teams": [],
                "block_on_rejected_reviews": False,
                "block_on_official_review_requests": False,
                "block_on_outdated_branch": False,
                "dismiss_stale_approvals": False,
                "ignore_stale_approvals": False,
                "require_signed_commits": False,
                "protected_file_patterns": "",
                "unprotected_file_patterns": "",
                "block_admin_merge_override": True,
            }
        }

        verified = set()
        for protection in self._get(repo):
            rule_name = protection.get("rule_name")
            if rule_name not in check_lists:
                continue

            verified.add(rule_name)
            for key, expected_val in check_lists[rule_name].items():
                actual_val = protection.get(key)
                if actual_val == expected_val:
                    continue

                logging.info(
                    f"[{repo}] {rule_name}: {key} is {actual_val}, expected "
                    f"{expected_val}"
                )

        if len(verified) < len(check_lists):
            logging.info(
                f"[{repo}] required branch protections not found: "
                f"{set(check_lists.keys()) - verified}"
            )

    def verify(self):
        for repo in self._repos.get():
            self._verify_repo(repo["full_name"])
