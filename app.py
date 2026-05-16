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
from ml_core.predict import load_model_metrics, predict_topic
from ui_components import render_sidebar


st.set_page_config(
    page_title="Lecture Lab",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    defaults = {
        "results": None,
        "source_filename": "",
        "processing_error": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_page_style():
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;0,700;1,400;1,600&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">

        <style>
            :root {
                --bg:           #f7f4ef;
                --bg-2:         #ffffff;
                --bg-3:         #faf8f5;
                --bg-4:         #f2ede6;
                --border:       #e2d9cc;
                --border-soft:  #ede8e0;
                --text:         #1c1917;
                --text-2:       #3d3530;
                --muted:        #7c6e62;
                --muted-2:      #a8998c;
                --amber:        #b45309;
                --amber-mid:    #d97706;
                --amber-bright: #f59e0b;
                --amber-soft:   #fef3c7;
                --amber-glow:   rgba(180, 83, 9, 0.08);
                --green:        #047857;
                --green-soft:   #ecfdf5;
                --red:          #b91c1c;
                --red-soft:     #fef2f2;
                --shadow-sm:    0 1px 3px rgba(28,25,23,0.07), 0 1px 2px rgba(28,25,23,0.04);
                --shadow-md:    0 4px 16px rgba(28,25,23,0.08), 0 2px 6px rgba(28,25,23,0.05);
                --radius:       10px;
                --radius-lg:    14px;
            }

            *, *::before, *::after { box-sizing: border-box; }

            html, body, .stApp {
                background: var(--bg) !important;
                color: var(--text);
                font-family: 'DM Sans', sans-serif;
            }

            [data-testid="stHeader"],
            [data-testid="stToolbar"],
            .viewerBadge_container__r5tak,
            #MainMenu { display: none !important; }

            .block-container {
                padding-top: 2rem;
                padding-bottom: 3rem;
                max-width: 1340px;
            }

            /* ── Sidebar ── */
            [data-testid="stSidebar"] {
                background: var(--bg-2) !important;
                border-right: 1px solid var(--border) !important;
            }
            [data-testid="stSidebar"] > div:first-child { background: transparent; }

            /* ── Typography ── */
            h1, h2 { font-family: 'Lora', Georgia, serif; letter-spacing: -0.02em; color: var(--text); }
            h3, h4 { font-family: 'DM Sans', sans-serif; letter-spacing: -0.01em; color: var(--text); }

            /* ── Hero ── */
            .hero-wrap {
                padding: 0.25rem 0 2rem;
                border-bottom: 1px solid var(--border-soft);
                margin-bottom: 2rem;
            }
            .hero-eyebrow {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                color: var(--amber);
                margin-bottom: 0.8rem;
            }
            .hero-eyebrow::before {
                content: '';
                display: inline-block;
                width: 22px; height: 2px;
                background: var(--amber-bright);
                border-radius: 2px;
            }
            .hero-title {
                font-family: 'Lora', Georgia, serif;
                font-size: clamp(1.9rem, 3vw, 2.75rem);
                font-weight: 700;
                line-height: 1.18;
                color: var(--text);
                margin: 0 0 0.65rem;
                max-width: 820px;
            }
            .hero-title em { font-style: italic; color: var(--amber); }
            .hero-sub {
                font-size: 0.95rem;
                color: var(--muted);
                max-width: 620px;
                line-height: 1.7;
            }

            /* ── Panels ── */
            [data-testid="stVerticalBlockBorderWrapper"] {
                background: var(--bg-2) !important;
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-lg) !important;
                box-shadow: var(--shadow-md) !important;
            }

            /* ── Panel header ── */
            .ph {
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 1rem;
                margin-bottom: 1.25rem;
                padding-bottom: 0.9rem;
                border-bottom: 1px solid var(--border-soft);
            }
            .ph-title { font-family:'Lora',Georgia,serif; font-size:1.08rem; font-weight:600; color:var(--text); margin:0; }
            .ph-sub   { font-size:0.78rem; color:var(--muted-2); font-family:'DM Mono',monospace; }

            /* ── Metric grid ── */
            .metric-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 0.65rem;
                margin-bottom: 1.1rem;
            }
            .metric-card {
                background: var(--bg-3);
                border: 1px solid var(--border-soft);
                border-radius: var(--radius);
                padding: 1rem;
                transition: border-color 0.2s, box-shadow 0.2s;
            }
            .metric-card:hover {
                border-color: var(--amber-bright);
                box-shadow: 0 2px 8px rgba(245,158,11,0.1);
            }
            .metric-label {
                font-size: 0.68rem; font-weight:700; letter-spacing:0.09em;
                text-transform:uppercase; color:var(--muted-2); margin-bottom:0.5rem;
            }
            .metric-value { font-family:'DM Mono',monospace; font-size:0.9rem; color:var(--text-2); line-height:1.4; }

            /* ── ML badge ── */
            .ml-badge {
                display: inline-flex; align-items:center; gap:0.3rem;
                background: var(--amber-soft);
                border: 1px solid rgba(245,158,11,0.35);
                color: var(--amber);
                border-radius: 999px;
                padding: 0.22rem 0.6rem;
                font-size: 0.78rem;
                font-family: 'DM Mono', monospace;
                font-weight: 500;
            }
            .ml-badge::before { content:'◆'; font-size:0.45rem; }

            /* ── Empty state ── */
            .empty-state {
                background: var(--bg-3);
                border: 1.5px dashed var(--border);
                border-radius: var(--radius);
                padding: 2.75rem 2rem;
                text-align: center;
            }
            .empty-icon  { font-size:2rem; margin-bottom:0.75rem; opacity:0.45; }
            .empty-label { font-family:'Lora',serif; font-size:1rem; color:var(--muted); margin-bottom:0.3rem; }
            .empty-hint  { font-size:0.82rem; color:var(--muted-2); }

            /* ── Summary ── */
            .summary-item {
                display: flex; gap:0.85rem;
                padding: 0.9rem 1rem;
                background: var(--bg-3);
                border: 1px solid var(--border-soft);
                border-left: 3px solid var(--amber-bright);
                border-radius: 0 var(--radius) var(--radius) 0;
                margin-bottom: 0.5rem;
                font-size: 0.93rem; line-height:1.65; color:var(--text-2);
                transition: background 0.15s, border-left-color 0.15s;
            }
            .summary-item:hover { background:var(--amber-soft); border-left-color:var(--amber); }
            .summary-num { font-family:'DM Mono',monospace; font-size:0.7rem; color:var(--amber); min-width:1.5rem; padding-top:0.22rem; opacity:0.75; }

            /* ── Quiz ── */
            .quiz-q {
                background: var(--bg-3);
                border: 1px solid var(--border-soft);
                border-radius: var(--radius);
                padding: 1.1rem 1.2rem; margin-bottom:1rem;
                transition: border-color 0.15s;
            }
            .quiz-q:hover { border-color:var(--border); }
            .quiz-num { font-family:'DM Mono',monospace; font-size:0.68rem; font-weight:500; color:var(--amber); letter-spacing:0.08em; margin-bottom:0.4rem; }
            .quiz-text { font-size:0.95rem; font-weight:500; color:var(--text); line-height:1.55; }

            /* ── File card ── */
            .file-card {
                background: var(--bg-3); border:1px solid var(--border-soft); border-radius:var(--radius);
                padding:0.85rem 1.1rem; margin:0.75rem 0 1rem;
                display:flex; align-items:center; gap:0.85rem;
            }
            .file-icon { font-size:1.25rem; opacity:0.65; }
            .file-name { font-family:'DM Mono',monospace; font-size:0.84rem; color:var(--text); font-weight:500; }
            .file-meta { font-size:0.77rem; color:var(--muted-2); margin-top:0.12rem; }

            /* ── ML eval ── */
            .ml-eval {
                background: var(--bg-3); border:1px solid var(--border-soft);
                border-radius: var(--radius-lg); padding:1.2rem; margin:1rem 0;
            }
            .ml-eval-title {
                font-family:'DM Mono',monospace; font-size:0.7rem; letter-spacing:0.1em;
                text-transform:uppercase; color:var(--amber); margin-bottom:0.9rem;
                display:flex; align-items:center; gap:0.45rem;
            }
            .ml-eval-title::before { content:'▸'; opacity:0.55; }
            .ml-table { width:100%; border-collapse:collapse; font-size:0.84rem; font-family:'DM Mono',monospace; }
            .ml-table th {
                text-align:left; padding:0.5rem 0.7rem; color:var(--muted-2);
                font-size:0.68rem; letter-spacing:0.07em; text-transform:uppercase;
                border-bottom:1px solid var(--border); font-weight:700; background:var(--bg-4);
            }
            .ml-table td {
                padding:0.58rem 0.7rem; border-bottom:1px solid var(--border-soft);
                color:var(--text-2); vertical-align:top; line-height:1.5;
            }
            .ml-table tr:last-child td { border-bottom:none; }
            .ml-table tr:hover td { background:var(--bg-4); }
            .acc-hi { color:var(--green); font-weight:600; }

            /* ── Tabs ── */
            .stTabs [data-baseweb="tab-list"] {
                gap:0; background:transparent;
                border-bottom:1px solid var(--border) !important;
            }
            .stTabs [data-baseweb="tab"] {
                background:transparent !important; color:var(--muted) !important;
                font-size:0.85rem !important; font-weight:600 !important;
                font-family:'DM Sans',sans-serif !important; letter-spacing:0.01em;
                padding:0.6rem 1.1rem !important; border-radius:0 !important;
                border-bottom:2px solid transparent !important; margin-bottom:-1px;
            }
            .stTabs [aria-selected="true"] {
                color:var(--amber) !important;
                border-bottom-color:var(--amber-bright) !important;
            }
            .stTabs [data-baseweb="tab-panel"] { padding-top:1.2rem; }

            /* ── Buttons ── */
            .stButton > button,
            .stDownloadButton > button {
                font-family:'DM Sans',sans-serif !important; font-weight:600 !important;
                font-size:0.88rem !important; border-radius:var(--radius) !important;
                min-height:2.7rem !important; transition:all 0.18s !important;
                border:1px solid var(--border) !important;
                background:var(--bg-2) !important; color:var(--text-2) !important;
                box-shadow:var(--shadow-sm) !important;
            }
            .stButton > button:hover,
            .stDownloadButton > button:hover {
                border-color:var(--amber-bright) !important; color:var(--amber) !important;
                background:var(--amber-soft) !important;
                box-shadow:0 2px 8px rgba(245,158,11,0.15) !important;
            }
            [data-testid="stBaseButton-primary"],
            .stButton > button[kind="primary"] {
                background:var(--amber) !important; border-color:var(--amber) !important;
                color:#ffffff !important; box-shadow:0 2px 8px rgba(180,83,9,0.25) !important;
            }
            [data-testid="stBaseButton-primary"]:hover,
            .stButton > button[kind="primary"]:hover {
                background:var(--amber-mid) !important; border-color:var(--amber-mid) !important;
                color:#ffffff !important; box-shadow:0 4px 12px rgba(180,83,9,0.3) !important;
            }

            /* ── Upload zone ── */
            [data-testid="stFileUploaderDropzone"] {
                background:var(--bg-3) !important; border:1.5px dashed var(--border) !important;
                border-radius:var(--radius) !important; transition:border-color 0.2s;
            }
            [data-testid="stFileUploaderDropzone"]:hover { border-color:var(--amber-bright) !important; }
            [data-testid="stFileUploaderDropzone"] button {
                background:var(--amber-soft) !important;
                border:1px solid rgba(245,158,11,0.4) !important;
                color:var(--amber) !important; border-radius:8px !important;
            }

            /* ── Text area ── */
            .stTextArea textarea {
                background:var(--bg-3) !important; border:1px solid var(--border) !important;
                border-radius:var(--radius) !important; color:var(--text) !important;
                font-family:'DM Mono',monospace !important; font-size:0.84rem !important; line-height:1.7 !important;
            }

            /* ── Misc ── */
            [data-testid="stAlert"] { border-radius:var(--radius) !important; font-size:0.88rem !important; }
            [data-testid="stExpander"] { background:var(--bg-3) !important; border:1px solid var(--border-soft) !important; border-radius:var(--radius) !important; }
            .stCaption { color:var(--muted-2) !important; font-size:0.8rem !important; }
            hr { border:none; border-top:1px solid var(--border-soft); margin:1rem 0; }

            @media (max-width: 860px) { .metric-grid { grid-template-columns: repeat(2, 1fr); } }
            @media (max-width: 560px) { .metric-grid { grid-template-columns: 1fr; } }
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


def render_panel_header(title, subtitle=""):
    sub = f'<span class="ph-sub">{subtitle}</span>' if subtitle else ""
    st.markdown(f'<div class="ph"><h3 class="ph-title">{title}</h3>{sub}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────
#  Hero
# ─────────────────────────────────────────────────

def render_hero():
    st.markdown(
        """
        <div class="hero-wrap">
            <div class="hero-eyebrow">Lecture Lab · AI Analysis</div>
            <h1 class="hero-title">
                Transcript, tóm tắt & quiz<br>
                từ audio bài giảng — <em>tức thì.</em>
            </h1>
            <p class="hero-sub">
                Tải lên file audio, hệ thống sẽ chuyển đổi thành transcript sạch, trích xuất
                ý chính, sinh bộ câu hỏi ôn tập và phân loại chủ đề bằng ML model.
            </p>
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

            st.write("② Làm sạch & chuẩn hoá transcript")
            clean_data = cleanup_transcript(raw_transcript)
            clean_transcript = clean_data.get("clean_transcript", raw_transcript)

            st.write("③ Tóm tắt nội dung chính")
            summary_data = summarize_lecture(clean_transcript)

            st.write("④ Sinh câu hỏi trắc nghiệm + phân loại topic")
            quiz_data = generate_quiz(clean_transcript, summary_data)
            topic_prediction = predict_topic(clean_transcript)

            st.session_state.results = {
                "transcript": clean_transcript,
                "raw_transcript": raw_transcript,
                "cleanup_corrections": clean_data.get("corrections", []),
                "summary": summary_data.get("summary", []),
                "quiz": quiz_data.get("quiz", []),
                "metadata": summary_data.get("metadata", {}),
                "topic_prediction": topic_prediction,
            }
            st.session_state.source_filename = uploaded_file.name
            st.session_state.processing_error = ""
            status.update(label="✓ Phân tích hoàn tất", state="complete", expanded=False)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


# ─────────────────────────────────────────────────
#  Upload panel
# ─────────────────────────────────────────────────

def render_upload_panel():
    with st.container(border=True):
        render_panel_header("Đầu vào", "MP3 · WAV · M4A")

        uploaded_file = st.file_uploader(
            "Tải file audio", type=["mp3", "wav", "m4a"], label_visibility="collapsed",
        )

        if uploaded_file:
            ext = uploaded_file.name.rsplit(".", 1)[-1].upper()
            st.markdown(
                f"""
                <div class="file-card">
                    <div class="file-icon">🎙</div>
                    <div>
                        <div class="file-name">{escape(uploaded_file.name)}</div>
                        <div class="file-meta">{format_file_size(uploaded_file.size)} &nbsp;·&nbsp; {ext}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.audio(uploaded_file)
            if st.button("Phân tích bài giảng →", type="primary", use_container_width=True):
                try:
                    process_audio(uploaded_file)
                    st.rerun()
                except Exception as exc:
                    st.session_state.processing_error = str(exc)
                    st.error(f"Lỗi: {exc}")
        else:
            st.markdown(
                """
                <div class="empty-state">
                    <div class="empty-icon">🎙</div>
                    <div class="empty-label">Chưa có file nào được chọn</div>
                    <div class="empty-hint">Kéo thả hoặc click để chọn file audio</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.session_state.results:
            st.markdown("<div style='margin-top:0.75rem'></div>", unsafe_allow_html=True)
            if st.button("Xoá kết quả", use_container_width=True):
                st.session_state.results = None
                st.session_state.source_filename = ""
                st.session_state.processing_error = ""
                st.rerun()


# ─────────────────────────────────────────────────
#  Metadata
# ─────────────────────────────────────────────────

def render_metadata(results):
    meta = results.get("metadata", {})
    tp   = results.get("topic_prediction", {})
    topic      = escape(str(meta.get("topic") or "—"))
    duration   = escape(str(meta.get("estimated_duration_minutes") or "?"))
    diff_map   = {"beginner": "Cơ bản", "intermediate": "Trung bình", "advanced": "Nâng cao"}
    difficulty = escape(diff_map.get(meta.get("difficulty_level"), "—"))
    pred_label = escape(str(tp.get("label") or "unknown"))
    conf_text  = f"{tp.get('confidence', 0.0) * 100:.1f}%" if tp.get("model_available") else "N/A"

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Chủ đề</div>
                <div class="metric-value">{topic}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Thời lượng</div>
                <div class="metric-value">{duration} phút</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Độ khó</div>
                <div class="metric-value">{difficulty}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">ML Prediction</div>
                <div class="metric-value"><span class="ml-badge">{pred_label} · {conf_text}</span></div>
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
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("↓ Markdown", data=to_markdown(results, src),
            file_name=get_export_filename(src, ".md"), mime="text/markdown", use_container_width=True)
    with col2:
        st.download_button("↓ JSON", data=to_json(results),
            file_name=get_export_filename(src, ".json"), mime="application/json", use_container_width=True)


# ─────────────────────────────────────────────────
#  ML metrics
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

    rows_html = ""
    for name, m in metrics.get("model_comparison", {}).items():
        params  = ", ".join(f"{k}={v}" for k, v in m.get("params", {}).items())
        acc_val = m.get("accuracy", 0.0)
        acc_cls = "acc-hi" if acc_val == accuracy else ""
        rows_html += f"""
        <tr>
            <td>{escape(name)}</td>
            <td>{escape(m.get("algorithm",""))}</td>
            <td style="color:var(--muted-2)">{escape(params) or "—"}</td>
            <td class="{acc_cls}">{acc_val * 100:.1f}%</td>
        </tr>"""

    st.markdown(
        f"""
        <div class="ml-eval">
            <div class="ml-eval-title">Model Evaluation Report</div>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="metric-label">Selected model</div>
                    <div class="metric-value">{sel_model}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Accuracy</div>
                    <div class="metric-value" style="color:var(--green);font-weight:600">{accuracy * 100:.1f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Dataset</div>
                    <div class="metric-value">{ds_size} samples</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Train / Test</div>
                    <div class="metric-value">{train_size} / {test_size}</div>
                </div>
            </div>
            <div style="font-size:0.78rem;color:var(--muted-2);margin-bottom:0.8rem;font-family:'DM Mono',monospace">{sel_algo}</div>
            <table class="ml-table">
                <thead><tr><th>Model</th><th>Algorithm</th><th>Params</th><th>Accuracy</th></tr></thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────
#  Tabs
# ─────────────────────────────────────────────────

def render_summary(summary):
    if not summary:
        st.warning("Chưa có dữ liệu tóm tắt.")
        return
    for i, point in enumerate(summary, 1):
        st.markdown(
            f"""
            <div class="summary-item">
                <span class="summary-num">#{i:02d}</span>
                <span>{escape(str(point))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_quiz(quiz):
    if not quiz:
        st.warning("Chưa có câu hỏi trắc nghiệm.")
        return
    st.caption("Chọn đáp án để kiểm tra và xem giải thích ngay.")
    for idx, q in enumerate(quiz, 1):
        options       = q.get("options", {})
        option_labels = [f"{k}. {v}" for k, v in options.items()]
        st.markdown(
            f"""
            <div class="quiz-q">
                <div class="quiz-num">CÂU {idx:02d}</div>
                <div class="quiz-text">{escape(str(q.get("question", "")))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not option_labels:
            st.warning("Câu hỏi này chưa có lựa chọn.")
            continue
        choice = st.radio(f"q{idx}", option_labels, index=None,
                          key=f"quiz_q_{idx}", label_visibility="collapsed")
        if choice:
            selected = choice.split(".", 1)[0]
            correct  = q.get("answer", "")
            exp      = q.get("explanation", "Không có giải thích.")
            if selected == correct:
                st.success(f"✓ Chính xác — đáp án: **{correct}**")
            else:
                st.error(f"✗ Chưa đúng — đáp án đúng là **{correct}**")
            st.info(f"💡 {exp}")


def render_transcript(results):
    transcript  = results.get("transcript", "")
    corrections = results.get("cleanup_corrections", [])
    if not transcript:
        st.warning("Chưa có transcript.")
        return
    st.text_area("transcript", value=transcript, height=420,
                 disabled=True, label_visibility="collapsed")
    if corrections:
        with st.expander(f"Chỉnh sửa transcript ({len(corrections)})"):
            for c in corrections:
                st.write(f"— {c}")


# ─────────────────────────────────────────────────
#  Results panel
# ─────────────────────────────────────────────────

def render_results_panel():
    with st.container(border=True):
        render_panel_header("Kết quả phân tích", "transcript · summary · quiz · ML")

        results = st.session_state.results
        if not results:
            st.markdown(
                """
                <div class="empty-state" style="padding:3rem 2rem">
                    <div class="empty-icon">📋</div>
                    <div class="empty-label">Kết quả sẽ xuất hiện ở đây</div>
                    <div class="empty-hint">Upload file audio và nhấn phân tích để bắt đầu</div>
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