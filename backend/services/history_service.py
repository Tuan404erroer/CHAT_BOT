"""
Service quản lý lịch sử chat.
Load/save chat_history.json và tính toán thống kê cho admin dashboard.
"""
import os
from datetime import datetime

from models.constants import (
    HISTORY_FILE, KNOWLEDGE_DIR, KNOWLEDGE_CONFIG_FILE, EXCLUDED_FILES
)
from utils.file_helpers import safe_read_json, safe_write_json
from services.prompt_service import get_system_prompts


def load_history():
    """Đọc toàn bộ lịch sử chat từ file."""
    return safe_read_json(HISTORY_FILE, default={})


def save_history(data):
    """Lưu toàn bộ lịch sử chat ra file."""
    safe_write_json(HISTORY_FILE, data)


def compute_stats(history_data):
    """Tính toán thống kê tổng hợp từ lịch sử chat cho admin dashboard.
    
    Returns:
        dict chứa: total_sessions, total_questions, satisfaction_rate,
        users, sessions, rated_messages, knowledge_files, system_prompts, ...
    """
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
                        if i > 0 and messages[i - 1].get("role") == "user":
                            question_content = messages[i - 1].get("content", "")

                        rated_messages.append({
                            "user": user_key,
                            "session_title": title,
                            "question": question_content,
                            "answer": (
                                msg.get("content", "")[:200] + "..."
                                if len(msg.get("content", "")) > 200
                                else msg.get("content", "")
                            ),
                            "rating": rating,
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
                "messages": messages,
                "last_updated": session_info.get("last_updated", 0),
            })

        users_list.append({
            "user_key": user_key,
            "session_count": user_session_count,
            "question_count": user_question_count,
        })

    satisfaction_rate = (
        round((total_up / total_rated * 100), 1) if total_rated > 0 else 0
    )

    # --- Quét file tri thức trong thư mục knowledge ---
    knowledge_config = safe_read_json(KNOWLEDGE_CONFIG_FILE, default={})
    knowledge_files = []

    if KNOWLEDGE_DIR.exists():
        for entry in os.listdir(KNOWLEDGE_DIR):
            full_path = KNOWLEDGE_DIR / entry
            if (
                entry.lower().endswith((".json", ".txt"))
                and full_path.is_file()
                and entry not in EXCLUDED_FILES
            ):
                file_size = os.path.getsize(full_path)

                # Default config nếu file chưa có trong config
                if entry not in knowledge_config:
                    knowledge_config[entry] = {
                        "enabled": True,
                        "description": "File dữ liệu mới",
                        "uploaded_at": datetime.now().isoformat(),
                    }

                cfg = knowledge_config[entry]
                knowledge_files.append({
                    "name": entry,
                    "size_kb": round(file_size / 1024, 1),
                    "enabled": cfg.get("enabled", True),
                    "description": cfg.get("description", ""),
                    "uploaded_at": cfg.get("uploaded_at", datetime.now().isoformat()),
                })

    # Lưu lại config đã cập nhật
    safe_write_json(KNOWLEDGE_CONFIG_FILE, knowledge_config)

    # Sắp xếp các phiên chat từ cũ đến mới để frontend có thể hiển thị chính xác (mới nhất nổi lên đầu)
    all_sessions.sort(key=lambda x: x.get("last_updated", 0))

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
        "system_prompts": get_system_prompts(),
        "greeting_hour": datetime.now().hour,
    }
