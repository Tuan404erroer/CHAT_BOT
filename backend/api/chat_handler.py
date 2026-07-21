"""
Chat Handler: Xử lý toàn bộ trang Chatbot.
Declare component, render giao diện, xử lý các action từ frontend.
"""
import json
import uuid

import streamlit as st
import streamlit.components.v1 as components

from models.constants import FRONTEND_DIR, CONSULT_FILE
from middleware.session_manager import (
    init_chat_session, get_user_key, ensure_user_history,
)
from services.rag_service import ensure_rag_system
from services.chat_service import process_query
from services.history_service import save_history
from services.user_service import save_user
from utils.file_helpers import safe_read_json, safe_write_json


def render_chat_page():
    """Render và xử lý toàn bộ trang Chatbot."""

    # --- CSS ẨN STREAMLIT HEADER ---
    st.markdown("""
    <style>
        #MainMenu, footer, header,
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stHeader"] { display: none !important; }

        .stApp { overflow: hidden; }

        .block-container,
        [data-testid="stMainBlockContainer"] {
            padding: 0 !important;
            max-width: 100% !important;
            overflow: hidden;
        }

        /* Đưa iframe component chiếm full viewport */
        [data-testid="stCustomComponentV1"],
        [data-testid="stCustomComponentV1"] > div,
        [data-testid="stCustomComponentV1"] iframe {
            position: fixed !important;
            top: 0 !important; left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            border: none !important;
            z-index: 999;
        }
    </style>
    <script>
        // Inject allow="microphone" vào iframe của custom component
        // để Web Speech API có thể hoạt động bên trong iframe
        function enableMicInIframe() {
            const iframes = document.querySelectorAll('[data-testid="stCustomComponentV1"] iframe');
            iframes.forEach(iframe => {
                if (!iframe.getAttribute('allow') || !iframe.getAttribute('allow').includes('microphone')) {
                    iframe.setAttribute('allow', 'microphone; autoplay');
                }
            });
        }
        // Chạy ngay và lặp lại vì iframe có thể load sau
        enableMicInIframe();
        const micObserver = new MutationObserver(enableMicInIframe);
        micObserver.observe(document.body, { childList: true, subtree: true });
        // Dừng theo dõi sau 10 giây để tiết kiệm tài nguyên
        setTimeout(() => micObserver.disconnect(), 10000);
    </script>
    """, unsafe_allow_html=True)

    # --- KHỞI TẠO SESSION ---
    init_chat_session()

    user_key = get_user_key()
    ensure_user_history()

    user_history = (
        st.session_state.history_data.get(user_key, {})
        if st.session_state.logged_in
        else {}
    )

    # --- KHỞI TẠO RAG SYSTEM ---
    qa_chain_all, qa_chain_diem_chuan, llm = ensure_rag_system()

    # --- KHAI BÁO CUSTOM COMPONENT ---
    _chat_component = components.declare_component(
        "chat_ui", path=str(FRONTEND_DIR)
    )

    # --- RENDER COMPONENT ---
    user_input = _chat_component(
        messages=json.dumps(st.session_state.messages, ensure_ascii=False),
        logged_in=st.session_state.logged_in,
        mssv=st.session_state.mssv,
        history=json.dumps(user_history, ensure_ascii=False),
        current_session_id=st.session_state.current_session_id,
        key="chat",
        default=None,
    )

    # --- XỬ LÝ ACTION TỪ FRONTEND ---
    if user_input is not None:
        ts = user_input.get("timestamp", 0)

        if ts != st.session_state.last_ts:
            st.session_state.last_ts = ts
            action = user_input.get("action", "chat")

            if action == "login":
                _handle_login(user_input)
            elif action == "logout":
                _handle_logout()
            elif action == "new_session":
                _handle_new_session()
            elif action == "load_session":
                _handle_load_session(user_input)
            elif action == "rate":
                _handle_rate(user_input)
            elif action == "consult_register":
                _handle_consult_register(user_input, ts)
            elif action == "chat":
                _handle_chat(user_input, qa_chain_all, qa_chain_diem_chuan, llm)


# ==============================================================================
# CÁC HÀM XỬ LÝ ACTION (PRIVATE)
# ==============================================================================

def _handle_login(user_input):
    mssv = user_input.get("mssv", "")
    dob = user_input.get("dob", "")

    st.session_state.logged_in = True
    st.session_state.mssv = mssv
    st.session_state.dob = dob
    st.session_state.messages = []
    st.session_state.current_session_id = str(uuid.uuid4())

    # Lưu tài khoản vào file users.json (tạo mới hoặc cập nhật last_login)
    save_user(mssv, dob)

    st.rerun()


def _handle_logout():
    st.session_state.logged_in = False
    st.session_state.mssv = ""
    st.session_state.dob = ""
    st.session_state.messages = []
    st.rerun()


def _handle_new_session():
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.rerun()


def _handle_load_session(user_input):
    user_key = get_user_key()
    st.session_state.current_session_id = user_input.get("session_id")
    session_info = (
        st.session_state.history_data
        .get(user_key, {})
        .get(st.session_state.current_session_id, {})
    )
    st.session_state.messages = session_info.get("messages", [])
    st.rerun()


def _handle_rate(user_input):
    msg_index = user_input.get("message_index")
    rating = user_input.get("rating")
    user_key = get_user_key()

    if msg_index is not None and msg_index < len(st.session_state.messages):
        st.session_state.messages[msg_index]["rating"] = rating

        user_history = st.session_state.history_data.get(user_key, {})
        if st.session_state.current_session_id in user_history:
            user_history[st.session_state.current_session_id]["messages"] = (
                st.session_state.messages
            )
            save_history(st.session_state.history_data)
    # KHÔNG RERUN - chỉ lưu vào file, giao diện frontend tự cập nhật


def _handle_consult_register(user_input, ts):
    user_key = get_user_key()
    consult_data = {
        "name": user_input.get("name", ""),
        "phone": user_input.get("phone", ""),
        "email": user_input.get("email", ""),
        "major": user_input.get("major", ""),
        "message": user_input.get("message", ""),
        "timestamp": ts,
        "user_key": user_key if st.session_state.logged_in else "guest",
    }

    consult_list = safe_read_json(CONSULT_FILE, default=[])
    consult_list.append(consult_data)
    safe_write_json(CONSULT_FILE, consult_list)
    st.rerun()


def _handle_chat(user_input, qa_chain_all, qa_chain_diem_chuan, llm):
    query = user_input.get("message", "")

    # Lưu tin nhắn user
    st.session_state.messages.append({"role": "user", "content": query})

    # Xử lý qua RAG pipeline
    answer, sources = process_query(query, qa_chain_all, qa_chain_diem_chuan, llm)

    # Lưu tin nhắn assistant
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
    })

    # --- LƯU LỊCH SỬ NGẦM (CẢ KHI CHƯA ĐĂNG NHẬP) ---
    user_key = get_user_key()
    if user_key not in st.session_state.history_data:
        st.session_state.history_data[user_key] = {}
    user_history = st.session_state.history_data[user_key]

    if st.session_state.current_session_id not in user_history:
        title_text = query[:20] + "..." if len(query) > 20 else query
        title = f"Chat: {title_text}"
        user_history[st.session_state.current_session_id] = {
            "title": title,
            "messages": st.session_state.messages,
        }
    else:
        user_history[st.session_state.current_session_id]["messages"] = (
            st.session_state.messages
        )

    save_history(st.session_state.history_data)

    # Rerun để gửi kết quả xuống frontend
    st.rerun()
