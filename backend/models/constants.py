"""
Hằng số và cấu hình mặc định cho toàn bộ backend.
Tất cả đường dẫn file đều được tính từ PROJECT_ROOT (thư mục gốc dự án).
"""
from pathlib import Path

# ==============================================================================
# ĐƯỜNG DẪN THƯ MỤC
# ==============================================================================
# backend/models/constants.py -> parent(models) -> parent(backend) -> parent(CHAT_BOT)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Thư mục data
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
CONFIG_DIR = DATA_DIR / "config"
STORAGE_DIR = DATA_DIR / "storage"

# Thư mục frontendz
FRONTEND_DIR = PROJECT_ROOT / "frontend_user"
FRONTEND_ADMIN_DIR = PROJECT_ROOT / "frontend_admin"

# ==============================================================================
# ĐƯỜNG DẪN FILE
# ==============================================================================
HISTORY_FILE = STORAGE_DIR / "chat_history.json"
CONSULT_FILE = STORAGE_DIR / "consult_registrations.json"
KNOWLEDGE_CONFIG_FILE = CONFIG_DIR / "knowledge_config.json"
SYSTEM_PROMPT_FILE = CONFIG_DIR / "prompts.json"

# ==============================================================================
# DANH SÁCH FILE LOẠI TRỪ (không phải knowledge)
# ==============================================================================
EXCLUDED_FILES = {
    "chat_history.json",
    "consult_registrations.json",
    "knowledge_config.json",
    "prompts.json",
}

# ==============================================================================
# CẤU HÌNH AI MODEL
# ==============================================================================
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
LLM_MODEL_NAME = "gemini-3.1-flash-lite"
LLM_TEMPERATURE = 0.3

# ==============================================================================
# PROMPT MẶC ĐỊNH (fallback khi file prompts.json không tồn tại)
# ==============================================================================
DEFAULT_PROMPTS = {
    "DEFAULT": {
        "name": "Tư Vấn Chung",
        "description": "Kịch bản mặc định xử lý mọi câu hỏi thông thường về tuyển sinh, quy chế.",
        "content": (
            "Bạn là chuyên gia tư vấn tuyển sinh thân thiện của Trường Cao đẳng Kỹ thuật Cao Thắng (Cao Thắng).\n"
            "Mọi từ 'trường', 'nhà trường', 'trường mình' trong câu hỏi đều MẶC ĐỊNH hiểu là Trường Cao đẳng Kỹ thuật Cao Thắng.\n\n"
            "Hôm nay là {current_date}.\n\n"
            "QUY TẮC PHÂN QUYỀN KIẾN THỨC TỐI THƯỢNG:\n"
            "1. THÔNG TIN TUYỂN SINH (Điểm chuẩn, ngành, học phí, quy chế): BẮT BUỘC dùng dữ liệu cung cấp. Không có thì nói chưa cập nhật, KHÔNG BỊA.\n"
            "2. THÔNG TIN LỊCH SỬ, VĨ NHÂN: Được phép dùng kiến thức nền để trả lời (VD: trường thành lập 1906, Bác Hồ và Bác Tôn từng học). "
            "NHƯNG PHẢI TRẢ LỜI CỰC KỲ NGẮN GỌN, ĐÚNG TRỌNG TÂM câu hỏi. TUYỆT ĐỐI KHÔNG viết văn hoa mỹ, sáo rỗng, không kể lể dài dòng.\n"
            "3. TƯƠNG TÁC: Nếu câu hỏi chưa rõ ràng, thêm 1 câu gợi mở ngắn gọn cuối bài.\n\n"
            "Thông tin tài liệu:\n{context}\n\n"
            "Câu hỏi của thí sinh: {question}\n"
            "Câu trả lời (Ngắn gọn, súc tích):"
        ),
    },
    "DIEM_CHUAN": {
        "name": "Tư Vấn Điểm Chuẩn",
        "description": "Kịch bản chuyên biệt dùng khi thí sinh hỏi về điểm số, điểm chuẩn.",
        "content": (
            "Bạn là chuyên gia phân tích điểm chuẩn của Trường Cao đẳng Kỹ thuật Cao Thắng. "
            "Hôm nay là {current_date}.\n\n"
            "QUY TẮC ĐẶC BIỆT:\n"
            "- Nếu thí sinh hỏi điểm chuẩn của 1 ngành cụ thể, hãy trình bày dạng danh sách gạch đầu dòng rõ ràng.\n"
            "- BẮT BUỘC chỉ sử dụng dữ liệu được cung cấp dưới đây, tuyệt đối không bịa số liệu.\n\n"
            "Dữ liệu tham khảo:\n{context}\n\n"
            "Câu hỏi của thí sinh: {question}\n"
            "Câu trả lời:"
        ),
    },
}
