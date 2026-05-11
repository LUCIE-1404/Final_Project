import streamlit as st

def render_sidebar():
    """Hàm vẽ thanh bên (sidebar) của ứng dụng."""
    with st.sidebar:
        st.markdown("<h1 style='text-align: center;'>👨‍🏫</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Hệ Thống AI Trợ Giảng</h3>", unsafe_allow_html=True)
        
        st.info("Hệ thống đang sẵn sàng phân tích.")
        
        st.markdown("---")
        st.markdown("**Hướng dẫn:**\n1. Upload file\n2. Bấm Xử lý\n3. Xem kết quả & Tải báo cáo")