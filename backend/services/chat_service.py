"""
Service xử lý câu hỏi người dùng qua RAG pipeline.
Pipeline: Bóc tách câu hỏi → Truy vấn từng ý → Tổng hợp kết quả.
"""
import re
import json


def process_query(prompt, qa_chain_all, qa_chain_diem_chuan, llm, chat_history=None):
    """Xử lý câu hỏi người dùng qua pipeline RAG đầy đủ:
    
    1. Bóc tách câu hỏi phức tạp thành các ý đơn lẻ (Mặc định Cao Thắng)
    2. Truy vấn từng ý qua Hybrid Search
    3. Tổng hợp kết quả thành câu trả lời hoàn chỉnh
    
    Returns:
        tuple: (answer_text, sources_list)
    """
    if chat_history is None:
        chat_history = []
        
    # Format lịch sử chat gần đây (lấy 4 tin nhắn gần nhất để làm ngữ cảnh)
    recent_history = chat_history[-4:] if len(chat_history) > 0 else []
    history_text = "\n".join([f"{'User' if msg['role']=='user' else 'Bot'}: {msg['content']}" for msg in recent_history])
    if not history_text:
        history_text = "Không có lịch sử trước đó."

    # ==================================================================
    # Bước 1: Bóc tách câu hỏi phức tạp và Khôi phục ngữ cảnh
    # ==================================================================
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

    try:
        msg = llm.invoke(rewrite_prompt)
        content = msg.content
        
        # Xử lý trường hợp content trả về là list thay vì string
        if isinstance(content, list):
            text_parts = [part["text"] if isinstance(part, dict) and "text" in part else str(part) for part in content]
            optimized_res = " ".join(text_parts).strip()
        else:
            optimized_res = str(content).strip()
        
        # Trích xuất mảng JSON bằng regex để tránh lỗi nếu LLM sinh ra văn bản thừa
        json_match = re.search(r'\[.*\]', optimized_res, re.DOTALL)
        if json_match:
            sub_queries = json.loads(json_match.group(0))
        else:
            sub_queries = [prompt]
            
        if not isinstance(sub_queries, list) or len(sub_queries) == 0:
            sub_queries = [prompt]
    except Exception as e:
        print("Rewrite Error:", e) # Log lỗi ra console
        sub_queries = [prompt]

    # ==================================================================
    # Bước 2: Truy vấn từng ý
    # ==================================================================
    sub_answers = []
    all_source_documents = []

    for sub_query in sub_queries:
        sub_query_lower = sub_query.lower()
        try:
            if "điểm chuẩn" in sub_query_lower or "diem chuan" in sub_query_lower:
                res = qa_chain_diem_chuan.invoke({"query": sub_query})
            else:
                res = qa_chain_all.invoke({"query": sub_query})

            sub_answers.append(res["result"])

            if "source_documents" in res:
                all_source_documents.extend(res["source_documents"])
        except Exception as e:
            sub_answers.append(f"(Lỗi khi quét ý '{sub_query}': {e})")

    # ==================================================================
    # Bước 3: Tổng hợp kết quả
    # ==================================================================
    sub_answers_text = "\n\n".join(sub_answers)
    synthesis_prompt = (
        "Bạn là một chuyên gia tư vấn tuyển sinh chuyên nghiệp của "
        "Trường Cao đẳng Kỹ thuật Cao Thắng.\n"
        "Nhiệm vụ: Hãy gộp các thông tin câu trả lời đơn lẻ dưới đây thành "
        "một văn bản tư vấn hoàn chỉnh.\n"
        "QUY TẮC CỐT LÕI (NGHIÊM NGẶT):\n"
        "1. GIỮ NGUYÊN CHI TIẾT: Có bao nhiêu thông tin, con số, phương thức xét tuyển "
        "ở dữ liệu gốc phải giữ lại trọn vẹn.\n"
        "2. NGẮN GỌN & TRỰC DIỆN: Đi thẳng vào vấn đề. TUYỆT ĐỐI KHÔNG thêm thắt "
        "các câu chào hỏi dài dòng, văn mẫu PR, sáo rỗng hay tự ca ngợi trường quá mức.\n"
        "3. CẤU TRÚC: Trình bày dễ đọc (gạch đầu dòng, số thứ tự).\n\n"
        f"Dữ liệu gốc BẮT BUỘC phải giữ nguyên chi tiết:\n{sub_answers_text}\n\n"
        "Câu trả lời tư vấn (Chuyên nghiệp, súc tích, không lan man):"
    )

    try:
        msg2 = llm.invoke(synthesis_prompt)
        content2 = msg2.content
        if isinstance(content2, list):
            text_parts2 = [part["text"] if isinstance(part, dict) and "text" in part else str(part) for part in content2]
            answer = " ".join(text_parts2).strip()
        else:
            answer = str(content2).strip()
    except Exception:
        answer = "\n\n".join(sub_answers)

    # ==================================================================
    # Bước 4: Chuẩn bị nguồn tài liệu tham khảo
    # ==================================================================
    sources = []
    if all_source_documents:
        best_doc = None
        max_overlap = -1
        answer_words = set(re.findall(r"\w+", answer.lower()))

        for doc in all_source_documents:
            doc_words = set(re.findall(r"\w+", doc.page_content.lower()))
            overlap = len(answer_words.intersection(doc_words))
            if overlap > max_overlap:
                max_overlap = overlap
                best_doc = doc

        if best_doc:
            original_json = best_doc.metadata.get("original_json")
            if original_json:
                sources.append(original_json)
            else:
                sources.append(best_doc.page_content)

    return answer, sources
