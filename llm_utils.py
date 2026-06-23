import os
import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"


def call_groq(prompt, api_key, max_tokens=1500):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.4
    }
    response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def chunk_commits(commits, chunk_size=12):
    for i in range(0, len(commits), chunk_size):
        yield commits[i:i + chunk_size]


def summarise_chunk(commits_chunk, api_key):
    commit_text = "\n".join([
        f"- [{c['date']}] {c['message']}"
        for c in commits_chunk
    ])
    prompt = f"""You are a technical writer. Read these git commit messages and extract the key changes.

Commits:
{commit_text}

Return a brief structured summary grouping changes into:
- New Features (if any)
- Bug Fixes (if any)
- Improvements (if any)
- Technical Changes (if any)

Rules:
- Skip merge commits, version bumps, typo fixes
- One line per change, clear and concise
- Only include sections that have actual content"""

    return call_groq(prompt, api_key, max_tokens=800)


def generate_changelog(commits, api_key):
    if len(commits) <= 15:
        commit_text = "\n".join([
            f"- [{c['date']}] {c['message']}"
            for c in commits
        ])
        prompt = f"""You are a senior technical writer. Convert these git commits into polished release notes.

Git commits:
{commit_text}

Write release notes with ONLY relevant sections (skip empty ones):

## 🚀 New Features
## 🐛 Bug Fixes
## ⚡ Improvements
## 🔧 Technical Changes

Rules:
- Group related commits into single meaningful points
- Each point must be one clear, specific sentence explaining WHAT changed and WHY it matters
- Skip merge commits, typo fixes, version bumps
- No author names
- Do not use vague phrases like "various improvements" or "minor updates"
- Be specific: name the function, module, or feature affected"""

        return call_groq(prompt, api_key, max_tokens=1500)

    else:
        chunk_summaries = []
        for i, chunk in enumerate(chunk_commits(commits, chunk_size=12)):
            summary = summarise_chunk(chunk, api_key)
            chunk_summaries.append(summary)

        combined = "\n\n---\n\n".join(chunk_summaries)

        final_prompt = f"""You are a senior technical writer. Below are summaries of git commits grouped in batches.
Merge them into one clean, well-structured set of release notes.

Batch summaries:
{combined}

Write the final release notes with ONLY relevant sections:

## 🚀 New Features
## 🐛 Bug Fixes
## ⚡ Improvements
## 🔧 Technical Changes

Rules:
- Merge duplicate or similar points into one
- Each point must be specific and meaningful
- Skip vague or trivial changes
- No author names
- Do not use filler phrases like "various improvements"
- Result should read as a single unified changelog, not a list of summaries"""

        return call_groq(prompt=final_prompt, api_key=api_key, max_tokens=1500)


def generate_linkedin_post(changelog, repo_name, api_key):
    prompt = f"""Write a short LinkedIn post announcing a software update for the project "{repo_name}".

Release notes:
{changelog}

Rules:
- Start with a strong hook (NOT "Excited to announce" or "I am happy to share")
- 150-200 words max
- Max 3 emojis
- Sound human and genuine, not corporate
- Highlight the 2-3 most impactful changes only
- End with: #BuildInPublic #OpenSource #GitHub and 2-3 relevant tech hashtags"""

    return call_groq(prompt, api_key, max_tokens=400)


def generate_tweet(changelog, repo_name, api_key):
    prompt = f"""Write a single tweet (under 280 characters) announcing an update to the project "{repo_name}".

Release notes:
{changelog}

Rules:
- Lead with the most impactful change
- Sound human
- Include 2 relevant hashtags
- No more than 280 characters total
- Return ONLY the tweet text, nothing else"""

    return call_groq(prompt, api_key, max_tokens=100)
