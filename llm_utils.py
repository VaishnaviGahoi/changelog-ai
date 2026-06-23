import os
import requests


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"


def call_groq(prompt, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1200,
        "temperature": 0.7
    }
    response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def generate_changelog(commits, api_key):
    commit_text = "\n".join([
        f"- [{c['date']}] {c['message']} (by {c['author']})"
        for c in commits
    ])

    prompt = f"""You are a technical writer. Convert these raw git commit messages into clean, human-readable release notes.

Git commits:
{commit_text}

Write release notes using only the sections that are relevant (skip empty ones):

## 🚀 New Features
## 🐛 Bug Fixes
## ⚡ Improvements
## 🔧 Technical Changes

Rules:
- Group related commits together
- Keep each point to one clear sentence
- Make it readable for both technical and non-technical audiences
- Do not include commit author names
- Skip merge commits and version bump commits"""

    return call_groq(prompt, api_key)


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

    return call_groq(prompt, api_key)


def generate_tweet(changelog, repo_name, api_key):
    prompt = f"""Write a single tweet (under 280 characters) announcing an update to the project "{repo_name}".

Release notes:
{changelog}

Rules:
- Lead with the most impactful change
- Sound human
- Include 2 relevant hashtags
- No more than 280 characters total"""

    return call_groq(prompt, api_key)
