# I Built an AI Code Reviewer That Never Sends My Code to the Cloud

*A local LLM reviews my GitHub pull requests, posts the feedback as a comment, and my proprietary code never leaves the machine. Here's the whole build.*

## Why this, why now

2026 is the year AI-native development stopped being a demo and became the default. OpenAI, Google, and Anthropic all shipped agent SDKs in the last twelve months. Every IDE now ships with an agent baked in. If you're not building with AI in the loop, you're writing code with one hand.

But here's the part nobody says out loud at the conference: most of these tools want your code. Your diff goes to a server you don't control, gets logged, maybe trains a model. For a side project, fine. For client work under NDA, or anything with real IP, that's a non-starter.

So I built a code review bot that runs entirely on my laptop. It pulls open PRs, sends the diff to a local model, and posts the review back to GitHub. The cloud never sees a single line. Cost: zero. Privacy: total.

## What it does

The bot does four things, in order:

1. Fetches open pull requests from a repo via the GitHub API.
2. Grabs the changed files (the actual diffs) for each PR.
3. Sends each patch to a local LLM running on Ollama and asks for a review — bugs, performance, style.
4. Posts the review back as a comment on the PR.

You run it, it reviews, you read. No subscription, no API bill, no data leaving your network.

## The stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python | Fastest path from idea to working script |
| GitHub | REST API v3 | Stable, well-documented, no SDK bloat |
| HTTP | `requests` | It just works |
| LLM runtime | Ollama | One command to serve a model locally |
| Model | `mistral` | Small enough to run on a laptop, sharp enough for code |
| Auth | Personal Access Token | `repo` + `pull_requests` scope, nothing more |

## How it works

First, pull the changed files for a given PR. I don't fetch the whole repo — I only want the patch, the lines that actually changed.

```python
import requests, os

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}",
           "Accept": "application/vnd.github.v3+json"}

def get_pr_files(owner, repo, pr_number):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    # each file carries a "patch" — the diff. That's all the model needs.
    return [(f["filename"], f.get("patch", "")) for f in resp.json()]
```

Then send each patch to the local model and post the result back. Ollama exposes an HTTP endpoint on `localhost:11434`, so the "AI" part is just another POST request — to your own machine.

```python
def review_and_post(owner, repo, pr_number, filename, patch):
    prompt = (f"You are an expert code reviewer. Review this diff for "
              f"{filename}. Flag bugs, performance issues, and style. "
              f"Be specific and concise.\n\n{patch}")

    r = requests.post("http://localhost:11434/api/generate",
                      json={"model": "mistral", "prompt": prompt, "stream": False})
    review = r.json()["response"]

    comment = f"### AI review — `{filename}`\n\n{review}"
    requests.post(
        f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments",
        headers=HEADERS, json={"body": comment})
```

That's the core loop. Fetch, review, post — and the diff only ever travels between two processes on the same laptop.

## What I changed

The tutorial I started from hardcodes the token and reviews everything in one blob. I made four changes that take it from toy to usable:

1. **Token in an env var, never in the file.** `os.environ["GITHUB_TOKEN"]`. A PAT pasted into source is one `git push` away from disaster.
2. **Review only the patch, not the whole file.** Sending just the changed lines keeps the prompt small, so a 7B model stays fast and stays on-topic instead of re-reviewing untouched code.
3. **One comment per file, not one giant dump.** Reviewing `auth.py` and `utils.py` in separate comments makes the feedback scannable. A 600-line wall of text gets ignored.
4. **Dedupe already-reviewed PRs.** I keep a small local JSON of `pr_number` + commit SHA. If nothing changed since the last run, skip it. No spamming the same PR every time the script runs.

## Where it breaks

I'd be lying if I called this production-grade. Honest limits:

- **It misses cross-file logic.** The model sees one diff at a time. A bug that only shows up because of how two files interact? Invisible to it.
- **It can get noisy.** Small models love to suggest "add error handling" on every function. You learn to skim.
- **GitHub rate limits.** Authenticated requests cap at 5,000/hour. Fine for one repo, not for scanning an org's worth of PRs in a loop.
- **The PAT is a liability.** It has write access to your repos. Keep it in an env var, scope it tightly, and rotate it.

## Takeaway

You don't need a cloud API to get useful code review from an LLM. A laptop, Ollama, and 60 lines of Python get you a reviewer that's free, private, and good enough to catch the obvious stuff before a human ever looks.

It won't replace your senior engineer. But it'll save them from reviewing the typos — and it'll do it without your code ever leaving the building.

*Built on the foundation of Aman Kharwal's tutorial, ["Build an AI Code Review Bot for GitHub"](https://amanxai.com/2026/03/18/build-an-ai-code-review-bot-for-github/). I adapted the architecture and extended it with env-based auth, patch-only review, per-file comments, and dedupe.*

### Sources
- [Aman Kharwal — Build an AI Code Review Bot for GitHub](https://amanxai.com/2026/03/18/build-an-ai-code-review-bot-for-github/)
- [LangChain — AI Agent Frameworks (2026)](https://www.langchain.com/resources/ai-agent-frameworks)
- [Gartner — Hype Cycle for Agentic AI](https://www.gartner.com/en/articles/hype-cycle-for-agentic-ai)
