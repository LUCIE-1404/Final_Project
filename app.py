import os
import tempfile
from html import escape

import streamlit as st

from export import get_export_filename, to_json, to_markdown
from gemini_service import (
    cleanup_transcript,
    generate_quiz,
    summarize_lecture,
    transcribe_audio,
)
from ml_core.predict import (
    DEFAULT_DIFFICULTY_METRICS_PATH,
    load_model_metrics,
    predict_difficulty,
    predict_topic,
)
from ui_components import render_sidebar


st.set_page_config(
    page_title="Lecture Lab",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    defaults = {
        "results": None,
        "source_filename": "",
        "processing_error": "",
        "uploader_reset_counter": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def apply_page_style():
    st.markdown(
        """
        <style>
        /* ═══════════════════════════════════════
           TOKENS
        ═══════════════════════════════════════ */
        :root {
            /* Surfaces */
            --s0: #faf7f2;        /* page bg   */
            --s1: #ffffff;        /* card bg   */
            --s2: #f5f1ea;        /* inset bg  */
            --s3: #ece7de;        /* deep inset */

            /* Borders */
            --b1: #e3ddd4;
            --b2: #d5cec3;
            --b3: #c4bbb0;

            /* Text */
            --t1: #1a1714;        /* heading   */
            --t2: #3a342e;        /* body      */
            --t3: #7a6f65;        /* secondary */
            --t4: #a89e95;        /* muted     */

            /* Brand — warm amber */
            --a1: #c26a10;        /* strong    */
            --a2: #e07c12;        /* base      */
            --a3: #f5a623;        /* bright    */
            --a4: #fef0d4;        /* tint      */
            --a5: #fff8ed;        /* faint     */

            /* Semantic */
            --ok:  #166534;
            --ok-bg: #f0fdf4;
            --ok-b: #bbf7d0;
            --err: #991b1b;
            --err-bg: #fef2f2;
            --info-bg: #eff6ff;
            --info-b: #bfdbfe;
            --info: #1d4ed8;

            /* Type stack — 100% reliable, no CDN */
            --f-serif: "Georgia", "Times New Roman", serif;
            --f-sans:  "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
            --f-mono:  "SF Mono", "Cascadia Code", "Fira Code", "Menlo", "Consolas", monospace;

            /* Geometry */
            --r1: 8px;
            --r2: 12px;
            --r3: 16px;

            /* Shadow */
            --sh1: 0 1px 3px rgba(26,23,20,.06), 0 1px 2px rgba(26,23,20,.04);
            --sh2: 0 4px 12px rgba(26,23,20,.08), 0 2px 4px rgba(26,23,20,.05);
            --sh3: 0 8px 28px rgba(26,23,20,.10), 0 3px 8px rgba(26,23,20,.06);
        }

        /* ═══════════════════════════════════════
           RESET / BASE
        ═══════════════════════════════════════ */
        *, *::before, *::after { box-sizing: border-box; }

        html, body, .stApp {
            background: var(--s0) !important;
            color: var(--t2);
            font-family: var(--f-sans);
            font-size: 15px;
            line-height: 1.6;
            -webkit-font-smoothing: antialiased;
        }

        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        #MainMenu { display: none !important; }

        .block-container {
            padding-top: 1.75rem;
            padding-bottom: 3rem;
            max-width: 1300px;
        }

        /* ═══════════════════════════════════════
           SIDEBAR
        ═══════════════════════════════════════ */
        [data-testid="stSidebar"] {
            background: var(--s1) !important;
            border-right: 1px solid var(--b1) !important;
        }
        [data-testid="stSidebar"] * { font-family: var(--f-sans) !important; }

        /* ═══════════════════════════════════════
           HERO
        ═══════════════════════════════════════ */
        .hero {
            padding: 0.5rem 0 2.25rem;
            margin-bottom: 1.75rem;
            border-bottom: 1px solid var(--b1);
        }

        /* Tag pill above title */
        .hero-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--a4);
            border: 1px solid rgba(194,106,16,.2);
            border-radius: 999px;
            padding: 0.28rem 0.75rem;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: var(--a1);
            margin-bottom: 1.1rem;
        }
        .hero-tag-dot {
            width: 6px; height: 6px;
            border-radius: 50%;
            background: var(--a3);
        }

        /* Title uses Georgia — always available */
        .hero-title {
            font-family: var(--f-serif);
            font-size: clamp(2rem, 3vw, 2.8rem);
            font-weight: 700;
            line-height: 1.18;
            letter-spacing: -0.025em;
            color: var(--t1);
            margin: 0 0 0.9rem;
            max-width: 780px;
        }
        /* Italic accent in title */
        .hero-title .hl {
            font-style: italic;
            color: var(--a2);
        }

        /* Subtitle */
        .hero-desc {
            font-size: 0.96rem;
            color: var(--t3);
            max-width: 580px;
            line-height: 1.75;
        }

        /* Step chips */
        .hero-steps {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1.35rem;
        }
        .step-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            background: var(--s1);
            border: 1px solid var(--b1);
            border-radius: 999px;
            padding: 0.3rem 0.75rem;
            font-size: 0.78rem;
            color: var(--t3);
        }
        .step-chip-n {
            font-family: var(--f-mono);
            font-size: 0.68rem;
            color: var(--a2);
            font-weight: 600;
        }

        /* ═══════════════════════════════════════
           PANELS
        ═══════════════════════════════════════ */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--s1) !important;
            border: 1px solid var(--b1) !important;
            border-radius: var(--r3) !important;
            box-shadow: var(--sh2) !important;
        }

        /* Panel header */
        .panel-hdr {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 1rem;
            margin-bottom: 1.15rem;
            border-bottom: 1px solid var(--b1);
        }
        .panel-hdr-left {
            display: flex;
            align-items: center;
            gap: 0.6rem;
        }
        .panel-hdr-dot {
            width: 8px; height: 8px;
            border-radius: 50%;
            background: var(--a3);
            flex-shrink: 0;
        }
        .panel-hdr-title {
            font-family: var(--f-serif);
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--t1);
            letter-spacing: -0.01em;
            margin: 0;
        }
        .panel-hdr-badge {
            font-family: var(--f-mono);
            font-size: 0.72rem;
            color: var(--t4);
            background: var(--s2);
            border: 1px solid var(--b1);
            border-radius: 6px;
            padding: 0.15rem 0.5rem;
        }

        /* ═══════════════════════════════════════
           METRICS
        ═══════════════════════════════════════ */
        .metrics-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.6rem;
            margin-bottom: 1rem;
        }
        .metric {
            background: var(--s2);
            border: 1px solid var(--b1);
            border-radius: var(--r1);
            padding: 0.9rem 1rem;
            transition: border-color .18s;
        }
        .metric:hover { border-color: var(--a3); }
        .metric-lbl {
            font-size: 0.67rem;
            font-weight: 700;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            color: var(--t4);
            margin-bottom: 0.45rem;
        }
        .metric-val {
            font-family: var(--f-mono);
            font-size: 0.88rem;
            color: var(--t1);
            font-weight: 500;
            line-height: 1.35;
        }

        /* ML badge */
        .ml-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.28rem;
            background: var(--a4);
            border: 1px solid rgba(194,106,16,.25);
            color: var(--a1);
            border-radius: 999px;
            padding: 0.2rem 0.55rem;
            font-family: var(--f-mono);
            font-size: 0.74rem;
        }

        /* ═══════════════════════════════════════
           UPLOAD PANEL
        ═══════════════════════════════════════ */
        .file-card {
            background: var(--s2);
            border: 1px solid var(--b1);
            border-radius: var(--r1);
            padding: 0.85rem 1rem;
            margin: 0.7rem 0 0.9rem;
            display: flex;
            align-items: center;
            gap: 0.8rem;
            animation: fadeSlideUp .22s ease-out both;
        }
        .file-card-icon {
            width: 36px; height: 36px;
            background: var(--a4);
            border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1rem;
            flex-shrink: 0;
        }
        .file-card-name {
            font-family: var(--f-mono);
            font-size: 0.84rem;
            color: var(--t1);
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .file-card-meta {
            font-size: 0.76rem;
            color: var(--t4);
            margin-top: 0.1rem;
        }

        .upload-ready {
            background: var(--a5);
            border: 1px solid rgba(194,106,16,.18);
            border-radius: var(--r1);
            padding: 0.75rem 0.9rem;
            margin: 0.7rem 0 0.9rem;
            color: var(--t3);
            font-size: 0.84rem;
            line-height: 1.55;
            animation: fadeSlideUp .22s ease-out both;
        }

        .upload-actions {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            margin-top: 0.85rem;
            animation: fadeSlideUp .24s ease-out both;
        }

        @keyframes fadeSlideUp {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Empty state */
        .empty {
            background: var(--s2);
            border: 1.5px dashed var(--b2);
            border-radius: var(--r2);
            padding: 3rem 2rem;
            text-align: center;
        }
        .empty-icon {
            font-size: 1.75rem;
            margin-bottom: 0.7rem;
            opacity: 0.35;
            display: block;
        }
        .empty-title {
            font-family: var(--f-sans);
            font-size: 1rem;
            font-weight: 600;
            letter-spacing: 0;
            color: var(--t3);
            margin-bottom: 0.3rem;
        }
        .empty-hint { font-size: 0.82rem; color: var(--t4); }

        /* ═══════════════════════════════════════
           SUMMARY ITEMS
        ═══════════════════════════════════════ */
        .sum-item {
            display: flex;
            gap: 0.9rem;
            align-items: flex-start;
            padding: 0.9rem 1rem;
            background: var(--s2);
            border: 1px solid var(--b1);
            border-radius: var(--r1);
            margin-bottom: 0.5rem;
            font-size: 0.92rem;
            color: var(--t2);
            line-height: 1.65;
            transition: background .15s, border-color .15s;
        }
        .sum-item:hover {
            background: var(--a5);
            border-color: rgba(194,106,16,.25);
        }
        .sum-num {
            font-family: var(--f-mono);
            font-size: 0.7rem;
            color: var(--a2);
            min-width: 1.6rem;
            padding-top: 0.28rem;
            font-weight: 600;
        }

        /* ═══════════════════════════════════════
           QUIZ
        ═══════════════════════════════════════ */
        .quiz-card {
            background: var(--s2);
            border: 1px solid var(--b1);
            border-radius: var(--r2);
            padding: 1.1rem 1.2rem;
            margin-bottom: 0.9rem;
            transition: border-color .15s;
        }
        .quiz-card:hover { border-color: var(--b2); }
        .quiz-label {
            font-family: var(--f-mono);
            font-size: 0.67rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--a2);
            margin-bottom: 0.4rem;
        }
        .quiz-text {
            font-size: 0.94rem;
            font-weight: 600;
            color: var(--t1);
            line-height: 1.55;
        }
        .quiz-options {
            margin: 0.45rem 0 1.35rem;
        }
        .quiz-options label,
        .quiz-options span,
        .quiz-options p,
        [data-testid="stRadio"] label,
        [data-testid="stRadio"] label * {
            color: var(--t2) !important;
            opacity: 1 !important;
            -webkit-text-fill-color: var(--t2) !important;
        }
        [data-testid="stRadio"] [role="radiogroup"] {
            gap: 0.28rem;
        }
        [data-testid="stRadio"] div[role="radiogroup"] > label {
            background: var(--s1) !important;
            border: 1px solid var(--b1) !important;
            border-radius: var(--r1) !important;
            padding: 0.55rem 0.75rem !important;
            margin-bottom: 0.34rem !important;
            transition: border-color .15s, background .15s;
        }
        [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
            background: var(--a5) !important;
            border-color: var(--a3) !important;
        }

        /* ═══════════════════════════════════════
           ML EVAL TABLE
        ═══════════════════════════════════════ */
        .ml-block {
            background: var(--s2);
            border: 1px solid var(--b1);
            border-radius: var(--r2);
            padding: 1.1rem 1.2rem;
            margin: 0.9rem 0 1rem;
        }
        .ml-block-title {
            font-family: var(--f-mono);
            font-size: 0.67rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: var(--a1);
            margin-bottom: 0.85rem;
        }
        .ml-tbl {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.82rem;
            font-family: var(--f-mono);
        }
        .ml-tbl th {
            text-align: left;
            padding: 0.45rem 0.65rem;
            font-size: 0.67rem;
            font-weight: 700;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: var(--t4);
            border-bottom: 1px solid var(--b1);
            background: var(--s3);
        }
        .ml-tbl td {
            padding: 0.55rem 0.65rem;
            border-bottom: 1px solid var(--b1);
            color: var(--t2);
            vertical-align: top;
            line-height: 1.45;
        }
        .ml-tbl tr:last-child td { border-bottom: none; }
        .ml-tbl tr:hover td { background: var(--s3); }
        .acc-best { color: var(--ok); font-weight: 700; }

        /* ═══════════════════════════════════════
           TABS
        ═══════════════════════════════════════ */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            background: transparent;
            border-bottom: 1px solid var(--b1) !important;
            padding-bottom: 0;
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent !important;
            color: var(--t3) !important;
            font-size: 0.84rem !important;
            font-weight: 600 !important;
            font-family: var(--f-sans) !important;
            padding: 0.55rem 1rem !important;
            border-radius: 0 !important;
            border-bottom: 2px solid transparent !important;
            margin-bottom: -1px;
            transition: color .15s;
        }
        .stTabs [aria-selected="true"] {
            color: var(--a1) !important;
            border-bottom-color: var(--a2) !important;
        }
        .stTabs [data-baseweb="tab-panel"] { padding-top: 1.1rem; }

        /* ═══════════════════════════════════════
           BUTTONS
        ═══════════════════════════════════════ */
        .stButton > button,
        .stDownloadButton > button {
            font-family: var(--f-sans) !important;
            font-weight: 600 !important;
            font-size: 0.87rem !important;
            border-radius: var(--r1) !important;
            min-height: 2.6rem !important;
            transition: all .18s !important;
            border: 1px solid var(--b2) !important;
            background: var(--s1) !important;
            color: var(--t2) !important;
            box-shadow: var(--sh1) !important;
        }
        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: var(--a3) !important;
            color: var(--a1) !important;
            background: var(--a5) !important;
        }
        [data-testid="stBaseButton-primary"],
        .stButton > button[kind="primary"] {
            background: var(--a1) !important;
            border-color: var(--a1) !important;
            color: #fff !important;
            box-shadow: 0 2px 8px rgba(194,106,16,.3) !important;
        }
        [data-testid="stBaseButton-primary"]:hover,
        .stButton > button[kind="primary"]:hover {
            background: var(--a2) !important;
            border-color: var(--a2) !important;
            box-shadow: 0 4px 14px rgba(194,106,16,.35) !important;
        }

        /* ═══════════════════════════════════════
           FILE UPLOADER
        ═══════════════════════════════════════ */
        [data-testid="stFileUploaderDropzone"] {
            background: var(--s2) !important;
            border: 1.5px dashed var(--b2) !important;
            border-radius: var(--r2) !important;
            display: flex !important;
            align-items: center !important;
            gap: 1rem !important;
            min-height: 80px !important;
            padding: 0.9rem 1rem !important;
            transition: border-color .18s, background .18s;
        }
        [data-testid="stFileUploaderDropzone"]:hover {
            border-color: var(--a3) !important;
            background: var(--a5) !important;
        }
        [data-testid="stFileUploaderDropzone"] * {
            font-family: var(--f-sans) !important;
            color: var(--t3) !important;
        }
        [data-testid="stFileUploaderDropzone"] button {
            background: var(--a4) !important;
            border: 1px solid rgba(194,106,16,.3) !important;
            color: transparent !important;
            border-radius: 7px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex: 0 0 auto !important;
            font-size: 0 !important;
            font-weight: 600 !important;
            min-height: 44px !important;
            min-width: 120px !important;
            padding: 0.45rem 0.9rem !important;
            overflow: hidden !important;
            position: relative !important;
            white-space: nowrap !important;
            z-index: 1 !important;
        }
        [data-testid="stFileUploaderDropzone"] button * {
            color: transparent !important;
            font-size: 0 !important;
        }
        [data-testid="stFileUploaderDropzone"] button::after {
            content: "Upload";
            position: absolute !important;
            inset: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: var(--a1) !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            line-height: 1 !important;
            text-align: center !important;
        }
        [data-testid="stFileUploaderDropzoneInstructions"] {
            display: flex !important;
            flex: 1 1 auto !important;
            flex-direction: column !important;
            gap: 0.12rem !important;
            line-height: 1.35 !important;
            margin: 0 !important;
            min-width: 0 !important;
        }
        [data-testid="stFileUploaderDropzoneInstructions"] span,
        [data-testid="stFileUploaderDropzoneInstructions"] small {
            display: block !important;
            margin: 0 !important;
            overflow-wrap: anywhere !important;
            white-space: normal !important;
        }
        [data-testid="stFileUploaderDropzoneInstructions"] small {
            color: var(--t3) !important;
            font-size: 0.84rem !important;
        }

        /* ═══════════════════════════════════════
           TEXT AREA
        ═══════════════════════════════════════ */
        .stTextArea textarea {
            background: var(--s2) !important;
            border: 1px solid var(--b1) !important;
            border-radius: var(--r1) !important;
            color: var(--t2) !important;
            -webkit-text-fill-color: var(--t2) !important;
            opacity: 1 !important;
            font-family: var(--f-mono) !important;
            font-size: 0.83rem !important;
            line-height: 1.72 !important;
        }
        .stTextArea textarea:disabled {
            color: var(--t2) !important;
            -webkit-text-fill-color: var(--t2) !important;
            opacity: 1 !important;
        }
        .stTextArea textarea:focus {
            border-color: var(--a3) !important;
            box-shadow: 0 0 0 3px rgba(194,106,16,.1) !important;
        }
        .transcript-box {
            background: var(--s2);
            border: 1px solid var(--b1);
            border-radius: var(--r1);
            color: var(--t2);
            font-family: var(--f-mono);
            font-size: 0.84rem;
            line-height: 1.75;
            max-height: 440px;
            overflow: auto;
            padding: 1rem 1.05rem;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
        }

        /* ═══════════════════════════════════════
           MISC STREAMLIT OVERRIDES
        ═══════════════════════════════════════ */
        [data-testid="stAlert"] {
            border-radius: var(--r1) !important;
            font-size: 0.87rem !important;
            font-family: var(--f-sans) !important;
        }
        [data-testid="stExpander"] {
            background: var(--s2) !important;
            border: 1px solid var(--b1) !important;
            border-radius: var(--r1) !important;
        }
        .stCaption, [data-testid="stCaptionContainer"] {
            color: var(--t4) !important;
            font-size: 0.79rem !important;
        }
        [data-testid="stRadio"] label {
            font-family: var(--f-sans) !important;
            font-size: 0.9rem !important;
            color: var(--t2) !important;
        }
        [data-testid="stStatusWidget"] {
            background: var(--s1) !important;
            border: 1px solid var(--b1) !important;
            border-radius: var(--r1) !important;
        }
        hr {
            border: none;
            border-top: 1px solid var(--b1);
            margin: 1rem 0;
        }

        @media (max-width: 860px) { .metrics-row { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 560px) { .metrics-row { grid-template-columns: 1fr; } }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────

def format_file_size(size_bytes):
    if not size_bytes:
        return "0 KB"
    kb = size_bytes / 1024
    return f"{kb:.1f} KB" if kb < 1024 else f"{kb / 1024:.2f} MB"


def render_panel_header(title, badge=""):
    badge_html = f'<span class="panel-hdr-badge">{badge}</span>' if badge else ""
    st.markdown(
        f"""
        <div class="panel-hdr">
            <div class="panel-hdr-left">
                <div class="panel-hdr-dot"></div>
                <h3 class="panel-hdr-title">{title}</h3>
            </div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────
#  Hero
# ─────────────────────────────────────────────────

def render_hero():
    st.markdown(
        """
        <div class="hero">
            <div class="hero-tag">
                <div class="hero-tag-dot"></div>
                Lecture Lab · AI Analysis
            </div>
            <h1 class="hero-title">
                Biến audio bài giảng thành<br>
                transcript, tóm tắt và quiz
                <span class="hl"> — ngay lập tức.</span>
            </h1>
            <p class="hero-desc">
                Tải lên file audio, hệ thống tự động chuyển lời nói thành văn bản,
                trích xuất ý chính, sinh câu hỏi ôn tập và phân loại chủ đề bằng ML.
                Toàn bộ trong một luồng xử lý nhất quán.
            </p>
            <div class="hero-steps">
                <div class="step-chip"><span class="step-chip-n">01</span> Upload audio</div>
                <div class="step-chip"><span class="step-chip-n">02</span> Transcribe</div>
                <div class="step-chip"><span class="step-chip-n">03</span> Cleanup</div>
                <div class="step-chip"><span class="step-chip-n">04</span> Summarize</div>
                <div class="step-chip"><span class="step-chip-n">05</span> Quiz + ML</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────
#  Processing
# ─────────────────────────────────────────────────

def process_audio(uploaded_file):
    tmp_path = None
    suffix = f".{uploaded_file.name.split('.')[-1]}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name
    try:
        with st.status("Đang phân tích bài giảng…", expanded=True) as status:
            st.write("① Chuyển audio → transcript thô")
            raw_data = transcribe_audio(tmp_path)
            raw_transcript = raw_data.get("transcript", "")

            st.write("② Làm sạch và chuẩn hoá")
            clean_data = cleanup_transcript(raw_transcript)
            clean_transcript = clean_data.get("clean_transcript", raw_transcript)

            st.write("③ Tóm tắt nội dung")
            summary_data = summarize_lecture(clean_transcript)

            st.write("④ Sinh quiz + phân loại topic")
            quiz_data = generate_quiz(clean_transcript, summary_data)
            topic_prediction = predict_topic(clean_transcript)
            difficulty_prediction = predict_difficulty(clean_transcript)

            st.session_state.results = {
                "transcript": clean_transcript,
                "raw_transcript": raw_transcript,
                "cleanup_corrections": clean_data.get("corrections", []),
                "summary": summary_data.get("summary", []),
                "quiz": quiz_data.get("quiz", []),
                "metadata": summary_data.get("metadata", {}),
                "topic_prediction": topic_prediction,
                "difficulty_prediction": difficulty_prediction,
            }
            st.session_state.source_filename = uploaded_file.name
            st.session_state.processing_error = ""
            status.update(label="✓ Hoàn tất", state="complete", expanded=False)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ─────────────────────────────────────────────────
#  Upload panel
# ─────────────────────────────────────────────────

def render_upload_panel():
    with st.container(border=True):
        render_panel_header("Đầu vào", "MP3 · WAV · M4A")

        uploader_key = f"audio_uploader_{st.session_state.uploader_reset_counter}"
        uploaded_file = st.file_uploader(
            "audio",
            type=["mp3", "wav", "m4a"],
            label_visibility="collapsed",
            key=uploader_key,
        )

        if uploaded_file:
            st.markdown(
                """
                <style>
                [data-testid="stFileUploader"] {
                    display: none !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            ext = uploaded_file.name.rsplit(".", 1)[-1].upper()
            st.markdown(
                f"""
                <div class="file-card">
                    <div class="file-card-icon">🎙</div>
                    <div style="min-width:0">
                        <div class="file-card-name">{escape(uploaded_file.name)}</div>
                        <div class="file-card-meta">{format_file_size(uploaded_file.size)} · {ext}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.audio(uploaded_file)

            action_col, reset_col = st.columns([1.2, 0.8])
            with action_col:
                if st.button("Phân tích bài giảng →", type="primary", use_container_width=True):
                    try:
                        process_audio(uploaded_file)
                        st.rerun()
                    except Exception as exc:
                        st.session_state.processing_error = str(exc)
                        st.error(f"Lỗi: {exc}")
            with reset_col:
                if st.button("Đổi file", use_container_width=True):
                    st.session_state.uploader_reset_counter += 1
                    st.session_state.results = None
                    st.session_state.source_filename = ""
                    st.session_state.processing_error = ""
                    st.rerun()
        else:
            st.markdown(
                """
                <div class="upload-ready">
                    Kéo thả hoặc chọn file audio. Sau khi chọn file, bản xem trước và nút phân tích sẽ xuất hiện ngay bên dưới.
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.session_state.results:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Xoá và làm lại", use_container_width=True):
                st.session_state.results = None
                st.session_state.source_filename = ""
                st.session_state.processing_error = ""
                st.session_state.uploader_reset_counter += 1
                st.rerun()


# ─────────────────────────────────────────────────
#  Metadata strip
# ─────────────────────────────────────────────────

def render_metadata(results):
    meta = results.get("metadata", {})
    tp   = results.get("topic_prediction", {})
    dp   = results.get("difficulty_prediction", {})
    topic     = escape(str(meta.get("topic") or "—"))
    duration  = escape(str(meta.get("estimated_duration_minutes") or "?"))
    diff_map  = {"beginner": "Cơ bản", "intermediate": "Trung bình", "advanced": "Nâng cao"}
    difficulty_label = dp.get("label") or meta.get("difficulty_level")
    difficulty = escape(diff_map.get(difficulty_label, "—"))
    difficulty_conf = f"{dp.get('confidence', 0.0) * 100:.1f}%" if dp.get("model_available") else "N/A"
    pred_label = escape(str(tp.get("label") or "unknown"))
    conf_text  = f"{tp.get('confidence', 0.0) * 100:.1f}%" if tp.get("model_available") else "N/A"

    st.markdown(
        f"""
        <div class="metrics-row">
            <div class="metric">
                <div class="metric-lbl">Chủ đề</div>
                <div class="metric-val">{topic}</div>
            </div>
            <div class="metric">
                <div class="metric-lbl">Thời lượng</div>
                <div class="metric-val">{duration} phút</div>
            </div>
            <div class="metric">
                <div class="metric-lbl">ML difficulty</div>
                <div class="metric-val">
                    <span class="ml-badge">{difficulty} · {difficulty_conf}</span>
                </div>
            </div>
            <div class="metric">
                <div class="metric-lbl">ML topic</div>
                <div class="metric-val">
                    <span class="ml-badge">{pred_label} · {conf_text}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────
#  Downloads
# ─────────────────────────────────────────────────

def render_downloads(results):
    src = st.session_state.source_filename or "lecture"
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("↓ Markdown", data=to_markdown(results, src),
            file_name=get_export_filename(src, ".md"), mime="text/markdown", use_container_width=True)
    with c2:
        st.download_button("↓ JSON", data=to_json(results),
            file_name=get_export_filename(src, ".json"), mime="application/json", use_container_width=True)


# ─────────────────────────────────────────────────
#  ML block
# ─────────────────────────────────────────────────

def render_ml_metrics():
    metrics = load_model_metrics()
    if not metrics:
        return

    sel_model  = escape(metrics.get("selected_model", "—"))
    sel_algo   = escape(metrics.get("selected_algorithm", "—"))
    accuracy   = metrics.get("accuracy", 0.0)
    ds_size    = metrics.get("dataset_size", 0)
    train_size = metrics.get("train_size", 0)
    test_size  = metrics.get("test_size", 0)

    rows = ""
    for name, m in metrics.get("model_comparison", {}).items():
        params  = ", ".join(f"{k}={v}" for k, v in m.get("params", {}).items())
        acc_val = m.get("accuracy", 0.0)
        cls     = "acc-best" if acc_val == accuracy else ""
        rows += f"""<tr>
            <td>{escape(name)}</td>
            <td>{escape(m.get("algorithm",""))}</td>
            <td style="color:var(--t4)">{escape(params) or "—"}</td>
            <td class="{cls}">{acc_val*100:.1f}%</td>
        </tr>"""

    st.markdown(
        f"""
        <div class="ml-block">
            <div class="ml-block-title">Model Evaluation</div>
            <div class="metrics-row" style="margin-bottom:0.8rem">
                <div class="metric">
                    <div class="metric-lbl">Selected</div>
                    <div class="metric-val">{sel_model}</div>
                </div>
                <div class="metric">
                    <div class="metric-lbl">Accuracy</div>
                    <div class="metric-val" style="color:var(--ok);font-weight:700">{accuracy*100:.1f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-lbl">Dataset</div>
                    <div class="metric-val">{ds_size} samples</div>
                </div>
                <div class="metric">
                    <div class="metric-lbl">Train / Test</div>
                    <div class="metric-val">{train_size} / {test_size}</div>
                </div>
            </div>
            <div style="font-size:0.76rem;color:var(--t4);font-family:var(--f-mono);margin-bottom:0.7rem">{sel_algo}</div>
            <table class="ml-tbl">
                <thead><tr><th>Model</th><th>Algorithm</th><th>Params</th><th>Accuracy</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    difficulty_metrics = load_model_metrics(DEFAULT_DIFFICULTY_METRICS_PATH)
    if difficulty_metrics:
        difficulty_rows = ""
        difficulty_accuracy = difficulty_metrics.get("accuracy", 0.0)
        for name, model_metrics in difficulty_metrics.get("model_comparison", {}).items():
            params = ", ".join(f"{k}={v}" for k, v in model_metrics.get("params", {}).items())
            acc_val = model_metrics.get("accuracy", 0.0)
            cls = "acc-best" if acc_val == difficulty_accuracy else ""
            difficulty_rows += f"""<tr>
            <td>{escape(name)}</td>
            <td>{escape(model_metrics.get("algorithm", ""))}</td>
            <td style="color:var(--t4)">{escape(params) or "—"}</td>
            <td class="{cls}">{acc_val*100:.1f}%</td>
        </tr>"""

        st.markdown(
            f"""
            <div class="ml-block">
                <div class="ml-block-title">Difficulty Model Evaluation</div>
                <div class="metrics-row" style="margin-bottom:0.8rem">
                    <div class="metric">
                        <div class="metric-lbl">Selected</div>
                        <div class="metric-val">{escape(difficulty_metrics.get("selected_model", "—"))}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-lbl">Accuracy</div>
                        <div class="metric-val" style="color:var(--ok);font-weight:700">{difficulty_accuracy*100:.1f}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-lbl">Dataset</div>
                        <div class="metric-val">{difficulty_metrics.get("dataset_size", 0)} samples</div>
                    </div>
                    <div class="metric">
                        <div class="metric-lbl">Train / Test</div>
                        <div class="metric-val">{difficulty_metrics.get("train_size", 0)} / {difficulty_metrics.get("test_size", 0)}</div>
                    </div>
                </div>
                <div style="font-size:0.76rem;color:var(--t4);font-family:var(--f-mono);margin-bottom:0.7rem">{escape(difficulty_metrics.get("selected_algorithm", "—"))}</div>
                <table class="ml-tbl">
                    <thead><tr><th>Model</th><th>Algorithm</th><th>Params</th><th>Accuracy</th></tr></thead>
                    <tbody>{difficulty_rows}</tbody>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────
#  Tab: Summary
# ─────────────────────────────────────────────────

def render_summary(summary):
    if not summary:
        st.warning("Chưa có dữ liệu tóm tắt.")
        return
    for i, point in enumerate(summary, 1):
        st.markdown(
            f"""
            <div class="sum-item">
                <span class="sum-num">#{i:02d}</span>
                <span>{escape(str(point))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ─────────────────────────────────────────────────
#  Tab: Quiz
# ─────────────────────────────────────────────────

def render_quiz(quiz):
    if not quiz:
        st.warning("Chưa có câu hỏi trắc nghiệm.")
        return
    st.caption("Chọn đáp án để xem kết quả và giải thích ngay.")
    for idx, q in enumerate(quiz, 1):
        opts   = q.get("options", {})
        labels = [f"{k}. {v}" for k, v in opts.items()]

        st.markdown(
            f"""
            <div class="quiz-card">
                <div class="quiz-label">Câu {idx:02d}</div>
                <div class="quiz-text">{escape(str(q.get("question", "")))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not labels:
            st.warning("Câu này chưa có lựa chọn.")
            continue

        st.markdown('<div class="quiz-options">', unsafe_allow_html=True)
        choice = st.radio("", labels, index=None, key=f"quiz_q_{idx}", label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)
        if choice:
            sel     = choice.split(".", 1)[0]
            correct = q.get("answer", "")
            exp     = q.get("explanation", "Không có giải thích.")
            if sel == correct:
                st.success(f"✓ Chính xác — đáp án: **{correct}**")
            else:
                st.error(f"✗ Chưa đúng — đáp án là **{correct}**")
            st.info(f"💡 {exp}")


# ─────────────────────────────────────────────────
#  Tab: Transcript
# ─────────────────────────────────────────────────

def render_transcript(results):
    transcript  = results.get("transcript", "")
    corrections = results.get("cleanup_corrections", [])
    if not transcript:
        st.warning("Chưa có transcript.")
        return
    st.markdown(
        f'<div class="transcript-box">{escape(transcript)}</div>',
        unsafe_allow_html=True,
    )
    if corrections:
        with st.expander(f"Các chỉnh sửa ({len(corrections)})"):
            for c in corrections:
                st.write(f"— {c}")


# ─────────────────────────────────────────────────
#  Results panel
# ─────────────────────────────────────────────────

def render_results_panel():
    with st.container(border=True):
        render_panel_header("Kết quả phân tích", "summary · quiz · transcript · ML")

        results = st.session_state.results
        if not results:
            st.markdown(
                """
                <div class="empty" style="padding:3.5rem 2rem">
                    <span class="empty-icon">📋</span>
                    <div class="empty-title">Kết quả sẽ hiện ở đây</div>
                    <div class="empty-hint">Upload audio và nhấn Phân tích để bắt đầu</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        render_metadata(results)
        render_downloads(results)
        render_ml_metrics()

        tab_s, tab_q, tab_t = st.tabs(["Tóm tắt", "Trắc nghiệm", "Transcript"])
        with tab_s:
            render_summary(results.get("summary", []))
        with tab_q:
            render_quiz(results.get("quiz", []))
        with tab_t:
            render_transcript(results)


# ─────────────────────────────────────────────────
#  Entry
# ─────────────────────────────────────────────────

init_session_state()
apply_page_style()
render_sidebar(st.session_state.results)
render_hero()

left, right = st.columns([0.9, 1.1], gap="large")
with left:
    render_upload_panel()
with right:
    render_results_panel()
