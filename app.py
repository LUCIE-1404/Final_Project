import streamlit as st
from gemini_service import (
    get_client,
    SUMMARY_MODEL,
    QUIZ_MODEL,
    TRANSCRIPT_CLEANUP_MODEL,
    TRANSCRIPT_FALLBACK_MODEL,
    cleanup_transcript,
    transcribe_with_gemini_audio,
    generate_summary,
    parse_summary_response,
    generate_quiz,
    parse_quiz_response,
)
from speech_service import (
    CHIRP_MODEL,
    CHUNK_SECONDS,
    MAX_FILE_SIZE_MB,
    cleanup_audio_file,
    get_chirp_client,
    save_uploaded_audio,
    transcribe_with_chirp,
    validate_audio_file,
)
from export import to_markdown, to_json, get_export_filename

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI EdTech Assistant", page_icon="🎓", layout="wide")

PIPELINE_MODELS = {
    "Transcript": f"Google Chirp `{CHIRP_MODEL}` ({CHUNK_SECONDS}s/chunk)",
    "Cleanup": TRANSCRIPT_CLEANUP_MODEL,
    "Summary": SUMMARY_MODEL,
    "Quiz": QUIZ_MODEL,
}


DIFFICULTY_LABEL = {
    "beginner": "🟢 Cơ bản",
    "intermediate": "🟡 Trung bình",
    "advanced": "🔴 Nâng cao",
}


if "result" not in st.session_state:
    st.session_state.result = None
if "model_used" not in st.session_state:
    st.session_state.model_used = None
if "filename" not in st.session_state:
    st.session_state.filename = None

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3048/3048122.png", width=80)
    st.markdown("## AI EdTech Assistant")
    st.caption("Tóm tắt bài giảng & sinh trắc nghiệm tự động.")
    st.divider()

    st.markdown("**Pipeline model**")
    for step_name, model_name in PIPELINE_MODELS.items():
        st.caption(f"{step_name}: `{model_name}`")

    st.divider()
    st.markdown("**Hướng dẫn**")
    st.markdown(
        "1. Tải lên file ghi âm bài giảng\n"
        "2. Chọn mô hình AI phù hợp\n"
        "3. Nhấn **Phân tích**\n"
        "4. Xem kết quả ở 3 tab bên phải"
    )
    st.divider()
    st.caption(
        "Hỗ trợ: mp3 · mp4 · mpeg · mpga · m4a · wav · webm · flac · ogg "
        f"(≤ {MAX_FILE_SIZE_MB} MB)"
    )

# ── Main layout ───────────────────────────────────────────────────────────────
st.title("🎓 Hệ Thống Tóm Tắt & Sinh Trắc Nghiệm Tự Động")

st.caption(
    "Ứng dụng AI tối ưu hóa quá trình học tập — phân tích bài giảng trong vài chục giây."
)
st.divider()

col_input, col_output = st.columns([1, 2], gap="large")

# ── Input column ──────────────────────────────────────────────────────────────
with col_input:
    st.subheader("📂 Tải bài giảng lên")

    uploaded_file = st.file_uploader(
        "Chọn file audio",
        type=["mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm", "flac", "ogg"],
        label_visibility="collapsed",
    )
    glossary_text = st.text_area(
        "Thuật ngữ gợi ý",
        placeholder="Ví dụ: machine learning, gradient descent, hồi quy tuyến tính...",
        height=90,
    )

    if uploaded_file:
        st.audio(uploaded_file)
        size_mb = uploaded_file.size / (1024 * 1024)
        st.caption(f"📄 {uploaded_file.name} · {size_mb:.1f} MB")

        is_valid, error_msg = validate_audio_file(uploaded_file)

        if not is_valid:
            st.error(error_msg)
st.markdown("*Giải pháp AI toàn diện tối ưu hóa thời gian học tập.*")

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Đầu vào")
    uploaded_file = st.file_uploader("Tải bài giảng lên đây (.mp3, .wav, .m4a)", type=['mp3', 'wav', 'm4a'])
    
    if uploaded_file is not None:
        st.audio(uploaded_file, format='audio/wav')
        temp_path = f"temp_{uploaded_file.name}"
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        analyze_btn = st.button("🚀 Xử lý dữ liệu", type="primary", use_container_width=True)

with col2:
    st.subheader("Kết quả đầu ra")
    if uploaded_file is not None and analyze_btn:
        with st.spinner('⏳ Hệ thống AI đang quét và phân tích. Quá trình này có thể mất vài chục giây...'):
            final_result, model_used = process_audio_with_gemini(temp_path)
            
        if model_used:
            st.success(f"✅ Hoàn tất! (Mô hình sử dụng: {model_used})")
            with st.container(border=True):
                st.write(final_result)
 main
        else:
            analyze_clicked = st.button(
                "🚀 Phân tích bài giảng", type="primary", use_container_width=True
            )

            if analyze_clicked:
                st.session_state.result = None
                gemini_client = None
                chirp_client = None
                temp_path = None

                with st.status("🔄 Đang xử lý bài giảng...", expanded=True) as status:
                    try:
                        gemini_client = get_client()

                        # Bước 1: save temp file
                        st.write("📥 **Bước 1/6** — Đang lưu file audio tạm thời...")
                        temp_path = save_uploaded_audio(uploaded_file)
                        st.write("✔️ Lưu file hoàn tất.")

                        # Bước 2: transcript with Google Chirp
                        st.write(
                            f"🎧 **Bước 2/6** — Đang chia audio và transcribe bằng Google `{CHIRP_MODEL}`..."
                        )
                        try:
                            chirp_client = get_chirp_client()
                            transcript_data = transcribe_with_chirp(
                                chirp_client,
                                temp_path,
                                progress_callback=st.write,
                            )
                        except Exception as chirp_error:
                            st.warning(
                                "Google Chirp chưa dùng được hoặc lỗi cấu hình. "
                                f"Đang fallback sang Gemini `{TRANSCRIPT_FALLBACK_MODEL}`. "
                                f"Chi tiết: {chirp_error}"
                            )
                            transcript_data = transcribe_with_gemini_audio(
                                gemini_client, temp_path
                            )
                        st.write("✔️ Transcript hoàn tất.")

                        # Bước 3: cleanup transcript
                        st.write(
                            f"🧹 **Bước 3/6** — Gemini `{TRANSCRIPT_CLEANUP_MODEL}` đang làm sạch transcript..."
                        )
                        cleanup_data = cleanup_transcript(
                            gemini_client,
                            TRANSCRIPT_CLEANUP_MODEL,
                            transcript_data["raw_transcript"],
                            glossary_text.strip(),
                        )
                        transcript_data = {**transcript_data, **cleanup_data}
                        st.write("✔️ Làm sạch transcript hoàn tất.")

                        # Bước 4: summary with Gemini Flash-Lite
                        st.write(
                            f"📝 **Bước 4/6** — Gemini `{SUMMARY_MODEL}` đang tóm tắt..."
                        )
                        summary_raw = generate_summary(
                            gemini_client, SUMMARY_MODEL, transcript_data["transcript"]
                        )
                        summary_data = parse_summary_response(summary_raw)
                        st.write("✔️ Tóm tắt hoàn tất.")

                        # Bước 5: quiz with Gemini Pro
                        st.write(
                            f"📊 **Bước 5/6** — Gemini `{QUIZ_MODEL}` đang tạo trắc nghiệm..."
                        )
                        quiz_raw = generate_quiz(
                            gemini_client,
                            QUIZ_MODEL,
                            transcript_data["transcript"],
                            summary_data["summary"],
                        )
                        quiz_data = parse_quiz_response(quiz_raw)
                        st.write("✔️ Trắc nghiệm hoàn tất.")

                        # Bước 6: merge result
                        st.write("🔍 **Bước 6/6** — Đang kiểm tra và ghép kết quả...")
                        result = {
                            **transcript_data,
                            **summary_data,
                            **quiz_data,
                            "pipeline_models": PIPELINE_MODELS,
                        }
                        st.write("✔️ Dữ liệu hợp lệ.")

                        st.session_state.result = result
                        st.session_state.model_used = "Google Chirp + Gemini"
                        st.session_state.filename = uploaded_file.name
                        status.update(label="✅ Hoàn tất!", state="complete")

                    except Exception as e:
                        status.update(label="❌ Xử lý thất bại", state="error")
                        st.error(f"**Lỗi:** {e}")

                    finally:
                        cleanup_audio_file(temp_path)

    else:
        st.info("Chọn file audio để bắt đầu phân tích.")

        # Giữ kết quả cũ nếu user chưa upload file mới
        if st.session_state.result:
            st.caption(f"Đang hiển thị kết quả của: **{st.session_state.filename}**")

# ── Output column ─────────────────────────────────────────────────────────────
with col_output:
    st.subheader("📊 Kết quả phân tích")

    data = st.session_state.result

    if data is None:
        st.info("Kết quả sẽ hiển thị ở đây sau khi phân tích xong.")

    else:
        # Header info
        meta = data.get("metadata", {})
        difficulty_key = meta.get("difficulty_level", "")
        difficulty_str = DIFFICULTY_LABEL.get(difficulty_key, difficulty_key)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Mô hình", st.session_state.model_used or "N/A")
        m2.metric("Chủ đề", meta.get("topic", "N/A"))
        m3.metric("Thời lượng", f"{meta.get('estimated_duration_minutes', '?')} phút")
        m4.metric("Độ khó", difficulty_str or "N/A")

        st.divider()

        # ── Tabs ──────────────────────────────────────────────────────────────
        tab_transcript, tab_summary, tab_quiz = st.tabs(
            [
                "📝 Transcript",
                "📌 Tóm tắt",
                "📊 Trắc nghiệm",
            ]
        )

        # Tab 1: Transcript
        with tab_transcript:
            transcript = data.get("transcript", "")
            st.markdown("#### Nội dung bài giảng")

            if transcript:
                word_count = len(transcript.split())
                st.caption(f"Tổng số từ: {word_count}")
                with st.container(border=True):
                    st.markdown(transcript)

                corrections = data.get("cleanup_corrections", [])
                if corrections:
                    with st.expander("Các chỉnh sửa transcript"):
                        for correction in corrections:
                            st.markdown(f"- {correction}")

                raw_transcript = data.get("raw_transcript", "")
                if raw_transcript and raw_transcript != transcript:
                    with st.expander("Raw transcript trước cleanup"):
                        st.markdown(raw_transcript)

                transcript_segments = data.get("transcript_segments", [])
                if transcript_segments:
                    with st.expander("Segment transcript từ Google Chirp"):
                        for segment in transcript_segments[:50]:
                            start = segment.get("start", 0)
                            end = segment.get("end", 0)
                            text = segment.get("text", "").strip()
                            st.markdown(f"- **{start:.1f}s - {end:.1f}s:** {text}")
            else:
                st.warning("Không trích xuất được transcript.")

        # Tab 2: Summary
        with tab_summary:
            summary = data.get("summary", [])
            st.markdown("#### Các ý chính")

            if summary:
                for i, point in enumerate(summary, 1):
                    with st.container(border=True):
                        st.markdown(f"**{i}.** {point}")
            else:
                st.warning("Không tóm tắt được nội dung.")

        # Tab 3: Quiz
        with tab_quiz:
            quiz = data.get("quiz", [])
            st.markdown("#### Câu hỏi kiểm tra")

            if quiz:
                st.caption(f"Tổng số câu: {len(quiz)}")
                for i, q in enumerate(quiz, 1):
                    with st.container(border=True):
                        st.markdown(f"**Câu {i}:** {q.get('question', '')}")

                        options = q.get("options", {})
                        for key, val in options.items():
                            st.markdown(f"&nbsp;&nbsp;**{key}.** {val}")

                        with st.expander("Xem đáp án & giải thích"):
                            answer = q.get("answer", "")
                            explanation = q.get("explanation", "")
                            st.success(f"✅ Đáp án đúng: **{answer}**")
                            if explanation:
                                st.info(f"💡 {explanation}")
            else:
                st.warning("Không sinh được câu hỏi trắc nghiệm.")

        # ── Export ────────────────────────────────────────────────────────────
        st.divider()
        st.markdown("#### ⬇️ Tải kết quả")

        fname = st.session_state.filename or "bai_giang"
        col_dl1, col_dl2 = st.columns(2)

        with col_dl1:
            md_content = to_markdown(data, fname)
            st.download_button(
                label="📄 Tải Markdown (.md)",
                data=md_content.encode("utf-8"),
                file_name=get_export_filename(fname, ".md"),
                mime="text/markdown",
                use_container_width=True,
            )

        with col_dl2:
            json_content = to_json(data)
            st.download_button(
                label="🗂️ Tải JSON (.json)",
                data=json_content.encode("utf-8"),
                file_name=get_export_filename(fname, ".json"),
                mime="application/json",
                use_container_width=True,
            )
