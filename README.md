# GitHub AI Code Review Bot

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue) ![License: MIT](https://img.shields.io/badge/License-MIT-green) ![Runs 100% Local](https://img.shields.io/badge/LLM-100%25%20local-orange)

**A local LLM reviews your GitHub pull requests and posts the feedback as comments — your code never leaves the machine.**

## Overview

By 2026, AI-native development stopped being a novelty and became the default. Most teams now route pull requests through some kind of LLM reviewer before a human ever looks at them. The problem: nearly all of those tools ship your diff off to a third-party API. For proprietary code, that's a non-starter — you're handing your competitive advantage to whoever runs the endpoint.

This bot flips that model. It pulls open pull requests from a repo, sends the diff to a model running locally through [Ollama](https://ollama.com), and posts the review back as a comment on the PR. The only thing that leaves your machine is the comment itself. The code, the diff, and the prompt all stay on localhost.

It's intentionally small — a single `bot.py` you can read in one sitting and adapt to your own workflow. No SaaS account, no per-seat pricing, no telemetry. Set five environment variables, run one command, and your PRs get reviewed by a model you control.

## Features

- **100% local inference** — diffs are reviewed by a model running on your machine via Ollama. Nothing is sent to a hosted LLM.
- **Diff-only prompts** — reviews the patch, not the entire file, so prompts stay small, fast, and cheap on context.
- **One comment per file** — feedback lands where it's relevant instead of one giant wall of text.
- **No hardcoded secrets** — the GitHub token lives in an environment variable, never in source.
- **Model-agnostic** — defaults to `mistral`, but swap in any Ollama model with one env var.
- **Pure, testable helpers** — prompt building and comment formatting are isolated and covered by `test_bot.py`.

## How it works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  List open   │ ──▶ │ Fetch diffs  │ ──▶ │  Local LLM       │ ──▶ │ Post comment │
│  PRs (API)   │     │ per changed  │     │  review (Ollama  │     │  to PR (API) │
│              │     │ file         │     │  / mistral)      │     │              │
└──────────────┘     └──────────────┘     └──────────────────┘     └──────────────┘
   GitHub REST          GitHub REST          stays on localhost        GitHub REST
```

1. `get_pull_requests` lists open PRs for the configured repo.
2. `get_pr_files` fetches the changed files and their patches (diffs only).
3. `build_review_prompt` wraps each diff, `analyze_code` sends it to the local model.
4. `format_comment` shapes the response and `post_comment` posts it back — one comment per file. `review_repo` orchestrates the loop.

## Tech stack

| Layer | Choice |
| ----- | ------ |
| Language | Python 3.10+ |
| GitHub API | REST API v3 |
| HTTP client | `requests` |
| LLM runtime | Ollama (local) |
| Model | `mistral` (configurable) |
| Testing | `pytest` on pure helpers |

## Project structure

```
github-ai-code-review-bot/
├── bot.py          # get_pull_requests, get_pr_files, analyze_code,
│                   # build_review_prompt, format_comment, post_comment, review_repo
├── test_bot.py     # unit tests for the pure helper functions
├── ARTICLE.md
├── requirements.txt
├── LICENSE         # MIT
└── README.md
```

## Installation

**1. Clone and install dependencies**

```bash
git clone https://github.com/randhirmanekar15/github-ai-code-review-bot.git
cd github-ai-code-review-bot
pip install -r requirements.txt
```

**2. Install Ollama and pull the model**

```bash
# https://ollama.com
ollama pull mistral
ollama serve
```

**3. Create a scoped Personal Access Token (PAT)**

GitHub → **Settings → Developer settings → Personal access tokens**. Generate a token scoped to **only** the repo you want reviewed, with **`repo`** + **pull request** read/write. Set an expiry and copy it (you'll only see it once).

## Usage

```bash
export GITHUB_TOKEN="ghp_your_scoped_token"
export REPO_OWNER="randhirmanekar15"
export REPO_NAME="your-repo"
python bot.py
```

PowerShell:

```powershell
$env:GITHUB_TOKEN="ghp_..."; $env:REPO_OWNER="randhirmanekar15"; $env:REPO_NAME="your-repo"; python bot.py
```

The bot walks every open PR, reviews each changed file's diff locally, and posts one comment per file.

## Configuration

| Variable | Required | Default | Description |
| -------- | -------- | ------- | ----------- |
| `GITHUB_TOKEN` | Yes | — | Scoped PAT with `repo` + pull request read/write |
| `REPO_OWNER` | Yes | — | Owner of the repo to review |
| `REPO_NAME` | Yes | — | Name of the repo to review |
| `OLLAMA_MODEL` | No | `mistral` | Local model used for reviews |
| `OLLAMA_URL` | No | `http://localhost:11434/api/generate` | Ollama generate endpoint |

## Security

The GitHub token carries **write access** to your repo — treat it accordingly.

- **Never hardcode it.** The bot reads `GITHUB_TOKEN` from the environment only.
- **Scope it tightly.** Use a fine-grained PAT limited to the single repo.
- **Set an expiry and rotate.** Short-lived tokens limit the blast radius if one leaks.
- **Keep diffs local.** Confirm `OLLAMA_URL` points at localhost so code never leaves the box.

## Testing

```bash
pip install pytest
pytest
```

The pure helpers (`build_review_prompt`, `format_comment`) have no network dependencies and are unit-tested.

## Limitations

- **One diff at a time.** Reviews each file's patch in isolation, so it misses cross-file logic.
- **Small models can be noisy.** Treat the output as a first pass, not a gate.
- **GitHub rate limits.** 5,000 requests/hour per token.
- **Write-scoped token.** Scope tightly and rotate regularly.

## Roadmap

- [ ] Inline per-line comments instead of one comment per file
- [ ] Dedupe — skip PRs and diffs already reviewed
- [ ] Run as a GitHub Action triggered on `pull_request`
- [ ] Configurable review prompt / severity threshold
- [ ] Summary comment rolling up per-file feedback

## Credits

📖 Full write-up: [ARTICLE.md](ARTICLE.md).

Based on Aman Kharwal's tutorial, ["Build an AI Code Review Bot for GitHub"](https://amanxai.com/2026/03/18/build-an-ai-code-review-bot-for-github/).

**What I changed vs the source tutorial:**

- Moved the GitHub token into an environment variable — never hardcoded.
- Reviews only the patch/diff instead of whole files, keeping prompts small and fast.
- Posts one comment per file for more focused feedback.

## Author

Built by **Randhir Manekar** — [randhirmanekar.com](https://randhirmanekar.com) · [github.com/randhirmanekar15](https://github.com/randhirmanekar15)

## License

MIT — see [LICENSE](LICENSE).
