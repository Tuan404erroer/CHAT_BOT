"""
Session Manager: Quản lý Streamlit session_state tập trung.
Khởi tạo và cung cấp các helper truy cập session state.
"""
import uuid
import streamlit as st

from services.history_service import load_history


def init_chat_session():
    """Khởi tạo tất cả session state cần thiết cho trang Chat."""
    if "history_data" not in st.session_state:
        st.session_state.history_data = load_history()
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.mssv = ""
        st.session_state.dob = ""
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_ts" not in st.session_state:
        st.session_state.last_ts = 0

    # RAG system state
    if "rag_initialized" not in st.session_state:
        st.session_state.rag_initialized = False
        st.session_state.qa_chain_all = None
        st.session_state.qa_chain_diem_chuan = None
        st.session_state.llm = None

    # Khởi tạo session_id nếu rỗng
    if st.session_state.current_session_id is None:
        st.session_state.current_session_id = str(uuid.uuid4())


def init_admin_session():
    """Khởi tạo tất cả session state cần thiết cho trang Admin."""
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
    if "admin_otp" not in st.session_state:
        st.session_state.admin_otp = ""
    if "admin_email" not in st.session_state:
        st.session_state.admin_email = ""
    if "admin_otp_sent" not in st.session_state:
        st.session_state.admin_otp_sent = False
    if "admin_last_ts" not in st.session_state:
        st.session_state.admin_last_ts = 0


def get_user_key():
    """Lấy user_key từ session state (dùng để tra cứu lịch sử).
    
    Returns:
        str: "{mssv}_{dob}" nếu đã đăng nhập, "_guest_" nếu chưa
    """
    if st.session_state.logged_in:
        return st.session_state.mssv.strip()
    return "_guest_"


def ensure_user_history():
    """Đảm bảo user hiện tại có entry trong history_data."""
    if st.session_state.logged_in:
        user_key = get_user_key()
        if user_key not in st.session_state.history_data:
            st.session_state.history_data[user_key] = {}
