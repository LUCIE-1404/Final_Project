import streamlit as st
from google import genai
import os
import time
from dotenv import load_dotenv

st.set_page_config(page_title="AI EdTech Assistant", page_icon="🎓", layout="wide")

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_working_model():
    try:
        for m in client.models.list():
            name = m.name.replace("models/", "")
            if "gemini" in name and ("flash" in name or "pro" in name) and "live" not in name and "native" not in name:
                return name
    except Exception:
        pass
    return "gemini-2.5-flash"

def process_audio_with_gemini(audio_file_path):
    uploaded_file = None
    try:
        best_model = get_working_model()
        uploaded_file = client.files.upload(file=audio_file_path)
        
        prompt = """
        Hãy đóng vai một giáo viên chuyên môn cao. Dưới đây là file ghi âm của một bài giảng.
        Hãy nghe kỹ và thực hiện 3 nhiệm vụ sau bằng tiếng Việt:
        
        ### 1. Transcript
        Ghi lại toàn bộ nội dung lời nói trong audio.
        
        ### 2. TÓM TẮT BÀI GIẢNG
        Rút ra các ý chính quan trọng nhất dưới dạng gạch đầu dòng.
        
        ### 3. ĐỀ KIỂM TRA TRẮC NGHIỆM
        Tạo ra 3 câu hỏi trắc nghiệm (A, B, C, D) dựa trên nội dung bài giảng. Cung cấp đáp án đúng ở cuối mỗi câu.
        """
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=best_model,
                    contents=[uploaded_file, prompt]
                )
                return response.text, best_model
            except Exception as e:
                if "503" in str(e):
                    if attempt < max_retries - 1:
                        time.sleep(5)
                    else:
                        return f"Máy chủ Google liên tục quá tải. Vui lòng thử lại sau.", None
                else:
                    return f"❌ Đã xảy ra lỗi AI: {e}", None
    except Exception as e:
        return f"Đã xảy ra lỗi hệ thống: {e}", None
    finally:
        if uploaded_file:
            try:
                client.files.delete(name=uploaded_file.name)
            except:
                pass

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3048/3048122.png", width=100)
    st.markdown("## Về Hệ Thống")
    st.info("Hệ thống ứng dụng mô hình Trí tuệ nhân tạo tạo sinh để hỗ trợ quá trình dạy và học.")
    st.markdown("---")
    st.markdown("**Hướng dẫn:**")
    st.markdown("1. Tải lên file ghi âm bài giảng.\n2. Nhấn nút Phân tích.\n3. Nhận kết quả tóm tắt & trắc nghiệm.")

#Giao diện chính
st.title("🎓 Hệ Thống Tóm Tắt & Sinh Trắc Nghiệm Tự Động")
st.markdown("*Giải pháp AI toàn diện tối ưu hóa thời gian học tập.*")

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Đầu vào")
    uploaded_file = st.file_uploader("Tải bài giảng lên đây (.mp3, .wav)", type=['mp3', 'wav', 'm4a'])
    
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
        else:
            st.error(final_result)
            
        if os.path.exists(temp_path):
            os.remove(temp_path)
    elif uploaded_file is None:
        st.info("Vui lòng tải file ở cột bên trái để bắt đầu.")