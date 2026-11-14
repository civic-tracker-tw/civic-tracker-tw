"""
CivicTracker TW - Zero-Git-Dependency GitHub Repository & Pages Publisher
Allows publishing the entire project and static site to a dedicated GitHub account
purely via Python's built-in urllib (no Git CLI installation required on Windows).
"""

import argparse
import base64
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache", "data"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".db", ".db-shm", ".db-wal"}


def _github_api_request(
    method: str,
    endpoint: str,
    token: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    url = endpoint if endpoint.startswith("https://") else f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "CivicTracker-TW-Publisher/1.0",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}


def collect_project_files(root_dir: Path = BASE_DIR) -> List[Path]:
    files: List[Path] = []
    for path in sorted(root_dir.rglob("*")):
        if path.is_dir():
            continue
        rel_parts = path.relative_to(root_dir).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        if path.suffix in SKIP_SUFFIXES:
            continue
        files.append(path)
    return files


def publish_to_github(
    token: str,
    repo_name: str = "civic-tracker-tw",
    org_name: Optional[str] = None,
    private: bool = False,
) -> Dict[str, Any]:
    """
    1. Verifies authenticated GitHub user (or target Organization)
    2. Creates repository if it does not exist (under Organization or User)
    3. Uploads all project & dist/ files via GitHub Contents API
    4. Enables GitHub Pages on the repository
    """
    user_info = _github_api_request("GET", "/user", token)
    login_user = user_info["login"]
    owner = org_name.strip() if org_name and org_name.strip() else login_user
    print(f"[GitHubPublisher] Authenticated as '{login_user}', target owner: '{owner}'")

    # Create or get repository
    try:
        repo_info = _github_api_request("GET", f"/repos/{owner}/{repo_name}", token)
        print(f"[GitHubPublisher] Found existing repository: {repo_info['html_url']}")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            create_endpoint = f"/orgs/{owner}/repos" if (org_name and org_name.strip()) else "/user/repos"
            print(f"[GitHubPublisher] Creating new repository '{owner}/{repo_name}' via {create_endpoint}...")
            repo_info = _github_api_request(
                "POST",
                create_endpoint,
                token,
                {
                    "name": repo_name,
                    "description": "CivicTracker TW — 國會監督與首長政見追蹤平台 (Hydrogen x Argon Dual-Model Pipeline)",
                    "private": private,
                    "auto_init": True,
                },
            )
            print(f"[GitHubPublisher] Created repository: {repo_info['html_url']}")
        else:
            raise

    # Upload files via Contents API
    files = collect_project_files(BASE_DIR)
    uploaded_count = 0
    for fpath in files:
        rel_posix = fpath.relative_to(BASE_DIR).as_posix()
        content_b64 = base64.b64encode(fpath.read_bytes()).decode("ascii")

        # Check if file exists to get sha
        existing_sha = None
        try:
            existing = _github_api_request("GET", f"/repos/{owner}/{repo_name}/contents/{rel_posix}", token)
            existing_sha = existing.get("sha")
        except urllib.error.HTTPError:
            pass

        body: Dict[str, Any] = {
            "message": f"Sync {rel_posix} via CivicTracker Publisher",
            "content": content_b64,
            "branch": "main",
        }
        if existing_sha:
            body["sha"] = existing_sha

        _github_api_request("PUT", f"/repos/{owner}/{repo_name}/contents/{rel_posix}", token, body)
        uploaded_count += 1
        print(f"  [{uploaded_count}/{len(files)}] Uploaded: {rel_posix}")

    # Configure GitHub Pages to use GitHub Actions workflow
    pages_url = f"https://{owner}.github.io/{repo_name}/"
    try:
        _github_api_request(
            "POST",
            f"/repos/{owner}/{repo_name}/pages",
            token,
            {"build_type": "workflow"},
        )
        print(f"[GitHubPublisher] Enabled GitHub Pages (GitHub Actions workflow): {pages_url}")
    except urllib.error.HTTPError:
        # Pages might already be enabled
        pass

    return {
        "owner": owner,
        "repo_url": repo_info["html_url"],
        "pages_url": pages_url,
        "files_uploaded": uploaded_count,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish CivicTracker TW to GitHub without Git CLI")
    parser.add_argument("--repo", default="civic-tracker-tw", help="Target GitHub repository name")
    parser.add_argument("--org", default=os.environ.get("GITHUB_ORG", ""), help="Optional GitHub Organization name")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""), help="GitHub Personal Access Token")
    args = parser.parse_args()

    if not args.token:
        print(
            "[GitHubPublisher] Please provide a GitHub Personal Access Token via --token or GITHUB_TOKEN env var.",
            file=sys.stderr,
        )
        sys.exit(1)

    res = publish_to_github(token=args.token, repo_name=args.repo, org_name=args.org)
    print("\n============================================================")
    print(f"GitHub Repository: {res['repo_url']}")
    print(f"GitHub Pages URL:  {res['pages_url']}")
    print(f"Files Uploaded:    {res['files_uploaded']}")
    print("============================================================")
