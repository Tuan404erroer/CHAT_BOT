import streamlit as st
import streamlit.components.v1 as components
import os
import json
import uuid
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever

# --- BỘ GỘP HYBRID RETRIEVER TỰ ĐỊNH NGHĨA (SỬA LỖI MODULE RETRIEVERS) ---
from typing import Any, List
from langchain_core.retrievers import BaseRetriever

class CustomHybridRetriever(BaseRetriever):
    vector_retriever: Any
    bm25_retriever: Any
    
    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        # Gọi song song cả bộ tìm kiếm Vector và Từ khóa chính xác
        docs_vector = self.vector_retriever.invoke(query)
        docs_bm25 = self.bm25_retriever.invoke(query)
        
        # Gộp chung kết quả và loại bỏ các tài liệu trùng nội dung
        seen = set()
        combined = []
        for doc in docs_bm25 + docs_vector:
            if doc.page_content not in seen:
                combined.append(doc)
                seen.add(doc.page_content)
        return combined

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Tư Vấn Tuyển Sinh AI", page_icon="🎓", layout="wide")

# --- ĐIỀU HƯỚNG BẰNG QUERY PARAMS ---
page = st.query_params.get("page", "chat")

if page == "admin":
    # ==============================================================================
    # TRANG ADMIN
    # ==============================================================================
    import smtplib
    import random
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from datetime import datetime
    
    # Khởi tạo trạng thái Admin
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
    if "admin_otp" not in st.session_state:
        st.session_state.admin_otp = ""
    if "admin_email" not in st.session_state:
        st.session_state.admin_email = ""
    if "admin_otp_sent" not in st.session_state:
        st.session_state.admin_otp_sent = False

    def send_otp_email(receiver_email, otp):
        smtp_email = st.secrets.get("SMTP_EMAIL", "")
        smtp_password = st.secrets.get("SMTP_PASSWORD", "")
        
        if not smtp_email or not smtp_password:
            st.warning(f"⚠️ Chưa cấu hình SMTP_EMAIL và SMTP_PASSWORD trong secrets. OTP của bạn là: {otp}")
            return True
            
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = receiver_email
            msg['Subject'] = "🔐 Mã OTP Đăng Nhập Hệ Thống Admin"
            
            body = f"""
            Chào Admin,
            
            Bạn đang thực hiện đăng nhập vào hệ thống quản trị Tuyển Sinh AI.
            Mã OTP xác thực của bạn là:
            
            👉 {otp} 👈
            
            Mã này có hiệu lực trong vòng 5 phút. Vui lòng không chia sẻ mã này cho bất kỳ ai.
            
            Trân trọng,
            Hệ thống Tuyển sinh AI.
            """
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(smtp_email, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_email, receiver_email, text)
            server.quit()
            return True
        except Exception as e:
            st.error(f"❌ Không thể gửi email OTP: {e}")
            return False

    # Giao diện Đăng nhập
    if not st.session_state.admin_logged_in:
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
                margin-bottom: -25px; /* pull form up */
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
            /* Customizing Streamlit inputs */
            div[data-testid="stTextInput"] input {
                background-color: rgba(255, 255, 255, 0.05) !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
                color: #ffffff !important;
                border-radius: 12px !important;
                padding: 14px !important;
                font-size: 15px !important;
                transition: all 0.3s ease !important;
            }
            div[data-testid="stTextInput"] input:focus {
                border-color: #8b5cf6 !important;
                background-color: rgba(255, 255, 255, 0.1) !important;
                box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.2) !important;
            }
            /* Form Submit Button */
            div[data-testid="stForm"] button {
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
            div[data-testid="stForm"] button:hover {
                transform: translateY(-2px) scale(1.02) !important;
                box-shadow: 0 12px 25px rgba(99, 102, 241, 0.6) !important;
            }
            div[data-testid="stForm"] button:active {
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
                    admin_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
                    if password == admin_password:
                        if email:
                            # Sinh OTP ngẫu nhiên 6 chữ số
                            otp = str(random.randint(100000, 999999))
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
            st.markdown(f"""
            <div class="login-container">
                <div class="login-title">🔐 Xác thực OTP</div>
                <div class="login-subtitle">Mã OTP đã được gửi đến hộp thư<br><b style="color:#38bdf8">{st.session_state.admin_email}</b></div>
            </div>
            """, unsafe_allow_html=True)
            
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
                
        st.stop()

    # Nhúng CSS ẩn header của admin
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

    parent_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_admin_dir = os.path.join(parent_dir, "frontend_admin")
    _admin_component = components.declare_component("admin_ui", path=frontend_admin_dir)
    
    HISTORY_FILE = "chat_history.json"
    
    def load_history():
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    
    def compute_stats(history_data):
        total_sessions = 0
        total_questions = 0
        total_rated = 0
        total_up = 0
        total_down = 0
        
        users_list = []
        all_sessions = []
        rated_messages = []
        
        for user_key, sessions in history_data.items():
            user_session_count = len(sessions)
            user_question_count = 0
            
            for session_id, session_info in sessions.items():
                total_sessions += 1
                messages = session_info.get("messages", [])
                title = session_info.get("title", "Không có tiêu đề")
                
                session_questions = 0
                session_up = 0
                session_down = 0
                session_no_rate = 0
                
                for i, msg in enumerate(messages):
                    if msg.get("role") == "user":
                        total_questions += 1
                        session_questions += 1
                        user_question_count += 1
                    
                    if msg.get("role") == "assistant":
                        rating = msg.get("rating")
                        if rating:
                            total_rated += 1
                            if rating == "up":
                                total_up += 1
                                session_up += 1
                            elif rating == "down":
                                total_down += 1
                                session_down += 1
                            
                            question_content = ""
                            if i > 0 and messages[i-1].get("role") == "user":
                                question_content = messages[i-1].get("content", "")
                            
                            rated_messages.append({
                                "user": user_key,
                                "session_title": title,
                                "question": question_content,
                                "answer": msg.get("content", "")[:200] + "..." if len(msg.get("content", "")) > 200 else msg.get("content", ""),
                                "rating": rating
                            })
                        else:
                            session_no_rate += 1
                
                all_sessions.append({
                    "user": user_key,
                    "session_id": session_id,
                    "title": title,
                    "message_count": len(messages),
                    "question_count": session_questions,
                    "thumbs_up": session_up,
                    "thumbs_down": session_down,
                    "no_rating": session_no_rate,
                    "messages": messages
                })
            
            users_list.append({
                "user_key": user_key,
                "session_count": user_session_count,
                "question_count": user_question_count
            })
        
        satisfaction_rate = round((total_up / total_rated * 100), 1) if total_rated > 0 else 0
        
        KNOWLEDGE_CONFIG_FILE = "knowledge_config.json"
        knowledge_config = {}
        if os.path.exists(KNOWLEDGE_CONFIG_FILE):
            try:
                with open(KNOWLEDGE_CONFIG_FILE, "r", encoding="utf-8") as f:
                    knowledge_config = json.load(f)
            except Exception:
                pass

        knowledge_files = []
        for entry in os.listdir("."):
            if entry.lower().endswith((".json", ".txt")) and os.path.isfile(entry) and entry not in ["chat_history.json", "consult_registrations.json", "knowledge_config.json"]:
                file_size = os.path.getsize(entry)
                
                # Default config if not exists
                if entry not in knowledge_config:
                    knowledge_config[entry] = {
                        "enabled": True,
                        "description": "File dữ liệu mới",
                        "uploaded_at": datetime.now().isoformat()
                    }
                    
                cfg = knowledge_config[entry]
                
                knowledge_files.append({
                    "name": entry,
                    "size_kb": round(file_size / 1024, 1),
                    "enabled": cfg.get("enabled", True),
                    "description": cfg.get("description", ""),
                    "uploaded_at": cfg.get("uploaded_at", datetime.now().isoformat())
                })
                
        # Save updated config back to ensure sync
        try:
            with open(KNOWLEDGE_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(knowledge_config, f, ensure_ascii=False, indent=4)
        except Exception:
            pass
        
        return {
            "total_sessions": total_sessions,
            "total_questions": total_questions,
            "total_rated": total_rated,
            "total_up": total_up,
            "total_down": total_down,
            "satisfaction_rate": satisfaction_rate,
            "total_users": len(users_list),
            "users": users_list,
            "sessions": all_sessions,
            "rated_messages": rated_messages,
            "knowledge_files": knowledge_files,
            "greeting_hour": datetime.now().hour
        }

    history_data = load_history()
    stats = compute_stats(history_data)
    
    # Load consultation registrations
    CONSULT_FILE = "consult_registrations.json"
    consult_list = []
    if os.path.exists(CONSULT_FILE):
        try:
            with open(CONSULT_FILE, "r", encoding="utf-8") as f:
                consult_list = json.load(f)
        except Exception:
            consult_list = []
    
    stats["consult_registrations"] = consult_list

    if "admin_last_ts" not in st.session_state:
        st.session_state.admin_last_ts = 0

    admin_action = _admin_component(
        stats=json.dumps(stats, ensure_ascii=False),
        key="admin",
        default=None
    )
    
    # Handle admin actions from frontend
    if admin_action is not None:
        ts = admin_action.get("timestamp", 0)
        if ts != st.session_state.admin_last_ts:
            st.session_state.admin_last_ts = ts
            action = admin_action.get("action", "")
            
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
                    with open(CONSULT_FILE, "w", encoding="utf-8") as f:
                        json.dump(consult_list, f, ensure_ascii=False, indent=4)
                    st.rerun()
        
            elif action == "update_consult_status":
                idx = admin_action.get("index")
                status = admin_action.get("status", "")
                if idx is not None and 0 <= idx < len(consult_list):
                    consult_list[idx]["status"] = status
                    with open(CONSULT_FILE, "w", encoding="utf-8") as f:
                        json.dump(consult_list, f, ensure_ascii=False, indent=4)
                    st.rerun()
        
            elif action == "update_consult_note":
                idx = admin_action.get("index")
                note = admin_action.get("note", "")
                if idx is not None and 0 <= idx < len(consult_list):
                    consult_list[idx]["admin_note"] = note
                    with open(CONSULT_FILE, "w", encoding="utf-8") as f:
                        json.dump(consult_list, f, ensure_ascii=False, indent=4)
                    st.rerun()

            elif action == "update_knowledge_status":
                filename = admin_action.get("filename")
                enabled = admin_action.get("enabled")
            
                KNOWLEDGE_CONFIG_FILE = "knowledge_config.json"
                knowledge_config = {}
                if os.path.exists(KNOWLEDGE_CONFIG_FILE):
                    try:
                        with open(KNOWLEDGE_CONFIG_FILE, "r", encoding="utf-8") as f:
                            knowledge_config = json.load(f)
                    except Exception:
                        pass
                    
                if filename in knowledge_config:
                    knowledge_config[filename]["enabled"] = enabled
                    with open(KNOWLEDGE_CONFIG_FILE, "w", encoding="utf-8") as f:
                        json.dump(knowledge_config, f, ensure_ascii=False, indent=4)
                st.rerun()

            elif action == "delete_knowledge_file":
                filename = admin_action.get("filename")
                if filename and filename not in ["chat_history.json", "consult_registrations.json", "knowledge_config.json"]:
                    # Xóa file vật lý
                    if os.path.exists(filename):
                        os.remove(filename)
                
                    # Xóa khỏi config
                    KNOWLEDGE_CONFIG_FILE = "knowledge_config.json"
                    if os.path.exists(KNOWLEDGE_CONFIG_FILE):
                        try:
                            with open(KNOWLEDGE_CONFIG_FILE, "r", encoding="utf-8") as f:
                                knowledge_config = json.load(f)
                            if filename in knowledge_config:
                                del knowledge_config[filename]
                                with open(KNOWLEDGE_CONFIG_FILE, "w", encoding="utf-8") as f:
                                    json.dump(knowledge_config, f, ensure_ascii=False, indent=4)
                        except Exception:
                            pass
                st.rerun()

            elif action == "upload_knowledge_file":
                filename = admin_action.get("filename")
                content = admin_action.get("content")
            
                if filename and content and filename.lower().endswith((".json", ".txt")):
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(content)
                    
                    # Thêm vào config
                    KNOWLEDGE_CONFIG_FILE = "knowledge_config.json"
                    knowledge_config = {}
                    if os.path.exists(KNOWLEDGE_CONFIG_FILE):
                        try:
                            with open(KNOWLEDGE_CONFIG_FILE, "r", encoding="utf-8") as f:
                                knowledge_config = json.load(f)
                        except Exception:
                            pass
                
                    knowledge_config[filename] = {
                        "enabled": True,
                        "description": "File tải lên từ Admin",
                        "uploaded_at": datetime.now().isoformat()
                    }
                
                    with open(KNOWLEDGE_CONFIG_FILE, "w", encoding="utf-8") as f:
                        json.dump(knowledge_config, f, ensure_ascii=False, indent=4)
                    
                st.rerun()
    
    # Dừng chạy code bên dưới (phần chatbot)
    st.stop()

# ==============================================================================
# TRANG CHATBOT (MẶC ĐỊNH)
# ==============================================================================
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

# --- KHAI BÁO CUSTOM COMPONENT ---
parent_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(parent_dir, "frontend")
_chat_component = components.declare_component("chat_ui", path=frontend_dir)


# ==============================================================================
# [CẬP NHẬT 1] PROMPT PHÂN QUYỀN KIẾN THỨC (MỞ GIỚI HẠN LỊCH SỬ Ở ĐẦU FILE)
# ==============================================================================
PROMPT = PromptTemplate(
    template=(
        "Bạn là chuyên gia tư vấn tuyển sinh thân thiện của Trường Cao đẳng Kỹ thuật Cao Thắng (Cao Thắng).\n"
        "Mọi từ 'trường', 'nhà trường', 'trường mình' trong câu hỏi đều MẶC ĐỊNH hiểu là Trường Cao đẳng Kỹ thuật Cao Thắng.\n\n"
        "QUY TẮC PHÂN QUYỀN KIẾN THỨC TỐI THƯỢNG:\n"
        "1. THÔNG TIN TUYỂN SINH (Điểm chuẩn, ngành, học phí, quy chế): BẮT BUỘC dùng dữ liệu cung cấp. Không có thì nói chưa cập nhật, KHÔNG BỊA.\n"
        "2. THÔNG TIN LỊCH SỬ, VĨ NHÂN: Được phép dùng kiến thức nền để trả lời (VD: trường thành lập 1906, Bác Hồ và Bác Tôn từng học). NHƯNG PHẢI TRẢ LỜI CỰC KỲ NGẮN GỌN, ĐÚNG TRỌNG TÂM câu hỏi. TUYỆT ĐỐI KHÔNG viết văn hoa mỹ, sáo rỗng, không kể lể dài dòng.\n"
        "3. TƯƠNG TÁC: Nếu câu hỏi chưa rõ ràng, thêm 1 câu gợi mở ngắn gọn cuối bài.\n\n"
        "Thông tin tài liệu:\n{context}\n\n"
        "Câu hỏi của thí sinh: {question}\n"
        "Câu trả lời (Ngắn gọn, súc tích):"
    ),
    input_variables=["context", "question"],
)


# --- HÀM KHỞI TẠO HỆ THỐNG ---
@st.cache_resource
def get_global_rag_cache():
    return {"hash": None, "chains": None}

@st.cache_resource
def load_models():
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("Chưa cấu hình API Key trong Secrets!")

    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.3)
    return embeddings, llm

def setup_rag_system(config_hash=None):
    cache = get_global_rag_cache()
    if cache["hash"] == config_hash and cache["chains"] is not None:
        return cache["chains"]

    embeddings, llm = load_models()

    def collect_source_files():
        KNOWLEDGE_CONFIG_FILE = "knowledge_config.json"
        knowledge_config = {}
        if os.path.exists(KNOWLEDGE_CONFIG_FILE):
            try:
                with open(KNOWLEDGE_CONFIG_FILE, "r", encoding="utf-8") as f:
                    knowledge_config = json.load(f)
            except Exception:
                pass
                
        candidates = []
        for entry in os.listdir("."):
            if entry.lower().endswith((".json", ".txt")) and os.path.isfile(entry) and entry not in ["chat_history.json", "consult_registrations.json", "knowledge_config.json"]:
                # Kiểm tra trạng thái enabled
                cfg = knowledge_config.get(entry, {})
                if cfg.get("enabled", True):
                    candidates.append(entry)
        return sorted(set(candidates))

    def parse_multiple_json(text):
        decoder = json.JSONDecoder()
        index = 0
        results = []
        length = len(text)
        while index < length:
            while index < length and text[index].isspace():
                index += 1
            if index >= length:
                break
            try:
                value, next_index = decoder.raw_decode(text, index)
            except json.JSONDecodeError:
                break
            if isinstance(value, list):
                results.extend(value)
            else:
                results.append(value)
            index = next_index
        return results

    def load_json_items(path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw_data = json.load(handle)
        except json.JSONDecodeError:
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    raw_text = handle.read()
            except Exception as exc:
                st.warning(f"Không đọc được file {path}: {exc}")
                return []
            parsed = parse_multiple_json(raw_text)
            if parsed:
                return parsed
            if raw_text.strip():
                return [raw_text]
            return []
        except Exception as exc:
            st.warning(f"Không đọc được file {path}: {exc}")
            return []
        if isinstance(raw_data, list):
            return raw_data
        return [raw_data]

    def build_documents(source_files):
        docs = []
        
        def flatten_json_to_text(data):
            if isinstance(data, dict):
                parts = []
                for k, v in data.items():
                    clean_key = str(k).replace("_", " ").capitalize()
                    parts.append(f"{clean_key}: {flatten_json_to_text(v)}")
                return "\n".join(parts)
            elif isinstance(data, list):
                return "\n".join([f"- {flatten_json_to_text(item)}" for item in data])
            else:
                return str(data).strip()

        for path in source_files:
            filename = os.path.basename(path)
            
            if filename == "diem-chuan.json":
                for item in load_json_items(path):
                    if isinstance(item, dict) and "nganh" in item and "diem_chuan" in item:
                        diem_chuan_lines = []
                        for year, values in item["diem_chuan"].items():
                            diem_chuan_lines.append(f"  {year}: xet_hoc_ba={values.get('xet_hoc_ba')}, thi_thpt_quoc_gia={values.get('thi_thpt_quoc_gia')}, thi_danh_gia_nang_luc={values.get('thi_danh_gia_nang_luc')}")
                        content = f"Nganh: {item['nganh']}\nDiem chuan:\n" + "\n".join(diem_chuan_lines)
                        metadata = {
                            "nganh": item["nganh"],
                            "source_file": filename
                        }
                        docs.append(Document(page_content=content, metadata=metadata))
                continue
            
            for item in load_json_items(path):
                content = flatten_json_to_text(item)
                metadata = {"source_file": filename}
                if isinstance(item, dict):
                    if "id" in item: metadata["id"] = item["id"]
                    if "nganh" in item: metadata["nganh"] = item.get("nganh", "")
                    if "ma_nganh" in item: metadata["ma_nganh"] = item.get("ma_nganh", "")
                    if "ten_nganh" in item: metadata["ten_nganh"] = item.get("ten_nganh", "")
                
                docs.append(Document(page_content=content, metadata=metadata))
                
        return docs

    source_files = collect_source_files()
    if not source_files:
        cache["chains"] = None
        cache["hash"] = config_hash
        return None

    docs = build_documents(source_files)
    if not docs:
        cache["chains"] = None
        cache["hash"] = config_hash
        return None
    
    # 1. VECTOR SEARCH (Tìm theo ngữ nghĩa)
    vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
    chroma_retriever_all = vectorstore.as_retriever(search_kwargs={"k": 7})
    retriever_diem_chuan = vectorstore.as_retriever(
        search_kwargs={"k": 10, "filter": {"source_file": "diem-chuan.json"}}
    )
    
    # 2. BM25 SEARCH (Tìm theo từ khóa chính xác)
    bm25_retriever_all = BM25Retriever.from_documents(docs)
    bm25_retriever_all.k = 7
    
    # 3. KẾT HỢP SONG KIẾM HỢP BÍCH
    ensemble_retriever_all = CustomHybridRetriever(
        vector_retriever=chroma_retriever_all,
        bm25_retriever=bm25_retriever_all
    )

    qa_chain_all = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=ensemble_retriever_all,  
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT},
    )
    
    qa_chain_diem_chuan = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever_diem_chuan, 
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT},
    )
    cache["chains"] = (qa_chain_all, qa_chain_diem_chuan, llm)
    cache["hash"] = config_hash
    return cache["chains"]


# --- HÀM XỬ LÝ CÂU HỎI QUA RAG PIPELINE ---
def process_query(prompt, qa_chain_all, qa_chain_diem_chuan, llm):
    """Xử lý câu hỏi người dùng qua pipeline RAG đầy đủ:
    1. Bóc tách câu hỏi phức tạp thành các ý đơn lẻ (Mặc định Cao Thắng)
    2. Truy vấn từng ý qua Hybrid Search
    3. Tổng hợp kết quả thành câu trả lời hoàn chỉnh
    """
    # ==============================================================================
    # [CẬP NHẬT 2] BỘ DỊCH CÂU HỎI TRONG HÀM - ÉP MẶC ĐỊNH CAO THẮNG + GIỮ Ý LỊCH SỬ
    # ==============================================================================
    rewrite_prompt = (
        "Bạn là một hệ thống phân tách ngôn ngữ. Hệ thống này được thiết kế ĐỘC QUYỀN cho 'Trường Cao đẳng Kỹ thuật Cao Thắng'.\n"
        "Nhiệm vụ của bạn là tách câu hỏi phức tạp của người dùng thành một danh sách (array) các câu hỏi đơn lẻ để hệ thống RAG tìm kiếm.\n"
        "QUY TẮC TỐI THƯỢNG:\n"
        "1. MẶC ĐỊNH NGỮ CẢNH: Bất cứ khi nào người dùng dùng các từ như 'trường', 'nhà trường', 'trường mình', 'trường đó', 'ở đây', bạn BẮT BUỘC phải thay thế cụm từ đó bằng 'Trường Cao đẳng Kỹ thuật Cao Thắng' trong câu hỏi đầu ra.\n"
        "2. GIỮ NGUYÊN Ý NGHĨA: Tuyệt đối không được lược bỏ hoặc bỏ qua các câu hỏi mang tính chất lịch sử, vĩ nhân hoặc danh nhân.\n"
        "3. BẮT BUỘC trả về ĐÚNG định dạng JSON mảng (bắt đầu bằng [ và kết thúc bằng ]).\n"
        "4. TUYỆT ĐỐI KHÔNG thêm bất kỳ văn bản giải thích nào khác ngoài JSON.\n\n"
        "VÍ DỤ:\n"
        "- Input: Điểm chuẩn của trường là bao nhiêu? Có những ai nổi tiếng từng học ở đây?\n"
        '- Output: ["Điểm chuẩn của trường Cao đẳng Kỹ thuật Cao Thắng là bao nhiêu?", "Có những người nổi tiếng nào từng học tại trường Cao đẳng Kỹ thuật Cao Thắng?"]\n\n'
        f"- Input: {prompt}\n"
        "- Output:"
    )
    
    try:
        optimized_res = llm.invoke(rewrite_prompt).content.strip()
        if optimized_res.startswith("```json"):
            optimized_res = optimized_res[7:]
        if optimized_res.startswith("```"):
            optimized_res = optimized_res[3:]
        if optimized_res.endswith("```"):
            optimized_res = optimized_res[:-3]
            
        sub_queries = json.loads(optimized_res.strip())
        if not isinstance(sub_queries, list) or len(sub_queries) == 0:
            sub_queries = [prompt]
    except Exception:
        sub_queries = [prompt]

    # Bước 2: Truy vấn từng ý
    sub_answers = []
    all_source_documents = []
    
    for sub_query in sub_queries:
        sub_query_lower = sub_query.lower()
        try:
            if "điểm chuẩn" in sub_query_lower or "diem chuan" in sub_query_lower:
                res = qa_chain_diem_chuan.invoke({"query": sub_query})
            else:
                res = qa_chain_all.invoke({"query": sub_query})
                
            sub_answers.append(res['result'])
            
            if "source_documents" in res:
                all_source_documents.extend(res["source_documents"])
        except Exception as e:
            sub_answers.append(f"(Lỗi khi quét ý '{sub_query}': {e})")

    # Bước 3: Tổng hợp kết quả
    
    sub_answers_text = "\n\n".join(sub_answers)
    synthesis_prompt = (
        "Bạn là một chuyên gia tư vấn tuyển sinh chuyên nghiệp của Trường Cao đẳng Kỹ thuật Cao Thắng.\n"
        "Nhiệm vụ: Hãy gộp các thông tin câu trả lời đơn lẻ dưới đây thành một văn bản tư vấn hoàn chỉnh.\n"
        "QUY TẮC CỐT LÕI (NGHIÊM NGẶT):\n"
        "1. GIỮ NGUYÊN CHI TIẾT: Có bao nhiêu thông tin, con số, phương thức xét tuyển ở dữ liệu gốc phải giữ lại trọn vẹn.\n"
        "2. NGẮN GỌN & TRỰC DIỆN: Đi thẳng vào vấn đề. TUYỆT ĐỐI KHÔNG thêm thắt các câu chào hỏi dài dòng, văn mẫu PR, sáo rỗng hay tự ca ngợi trường quá mức.\n"
        "3. CẤU TRÚC: Trình bày dễ đọc (gạch đầu dòng, số thứ tự).\n\n"
        f"Dữ liệu gốc BẮT BUỘC phải giữ nguyên chi tiết:\n{sub_answers_text}\n\n"
        "Câu trả lời tư vấn (Chuyên nghiệp, súc tích, không lan man):"
    )
    
    try:
        answer = llm.invoke(synthesis_prompt).content.strip()
    except Exception:
        answer = "\n\n".join(sub_answers)

    # Bước 4: Chuẩn bị nguồn tài liệu
    sources = []
    seen_docs = set()
    for doc in all_source_documents:
        if doc.page_content not in seen_docs:
            sources.append(doc.page_content[:200] + "...")
            seen_docs.add(doc.page_content)

    return answer, sources


# --- KHỞI TẠO VÀ CHẠY ỨNG DỤNG ---
def get_rag_hash():
    KNOWLEDGE_CONFIG_FILE = "knowledge_config.json"
    hash_str = ""
    if os.path.exists(KNOWLEDGE_CONFIG_FILE):
        try:
            with open(KNOWLEDGE_CONFIG_FILE, "r", encoding="utf-8") as f:
                hash_str += f.read()
        except: pass
    
    # Also hash file modified times
    for entry in os.listdir("."):
        if entry.lower().endswith((".json", ".txt")):
            hash_str += f"{entry}_{os.path.getmtime(entry)}"
            
    import hashlib
    return hashlib.md5(hash_str.encode()).hexdigest()

# LAZY LOADING: Chỉ khởi tạo RAG system khi cần thiết (không load mỗi lần rerun)
if "rag_initialized" not in st.session_state:
    st.session_state.rag_initialized = False
    st.session_state.qa_chain_all = None
    st.session_state.qa_chain_diem_chuan = None
    st.session_state.llm = None

def ensure_rag_system():
    """Đảm bảo RAG system đã được khởi tạo (chỉ load 1 lần)"""
    if not st.session_state.rag_initialized:
        with st.spinner("🔄 Đang khởi tạo hệ thống AI..."):
            rag_hash = get_rag_hash()
            chips = setup_rag_system(rag_hash)
            if chips is None:
                st.error("❌ Không tìm thấy file dữ liệu hợp lệ. Vui lòng kiểm tra lại!")
                st.stop()
            st.session_state.qa_chain_all, st.session_state.qa_chain_diem_chuan, st.session_state.llm = chips
            st.session_state.rag_initialized = True
    return st.session_state.qa_chain_all, st.session_state.qa_chain_diem_chuan, st.session_state.llm

HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- SESSION STATE ---
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

user_key = f"{st.session_state.mssv}_{st.session_state.dob}" if st.session_state.logged_in else "_guest_"
if st.session_state.logged_in and user_key not in st.session_state.history_data:
    st.session_state.history_data[user_key] = {}

# Khởi tạo session_id nếu rỗng
if st.session_state.current_session_id is None:
    st.session_state.current_session_id = str(uuid.uuid4())

user_history = st.session_state.history_data.get(user_key, {}) if st.session_state.logged_in else {}

# --- RENDER COMPONENT & XỬ LÝ ---
user_input = _chat_component(
    messages=json.dumps(st.session_state.messages, ensure_ascii=False),
    logged_in=st.session_state.logged_in,
    mssv=st.session_state.mssv,
    history=json.dumps(user_history, ensure_ascii=False),
    current_session_id=st.session_state.current_session_id,
    key="chat",
    default=None
)

# Khi nhận được tin nhắn mới từ frontend
if user_input is not None:
    ts = user_input.get("timestamp", 0)
    
    if ts != st.session_state.last_ts:
        st.session_state.last_ts = ts
        
        action = user_input.get("action", "chat")
        
        if action == "login":
            st.session_state.logged_in = True
            st.session_state.mssv = user_input.get("mssv", "")
            st.session_state.dob = user_input.get("dob", "")
            st.session_state.messages = []
            st.session_state.current_session_id = str(uuid.uuid4())
            st.rerun()
            
        elif action == "logout":
            st.session_state.logged_in = False
            st.session_state.mssv = ""
            st.session_state.dob = ""
            st.session_state.messages = []
            st.rerun()
            
        elif action == "new_session":
            st.session_state.current_session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
            
        elif action == "load_session":
            st.session_state.current_session_id = user_input.get("session_id")
            session_info = st.session_state.history_data.get(user_key, {}).get(st.session_state.current_session_id, {})
            st.session_state.messages = session_info.get("messages", [])
            st.rerun()
            
        elif action == "rate":
            msg_index = user_input.get("message_index")
            rating = user_input.get("rating")
            if msg_index is not None and msg_index < len(st.session_state.messages):
                st.session_state.messages[msg_index]["rating"] = rating
                
                user_history = st.session_state.history_data.get(user_key, {})
                if st.session_state.current_session_id in user_history:
                    user_history[st.session_state.current_session_id]["messages"] = st.session_state.messages
                    save_history(st.session_state.history_data)
            # KHÔNG RERUN - chỉ lưu vào file, giao diện frontend tự cập nhật
            
        elif action == "consult_register":
            # Save consultation registration to a separate JSON file
            consult_data = {
                "name": user_input.get("name", ""),
                "phone": user_input.get("phone", ""),
                "email": user_input.get("email", ""),
                "major": user_input.get("major", ""),
                "message": user_input.get("message", ""),
                "timestamp": ts,
                "user_key": user_key if st.session_state.logged_in else "guest"
            }
            
            CONSULT_FILE = "consult_registrations.json"
            consult_list = []
            if os.path.exists(CONSULT_FILE):
                try:
                    with open(CONSULT_FILE, "r", encoding="utf-8") as f:
                        consult_list = json.load(f)
                except Exception:
                    consult_list = []
            
            consult_list.append(consult_data)
            with open(CONSULT_FILE, "w", encoding="utf-8") as f:
                json.dump(consult_list, f, ensure_ascii=False, indent=4)
            
            st.rerun()
            
        elif action == "chat":
            query = user_input.get("message", "")
            
            # Lưu tin nhắn user
            st.session_state.messages.append({"role": "user", "content": query})
            
            # Xử lý qua RAG pipeline
            answer, sources = process_query(query, qa_chain_all, qa_chain_diem_chuan, llm)
            
            # Lưu tin nhắn assistant
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })
            
            # --- LƯU LỊCH SỬ NGẦM (CHỈ KHI ĐÃ ĐĂNG NHẬP) ---
            if st.session_state.logged_in:
                user_key = f"{st.session_state.mssv}_{st.session_state.dob}"
                if user_key not in st.session_state.history_data:
                    st.session_state.history_data[user_key] = {}
                user_history = st.session_state.history_data[user_key]
                if st.session_state.current_session_id not in user_history:
                    # Lấy 20 ký tự đầu làm tiêu đề
                    title_text = query[:20] + "..." if len(query) > 20 else query
                    title = f"Chat: {title_text}"
                    user_history[st.session_state.current_session_id] = {
                        "title": title,
                        "messages": st.session_state.messages
                    }
                else:
                    user_history[st.session_state.current_session_id]["messages"] = st.session_state.messages
                    
                save_history(st.session_state.history_data)
            
            # Rerun để gửi kết quả xuống frontend
            st.rerun()