"""
Admin Handler: Xử lý toàn bộ trang Admin Dashboard.
Bao gồm: đăng nhập OTP, dashboard component, xử lý admin actions.
"""
import json

import streamlit as st
import streamlit.components.v1 as components

from models.constants import FRONTEND_ADMIN_DIR, CONSULT_FILE
from middleware.session_manager import init_admin_session
from services.auth_service import (
    validate_admin_login, generate_otp, send_otp_email, is_smtp_configured,
)
from services.history_service import load_history, compute_stats
from services.knowledge_service import (
    update_knowledge_status, delete_knowledge_file, upload_knowledge_file,
)
from services.prompt_service import save_system_prompts
from utils.file_helpers import safe_read_json, safe_write_json


def render_admin_page():
    """Render và xử lý toàn bộ trang Admin."""
    init_admin_session()

    # --- GIAO DIỆN ĐĂNG NHẬP ---
    if not st.session_state.admin_logged_in:
        _render_login_page()
        st.stop()

    # --- GIAO DIỆN ADMIN DASHBOARD ---
    _render_dashboard()
    st.stop()


# ==============================================================================
# ĐĂNG NHẬP ADMIN
# ==============================================================================

def _render_login_page():
    """Render giao diện đăng nhập admin (email + password + OTP)."""
    # CSS cho trang đăng nhập
    st.markdown("""
    <style>
        #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"] { display: none !important; }
        /* Animated gradient background */
        .stApp {
            background: linear-gradient(-45deg, #0f172a, #312e81, #1e1b4b, #0f172a) !important;
            background-size: 400% 400% !important;
            animation: gradientBG 15s ease infinite !important;
            color: #f8fafc !important;
        }
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .block-container, [data-testid="stMainBlockContainer"] {
            padding-top: 10vh !important;
            max-width: 480px !important;
            margin: 0 auto !important;
            z-index: 10 !important;
        }
        /* Glowing container for title */
        .login-container {
            padding: 40px 30px 20px 30px;
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-bottom: none;
            border-radius: 24px 24px 0 0;
            text-align: center;
            margin-bottom: -25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            position: relative;
            z-index: 20;
        }
        .login-title {
            background: linear-gradient(to right, #a855f7, #3b82f6, #06b6d4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 30px;
            font-weight: 850;
            margin-bottom: 8px;
            letter-spacing: -0.03em;
        }
        .login-subtitle {
            color: #cbd5e1;
            font-size: 15px;
            font-weight: 400;
        }
        /* Streamlit Form Container */
        div[data-testid="stForm"] {
            background: rgba(15, 23, 42, 0.5) !important;
            backdrop-filter: blur(20px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 0 0 24px 24px !important;
            padding: 40px 35px 30px 35px !important;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5) !important;
            position: relative;
            z-index: 10;
        }
        /* Input Labels */
        div[data-testid="stTextInput"] label p {
            color: #e2e8f0 !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            letter-spacing: 0.02em !important;
        }
        /* Input wrapper */
        div[data-testid="stTextInput"] > div > div {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
            display: flex !important;
            align-items: center !important;
        }
        div[data-testid="stTextInput"] > div > div:focus-within {
            border-color: #8b5cf6 !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
            box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2) !important;
        }
        div[data-testid="stTextInput"] div[data-baseweb="base-input"],
        div[data-testid="stTextInput"] input {
            background-color: transparent !important;
            border: none !important;
            color: #ffffff !important;
            box-shadow: none !important;
        }
        div[data-testid="stTextInput"] input {
            padding: 14px !important;
            font-size: 15px !important;
            outline: none !important;
            flex: 1 !important;
            min-width: 0 !important;
        }
        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within {
            border: none !important;
            box-shadow: none !important;
            background-color: transparent !important;
        }
        /* Password toggle eye icon */
        div[data-testid="stTextInput"] button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 1px 0 4px !important;
            margin: 0 !important;
            width: auto !important;
            min-width: auto !important;
            color: rgba(255, 255, 255, 0.5) !important;
            flex-shrink: 0 !important;
            cursor: pointer !important;
            margin-top: 0 !important;
        }
        div[data-testid="stTextInput"] button:hover {
            color: rgba(255, 255, 255, 0.9) !important;
            background: transparent !important;
            box-shadow: none !important;
            transform: none !important;
        }
        /* Form Submit Button */
        div[data-testid="stFormSubmitButton"] button {
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
            color: white !important;
            border: none !important;
            padding: 12px 24px !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            width: 100% !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            margin-top: 15px !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 12px 25px rgba(99, 102, 241, 0.6) !important;
        }
        div[data-testid="stFormSubmitButton"] button:active {
            transform: translateY(0) scale(0.98) !important;
        }
        /* Back button style */
        .stButton > button {
            background: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            color: #cbd5e1 !important;
            margin-top: 20px !important;
            border-radius: 12px !important;
            font-weight: 500 !important;
            transition: all 0.2s !important;
        }
        .stButton > button:hover {
            background: rgba(255, 255, 255, 0.05) !important;
            color: white !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    if not st.session_state.admin_otp_sent:
        # --- Bước 1: Nhập email + mật khẩu ---
        st.markdown("""
        <div class="login-container">
            <div class="login-title">🎓 Cổng Admin Tuyển Sinh</div>
            <div class="login-subtitle">Nhập thông tin quản trị viên để tiếp tục</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("admin_login_form"):
            email = st.text_input("📧 Email Admin", placeholder="admin@example.com")
            password = st.text_input("🔑 Mật khẩu", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Gửi mã OTP")

            if submit:
                if validate_admin_login(email, password):
                    if email:
                        otp = generate_otp()
                        st.session_state.admin_otp = otp
                        st.session_state.admin_email = email

                        with st.spinner("Đang gửi OTP..."):
                            if send_otp_email(email, otp):
                                st.session_state.admin_otp_sent = True
                                st.rerun()
                    else:
                        st.error("Vui lòng nhập Email!")
                else:
                    st.error("Mật khẩu không chính xác!")
    else:
        # --- Bước 2: Xác thực OTP ---
        smtp_configured = is_smtp_configured()
        smtp_configured = False

        if smtp_configured:
            subtitle_text = (
                f'Mã OTP đã được gửi đến hộp thư<br>'
                f'<b style="color:#38bdf8">{st.session_state.admin_email}</b>'
            )
        else:
            subtitle_text = "Nhập mã OTP bên dưới để xác nhận đăng nhập"

        st.markdown(f"""
        <div class="login-container">
            <div class="login-title">🔐 Xác thực OTP</div>
            <div class="login-subtitle">{subtitle_text}</div>
        </div>
        """, unsafe_allow_html=True)

        if not smtp_configured:
            st.info(f"🔑 Mã OTP của bạn là: **{st.session_state.admin_otp}**")

        with st.form("admin_otp_form"):
            otp_input = st.text_input("💬 Nhập mã OTP 6 số", placeholder="123456")
            verify = st.form_submit_button("Xác nhận đăng nhập")

            if verify:
                if otp_input.strip() == st.session_state.admin_otp:
                    st.session_state.admin_logged_in = True
                    st.rerun()
                else:
                    st.error("Mã OTP không chính xác!")

        if st.button("⬅️ Quay lại đăng nhập", use_container_width=True):
            st.session_state.admin_otp_sent = False
            st.rerun()


# ==============================================================================
# ADMIN DASHBOARD
# ==============================================================================

def _render_dashboard():
    """Render admin dashboard với custom component."""
    # CSS ẩn header admin
    st.markdown("""
    <style>
        #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"] { display: none !important; }
        .stApp { overflow: hidden; }
        .block-container, [data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; overflow: hidden; }
        [data-testid="stCustomComponentV1"], [data-testid="stCustomComponentV1"] > div, [data-testid="stCustomComponentV1"] iframe {
            position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; border: none !important; z-index: 999;
        }
    </style>
    """, unsafe_allow_html=True)

    _admin_component = components.declare_component(
        "admin_ui", path=str(FRONTEND_ADMIN_DIR)
    )

    # Load data
    history_data = load_history()
    stats = compute_stats(history_data)

    # Load consultation registrations
    consult_list = safe_read_json(CONSULT_FILE, default=[])
    stats["consult_registrations"] = consult_list

    # Render component
    admin_action = _admin_component(
        stats=json.dumps(stats, ensure_ascii=False),
        key="admin",
        default=None,
    )

    # Handle admin actions from frontend
    if admin_action is not None:
        ts = admin_action.get("timestamp", 0)
        if ts != st.session_state.admin_last_ts:
            st.session_state.admin_last_ts = ts
            action = admin_action.get("action", "")
            _dispatch_admin_action(action, admin_action, consult_list)


def _dispatch_admin_action(action, admin_action, consult_list):
    """Phân luồng xử lý các action từ admin frontend."""
    if action == "admin_logout":
        st.session_state.admin_logged_in = False
        st.session_state.admin_otp_sent = False
        st.session_state.admin_otp = ""
        st.session_state.admin_email = ""
        st.rerun()

    elif action == "delete_consult":
        idx = admin_action.get("index")
        if idx is not None and 0 <= idx < len(consult_list):
            consult_list.pop(idx)
            safe_write_json(CONSULT_FILE, consult_list)
            st.rerun()

    elif action == "update_consult_status":
        idx = admin_action.get("index")
        status = admin_action.get("status", "")
        if idx is not None and 0 <= idx < len(consult_list):
            consult_list[idx]["status"] = status
            safe_write_json(CONSULT_FILE, consult_list)
            st.rerun()

    elif action == "update_consult_note":
        idx = admin_action.get("index")
        note = admin_action.get("note", "")
        if idx is not None and 0 <= idx < len(consult_list):
            consult_list[idx]["admin_note"] = note
            safe_write_json(CONSULT_FILE, consult_list)
            st.rerun()

    elif action == "update_knowledge_status":
        filename = admin_action.get("filename")
        enabled = admin_action.get("enabled")
        update_knowledge_status(filename, enabled)
        st.session_state.rag_initialized = False
        st.rerun()

    elif action == "delete_knowledge_file":
        filename = admin_action.get("filename")
        if filename and filename not in {
            "chat_history.json", "consult_registrations.json", "knowledge_config.json"
        }:
            delete_knowledge_file(filename)
            st.session_state.rag_initialized = False
            st.rerun()

    elif action == "update_system_prompt":
        prompts_dict = admin_action.get("prompts", {})
        if save_system_prompts(prompts_dict):
            st.session_state.rag_initialized = False
        st.rerun()

    elif action == "upload_knowledge_file":
        filename = admin_action.get("filename")
        content = admin_action.get("content")
        upload_knowledge_file(filename, content)
        st.rerun()
