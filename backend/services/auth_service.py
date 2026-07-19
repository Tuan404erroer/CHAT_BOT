"""
Service xác thực Admin.
Quản lý tài khoản admin, gửi OTP qua email.
"""
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import streamlit as st

# Danh sách tài khoản admin (email -> mật khẩu riêng)
ADMIN_ACCOUNTS = {
    "0306231010@caothang.edu.vn": "365478",
}


def validate_admin_login(email, password):
    """Kiểm tra thông tin đăng nhập admin.
    
    Returns:
        bool: True nếu email + password hợp lệ
    """
    # Ưu tiên tài khoản riêng
    if email in ADMIN_ACCOUNTS:
        return password == ADMIN_ACCOUNTS[email]

    # Fallback mật khẩu chung từ secrets
    admin_password = st.secrets.get("ADMIN_PASSWORD", "admin123")
    admin_account = st.secrets.get("SMTP_EMAIL", "admin123")
    return password == admin_password and email == admin_account


def generate_otp():
    """Sinh mã OTP ngẫu nhiên 6 chữ số."""
    return str(random.randint(100000, 999999))


def send_otp_email(receiver_email, otp):
    """Gửi mã OTP qua email.
    
    Nếu SMTP chưa cấu hình, hiển thị OTP trực tiếp trên giao diện.
    
    Returns:
        bool: True nếu gửi thành công (hoặc hiển thị trên UI)
    """
    smtp_email = st.secrets.get("SMTP_EMAIL", "")
    smtp_password = st.secrets.get("SMTP_PASSWORD", "")


    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_email
        msg["To"] = receiver_email
        msg["Subject"] = "🔐 Mã OTP Đăng Nhập Hệ Thống Admin"

        body = f"""
        Chào Admin,
        
        Bạn đang thực hiện đăng nhập vào hệ thống quản trị Tuyển Sinh AI.
        Mã OTP xác thực của bạn là:
        
        👉 {otp} 👈
        
        Mã này có hiệu lực trong vòng 5 phút. Vui lòng không chia sẻ mã này cho bất kỳ ai.
        
        Trân trọng,
        Hệ thống Tuyển sinh AI.
        """
        msg.attach(MIMEText(body, "plain", "utf-8"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_email, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_email, receiver_email, text)
        server.quit()
        return True
    except Exception as e:
        st.error(f"❌ Không thể gửi email OTP: {e}")
        return False


def is_smtp_configured():
    """Kiểm tra SMTP đã được cấu hình chưa."""
    return bool(st.secrets.get("SMTP_EMAIL", "")) and bool(
        st.secrets.get("SMTP_PASSWORD", "")
    )
