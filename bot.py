"""AI code review bot for GitHub, powered by a local LLM.

Fetches open pull requests, sends each changed file's diff to a local model for
review, and posts the suggestions back as PR comments. Your code never leaves the
machine.

Inspired by Aman Kharwal's tutorial:
https://amanxai.com/2026/03/18/build-an-ai-code-review-bot-for-github/
"""

from __future__ import annotations

import os

import requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.environ.get("OLLAMA_MODEL", "mistral")
API_TIMEOUT = 60  # seconds


def _headers() -> dict[str, str]:
    token = os.environ["GITHUB_TOKEN"]  # never hardcode a PAT
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def _get_paginated(url: str) -> list[dict]:
    """GET a GitHub list endpoint, following Link-header pagination."""
    results: list[dict] = []
    params = {"per_page": 100}
    while url:
        resp = requests.get(url, headers=_headers(), params=params, timeout=API_TIMEOUT)
        resp.raise_for_status()
        results.extend(resp.json())
        url = resp.links.get("next", {}).get("url")
        params = {}  # the "next" URL already carries the page cursor
    return results


def get_pull_requests(owner: str, repo: str) -> list[dict]:
    """List all open pull requests for a repo (paginated)."""
    return _get_paginated(f"https://api.github.com/repos/{owner}/{repo}/pulls")


def get_pr_files(owner: str, repo: str, pr_number: int) -> list[tuple[str, str]]:
    """Return [(filename, patch)] for a PR — only the changed lines (paginated)."""
    files = _get_paginated(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    )
    return [(f["filename"], f.get("patch", "")) for f in files]


def build_review_prompt(filename: str, patch: str) -> str:
    """Construct the review prompt for a single file diff."""
    return (
        "You are an expert software engineer performing a code review. Analyze the "
        f"following diff for {filename}. Flag bugs, performance issues, and style "
        "problems. Be specific and concise.\n\n"
        f"{patch}"
    )


def analyze_code(filename: str, patch: str) -> str:
    """Ask the local model to review a single diff."""
    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": build_review_prompt(filename, patch), "stream": False},
        timeout=API_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def format_comment(filename: str, review: str) -> str:
    """Format a review into a Markdown PR comment body."""
    return f"### AI review - `{filename}`\n\n{review}"


def post_comment(owner: str, repo: str, pr_number: int, body: str) -> None:
    """Post a comment on a PR."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    resp = requests.post(url, headers=_headers(), json={"body": body}, timeout=API_TIMEOUT)
    resp.raise_for_status()


def review_repo(owner: str, repo: str) -> None:
    """Review every changed file in every open PR."""
    for pr in get_pull_requests(owner, repo):
        number = pr["number"]
        for filename, patch in get_pr_files(owner, repo, number):
            if not patch:
                continue
            # Isolate per-file failures so one bad file doesn't abort the run.
            try:
                review = analyze_code(filename, patch)
                post_comment(owner, repo, number, format_comment(filename, review))
                print(f"Reviewed PR #{number}: {filename}")
            except Exception as exc:  # noqa: BLE001  keep going on the next file
                print(f"Skipped PR #{number} {filename}: {exc}")


def main() -> None:
    review_repo(os.environ["REPO_OWNER"], os.environ["REPO_NAME"])


if __name__ == "__main__":
    main()
