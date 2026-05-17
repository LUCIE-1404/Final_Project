import streamlit as st


def render_sidebar(results=None):
    """Render sidebar with warm parchment light aesthetic."""
    has_results = bool(results)

    if has_results:
        status_bg     = "#ecfdf5"
        status_border = "#a7f3d0"
        status_color  = "#047857"
        status_icon   = "✓"
        status_text   = "Phân tích hoàn tất"
        quiz_count    = len(results.get("quiz", []))
        summary_count = len(results.get("summary", []))
        topic         = results.get("metadata", {}).get("topic") or "—"
        stats_html = f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;margin-top:1rem">
            <div style="background:#faf8f5;border:1px solid #ede8e0;border-radius:8px;padding:0.75rem">
                <div style="font-size:0.65rem;letter-spacing:0.09em;text-transform:uppercase;color:#a8998c;margin-bottom:0.25rem;font-weight:700">Ý chính</div>
                <div style="font-family:'DM Mono',monospace;font-size:1.2rem;color:#1c1917;font-weight:500">{summary_count}</div>
            </div>
            <div style="background:#faf8f5;border:1px solid #ede8e0;border-radius:8px;padding:0.75rem">
                <div style="font-size:0.65rem;letter-spacing:0.09em;text-transform:uppercase;color:#a8998c;margin-bottom:0.25rem;font-weight:700">Câu hỏi</div>
                <div style="font-family:'DM Mono',monospace;font-size:1.2rem;color:#1c1917;font-weight:500">{quiz_count}</div>
            </div>
        </div>
        <div style="margin-top:0.5rem;background:#faf8f5;border:1px solid #ede8e0;border-radius:8px;padding:0.75rem">
            <div style="font-size:0.65rem;letter-spacing:0.09em;text-transform:uppercase;color:#a8998c;margin-bottom:0.25rem;font-weight:700">Chủ đề</div>
            <div style="font-size:0.85rem;color:#3d3530;line-height:1.4">{topic}</div>
        </div>
        """
    else:
        status_bg     = "#fef3c7"
        status_border = "#fcd34d"
        status_color  = "#92400e"
        status_icon   = "○"
        status_text   = "Chờ file audio"
        stats_html    = ""

    with st.sidebar:
        st.markdown(
            f"""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Lora:wght@600;700&family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&display=swap');

                [data-testid="stSidebar"] {{
                    background: #ffffff !important;
                    border-right: 1px solid #e2d9cc !important;
                }}
                [data-testid="stSidebar"] .stMarkdown p,
                [data-testid="stSidebar"] .stMarkdown li {{
                    color: #7c6e62 !important;
                    font-size: 0.88rem !important;
                    line-height: 1.65 !important;
                    font-family: 'DM Sans', sans-serif !important;
                }}
                [data-testid="stSidebar"] hr {{
                    border: none !important;
                    border-top: 1px solid #ede8e0 !important;
                    margin: 1rem 0 !important;
                }}
                [data-testid="stSidebar"] .stCaption,
                [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
                    color: #a8998c !important;
                    font-size: 0.78rem !important;
                    line-height: 1.6 !important;
                }}
            </style>

            <!-- Branding -->
            <div style="padding:0.5rem 0 1.4rem">
                <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#b45309;margin-bottom:0.5rem;font-family:'DM Sans',sans-serif">
                    ◆ &nbsp;Lecture Lab
                </div>
                <div style="font-family:'Lora',Georgia,serif;font-size:1.22rem;font-weight:700;color:#1c1917;line-height:1.22;margin-bottom:0.4rem">
                    AI Analysis<br>Workspace
                </div>
                <div style="font-size:0.8rem;color:#a8998c;font-family:'DM Sans',sans-serif">
                    Transcript · Summary · Quiz · ML
                </div>
            </div>

            <!-- Status -->
            <div style="background:{status_bg};border:1px solid {status_border};border-radius:9px;padding:0.75rem 1rem;margin-bottom:1.5rem;display:flex;align-items:center;gap:0.6rem">
                <span style="color:{status_color};font-size:0.95rem">{status_icon}</span>
                <span style="color:{status_color};font-size:0.84rem;font-weight:600;font-family:'DM Sans',sans-serif">{status_text}</span>
            </div>

            {stats_html}
            """,
            unsafe_allow_html=True,
        )

        # Pipeline
        st.markdown(
            """
            <div style="margin-top:1.4rem;margin-bottom:0.7rem">
                <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#b45309;font-family:'DM Sans',sans-serif">
                    Pipeline
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        steps = [
            ("①", "Upload audio",        "MP3, WAV, M4A"),
            ("②", "Transcribe",          "Gemini speech-to-text"),
            ("③", "Cleanup",             "Chuẩn hoá & sửa lỗi"),
            ("④", "Summarize",           "Trích xuất ý chính"),
            ("⑤", "Quiz + ML Classify",  "Sinh câu hỏi & predict topic"),
        ]

        for icon, title, hint in steps:
            st.markdown(
                f"""
                <div style="display:flex;gap:0.7rem;align-items:flex-start;padding:0.5rem 0;border-bottom:1px solid #f2ede6">
                    <span style="font-family:'DM Mono',monospace;font-size:0.82rem;color:#d97706;min-width:1.4rem;padding-top:0.05rem">{icon}</span>
                    <div>
                        <div style="font-size:0.86rem;font-weight:600;color:#1c1917;font-family:'DM Sans',sans-serif">{title}</div>
                        <div style="font-size:0.76rem;color:#a8998c;margin-top:0.1rem;font-family:'DM Sans',sans-serif">{hint}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
        st.markdown("---")

        # Formats
        st.markdown(
            """
            <div style="font-size:0.68rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#b45309;margin-bottom:0.55rem;font-family:'DM Sans',sans-serif">
                Định dạng hỗ trợ
            </div>
            <div style="display:flex;gap:0.4rem;flex-wrap:wrap">
                <span style="background:#faf8f5;border:1px solid #e2d9cc;border-radius:5px;padding:0.2rem 0.6rem;font-family:'DM Mono',monospace;font-size:0.78rem;color:#7c6e62">MP3</span>
                <span style="background:#faf8f5;border:1px solid #e2d9cc;border-radius:5px;padding:0.2rem 0.6rem;font-family:'DM Mono',monospace;font-size:0.78rem;color:#7c6e62">WAV</span>
                <span style="background:#faf8f5;border:1px solid #e2d9cc;border-radius:5px;padding:0.2rem 0.6rem;font-family:'DM Mono',monospace;font-size:0.78rem;color:#7c6e62">M4A</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.caption(
            "Transcript & tóm tắt được xử lý bởi **Gemini**. "
            "Phân loại topic dùng Python ML model tự train."
        )