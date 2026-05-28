import json
import warnings
import os
import requests

GITEA_HOST = os.getenv("GITEA_HOST")
GITEA_TOKEN = os.getenv("GITEA_TOKEN")


warnings.filterwarnings("ignore")


def make_request(*args, **kwargs):
    headers = {
        "Authorization": f"Bearer {GITEA_TOKEN}",
        "Accept": "application/json"
    }
    kwargs["headers"] = {
        **kwargs.get("headers", {}),
        **headers
    }

    kwargs["verify"] = False

    response = requests.request(*args, **kwargs)
    response.raise_for_status()
    return response.json()


def get_repos():
    url = f"{GITEA_HOST}/api/v1/user/repos"
    response = make_request("get", url)
    return [i.get("full_name") for i in response]


def get_branch_protections(repo):
    url = f"{GITEA_HOST}/api/v1/repos/{repo}/branch_protections"
    response = make_request("get", url)
    return response


def verify_branch_protections(protections):
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

    is_good = True
    for protection in protections:
        rule_name = protection.get("rule_name")
        if rule_name not in check_lists:
            continue

        log_prefix = f"\t{rule_name}: "
        verified.add(rule_name)
        for key, expected_val in check_lists[rule_name].items():
            actual_val = protection.get(key)
            if actual_val == expected_val:
                continue

            is_good = False
            print(
                f"{log_prefix}{key} is {actual_val}, expected "
                f"{expected_val}"
            )

    if len(verified) < len(check_lists):
        print(
            f"{log_prefix}required branch protections not found: "
            f"{set(check_lists.keys()) - verified}"
        )


def main():
    repos = get_repos()
    for repo in repos:
        print(f"checking branch protections for {repo}")
        protections = get_branch_protections(repo)
        verify_branch_protections(protections)


if __name__ == '__main__':
    main()
