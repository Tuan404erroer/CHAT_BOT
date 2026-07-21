"""
Service quản lý tài khoản người dùng.
Lưu/đọc danh sách user từ file users.json để duy trì đăng nhập qua F5.
"""
from datetime import datetime
import hashlib

from models.constants import USERS_FILE
from utils.file_helpers import safe_read_json, safe_write_json


def _hash_password(password: str) -> str:
    """Băm mật khẩu sử dụng SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_user(mssv, name, email, password):
    """Đăng ký tài khoản mới.
    
    Returns:
        tuple: (success (bool), message (str))
    """
    users = safe_read_json(USERS_FILE, default={})
    user_key = mssv.strip()
    
    if user_key in users:
        return False, "Tài khoản (SĐT/MSSV) này đã tồn tại!"
        
    # Check if email is already used
    for u in users.values():
        if u.get("email") == email.strip():
            return False, "Email này đã được sử dụng!"
            
    users[user_key] = {
        "mssv": user_key,
        "name": name.strip(),
        "email": email.strip(),
        "password_hash": _hash_password(password),
        "created_at": datetime.now().isoformat(),
        "last_login": datetime.now().isoformat(),
    }
    
    safe_write_json(USERS_FILE, users)
    return True, "Đăng ký thành công!"


def verify_login(mssv, password):
    """Kiểm tra thông tin đăng nhập.
    
    Returns:
        tuple: (success (bool), message (str))
    """
    users = safe_read_json(USERS_FILE, default={})
    user_key = mssv.strip()
    
    if user_key not in users:
        return False, "Tài khoản không tồn tại!"
        
    user_data = users[user_key]
    
    # Check password
    if user_data.get("password_hash") != _hash_password(password):
        # Backward compatibility for old users who didn't have password_hash
        if user_data.get("dob") and not user_data.get("password_hash"):
            return False, "Tài khoản cũ cần được cập nhật. Vui lòng đăng ký lại."
        return False, "Sai mật khẩu!"
        
    # Update last login
    user_data["last_login"] = datetime.now().isoformat()
    safe_write_json(USERS_FILE, users)
    
    return True, "Đăng nhập thành công!"


def get_user_by_email(email):
    """Tìm user bằng email để cấp lại mật khẩu.
    
    Returns:
        str|None: user_key (mssv) nếu tìm thấy, ngược lại None
    """
    users = safe_read_json(USERS_FILE, default={})
    email = email.strip()
    
    for key, data in users.items():
        if data.get("email") == email:
            return key
            
    return None


def update_password(mssv, new_password):
    """Cập nhật mật khẩu mới cho user."""
    users = safe_read_json(USERS_FILE, default={})
    user_key = mssv.strip()
    
    if user_key in users:
        users[user_key]["password_hash"] = _hash_password(new_password)
        safe_write_json(USERS_FILE, users)
        return True
    return False


def get_all_users():
    """Lấy danh sách tất cả user đã đăng ký."""
    return safe_read_json(USERS_FILE, default={})
