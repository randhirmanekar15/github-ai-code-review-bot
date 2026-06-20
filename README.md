# GitHub AI Code Review Bot

Fetches open pull requests, sends each changed file's diff to a **local** LLM for review, and posts the suggestions back as PR comments. Your proprietary code never leaves the machine.

Runs locally on [Ollama](https://ollama.com).

## Stack

| Piece | Choice |
|-------|--------|
| Language | Python |
| GitHub | REST API v3 |
| LLM runtime | Ollama (local) |
| Model | `mistral` |

## Setup

```bash
ollama pull mistral
pip install -r requirements.txt
```

Create a GitHub Personal Access Token with `repo` + `pull_requests` scope, then set env vars (never hardcode the token):

```bash
export GITHUB_TOKEN=ghp_xxx
export REPO_OWNER=your_username
export REPO_NAME=your_repo
```

## Usage

```bash
python bot.py
```

## Test

```bash
pip install pytest
pytest        # pure helpers, no network
```

## Limitations

- Reviews one diff at a time — misses cross-file logic.
- Small models can be noisy ("add error handling" everywhere).
- GitHub authenticated requests cap at 5,000/hour.
- The PAT has write access — keep it in an env var, scope it tightly, rotate it.

---

Inspired by Aman Kharwal's tutorial, [Build an AI Code Review Bot for GitHub](https://amanxai.com/2026/03/18/build-an-ai-code-review-bot-for-github/). Rebuilt and extended (env-based auth, patch-only review, per-file comments).

MIT licensed.
