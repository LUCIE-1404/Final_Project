import streamlit as st
import os, tempfile
from ui_components import render_sidebar
from gemini_service import transcribe_audio, cleanup_transcript, summarize_lecture, generate_quiz
from export import to_markdown, get_export_filename

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="AI Lecture Assistant", layout="wide")

# Khởi tạo bộ nhớ session_state
if "results" not in st.session_state:
    st.session_state.results = None

render_sidebar()

st.title("🎓 Hệ Thống Tóm Chép & Tự Động Tạo Trắc Nghiệm")
st.caption("Ứng dụng Trí tuệ nhân tạo hỗ trợ ôn tập bài giảng hiệu quả.")
st.markdown("---")

col_in, col_out = st.columns([1, 1], gap="large")

with col_in:
    st.subheader("Đầu vào")
    up_file = st.file_uploader("Tải file audio", type=["mp3", "wav", "m4a"], label_visibility="collapsed")
    
    if up_file:
        st.audio(up_file)
        if st.button("🚀 Xử lý dữ liệu", type="primary", use_container_width=True):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{up_file.name.split('.')[-1]}") as tmp:
                tmp.write(up_file.getvalue())
                tmp_path = tmp.name
            try:
                with st.status("AI đang phân tích bài giảng...", expanded=True) as s:
                    # Chạy luồng xử lý AI
                    raw = transcribe_audio(tmp_path).get("transcript", "")
                    clean_data = cleanup_transcript(raw)
                    txt = clean_data.get("clean_transcript", raw)
                    sum_d = summarize_lecture(txt)
                    quiz_d = generate_quiz(txt, sum_d)
                    
                    # Lưu kết quả
                    st.session_state.results = {
                        "transcript": txt, 
                        "summary": sum_d.get("summary", []),
                        "quiz": quiz_d.get("quiz", []), 
                        "metadata": sum_d.get("metadata", {})
                    }
                st.rerun() # Làm mới để hiện kết quả
            except Exception as e:
                st.error(f"Lỗi hệ thống: {e}")
            finally:
                if os.path.exists(tmp_path): os.remove(tmp_path)

with col_out:
    st.subheader("Kết quả đầu ra")
    
    if not st.session_state.results:
        st.info("Hãy upload file và nhấn 'Xử lý dữ liệu' để bắt đầu.")
    else:
        res = st.session_state.results
        tab1, tab2, tab3 = st.tabs(["📌 Tóm tắt ý chính", "📊 Bài tập trắc nghiệm", "📝 Transcript đầy đủ"])
        
        with tab1:
            st.markdown("### 📌 Nội dung cốt lõi")
            for i in res['summary']:
                st.write(f"✅ {i}")
        
        with tab2:
            st.markdown("### 📊 Kiểm tra kiến thức")
            st.caption("Chọn đáp án của bạn để kiểm tra kết quả.")
            
            # LOGIC TRẮC NGHIỆM TƯƠNG TÁC
            for idx, q in enumerate(res['quiz'], 1):
                st.write(f"**Câu {idx}: {q['question']}**")
                
                # Tạo danh sách các lựa chọn để hiển thị
                options_labels = [f"{k}. {v}" for k, v in q['options'].items()]
                
                # Widget chọn đáp án (Radio)
                # index=None giúp không có câu nào được chọn mặc định
                choice = st.radio(
                    f"Lựa chọn cho câu {idx}:",
                    options_labels,
                    index=None,
                    key=f"quiz_q_{idx}",
                    label_visibility="collapsed"
                )
                
                # Khi người dùng đã chọn một option (choice không còn là None)
                if choice:
                    selected_letter = choice[0] # Lấy ký tự đầu tiên 'A', 'B', 'C' hoặc 'D'
                    correct_answer = q['answer']
                    
                    if selected_letter == correct_answer:
                        st.success(f"🎯 Chính xác! Đáp án đúng là {correct_answer}")
                    else:
                        st.error(f"❌ Chưa đúng! Đáp án chính xác là {correct_answer}")
                    
                    # Tự động "sổ" phần giải thích xuống dưới
                    st.info(f"💡 **Giải thích:** {q.get('explanation', 'Không có giải thích chi tiết.')}")
                
                st.markdown("---") # Đường kẻ phân cách giữa các câu hỏi

        with tab3:
            st.markdown("### 📝 Văn bản bài giảng")
            
            # Lấy text ra an toàn, đề phòng biến bị rỗng
            transcript_text = res.get('transcript', '')
            
            if not transcript_text:
                st.warning("⚠️ Đang có lỗi hiển thị văn bản trực tiếp. Bạn hãy tải file (.md) về để xem nhé!")
            else:
                # Dùng text_area để tạo hộp chứa có thanh cuộn, chống lỗi với văn bản siêu dài
                st.text_area(
                    "Nội dung chi tiết", 
                    value=transcript_text, 
                    height=400, # Giới hạn chiều cao hộp để có thanh cuộn
                    disabled=True, # Khóa không cho người dùng gõ sửa linh tinh
                    label_visibility="collapsed"
                )