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

/* ── Auth Page ────────────────────────────────────────────── */
.auth-page-wrap {
    position: fixed; inset: 0; z-index: 9999;
    display: flex; align-items: center; justify-content: center;
    background: #060913;
    overflow: hidden;
    font-family: 'Inter', sans-serif;
}

/* animated blobs */
.auth-blob {
    position: absolute; border-radius: 50%; filter: blur(80px); opacity: .55;
    animation: blobDrift 14s ease-in-out infinite alternate;
}
.auth-blob-1 { width:520px;height:520px; background:radial-gradient(circle,#6366f1,#4f46e5); top:-160px;left:-120px; animation-delay:0s; }
.auth-blob-2 { width:400px;height:400px; background:radial-gradient(circle,#0ea5e9,#06b6d4); bottom:-100px;right:-80px; animation-delay:-5s; }
.auth-blob-3 { width:300px;height:300px; background:radial-gradient(circle,#f472b6,#e11d48); top:30%;right:10%; opacity:.35; animation-delay:-9s; }
@keyframes blobDrift {
    0%   { transform: translate(0,0) scale(1); }
    50%  { transform: translate(30px,-40px) scale(1.08); }
    100% { transform: translate(-20px,30px) scale(.94); }
}

/* grid overlay */
.auth-grid {
    position: absolute; inset: 0;
    background-image: linear-gradient(rgba(99,102,241,.07) 1px,transparent 1px),
                      linear-gradient(90deg,rgba(99,102,241,.07) 1px,transparent 1px);
    background-size: 44px 44px;
    mask-image: radial-gradient(ellipse 80% 70% at 50% 50%, black 40%, transparent 100%);
}

/* glass card */
.auth-glass {
    position: relative; z-index: 2;
    width: 480px; max-width: calc(100vw - 2rem);
    padding: 2.5rem 2.75rem 2.75rem;
    border-radius: 1.75rem;
    background: rgba(15,20,40,.72);
    backdrop-filter: blur(24px) saturate(180%);
    -webkit-backdrop-filter: blur(24px) saturate(180%);
    border: 1px solid rgba(255,255,255,.1);
    box-shadow: 0 0 0 1px rgba(99,102,241,.15),
                0 32px 80px rgba(0,0,0,.5),
                inset 0 1px 0 rgba(255,255,255,.07);
    animation: cardIn .55s cubic-bezier(.22,1,.36,1) both;
}
@keyframes cardIn {
    from { opacity:0; transform: translateY(28px) scale(.97); }
    to   { opacity:1; transform: none; }
}

/* logo mark */
.auth-logo-ring {
    display: flex; align-items: center; justify-content: center;
    width: 64px; height: 64px; border-radius: 20px; margin: 0 auto 1.25rem;
    background: linear-gradient(135deg,#6366f1 0%,#0ea5e9 100%);
    box-shadow: 0 0 0 8px rgba(99,102,241,.15), 0 16px 32px rgba(99,102,241,.35);
    font-size: 2rem;
    animation: logoPulse 3s ease-in-out infinite;
}
@keyframes logoPulse {
    0%,100% { box-shadow: 0 0 0 8px rgba(99,102,241,.15), 0 16px 32px rgba(99,102,241,.35); }
    50%      { box-shadow: 0 0 0 14px rgba(99,102,241,.08), 0 16px 32px rgba(99,102,241,.5); }
}

.auth-title {
    text-align: center;
    font-size: 2rem !important; font-weight: 800 !important;
    letter-spacing: -.04em;
    background: linear-gradient(135deg,#fff 30%,#a5b4fc);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: .25rem !important;
}
.auth-sub {
    text-align: center; color: #94a3b8;
    font-size: .95rem; margin-bottom: 2rem;
}

/* tab switcher */
.auth-tab-bar {
    display: flex; gap: 6px;
    background: rgba(255,255,255,.06);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 999px; padding: 5px;
    margin-bottom: 2rem;
}
.auth-tab-btn {
    flex: 1; padding: .55rem 1rem;
    border: none; border-radius: 999px;
    font-size: .9rem; font-weight: 600;
    cursor: pointer; transition: all .25s ease;
    background: transparent; color: #64748b;
}
.auth-tab-btn.cf-active {
    background: linear-gradient(135deg,#6366f1,#0ea5e9);
    color: #fff;
    box-shadow: 0 6px 20px rgba(99,102,241,.4);
}

/* input fields */
.cf-field { margin-bottom: 1.25rem; }
.cf-label {
    display: block; font-size: .82rem; font-weight: 600;
    color: #94a3b8; letter-spacing: .06em; text-transform: uppercase;
    margin-bottom: .5rem;
}
.cf-input-wrap { position: relative; }
.cf-input-icon {
    position: absolute; left: 1rem; top: 50%; transform: translateY(-50%);
    font-size: 1.1rem; pointer-events: none;
}
.cf-input {
    width: 100%; padding: .82rem 1rem .82rem 2.75rem;
    border-radius: .9rem;
    border: 1.5px solid rgba(255,255,255,.1);
    background: rgba(255,255,255,.05);
    color: #f1f5f9; font-size: .97rem;
    outline: none; transition: all .2s ease;
    font-family: 'Inter', sans-serif;
}
.cf-input::placeholder { color: #475569; }
.cf-input:focus {
    border-color: #6366f1;
    background: rgba(99,102,241,.1);
    box-shadow: 0 0 0 4px rgba(99,102,241,.2);
}

/* password strength */
.cf-strength-bar {
    display: flex; gap: 4px; margin-top: .5rem; height: 4px;
}
.cf-seg {
    flex: 1; border-radius: 99px; background: rgba(255,255,255,.1);
    transition: background .3s ease;
}
.cf-strength-label { font-size: .74rem; color: #64748b; margin-top: .35rem; }

/* primary button */
.cf-btn {
    width: 100%; padding: .9rem 1.5rem; margin-top: .5rem;
    border: none; border-radius: .9rem; cursor: pointer;
    font-size: 1rem; font-weight: 700; color: #fff;
    background: linear-gradient(135deg,#6366f1 0%,#0ea5e9 100%);
    box-shadow: 0 10px 30px rgba(99,102,241,.35);
    transition: all .22s ease;
    position: relative; overflow: hidden;
    font-family: 'Inter', sans-serif;
}
.cf-btn:hover { transform: translateY(-2px); box-shadow: 0 16px 40px rgba(99,102,241,.5); }
.cf-btn:active { transform: translateY(0); }
.cf-btn::after {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(135deg,rgba(255,255,255,.18),transparent);
    border-radius: inherit;
}

/* divider */
.cf-divider {
    display: flex; align-items: center; gap: .75rem;
    color: #334155; font-size: .8rem; margin: 1.25rem 0;
}
.cf-divider::before,.cf-divider::after {
    content:''; flex:1; height:1px; background:rgba(255,255,255,.08);
}

/* panels */
.cf-panel { animation: panelIn .3s ease both; }
@keyframes panelIn {
    from { opacity:0; transform: translateX(14px); }
    to   { opacity:1; transform: none; }
}

/* feature pills */
.cf-pills {
    display: flex; flex-wrap: wrap; gap: .5rem;
    margin-top: 1.75rem; justify-content: center;
}
.cf-pill {
    display: inline-flex; align-items: center; gap: .4rem;
    padding: .38rem .85rem;
    border: 1px solid rgba(99,102,241,.3);
    border-radius: 999px; background: rgba(99,102,241,.08);
    color: #a5b4fc; font-size: .78rem; font-weight: 500;
}

/* canvas particles */
#auth-canvas {
    position: absolute; inset: 0; z-index: 1; pointer-events: none;
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
    # ── Inject full-page auth shell (HTML/CSS/JS) ─────────────────────────
    st.markdown("""
    <div class="auth-page-wrap" id="auth-root">
        <!-- animated blobs -->
        <div class="auth-blob auth-blob-1"></div>
        <div class="auth-blob auth-blob-2"></div>
        <div class="auth-blob auth-blob-3"></div>
        <!-- grid + particles -->
        <div class="auth-grid"></div>
        <canvas id="auth-canvas"></canvas>
        <!-- glass card -->
        <div class="auth-glass">
            <div class="auth-logo-ring">🧠</div>
            <h1 class="auth-title">CogniFlow</h1>
            <p class="auth-sub">Enterprise AI Knowledge Assistant</p>
            <!-- tab bar -->
            <div class="auth-tab-bar">
                <button class="auth-tab-btn cf-active" id="tab-login-btn" onclick="cfSwitchTab('login')">Sign In</button>
                <button class="auth-tab-btn" id="tab-register-btn" onclick="cfSwitchTab('register')">Create Account</button>
            </div>
            <!-- Login Panel -->
            <div id="cf-login-panel" class="cf-panel">
                <div class="cf-field">
                    <label class="cf-label">Username</label>
                    <div class="cf-input-wrap">
                        <span class="cf-input-icon">👤</span>
                        <input id="cf-login-user" class="cf-input" type="text" placeholder="Enter your username" autocomplete="username" />
                    </div>
                </div>
                <div class="cf-field">
                    <label class="cf-label">Password</label>
                    <div class="cf-input-wrap">
                        <span class="cf-input-icon">🔑</span>
                        <input id="cf-login-pass" class="cf-input" type="password" placeholder="Enter your password" autocomplete="current-password" />
                    </div>
                </div>
                <button class="cf-btn" onclick="cfDoLogin()">Sign In →</button>
                <div class="cf-pills">
                    <span class="cf-pill">⚡ Instant answers</span>
                    <span class="cf-pill">🔒 JWT secured</span>
                    <span class="cf-pill">🤖 Agentic AI</span>
                </div>
            </div>
            <!-- Register Panel -->
            <div id="cf-register-panel" class="cf-panel" style="display:none">
                <div class="cf-field">
                    <label class="cf-label">Username</label>
                    <div class="cf-input-wrap">
                        <span class="cf-input-icon">👤</span>
                        <input id="cf-reg-user" class="cf-input" type="text" placeholder="Choose a username (min 3 chars)" autocomplete="username" />
                    </div>
                </div>
                <div class="cf-field">
                    <label class="cf-label">Password</label>
                    <div class="cf-input-wrap">
                        <span class="cf-input-icon">🔑</span>
                        <input id="cf-reg-pass" class="cf-input" type="password" placeholder="Create a strong password" autocomplete="new-password" oninput="cfStrength(this.value)" />
                    </div>
                    <div class="cf-strength-bar">
                        <div class="cf-seg" id="seg0"></div>
                        <div class="cf-seg" id="seg1"></div>
                        <div class="cf-seg" id="seg2"></div>
                        <div class="cf-seg" id="seg3"></div>
                    </div>
                    <div class="cf-strength-label" id="cf-strength-lbl">Enter a password</div>
                </div>
                <button class="cf-btn" onclick="cfDoRegister()">Create Account →</button>
                <div class="cf-pills">
                    <span class="cf-pill">📄 PDF indexing</span>
                    <span class="cf-pill">🌐 Web search</span>
                    <span class="cf-pill">💬 Memory</span>
                </div>
            </div>
            <!-- status -->
            <div id="cf-status" style="margin-top:1rem;font-size:.88rem;text-align:center;min-height:1.4em"></div>
        </div>
    </div>

    <script>
    (function(){
        /* ── Particle canvas ── */
        const canvas = document.getElementById('auth-canvas');
        const ctx    = canvas ? canvas.getContext('2d') : null;
        let W, H, particles = [];
        function resize(){
            if(!canvas) return;
            W = canvas.width  = window.innerWidth;
            H = canvas.height = window.innerHeight;
        }
        function mkPart(){
            return {
                x: Math.random()*W, y: Math.random()*H,
                r: Math.random()*1.8+.4,
                vx: (Math.random()-.5)*.35,
                vy: (Math.random()-.5)*.35,
                a: Math.random()*.5+.2
            };
        }
        function initParticles(){
            particles = Array.from({length:90}, mkPart);
        }
        function drawParticles(){
            if(!ctx) return;
            ctx.clearRect(0,0,W,H);
            particles.forEach(p=>{
                p.x += p.vx; p.y += p.vy;
                if(p.x<0)p.x=W; if(p.x>W)p.x=0;
                if(p.y<0)p.y=H; if(p.y>H)p.y=0;
                ctx.beginPath();
                ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
                ctx.fillStyle = `rgba(139,92,246,${p.a})`;
                ctx.fill();
            });
            requestAnimationFrame(drawParticles);
        }
        window.addEventListener('resize', ()=>{ resize(); initParticles(); });
        resize(); initParticles(); drawParticles();

        /* ── Tab switch ── */
        window.cfSwitchTab = function(tab){
            const loginPanel    = document.getElementById('cf-login-panel');
            const registerPanel = document.getElementById('cf-register-panel');
            const btnL = document.getElementById('tab-login-btn');
            const btnR = document.getElementById('tab-register-btn');
            clearStatus();
            if(tab==='login'){
                loginPanel.style.display=''; registerPanel.style.display='none';
                btnL.classList.add('cf-active'); btnR.classList.remove('cf-active');
                loginPanel.classList.remove('cf-panel'); void loginPanel.offsetWidth;
                loginPanel.classList.add('cf-panel');
            } else {
                loginPanel.style.display='none'; registerPanel.style.display='';
                btnR.classList.add('cf-active'); btnL.classList.remove('cf-active');
                registerPanel.classList.remove('cf-panel'); void registerPanel.offsetWidth;
                registerPanel.classList.add('cf-panel');
            }
        };

        /* ── Status ── */
        function setStatus(msg, isErr){
            const el = document.getElementById('cf-status');
            if(!el) return;
            el.style.color = isErr ? '#f87171' : '#34d399';
            el.textContent = msg;
        }
        function clearStatus(){
            const el = document.getElementById('cf-status');
            if(el) el.textContent='';
        }

        /* ── Password strength ── */
        const COLORS = ['#ef4444','#f97316','#eab308','#22c55e'];
        const LABELS = ['Too short','Weak — add symbols','Fair — add numbers','Strong ✓'];
        window.cfStrength = function(v){
            let score = 0;
            if(v.length>=8) score++;
            if(/[A-Z]/.test(v)&&/[a-z]/.test(v)) score++;
            if(/[0-9]/.test(v)) score++;
            if(/[^A-Za-z0-9]/.test(v)) score++;
            for(let i=0;i<4;i++){
                const seg = document.getElementById('seg'+i);
                if(seg) seg.style.background = i<score ? COLORS[score-1] : 'rgba(255,255,255,.1)';
            }
            const lbl = document.getElementById('cf-strength-lbl');
            if(lbl){ lbl.textContent = v.length>0 ? LABELS[Math.min(score,3)] : 'Enter a password'; lbl.style.color = score>0?COLORS[score-1]:'#64748b'; }
        };

        /* ── Button loading ── */
        function setBtnLoading(btn, loading){
            if(!btn) return;
            btn.disabled = loading;
            btn.style.opacity = loading ? '.7' : '1';
            btn.textContent = loading ? 'Please wait...' : btn._label;
        }

        /* ── Login ── */
        window.cfDoLogin = async function(){
            const u = document.getElementById('cf-login-user').value.trim();
            const p = document.getElementById('cf-login-pass').value;
            if(!u||!p){ setStatus('Please fill in all fields.', true); return; }
            const btn = document.querySelector('#cf-login-panel .cf-btn');
            if(btn) btn._label = btn.textContent;
            setBtnLoading(btn, true);
            clearStatus();
            try {
                const res = await fetch('/api/auth/login', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({username:u, password:p})
                });
                const data = await res.json();
                if(res.ok && data.access_token){
                    // write into Streamlit hidden field + trigger form submit
                    setStatus('✓ Signed in! Loading your workspace…', false);
                    document.getElementById('cf-token-store').value = data.access_token;
                    document.getElementById('cf-login-trigger').click();
                } else {
                    const msg = typeof data.detail==='string' ? data.detail : 'Invalid credentials.';
                    setStatus(msg, true);
                }
            } catch(e){ setStatus('Backend unavailable.', true); }
            finally { setBtnLoading(btn, false); }
        };

        /* ── Register ── */
        window.cfDoRegister = async function(){
            const u = document.getElementById('cf-reg-user').value.trim();
            const p = document.getElementById('cf-reg-pass').value;
            if(!u||!p){ setStatus('Please fill in all fields.', true); return; }
            const btn = document.querySelector('#cf-register-panel .cf-btn');
            if(btn) btn._label = btn.textContent;
            setBtnLoading(btn, true);
            clearStatus();
            try {
                const res = await fetch('/api/auth/register', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({username:u, password:p})
                });
                const data = await res.json();
                if(res.ok){
                    setStatus('✓ Account created! Signing you in…', false);
                    // auto-login
                    const lr = await fetch('/api/auth/login', {
                        method:'POST', headers:{'Content-Type':'application/json'},
                        body: JSON.stringify({username:u, password:p})
                    });
                    const ld = await lr.json();
                    if(lr.ok && ld.access_token){
                        document.getElementById('cf-token-store').value = ld.access_token;
                        document.getElementById('cf-login-trigger').click();
                    }
                } else {
                    const msg = typeof data.detail==='string' ? data.detail :
                        (Array.isArray(data.detail) ? data.detail.map(d=>d.msg||d).join(' ') : 'Registration failed.');
                    setStatus(msg, true);
                }
            } catch(e){ setStatus('Backend unavailable.', true); }
            finally { setBtnLoading(btn, false); }
        };

        /* enter key support */
        ['cf-login-user','cf-login-pass'].forEach(id=>{
            const el = document.getElementById(id);
            if(el) el.addEventListener('keydown', e=>{ if(e.key==='Enter') window.cfDoLogin(); });
        });
        ['cf-reg-user','cf-reg-pass'].forEach(id=>{
            const el = document.getElementById(id);
            if(el) el.addEventListener('keydown', e=>{ if(e.key==='Enter') window.cfDoRegister(); });
        });
    })();
    </script>
    """, unsafe_allow_html=True)

    # Hidden Streamlit form — captures the JWT from the JS fetch and triggers a rerun
    with st.form("__cf_auth_bridge", clear_on_submit=True):
        token_input = st.text_input("token", key="cf_token_store", label_visibility="collapsed")
        trigger = st.form_submit_button("go", type="primary")
        if trigger and token_input:
            st.session_state.token = token_input
            st.rerun()

    # inject IDs so JS can find the hidden inputs
    st.markdown("""
    <script>
    (function waitForInputs(){
        const inp = document.querySelector('input[data-testid="stTextInput"]') ||
                    document.querySelector('.stTextInput input');
        const btn = document.querySelector('button[kind="primaryFormSubmit"]') ||
                    document.querySelector('.stFormSubmitButton button');
        if(inp && btn){
            inp.id = 'cf-token-store';
            btn.id = 'cf-login-trigger';
            // hide the Streamlit form from view
            const form = inp.closest('[data-testid="stForm"]') ||
                         inp.closest('form') ||
                         inp.parentElement?.parentElement?.parentElement;
            if(form) form.style.cssText='position:absolute;left:-9999px;opacity:0;pointer-events:none;height:0;overflow:hidden';
        } else { setTimeout(waitForInputs, 80); }
    })();
    </script>
    """, unsafe_allow_html=True)

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
