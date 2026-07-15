"""
Entry point cho ứng dụng Streamlit.
Routing giữa trang Chat và trang Admin dựa trên query parameter.

Chạy: streamlit run backend/main.py
"""
import sys
from pathlib import Path

# Thêm thư mục backend/ vào Python path để import sạch sẽ
# Ví dụ: from services.rag_service import ...
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="Tư Vấn Tuyển Sinh AI",
    page_icon="🎓",
    layout="wide",
)

# --- ĐIỀU HƯỚNG BẰNG QUERY PARAMS ---
page = st.query_params.get("page", "chat")

if page == "admin":
    from api.admin_handler import render_admin_page
    render_admin_page()
else:
    from api.chat_handler import render_chat_page
    render_chat_page()
