"""
Service quản lý tài khoản người dùng (Sử dụng Google SSO).
Lưu/đọc danh sách user từ file users.json.
"""
from datetime import datetime

from models.constants import USERS_FILE
from utils.file_helpers import safe_read_json, safe_write_json

def google_login_or_register(email, name, picture):
    """
    Xử lý khi người dùng đăng nhập bằng Google.
    Nếu email chưa tồn tại -> Đăng ký mới.
    Nếu đã tồn tại -> Cập nhật last_login.
    """
    users = safe_read_json(USERS_FILE, default={})
    user_key = email.strip()
    
    if user_key not in users:
        # User mới
        users[user_key] = {
            "email": user_key,
            "name": name.strip() if name else "Sinh viên",
            "picture": picture,
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
        }
    else:
        # Cập nhật thông tin mới nhất từ Google
        users[user_key]["name"] = name.strip() if name else users[user_key].get("name", "Sinh viên")
        users[user_key]["picture"] = picture
        users[user_key]["last_login"] = datetime.now().isoformat()
        
    safe_write_json(USERS_FILE, users)
    return users[user_key]
