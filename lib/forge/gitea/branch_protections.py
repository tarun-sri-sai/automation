import logging
from lib.forge.branch_protections import BranchProtections
from .client import GiteaClient
from .repos import GiteaRepos


class GiteaBranchProtections(BranchProtections):
    @staticmethod
    def _get(repo):
        host = GiteaClient.get_host()
        url = f"{host}/api/v1/repos/{repo}/branch_protections"

        response = GiteaClient.make_request("GET", url)
        return response

    @staticmethod
    def _verify_repo(repo):
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
        for protection in GiteaBranchProtections._get(repo):
            rule_name = protection.get("rule_name")
            if rule_name not in check_lists:
                continue

            verified.add(rule_name)
            for key, expected_val in check_lists[rule_name].items():
                actual_val = protection.get(key)
                if actual_val == expected_val:
                    continue

                logging.info(
                    f"rule [{rule_name}]: {key} is {actual_val}, expected "
                    f"{expected_val}"
                )

        if len(verified) < len(check_lists):
            logging.info(
                f"rule [{rule_name}]: required branch protections not found: "
                f"{set(check_lists.keys()) - verified}"
            )

    @staticmethod
    def verify():
        for repo in GiteaRepos.get():
            GiteaBranchProtections._verify_repo(repo)
