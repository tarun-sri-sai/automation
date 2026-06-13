
from lib.forge.branch_protections import BranchProtections
import logging


class GithubBranchProtections(BranchProtections):
    def __init__(self, client, repos):
        self._client = client
        self._repos = repos

    def _get(self, repo):
        url = f"/graphql"
        owner, name = repo.split("/", 1)
        query = """
            query($owner: String!, $name: String!) {
                repository(owner: $owner, name: $name) {
                    branchProtectionRules(first: 100) {
                        nodes {
                            allowsDeletions
                            allowsForcePushes
                            blocksCreations
                            dismissesStaleReviews
                            isAdminEnforced
                            lockAllowsFetchAndMerge
                            lockBranch
                            pattern
                            requireLastPushApproval
                            requiredApprovingReviewCount
                            requiredDeploymentEnvironments
                            requiredStatusCheckContexts
                            requiresApprovingReviews
                            requiresCodeOwnerReviews
                            requiresCommitSignatures
                            requiresConversationResolution
                            requiresDeployments
                            requiresLinearHistory
                            requiresStatusChecks
                            requiresStrictStatusChecks
                            restrictsPushes
                            restrictsReviewDismissals
                            branchProtectionRuleConflicts(first: 100) { 
                                nodes { 
                                    conflictingBranchProtectionRule { 
                                        pattern 
                                    } 
                                } 
                            }
                            bypassForcePushAllowances(first: 100) {
                                nodes {
                                    actor { 
                                        ... on User { 
                                            login 
                                        } 
                                    } 
                                } 
                            }
                            bypassPullRequestAllowances(first: 100) {
                                nodes { 
                                    actor { 
                                        ... on User { 
                                            login 
                                        } 
                                    } 
                                } 
                            }
                            pushAllowances(first: 100) { 
                                nodes { 
                                    actor { 
                                        ... on User { 
                                            login 
                                        } 
                                    } 
                                } 
                            }
                            reviewDismissalAllowances(first: 100) { 
                                nodes { 
                                    actor { 
                                        ... on User { 
                                            login 
                                        } 
                                    } 
                                } 
                            }
                        }
                    }
                }
            }
        """
        response = self._client.make_request("POST", url, json={
            "query": query,
            "variables": {"owner": owner, "name": name},
        })

        return response.json()["data"]["repository"][
            "branchProtectionRules"
        ]["nodes"]

    def _verify_repo(self, repo):
        check_lists = {
            "**": {
                "allowsDeletions": False,
                "allowsForcePushes": False,
                "blocksCreations": False,
                "dismissesStaleReviews": False,
                "isAdminEnforced": True,
                "lockAllowsFetchAndMerge": False,
                "lockBranch": False,
                "requireLastPushApproval": False,
                "requiredApprovingReviewCount": None,
                "requiredDeploymentEnvironments": [],
                "requiredStatusCheckContexts": [],
                "requiresApprovingReviews": False,
                "requiresCodeOwnerReviews": False,
                "requiresCommitSignatures": False,
                "requiresConversationResolution": False,
                "requiresDeployments": False,
                "requiresLinearHistory": False,
                "requiresStatusChecks": False,
                "requiresStrictStatusChecks": True,
                "restrictsPushes": False,
                "restrictsReviewDismissals": False,
                "branchProtectionRuleConflicts": {
                    "nodes": []
                },
                "bypassForcePushAllowances": {
                    "nodes": []
                },
                "bypassPullRequestAllowances": {
                    "nodes": []
                },
                "pushAllowances": {
                    "nodes": []
                },
                "reviewDismissalAllowances": {
                    "nodes": []
                }
            }
        }

        verified = set()
        for protection in self._get(repo):
            rule_name = protection.get("pattern")
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
