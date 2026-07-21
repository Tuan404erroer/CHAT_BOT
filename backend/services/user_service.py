"""
Service quản lý tài khoản người dùng.
Lưu/đọc danh sách user từ file users.json để duy trì đăng nhập qua F5.
"""
from datetime import datetime

from models.constants import USERS_FILE
from utils.file_helpers import safe_read_json, safe_write_json


def save_user(mssv, dob):
    """Lưu tài khoản người dùng vào file users.json.
    
    Nếu user đã tồn tại thì cập nhật last_login.
    Nếu chưa thì tạo mới.
    """
    users = safe_read_json(USERS_FILE, default={})
    user_key = f"{mssv}_{dob}"

    if user_key in users:
        users[user_key]["last_login"] = datetime.now().isoformat()
    else:
        users[user_key] = {
            "mssv": mssv,
            "dob": dob,
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat(),
        }

    safe_write_json(USERS_FILE, users)


def user_exists(mssv, dob):
    """Kiểm tra tài khoản người dùng có tồn tại trong file không.
    
    Returns:
        bool: True nếu user đã từng đăng nhập
    """
    users = safe_read_json(USERS_FILE, default={})
    user_key = f"{mssv}_{dob}"
    return user_key in users


def get_all_users():
    """Lấy danh sách tất cả user đã đăng ký."""
    return safe_read_json(USERS_FILE, default={})
