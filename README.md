# 📝 Smart Changelog Generator

Paste any public GitHub repo → AI reads recent commits → generates human-readable release notes + a LinkedIn post + a tweet. Instantly.

## What it does
- Fetches last N commits from any public GitHub repo
- Groups and rewrites them into clean release notes (Features / Bug Fixes / Improvements)
- Generates a ready-to-post LinkedIn announcement
- Generates a tweet under 280 characters

## Tech Stack
- Python + Streamlit (UI)
- GitHub REST API (commit fetching)
- Groq API — llama3-8b-8192 (free LLM)

## Setup

### 1. Get a free Groq API key
Go to https://console.groq.com → Sign up → Create API Key (free, takes 30 seconds)

### 2. Clone and install
```bash
git clone https://github.com/VaishnaviGahoi/smart-changelog
cd smart-changelog
pip install -r requirements.txt
```

### 3. Add your API key
```bash
cp .env.example .env
```
Open `.env` and paste your Groq API key.

### 4. Run
```bash
streamlit run app.py
```

Opens at http://localhost:8501

## Usage
1. Paste any public GitHub repo URL
2. Choose how many commits to analyse (5–50)
3. Click Generate
4. Copy your release notes, LinkedIn post, and tweet

## Built by
Vaishnavi Gahoi — [LinkedIn](https://linkedin.com/in/vaishnavigahoi) | [GitHub](https://github.com/VaishnaviGahoi)
