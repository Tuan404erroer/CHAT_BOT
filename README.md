
## 📖 Project Overview (Tổng quan dự án)

Đồ án này tập trung vào việc xây dựng một trợ lý ảo AI thông minh, giúp giải đáp tự động các thắc mắc của thí sinh về thông tin tuyển sinh (điểm chuẩn, phương thức xét tuyển, học phí, v.v.). Hệ thống sử dụng mô hình ngôn ngữ lớn (LLM) kết hợp với kỹ thuật Retrieval-Augmented Generation (RAG) để đảm bảo câu trả lời chính xác dựa trên dữ liệu của nhà trường.

- **Frontend:** Vanilla HTML/CSS/JS (Được thiết kế dạng Component độc lập, giao diện hiện đại)
- **Backend:** Python (Streamlit framework làm cầu nối Web Server)
- **AI Engine:** Google Gemini (Gemini 3.1 Flash) thông qua Google AI Studio
- **Vector Database:** ChromaDB (Áp dụng Hybrid RAG Search)
- **Architecture:** Client-Server thông qua Streamlit Components

---

## ✨ Key Features (Tính năng chính)

### 🎓 Dành cho Người dùng (Thí sinh / Sinh viên)
- **Hỏi đáp thông minh (AI Chat):** Trò chuyện tự nhiên với Chatbot để hỏi về ngành học, điểm chuẩn, thông tin trường. Hỗ trợ hiển thị Markdown và trích dẫn nguồn tài liệu.
- **Nhận diện giọng nói (Speech-to-Text):** Hỗ trợ nhập liệu bằng giọng nói (Voice input).
- **Lưu trữ lịch sử hội thoại:** Theo dõi và tải lại các đoạn chat cũ (yêu cầu đăng nhập MSSV/Ngày sinh).
- **Đăng ký tư vấn:** Biểu mẫu cho phép thí sinh để lại thông tin (SĐT, Email, Ngành quan tâm) để ban tuyển sinh liên hệ.
- **Giao diện tùy chỉnh:** Hỗ trợ chế độ Sáng/Tối (Light/Dark mode), giao diện Responsive mượt mà.

### 🛡️ Dành cho Quản trị viên (Admin Dashboard)
- **Xác thực bảo mật (Auth):** Đăng nhập an toàn qua hệ thống gửi mã OTP xác thực qua Email (SMTP).
- **Quản lý hội thoại:** Xem, duyệt và theo dõi các đoạn chat của người dùng.
- **Quản lý dữ liệu (Context/Docs):** Tải lên các file tài liệu (PDF, Text) để Chatbot học và làm cơ sở dữ liệu cho RAG.
- **Quản lý Prompt & Model:** Tùy chỉnh System Prompt cho AI (Prompt mặc định, Prompt điểm chuẩn) và theo dõi thông tin model đang sử dụng.
- **Quản lý biểu mẫu:** Xem danh sách thí sinh đã đăng ký tư vấn để liên hệ lại.

---

## 📂 Project Structure (Cấu trúc thư mục)

```text
/CHAT_BOT
│
├── /frontend_user     # Mã nguồn giao diện Chatbot (HTML/CSS/JS được module hóa)
│
├── /frontend_admin    # Mã nguồn giao diện Admin Dashboard (HTML/CSS/JS)
│
├── /backend           # Mã nguồn Python xử lý logic server
│   ├── /api           # Các handler xử lý API (chat_handler, admin_handler)
│   ├── /services      # Logic nghiệp vụ (chat_service, history_service, v.v.)
│   ├── /models        # Kết nối AI (Gemini), RAG, ChromaDB
│   └── main.py        # Entry point của ứng dụng Streamlit
│
├── /data              # Nơi chứa dữ liệu tài liệu vector (ChromaDB)
│
├── .streamlit/        # Cấu hình file secrets.toml (API Keys, SMTP config)
│
└── README.md          # Tài liệu hướng dẫn (File này)
```

---

## 🚀 Getting Started (Hướng dẫn cài đặt)

### 1. Cài đặt môi trường
- Yêu cầu Python 3.11 trở xuống
- Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

### 2. Cấu hình bảo mật (Secrets)
Tạo file `.streamlit/secrets.toml` và điền các thông số:
```toml
# Ví dụ cấu hình
GOOGLE_API_KEY = "AIzaSy..."

[SMTP]
EMAIL = "your_email@gmail.com"
APP_PASSWORD = "your_app_password"
```

### 3. Khởi chạy Ứng dụng
```bash
streamlit run backend/main.py
```
Ứng dụng sẽ tự động mở trên trình duyệt tại địa chỉ mặc định `http://localhost:8501`.

---
*Đồ án được xây dựng với mục tiêu áp dụng công nghệ AI tạo sinh (Generative AI) vào thực tiễn tuyển sinh giáo dục.*
