"""Idempotent GitHub setup; invoke using an already authorized admin identity."""

import argparse
import json
import subprocess

REPOSITORY = "zeroemployeeorg/zeointegrations"
ENVIRONMENT = "pypi"
DESIRED = {
    "wait_timer": 0,
    "reviewers": [],
    "prevent_self_review": False,
    "deployment_branch_policy": {
        "protected_branches": False,
        "custom_branch_policies": True,
    },
}


def api(path, method="GET", body=None):
    args = ["gh", "api", "--method", method, path]
    data = None
    if body is not None:
        args.extend(["--input", "-"])
        data = json.dumps(body)
    result = subprocess.run(args, input=data, text=True, capture_output=True, check=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    repo = api(f"repos/{REPOSITORY}")
    if not args.apply:
        print(json.dumps({"repository": REPOSITORY, "environment": ENVIRONMENT,
                          "desired": DESIRED, "branch": "main",
                          "admin_available": repo["permissions"].get("admin", False),
                          "applied": False}, indent=2))
        return
    if not repo["permissions"].get("admin", False):
        raise SystemExit("Administration-write permission required; no identity fallback")
    endpoint = f"repos/{REPOSITORY}/environments/{ENVIRONMENT}"
    api(endpoint, "PUT", DESIRED)
    policies = api(endpoint + "/deployment-branch-policies")["branch_policies"]
    for policy in policies:
        if policy["name"] != "main" or policy["type"] != "branch":
            api(endpoint + f'/deployment-branch-policies/{policy["id"]}', "DELETE")
    if not any(p["name"] == "main" and p["type"] == "branch" for p in policies):
        api(endpoint + "/deployment-branch-policies", "POST", {"name": "main", "type": "branch"})
    actual = api(endpoint)
    if any(rule["type"] in {"required_reviewers", "wait_timer"} for rule in actual.get("protection_rules", [])):
        raise SystemExit("Unexpected deployment review/wait gate remains")
    branches = api(endpoint + "/deployment-branch-policies")["branch_policies"]
    if [(p["name"], p["type"]) for p in branches] != [("main", "branch")]:
        raise SystemExit("Environment branch policy readback did not match main-only")
    print(json.dumps({"repository": REPOSITORY, "environment": ENVIRONMENT,
                      "main_only": True, "human_release_gate": False, "applied": True}))


if __name__ == "__main__":
    main()
