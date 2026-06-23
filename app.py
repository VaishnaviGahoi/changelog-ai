import streamlit as st
import os
import json
import urllib.parse
from datetime import datetime
from github_utils import fetch_commits, parse_repo_url
from llm_utils import generate_changelog, generate_linkedin_post, generate_tweet

# ── CONFIG: works both locally and on Streamlit Cloud ──────────────────
def is_cloud():
    try:
        _ = st.secrets["GROQ_API_KEY"]
        return True
    except:
        return False

CONFIG_FILE = "config.json"
HISTORY_FILE = "history.json"

def load_config():
    if is_cloud():
        return {
            "groq_api_key": st.secrets.get("GROQ_API_KEY", ""),
            "github_token": st.secrets.get("GITHUB_TOKEN", "")
        }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"groq_api_key": os.getenv("GROQ_API_KEY", ""), "github_token": os.getenv("GITHUB_TOKEN", "")}

def save_config(data):
    if not is_cloud():
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)

def load_history():
    if is_cloud():
        return st.session_state.get("cloud_history", [])
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(entry):
    if is_cloud():
        h = st.session_state.get("cloud_history", [])
        h.insert(0, entry)
        st.session_state.cloud_history = h[:20]
    else:
        history = load_history()
        history.insert(0, entry)
        with open(HISTORY_FILE, "w") as f:
            json.dump(history[:20], f, indent=2)

# ── PAGE CONFIG ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Changelog AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #0d0d14 !important;
    color: #e2e8f0 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
[data-testid="stSidebar"] { background: #0a0a10 !important; }
[data-testid="stHeader"] { background: transparent !important; }
h1, h2, h3 { color: #f1f5f9 !important; font-family: 'Space Grotesk', sans-serif !important; }

.pipeline-bar {
    display: flex; align-items: center; justify-content: center;
    gap: 0; margin: 1.5rem 0 2rem 0;
}
.pipe-step {
    background: #13131f; border: 1px solid #2a2a3d; border-radius: 8px;
    padding: 0.5rem 1.2rem; font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem; color: #818cf8; letter-spacing: 0.08em;
}
.pipe-step.active { border-color: #f59e0b; color: #f59e0b; }
.pipe-arrow { color: #2a2a3d; font-size: 1.2rem; padding: 0 0.4rem; }

.stTextInput input, .stTextArea textarea {
    background: #0d0d14 !important; border: 1px solid #2a2a3d !important;
    color: #e2e8f0 !important; font-family: 'JetBrains Mono', monospace !important;
    border-radius: 8px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #f59e0b !important;
    box-shadow: 0 0 0 2px rgba(245,158,11,0.15) !important;
}

div[data-testid="stButton"] button {
    background: linear-gradient(135deg, #f59e0b, #d97706) !important;
    color: #0d0d14 !important; border: none !important;
    font-weight: 700 !important; border-radius: 8px !important;
    padding: 0.5rem 1.5rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

.stCode code {
    background: #0a0a10 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important; color: #c4b5fd !important;
}

.key-saved { color: #10b981; font-size: 0.75rem; margin-top: 4px; }
.char-ok { color: #10b981; font-size: 0.75rem; }
.char-warn { color: #f59e0b; font-size: 0.75rem; }
hr { border-color: #1e1e30 !important; }
[data-testid="stMarkdownContainer"] p { color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ───────────────────────────────────────────────────────
config = load_config()
if "groq_key" not in st.session_state:
    st.session_state.groq_key = config.get("groq_api_key", "")
if "github_token" not in st.session_state:
    st.session_state.github_token = config.get("github_token", "")
if "results" not in st.session_state:
    st.session_state.results = None
if "prefill_url" not in st.session_state:
    st.session_state.prefill_url = ""

# ── HEADER ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 2rem 0 0.5rem 0;">
  <div style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; letter-spacing:0.2em; color:#475569; margin-bottom:0.5rem;">DEVELOPER TOOL</div>
  <h1 style="font-size:2.6rem; font-weight:700; margin:0; background: linear-gradient(135deg,#f59e0b,#818cf8); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">Changelog AI</h1>
  <p style="color:#64748b; margin-top:0.4rem; font-size:0.95rem;">Raw commits → polished release notes + LinkedIn post + tweet. In seconds.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="pipeline-bar">
  <span class="pipe-step active">01 · CONNECT</span>
  <span class="pipe-arrow">──▶</span>
  <span class="pipe-step">02 · FETCH COMMITS</span>
  <span class="pipe-arrow">──▶</span>
  <span class="pipe-step">03 · AI GENERATE</span>
  <span class="pipe-arrow">──▶</span>
  <span class="pipe-step">04 · PUBLISH</span>
</div>
""", unsafe_allow_html=True)

# ── API KEY SECTION ──────────────────────────────────────────────────────
cloud_mode = is_cloud()
if cloud_mode:
    if st.session_state.groq_key:
        st.success("✓ API keys loaded from Streamlit Secrets")
    else:
        st.error("No GROQ_API_KEY found in Streamlit Secrets. Add it in your app settings.")
else:
    with st.expander("⚙️ API Keys — click to configure", expanded=not bool(st.session_state.groq_key)):
        col_g, col_gh, col_save = st.columns([3, 3, 1])
        with col_g:
            new_groq = st.text_input(
                "Groq API Key", value=st.session_state.groq_key,
                type="password", placeholder="gsk_xxxxxxxxxxxxxxxxxxxx",
                help="Free at console.groq.com"
            )
        with col_gh:
            new_gh = st.text_input(
                "GitHub Token (optional)", value=st.session_state.github_token,
                type="password", placeholder="ghp_xxxxxxxxxxxx"
            )
        with col_save:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Save 💾", use_container_width=True):
                st.session_state.groq_key = new_groq
                st.session_state.github_token = new_gh
                save_config({"groq_api_key": new_groq, "github_token": new_gh})
                st.success("Keys saved locally!")
        if st.session_state.groq_key:
            st.markdown('<div class="key-saved">✓ Groq key loaded</div>', unsafe_allow_html=True)

st.markdown("---")

# ── MAIN INPUT ───────────────────────────────────────────────────────────
history = load_history()
left_col, right_col = st.columns([2, 1])

with left_col:
    repo_url = st.text_input(
        "GitHub Repository URL",
        value=st.session_state.prefill_url,
        placeholder="https://github.com/langchain-ai/langchain"
    )
    num_commits = st.slider("Commits to analyse", 5, 50, 15, 5)
    gen_col, _ = st.columns([1, 3])
    with gen_col:
        generate_btn = st.button("⚡ Generate", use_container_width=True)

with right_col:
    if history:
        st.markdown("<div style='font-size:0.8rem; color:#64748b; margin-bottom:0.5rem; font-family:JetBrains Mono,monospace; letter-spacing:0.08em;'>RECENT SEARCHES</div>", unsafe_allow_html=True)
        for i, h in enumerate(history[:5]):
            repo_display = h["repo"].replace("https://github.com/", "")
            if st.button(f"↩ {repo_display}", key=f"hist_{h['ts']}_{i}", use_container_width=True):
                st.session_state.prefill_url = h["repo"]
                st.rerun()
    else:
        st.markdown("""
        <div style='background:#13131f; border:1px dashed #2a2a3d; border-radius:10px; padding:1.2rem; text-align:center;'>
            <div style='color:#334155; font-size:0.82rem;'>Recent searches appear here</div>
        </div>""", unsafe_allow_html=True)
# ── GENERATE ─────────────────────────────────────────────────────────────
if generate_btn:
    if not st.session_state.groq_key:
        st.error("Add your Groq API key above first.")
        st.stop()
    if not repo_url:
        st.error("Paste a GitHub repo URL.")
        st.stop()

    owner, repo = parse_repo_url(repo_url)
    if not owner:
        st.error("Invalid URL. Use: https://github.com/username/repo")
        st.stop()

    if st.session_state.github_token:
        os.environ["GITHUB_TOKEN"] = st.session_state.github_token

    with st.status("🔄 Transforming commits into content...", expanded=True) as status:
        st.write(f"📡 Fetching last {num_commits} commits from `{owner}/{repo}`...")
        commits, error = fetch_commits(repo_url, num_commits)
        if error:
            status.update(label="Failed", state="error")
            st.error(error)
            st.stop()
        st.write(f"✅ {len(commits)} commits fetched. Generating release notes...")
        try:
            changelog = generate_changelog(commits, st.session_state.groq_key)
        except Exception as e:
            status.update(label="LLM error", state="error")
            st.error(f"Groq error: {e}")
            st.stop()
        st.write("💼 Writing LinkedIn post...")
        linkedin = generate_linkedin_post(changelog, f"{owner}/{repo}", st.session_state.groq_key)
        st.write("🐦 Writing tweet...")
        tweet = generate_tweet(changelog, f"{owner}/{repo}", st.session_state.groq_key)
        status.update(label="Done! Content ready below 👇", state="complete")

    save_history({"repo": repo_url, "ts": datetime.now().strftime("%d %b %Y, %H:%M"), "commits": len(commits)})
    st.session_state.results = {
        "changelog": changelog, "linkedin": linkedin,
        "tweet": tweet, "repo": f"{owner}/{repo}"
    }

# ── RESULTS ──────────────────────────────────────────────────────────────
if st.session_state.results:
    r = st.session_state.results
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📋 Release Notes", "💼 LinkedIn Post", "🐦 Tweet"])

    with tab1:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:0.72rem;letter-spacing:0.12em;color:#f59e0b;text-transform:uppercase;margin-bottom:0.8rem;">RELEASE NOTES · MARKDOWN</div>', unsafe_allow_html=True)
        st.markdown(r["changelog"])
        st.markdown("---")
        st.code(r["changelog"], language=None)
        st.download_button(
            "⬇ Download as .md", r["changelog"],
            file_name=f"{r['repo'].split('/')[-1]}-changelog.md",
            mime="text/markdown"
        )

    with tab2:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:0.72rem;letter-spacing:0.12em;color:#f59e0b;text-transform:uppercase;margin-bottom:0.8rem;">LINKEDIN POST · COPY & POST</div>', unsafe_allow_html=True)
        st.code(r["linkedin"], language=None)
        st.markdown(f"""
        <div style='margin-top:1rem;'>
            <a href="https://www.linkedin.com/feed/" target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;padding:0.5rem 1rem;border-radius:8px;
                      background:#0077b5;color:white;text-decoration:none;font-weight:600;font-size:0.85rem;">
                🔗 Open LinkedIn → paste above
            </a>
        </div>
        <div style='margin-top:0.6rem;font-size:0.76rem;color:#475569;'>
            💡 Copy the text above → click → paste into "Start a post"
        </div>""", unsafe_allow_html=True)

    with tab3:
        char_count = len(r["tweet"])
        char_class = "char-ok" if char_count <= 280 else "char-warn"
        st.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:0.72rem;letter-spacing:0.12em;color:#f59e0b;text-transform:uppercase;margin-bottom:0.8rem;">TWEET · {char_count}/280 CHARS</div>', unsafe_allow_html=True)
        st.code(r["tweet"], language=None)
        st.markdown(f'<div class="{char_class}">{"✓" if char_count<=280 else "⚠"} {char_count} characters</div>', unsafe_allow_html=True)
        tweet_encoded = urllib.parse.quote(r["tweet"][:280])
        st.markdown(f"""
        <div style='margin-top:1rem;'>
            <a href="https://twitter.com/intent/tweet?text={tweet_encoded}" target="_blank"
               style="display:inline-flex;align-items:center;gap:8px;padding:0.5rem 1rem;border-radius:8px;
                      background:#1da1f2;color:white;text-decoration:none;font-weight:600;font-size:0.85rem;">
                🐦 Post to X / Twitter directly
            </a>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div style='text-align:center;color:#334155;font-size:0.78rem;font-family:JetBrains Mono,monospace;'>
        Generated for · {r['repo']} · Changelog AI by Vaishnavi Gahoi
    </div>""", unsafe_allow_html=True)
