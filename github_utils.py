import requests
import re
import os


def parse_repo_url(url):
    pattern = r'github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$'
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2).strip()
    return None, None


def fetch_commits(repo_url, num_commits=20):
    owner, repo = parse_repo_url(repo_url)
    if not owner or not repo:
        return None, "Invalid GitHub URL. Use format: https://github.com/username/repo"

    api_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {"Accept": "application/vnd.github.v3+json"}

    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        response = requests.get(api_url, headers=headers, params={"per_page": num_commits}, timeout=10)
        if response.status_code == 404:
            return None, "Repo not found. Make sure it is public."
        if response.status_code == 403:
            return None, "GitHub rate limit hit. Add a GITHUB_TOKEN in your .env file."
        response.raise_for_status()

        commits = response.json()
        commit_data = []
        for c in commits:
            msg = c["commit"]["message"].split("\n")[0]
            commit_data.append({
                "message": msg,
                "author": c["commit"]["author"]["name"],
                "date": c["commit"]["author"]["date"][:10]
            })
        return commit_data, None

    except requests.exceptions.Timeout:
        return None, "Request timed out. Check your internet connection."
    except Exception as e:
        return None, f"Error: {str(e)}"
