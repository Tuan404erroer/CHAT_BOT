import os
import tomllib
from langchain_google_genai import ChatGoogleGenerativeAI

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomllib.load(f)
api_key = secrets.get("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.0,
    google_api_key=api_key
)

history_text = """User: Điểm chuẩn dgnl ngành cntt 2026 là bao nhiêu
Bot: Dựa trên dữ liệu được cung cấp, điểm chuẩn ĐGNL ngành Công nghệ Thông tin năm 2026 như sau: Điểm chuẩn ĐGNL (2026): 600"""
prompt = "còn 2025 là bao nhiêu"

rewrite_prompt = (
        "Bạn là một hệ thống phân tách ngôn ngữ và phân tích ngữ cảnh. Hệ thống này được thiết kế ĐỘC QUYỀN cho "
        "'Trường Cao đẳng Kỹ thuật Cao Thắng'.\n"
        "Nhiệm vụ của bạn là đọc Lịch sử trò chuyện và Câu hỏi hiện tại của người dùng, từ đó khôi phục lại "
        "đầy đủ ngữ cảnh (nếu người dùng hỏi viết tắt, hỏi tiếp nối) và tách thành danh sách (array) "
        "các câu hỏi đơn lẻ hoàn chỉnh để hệ thống RAG tìm kiếm.\n"
        "QUY TẮC TỐI THƯỢNG:\n"
        "1. KHÔI PHỤC NGỮ CẢNH: Nếu câu hỏi là 'Còn ngành IT thì sao?', 'Còn năm 2025 thì sao?', "
        "hãy nhìn vào lịch sử để biết trước đó đang nói về điểm chuẩn, học phí hay môn học nào, từ đó viết lại "
        "thành câu hỏi hoàn chỉnh (Ví dụ: 'Điểm chuẩn năm 2025 của ngành IT là bao nhiêu?').\n"
        "2. MẶC ĐỊNH NGỮ CẢNH TRƯỜNG: Bất cứ khi nào người dùng dùng các từ như 'trường', 'nhà trường', "
        "'trường mình', 'trường đó', 'ở đây', bạn BẮT BUỘC phải thay thế cụm từ đó bằng "
        "'Trường Cao đẳng Kỹ thuật Cao Thắng' trong câu hỏi đầu ra.\n"
        "3. GIỮ NGUYÊN Ý NGHĨA: Tuyệt đối không được lược bỏ hoặc bỏ qua các câu hỏi mang "
        "tính chất lịch sử, vĩ nhân hoặc danh nhân.\n"
        "4. BẮT BUỘC trả về ĐÚNG định dạng JSON mảng (bắt đầu bằng [ và kết thúc bằng ]).\n"
        "5. TUYỆT ĐỐI KHÔNG thêm bất kỳ văn bản giải thích nào khác ngoài JSON.\n\n"
        "VÍ DỤ 1 (Tách câu hỏi):\n"
        "- Lịch sử: Không có\n"
        "- Input: Điểm chuẩn của trường là bao nhiêu? Có những ai nổi tiếng từng học ở đây?\n"
        '- Output: ["Điểm chuẩn của trường Cao đẳng Kỹ thuật Cao Thắng là bao nhiêu?", '
        '"Có những người nổi tiếng nào từng học tại trường Cao đẳng Kỹ thuật Cao Thắng?"]\n\n'
        "VÍ DỤ 2 (Tiếp nối ngữ cảnh):\n"
        "- Lịch sử:\nUser: Điểm chuẩn ĐGNL ngành IT 2026 là bao nhiêu?\nBot: Điểm chuẩn là 600.\n"
        "- Input: còn năm 2025 là bao nhiêu?\n"
        '- Output: ["Điểm chuẩn ĐGNL của ngành IT năm 2025 tại Trường Cao đẳng Kỹ thuật Cao Thắng là bao nhiêu?"]\n\n'
        f"--- BẮT ĐẦU ---\n"
        f"- Lịch sử trò chuyện gần đây:\n{history_text}\n"
        f"- Input: {prompt}\n"
        "- Output:"
    )

print(llm.invoke(rewrite_prompt).content.strip())
