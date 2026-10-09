import hashlib
import os
import re
import requests
import streamlit as st
from datetime import datetime

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="CogniFlow | Enterprise AI Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Professional Design System
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap');

:root {
    --primary: #2563eb;
    --primary-dark: #1e40af;
    --primary-light: #3b82f6;
    --secondary: #64748b;
    --accent: #06b6d4;
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --background: #f8fafc;
    --surface: #ffffff;
    --surface-hover: #f1f5f9;
    --border: #e2e8f0;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
    --radius-sm: 0.375rem;
    --radius-md: 0.5rem;
    --radius-lg: 0.75rem;
    --radius-xl: 1rem;
}

* {
    box-sizing: border-box;
}

.stApp {
    background: var(--background);
    color: var(--text-primary);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Playfair Display', Georgia, serif;
    color: var(--text-primary);
    font-weight: 600;
    line-height: 1.2;
}

h1 { font-size: 2.5rem !important; margin-bottom: 0.5rem; }
h2 { font-size: 2rem !important; margin-bottom: 0.5rem; }
h3 { font-size: 1.5rem !important; margin-bottom: 0.5rem; }

p {
    color: var(--text-secondary);
    line-height: 1.6;
    margin-bottom: 1rem;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 1.5rem;
}

[data-testid="stSidebar"] > div:first-child {
    padding: 0;
}

/* Brand Section */
.brand-section {
    padding: 0 0 2rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 2rem;
}

.brand-logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
}

.brand-icon {
    font-size: 2rem;
    line-height: 1;
}

.brand-name {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.025em;
}

.brand-tagline {
    font-size: 0.875rem;
    color: var(--text-muted);
    font-weight: 500;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

/* Navigation Buttons */
.nav-button {
    width: 100%;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    background: var(--surface);
    color: var(--text-primary);
    font-weight: 500;
    text-align: left;
    transition: all 0.2s ease;
    cursor: pointer;
}

.nav-button:hover {
    background: var(--surface-hover);
    border-color: var(--primary);
    color: var(--primary);
}

.nav-button.primary {
    background: var(--primary);
    color: white;
    border-color: var(--primary);
}

.nav-button.primary:hover {
    background: var(--primary-dark);
    border-color: var(--primary-dark);
}

/* Section Headers */
.section-header {
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin: 2rem 0 1rem 0;
}

/* Document Cards */
.document-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1rem;
    margin-bottom: 0.75rem;
    transition: all 0.2s ease;
}

.document-card:hover {
    border-color: var(--primary);
    box-shadow: var(--shadow-md);
}

.document-name {
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
}

.document-meta {
    font-size: 0.75rem;
    color: var(--text-muted);
}

/* Login Page Styling */
.login-container {
    max-width: 480px;
    margin: 4rem auto;
    padding: 2rem;
}

.login-header {
    text-align: center;
    margin-bottom: 2rem;
}

.login-logo {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.login-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.login-subtitle {
    color: var(--text-secondary);
    font-size: 1rem;
}

.login-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-xl);
    padding: 2rem;
    box-shadow: var(--shadow-lg);
}

.auth-tabs {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    background: var(--background);
    padding: 0.25rem;
    border-radius: var(--radius-md);
}

.auth-tab {
    flex: 1;
    padding: 0.75rem;
    text-align: center;
    border-radius: var(--radius-sm);
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
    background: transparent;
}

.auth-tab.active {
    background: var(--surface);
    color: var(--primary);
    box-shadow: var(--shadow-sm);
}

.auth-tab:hover:not(.active) {
    background: var(--surface-hover);
}

/* Form Styling */
.form-group {
    margin-bottom: 1.5rem;
}

.form-label {
    display: block;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
}

.form-input {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    font-size: 1rem;
    background: var(--surface);
    color: var(--text-primary);
    transition: all 0.2s ease;
}

.form-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.form-input::placeholder {
    color: var(--text-muted);
}

/* Button Styling */
.btn {
    width: 100%;
    padding: 0.875rem 1.5rem;
    border: none;
    border-radius: var(--radius-md);
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
}

.btn-primary {
    background: var(--primary);
    color: white;
}

.btn-primary:hover {
    background: var(--primary-dark);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
}

.btn-secondary {
    background: var(--surface);
    color: var(--text-primary);
    border: 1px solid var(--border);
}

.btn-secondary:hover {
    background: var(--surface-hover);
    border-color: var(--primary);
    color: var(--primary);
}

/* Dashboard Styling */
.dashboard-header {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 1.5rem 2rem;
    margin-bottom: 2rem;
}

.dashboard-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.5rem;
}

.dashboard-subtitle {
    color: var(--text-secondary);
    font-size: 1rem;
}

/* Agentic Toggle */
.agentic-section {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.05) 0%, rgba(6, 182, 212, 0.05) 100%);
    border: 1px solid rgba(37, 99, 235, 0.2);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 2rem;
}

.agentic-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
}

.agentic-title {
    font-weight: 600;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.agentic-badge {
    background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}

.agentic-description {
    color: var(--text-secondary);
    font-size: 0.875rem;
    line-height: 1.5;
}

/* Chat Styling */
.chat-container {
    max-width: 900px;
    margin: 0 auto;
}

.chat-message {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow-sm);
}

.chat-message.user {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.05) 0%, rgba(37, 99, 235, 0.02) 100%);
    border-left: 3px solid var(--primary);
}

.chat-message.assistant {
    background: var(--surface);
    border-left: 3px solid var(--accent);
}

.message-content {
    line-height: 1.6;
    color: var(--text-primary);
}

.source-reference {
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    font-size: 0.75rem;
    color: var(--text-muted);
}

/* Input Styling */
.chat-input-container {
    max-width: 900px;
    margin: 2rem auto;
}

/* Upload Section */
.upload-section {
    background: var(--surface);
    border: 2px dashed var(--border);
    border-radius: var(--radius-lg);
    padding: 2rem;
    text-align: center;
    transition: all 0.2s ease;
}

.upload-section:hover {
    border-color: var(--primary);
    background: var(--surface-hover);
}

.upload-icon {
    font-size: 2rem;
    margin-bottom: 1rem;
    color: var(--text-muted);
}

.upload-text {
    color: var(--text-secondary);
    font-weight: 500;
}

.upload-subtext {
    color: var(--text-muted);
    font-size: 0.875rem;
    margin-top: 0.5rem;
}

/* Stats Cards */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    text-align: center;
}

.stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: var(--primary);
    font-family: 'Playfair Display', Georgia, serif;
}

.stat-label {
    font-size: 0.875rem;
    color: var(--text-muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.25rem;
}


/* Chatbot space redesign */
.block-container { max-width: 1480px; padding: 2rem 3rem 4rem; }
.stApp > header { background: transparent; }
.login-container {
    max-width: 760px; margin: 2.5rem auto 1.25rem; padding: 2.25rem 2rem 1.5rem;
    border-radius: 1.75rem;
    background: radial-gradient(circle at 15% 15%, rgba(99,102,241,.22), transparent 32%), radial-gradient(circle at 85% 10%, rgba(6,182,212,.18), transparent 30%), linear-gradient(135deg,#111827,#1e293b);
    box-shadow: 0 24px 70px rgba(15,23,42,.22);
}
.login-header { margin-bottom: 0; }
.login-logo { display:inline-flex; align-items:center; justify-content:center; width:4.75rem; height:4.75rem; border-radius:1.5rem; background:linear-gradient(135deg,#f472b6,#8b5cf6 65%,#22d3ee); box-shadow:0 14px 28px rgba(139,92,246,.35); font-size:2.5rem; }
.login-title { color:#f8fafc; font-size:3rem; letter-spacing:-.05em; }
.login-subtitle { color:#cbd5e1; font-size:1.08rem; }
.login-card { max-width:560px; margin:0 auto; padding:1.75rem 2rem 2rem; border:1px solid rgba(148,163,184,.25); border-radius:1.5rem; background:rgba(255,255,255,.96); box-shadow:0 24px 60px rgba(15,23,42,.18); }
.login-card h3 { color:#0f172a; font-family:'Inter',sans-serif; font-size:1.35rem !important; }
.login-card [data-baseweb="input"] { border-radius:.85rem; }
.login-card button[kind="primary"] { border-radius:.85rem; background:linear-gradient(135deg,#4f46e5,#0891b2); border:none; box-shadow:0 10px 20px rgba(79,70,229,.2); }
.login-card button[kind="primary"]:hover { transform:translateY(-1px); }
.dashboard-header { position:relative; overflow:hidden; border:1px solid rgba(99,102,241,.18); border-radius:1.5rem; background:radial-gradient(circle at 92% 20%,rgba(34,211,238,.16),transparent 25%),linear-gradient(135deg,#fff,#eef2ff); padding:2rem 2.25rem; box-shadow:0 12px 30px rgba(15,23,42,.06); }
.dashboard-title { font-size:2.35rem; letter-spacing:-.04em; }
.chat-container { max-width:1080px; min-height:300px; margin:0 auto 1rem; padding:2.5rem 2rem; border:1px solid rgba(99,102,241,.16); border-radius:1.5rem; background:radial-gradient(circle at 15% 10%,rgba(99,102,241,.08),transparent 30%),linear-gradient(180deg,#fff,#f8fafc); box-shadow:0 14px 35px rgba(15,23,42,.06); }
.empty-chat-icon { display:inline-flex; align-items:center; justify-content:center; width:4.5rem; height:4.5rem; border-radius:1.35rem; background:linear-gradient(135deg,#eef2ff,#cffafe); font-size:2.25rem; box-shadow:0 12px 24px rgba(79,70,229,.14); }
.empty-chat-title { margin:1rem 0 .5rem; font-family:'Inter',sans-serif; font-size:1.65rem !important; }
.empty-chat-copy { max-width:560px; margin:0 auto 1.35rem; color:#64748b; }
.prompt-chip { display:inline-block; margin:.3rem; padding:.55rem .85rem; border:1px solid #c7d2fe; border-radius:999px; background:rgba(255,255,255,.8); color:#4338ca; font-size:.82rem; font-weight:600; }
[data-testid="stChatMessage"] { max-width:1080px; margin:0 auto .85rem; padding:.9rem 1.1rem; border:1px solid #e2e8f0; border-radius:1.2rem; background:#fff; box-shadow:0 8px 22px rgba(15,23,42,.055); }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { border-color:#c7d2fe; background:linear-gradient(135deg,#eef2ff,#fff); }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) { border-color:#bae6fd; background:linear-gradient(135deg,#f0f9ff,#fff); }
[data-testid="stChatMessageContent"] p { color:#1e293b; line-height:1.7; }
[data-testid="stChatInput"] { max-width:1080px; margin:1.2rem auto 0; }
[data-testid="stChatInput"] textarea { min-height:58px; border:2px solid #c7d2fe; border-radius:1.15rem; background:#fff; box-shadow:0 12px 28px rgba(79,70,229,.12); }
[data-testid="stChatInput"] textarea:focus { border-color:#6366f1; box-shadow:0 0 0 4px rgba(99,102,241,.14),0 12px 28px rgba(79,70,229,.12); }
[data-testid="stChatInput"] textarea::placeholder { color:#64748b !important; opacity:1 !important; }
[data-testid="stChatInput"] textarea { color:#0f172a !important; }
.source-reference { max-width:1080px; margin-left:auto; margin-right:auto; border-radius:.8rem; background:rgba(248,250,252,.72); padding:.75rem 1rem; }
@media (max-width:768px) { .block-container{padding:1rem .9rem 3rem;} .login-container{margin:1rem auto;padding:1.5rem 1rem;} .login-title{font-size:2.25rem;} .login-card{padding:1.25rem;} .dashboard-header{padding:1.35rem;} .chat-container{padding:1.5rem 1rem;} }


.login-card { display:none; }
[data-testid="stTabs"] { max-width:560px; margin:0 auto; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { gap:.35rem; padding:.35rem; border-radius:1rem; background:#e2e8f0; }
[data-testid="stTabs"] [data-baseweb="tab"] { flex:1; justify-content:center; border-radius:.75rem; color:#475569; font-weight:600; }
[data-testid="stTabs"] [aria-selected="true"] { background:#fff; color:#4338ca; box-shadow:0 4px 12px rgba(15,23,42,.08); }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display:none; }
[data-testid="stTabs"] [data-baseweb="tab-panel"] { margin-top:.75rem; padding:1.75rem 2rem 2rem; border:1px solid #e2e8f0; border-radius:1.5rem; background:rgba(255,255,255,.97); box-shadow:0 24px 60px rgba(15,23,42,.14); }
[data-testid="stTabs"] [data-baseweb="tab-panel"] h3 { color:#0f172a; font-family:'Inter',sans-serif; font-size:1.35rem !important; }
[data-testid="stTabs"] [data-baseweb="input"] { border-radius:.85rem; }
[data-testid="stTabs"] button[kind="primary"] { border-radius:.85rem; background:linear-gradient(135deg,#4f46e5,#0891b2); border:none; box-shadow:0 10px 20px rgba(79,70,229,.2); }


div[data-testid="stHorizontalBlock"] button {
    min-height: 3rem;
    border: 1px solid #c7d2fe;
    border-radius: 999px;
    background: rgba(255,255,255,.88);
    color: #4338ca;
    font-weight: 600;
    transition: all .2s ease;
}
div[data-testid="stHorizontalBlock"] button:hover {
    border-color: #6366f1;
    background: #eef2ff;
    color: #3730a3;
    transform: translateY(-1px);
    box-shadow: 0 8px 18px rgba(79,70,229,.12);
}

/* Responsive */
@media (max-width: 768px) {
    .login-container {
        margin: 2rem auto;
        padding: 1rem;
    }
    
    .dashboard-header {
        padding: 1rem;
    }
    
    .stats-grid {
        grid-template-columns: 1fr;
    }
}

/* Utility Classes */
.text-center { text-align: center; }
.text-muted { color: var(--text-muted); }
.mt-2 { margin-top: 0.5rem; }
.mt-4 { margin-top: 1rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)

# Session State
if "token" not in st.session_state:
    st.session_state.token = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "page" not in st.session_state:
    st.session_state.page = "login"

def _format_api_detail(detail):
    """Turn FastAPI/Pydantic error payloads into readable UI messages."""
    if isinstance(detail, dict):
        errors = detail.get("errors")
        if isinstance(errors, list):
            detail = errors
        elif detail.get("message"):
            return str(detail["message"])
    if isinstance(detail, list):
        messages = []
        for item in detail:
            if isinstance(item, dict):
                message = item.get("msg") or item.get("message") or "Invalid value."
                location = item.get("loc") or []
                field = next((str(value) for value in reversed(location) if value not in {"body", "query", "path"}), "")
                messages.append(f"{field}: {message}" if field else str(message))
            else:
                messages.append(str(item))
        return " ".join(messages)
    return str(detail or "The request could not be completed.")


def _unique_uploads(uploads):
    """Deduplicate repeated browser upload entries by filename and content."""
    unique = []
    seen = set()
    for upload in uploads or []:
        contents = upload.getvalue()
        fingerprint = (upload.name, len(contents), hashlib.sha256(contents).hexdigest())
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        unique.append((upload, contents))
    return unique


def _clean_answer_markers(answer):
    """Remove internal task-reference tokens before displaying an answer."""
    if not answer:
        return answer
    answer = re.sub(
        r"[\u3010\[]\s*Task\s*\d+\s*(?:answer|source)\s*[\u3011\]]",
        "",
        answer,
        flags=re.IGNORECASE,
    )
    answer = re.sub(r"\u3010[^\u3011\n]*\u3011", "", answer)
    answer = re.sub(r"\[[^\]]{1,200}\]\(https?://[^)]+\)", "", answer)
    answer = re.sub(r"[ \t]+([.,;:])", r"\1", answer)
    return re.sub(r"\n{3,}", "\n\n", answer).strip()


def api_request(method, path, **kwargs):
    headers = kwargs.pop("headers", {})
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        response = requests.request(method, f"{API_URL}{path}", headers=headers, timeout=60, **kwargs)
        if response.ok:
            return response.json()
        try:
            detail = response.json().get("detail", "The request could not be completed.")
        except ValueError:
            detail = f"The service returned an unexpected response (HTTP {response.status_code})."
        st.error(f"{_format_api_detail(detail)} [{method} {path}]")
    except requests.RequestException:
        st.error(f"The knowledge service is unavailable at {API_URL}. Please check that the backend is running.")
    return None


def render_sources(sources):
    """Render document filenames and web URLs without assuming one schema."""
    if not sources:
        return

    st.markdown('<div class="source-reference"><strong>Sources:</strong></div>', unsafe_allow_html=True)
    for source in sources:
        if isinstance(source, str):
            st.markdown(f"- {source}")
            continue
        label = source.get("filename") or source.get("title") or source.get("url", "Source")
        url = source.get("url")
        # Community discussions are useful leads but are not authoritative release sources.
        if url and "discuss.python.org" in str(url).lower():
            continue
        if url:
            st.markdown(f"- [{label}]({url})")
        else:
            st.markdown(f"- {label}")

# Login Page
if not st.session_state.token:
    st.markdown("""
    <div class="login-container">
        <div class="login-header">
            <div class="login-logo">🧠</div>
            <h1 class="login-title">CogniFlow</h1>
            <p class="login-subtitle">Enterprise AI Knowledge Assistant</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Auth Tabs
        tab1, tab2 = st.tabs(["Sign In", "Create Account"])
        
        with tab1:
            st.markdown('<h3 style="margin-bottom: 1.5rem;">Welcome Back</h3>', unsafe_allow_html=True)
            with st.form("login"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In", type="primary")
                
                if submitted:
                    result = api_request("POST", "/api/auth/login", json={"username": username, "password": password})
                    if result:
                        st.session_state.token = result["access_token"]
                        st.rerun()
        
        with tab2:
            st.markdown('<h3 style="margin-bottom: 1.5rem;">Create Account</h3>', unsafe_allow_html=True)
            st.markdown('<p class="text-muted">Join CogniFlow to access intelligent document analysis and AI-powered knowledge management.</p>', unsafe_allow_html=True)
            with st.form("register"):
                new_username = st.text_input("Username", placeholder="Choose a username")
                new_password = st.text_input("Password", type="password", placeholder="Create a password")
                submitted = st.form_submit_button("Create Account", type="primary")
                
                if submitted:
                    result = api_request("POST", "/api/auth/register", json={"username": new_username, "password": new_password})
                    if result:
                        st.success("✓ Account created successfully! Please sign in.")
        
    st.stop()

# Dashboard
st.markdown("""
<div class="dashboard-header">
    <h1 class="dashboard-title">CogniFlow Dashboard</h1>
    <p class="dashboard-subtitle">Intelligent Enterprise Knowledge Management</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("""
    <div class="brand-section">
        <div class="brand-logo">
            <span class="brand-icon">🧠</span>
            <span class="brand-name">CogniFlow</span>
        </div>
        <div class="brand-tagline">Enterprise AI Assistant</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">Workspace</div>', unsafe_allow_html=True)
    
    if st.button("📝 New Conversation", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()
    
    if st.button("🚪 Sign Out", use_container_width=True):
        st.session_state.token = None
        st.session_state.page = "login"
        st.rerun()
    
    st.markdown('<div class="section-header">Knowledge Base</div>', unsafe_allow_html=True)
    
    uploads = st.file_uploader("Upload Documents", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")
    unique_uploads = _unique_uploads(uploads)
    
    if unique_uploads:
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        st.markdown('<div class="upload-icon">📄</div>', unsafe_allow_html=True)
        count_label = "file" if len(unique_uploads) == 1 else "files"
        st.markdown(f'<div class="upload-text">{len(unique_uploads)} {count_label} selected</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("📤 Upload & Index", use_container_width=True):
            with st.spinner("Processing documents..."):
                files = [("files", (upload.name, contents, "application/pdf")) for upload, contents in unique_uploads]
                if api_request("POST", "/api/documents/upload", files=files):
                    st.success("✓ Documents uploaded and indexed successfully!")
                    st.rerun()
    
    documents = api_request("GET", "/api/documents") or {"documents": []}
    
    if documents.get("documents"):
        st.markdown('<div class="section-header">Your Documents</div>', unsafe_allow_html=True)
        
        for document in documents.get("documents", []):
            st.markdown(f"""
            <div class="document-card">
                <div class="document-name">📄 {document['filename']}</div>
                <div class="document-meta">{document['size_bytes']:,} bytes</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🗑️ Remove", key=f"delete_{document['filename']}", use_container_width=True):
                if api_request("DELETE", f"/api/documents/{document['filename']}"):
                    st.success("Document removed successfully!")
                    st.rerun()
    else:
        st.markdown('<p class="text-muted text-center" style="padding: 2rem;">No documents uploaded yet</p>', unsafe_allow_html=True)

# Main Content Area
st.markdown('<div class="section-header">AI Assistant</div>', unsafe_allow_html=True)

# Agentic Mode Toggle
st.markdown("""
<div class="agentic-section">
    <div class="agentic-header">
        <div class="agentic-title">
            <span>🤖</span>
            <span>Agentic AI Mode</span>
        </div>
        <span class="agentic-badge">ADVANCED</span>
    </div>
    <div class="agentic-description">
        Enable multi-step reasoning, self-reflection, and adaptive problem-solving for complex queries.
    </div>
</div>
""", unsafe_allow_html=True)

agentic_mode = st.checkbox(
    "Enable Agentic RAG",
    value=False,
    help="Use multi-step reasoning, document retrieval, Tavily web search, reflection, and self-correction.",
)

# Stats Section
if documents.get("documents"):
    st.markdown('<div class="stats-grid">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{len(documents.get('documents', []))}</div>
        <div class="stat-label">Documents</div>
    </div>
    """, unsafe_allow_html=True)
    
    total_size = sum(doc['size_bytes'] for doc in documents.get('documents', []))
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{total_size:,}</div>
        <div class="stat-label">Total Bytes</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="stat-card">
        <div class="stat-value">{len(st.session_state.messages)}</div>
        <div class="stat-label">Messages</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Chat Interface
st.markdown('<div class="section-header">Conversation</div>', unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
    <div class="chat-container">
        <div style="text-align: center;">
            <div class="empty-chat-icon">💬</div>
            <h3 class="empty-chat-title">Your AI workspace is ready</h3>
            <p class="empty-chat-copy">Ask about your documents, explore current information, or use CogniFlow as your everyday knowledge partner.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    prompt_columns = st.columns(3)
    quick_prompt = None
    prompt_options = [
        ("Summarize my documents", "Summarize my uploaded documents and highlight the key points."),
        ("Find a policy detail", "Find the most relevant policy detail in my uploaded documents."),
        ("Research a current topic", "Research a current topic and provide a concise, source-backed answer."),
    ]
    for column, (label, prompt) in zip(prompt_columns, prompt_options):
        with column:
            if st.button(label, key=f"quick_prompt_{label}", use_container_width=True):
                quick_prompt = prompt
else:
    quick_prompt = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = _clean_answer_markers(message["content"]) if message["role"] == "assistant" else message["content"]
        st.markdown(content)
        render_sources(message.get("sources", []))

# Chat Input
question = st.chat_input("Ask CogniFlow anything...")
question = quick_prompt or question

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    
    with st.chat_message("user"):
        st.markdown(question)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = api_request("POST", "/api/chat", json={
                "question": question, 
                "session_id": st.session_state.session_id, 
                "agentic": agentic_mode
            })
        
        if result:
            st.session_state.session_id = result["session_id"]
            sources = result.get("sources", [])
            
            answer = _clean_answer_markers(result["answer"])
            st.markdown(answer)
            
            render_sources(sources)
            
            st.session_state.messages.append({
                "role": "assistant", 
                "content": answer, 
                "sources": sources
            })

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; color: var(--text-muted); font-size: 0.875rem;">
    <p>CogniFlow Enterprise AI Assistant • Powered by Advanced RAG & Agentic AI</p>
    <p style="margin-top: 0.5rem;">© 2026 Enterprise Knowledge Solutions</p>
</div>
""", unsafe_allow_html=True)
