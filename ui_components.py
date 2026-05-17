from html import escape

import streamlit as st


def render_html(markup):
    st.markdown(markup.lstrip(), unsafe_allow_html=True)


def render_sidebar(results=None):
    has_results = bool(results)

    if has_results:
        status_bg = "#f0fdf4"
        status_border = "#bbf7d0"
        status_color = "#166534"
        status_icon = "OK"
        status_text = "Phan tich hoan tat"
        quiz_count = len(results.get("quiz", []))
        summary_count = len(results.get("summary", []))
        topic = escape(str(results.get("metadata", {}).get("topic") or "-"))
        stats_html = f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem;margin-top:1.1rem">
<div style="background:#f5f1ea;border:1px solid #e3ddd4;border-radius:8px;padding:.8rem .9rem">
<div style="font-size:.64rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#a89e95;margin-bottom:.3rem">Y chinh</div>
<div style="font-family:'SF Mono','Menlo',monospace;font-size:1.35rem;font-weight:600;color:#1a1714;line-height:1">{summary_count}</div>
</div>
<div style="background:#f5f1ea;border:1px solid #e3ddd4;border-radius:8px;padding:.8rem .9rem">
<div style="font-size:.64rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#a89e95;margin-bottom:.3rem">Cau hoi</div>
<div style="font-family:'SF Mono','Menlo',monospace;font-size:1.35rem;font-weight:600;color:#1a1714;line-height:1">{quiz_count}</div>
</div>
</div>
<div style="margin-top:.5rem;background:#f5f1ea;border:1px solid #e3ddd4;border-radius:8px;padding:.8rem .9rem">
<div style="font-size:.64rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#a89e95;margin-bottom:.3rem">Chu de nhan dang</div>
<div style="font-size:.87rem;color:#3a342e;line-height:1.45">{topic}</div>
</div>"""
    else:
        status_bg = "#fef3c7"
        status_border = "#fcd34d"
        status_color = "#92400e"
        status_icon = "..."
        status_text = "Cho file audio"
        stats_html = ""

    with st.sidebar:
        render_html(
            f"""<style>
[data-testid="stSidebar"] {{
background: #ffffff !important;
border-right: 1px solid #e3ddd4 !important;
}}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li {{
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif !important;
font-size: .88rem !important;
color: #7a6f65 !important;
line-height: 1.65 !important;
}}
[data-testid="stSidebar"] hr {{
border: none !important;
border-top: 1px solid #ece7de !important;
margin: 1rem 0 !important;
}}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] .stCaption {{
font-size: .77rem !important;
color: #a89e95 !important;
line-height: 1.6 !important;
}}
</style>
<div style="padding:.4rem 0 1.5rem">
<div style="display:inline-flex;align-items:center;gap:.4rem;background:#fef0d4;border:1px solid rgba(194,106,16,.2);border-radius:999px;padding:.24rem .65rem;font-size:.68rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#c26a10;margin-bottom:.75rem">
<span style="width:5px;height:5px;border-radius:50%;background:#f5a623;display:inline-block"></span>
Lecture Lab
</div>
<div style="font-family:Georgia,'Times New Roman',serif;font-size:1.25rem;font-weight:700;color:#1a1714;line-height:1.2;margin-bottom:.4rem">
AI Analysis<br>Workspace
</div>
<div style="font-size:.79rem;color:#a89e95">
Transcript - Summary - Quiz - ML
</div>
</div>
<div style="background:{status_bg};border:1px solid {status_border};border-radius:9px;padding:.7rem 1rem;margin-bottom:1.4rem;display:flex;align-items:center;gap:.55rem">
<span style="color:{status_color};font-size:.9rem;font-weight:700">{status_icon}</span>
<span style="color:{status_color};font-size:.84rem;font-weight:600">{status_text}</span>
</div>
{stats_html}"""
        )

        render_html(
            """<div style="margin-top:1.4rem;margin-bottom:.65rem;font-size:.66rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#c26a10">
Pipeline xu ly
</div>"""
        )

        steps = [
            ("01", "Upload audio", "MP3, WAV, M4A"),
            ("02", "Transcribe", "Gemini speech-to-text"),
            ("03", "Cleanup", "Chuan hoa va sua nhieu"),
            ("04", "Summarize", "Trich xuat y chinh"),
            ("05", "Quiz + ML Classify", "Sinh cau hoi va predict topic"),
        ]
        for num, title, hint in steps:
            render_html(
                f"""<div style="display:flex;gap:.7rem;padding:.48rem 0;border-bottom:1px solid #f5f1ea">
<span style="font-family:'SF Mono','Menlo',monospace;font-size:.7rem;color:#e07c12;min-width:1.6rem;padding-top:.05rem;font-weight:600">{num}</span>
<div>
<div style="font-size:.86rem;font-weight:600;color:#1a1714">{title}</div>
<div style="font-size:.75rem;color:#a89e95;margin-top:.08rem">{hint}</div>
</div>
</div>"""
            )

        render_html("<div style='height:.3rem'></div>")
        st.markdown("---")
        render_html(
            """<div style="font-size:.66rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#c26a10;margin-bottom:.55rem">Dinh dang</div>
<div style="display:flex;gap:.4rem">
<span style="background:#f5f1ea;border:1px solid #e3ddd4;border-radius:5px;padding:.18rem .55rem;font-family:'SF Mono','Menlo',monospace;font-size:.77rem;color:#7a6f65">MP3</span>
<span style="background:#f5f1ea;border:1px solid #e3ddd4;border-radius:5px;padding:.18rem .55rem;font-family:'SF Mono','Menlo',monospace;font-size:.77rem;color:#7a6f65">WAV</span>
<span style="background:#f5f1ea;border:1px solid #e3ddd4;border-radius:5px;padding:.18rem .55rem;font-family:'SF Mono','Menlo',monospace;font-size:.77rem;color:#7a6f65">M4A</span>
</div>"""
        )
        st.markdown("---")
        st.caption("Gemini xu ly transcript va tom tat. Topic classification dung ML model Python tu train.")
