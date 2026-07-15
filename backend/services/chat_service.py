"""
Service xử lý câu hỏi người dùng qua RAG pipeline.
Pipeline: Bóc tách câu hỏi → Truy vấn từng ý → Tổng hợp kết quả.
"""
import re
import json


def process_query(prompt, qa_chain_all, qa_chain_diem_chuan, llm):
    """Xử lý câu hỏi người dùng qua pipeline RAG đầy đủ:
    
    1. Bóc tách câu hỏi phức tạp thành các ý đơn lẻ (Mặc định Cao Thắng)
    2. Truy vấn từng ý qua Hybrid Search
    3. Tổng hợp kết quả thành câu trả lời hoàn chỉnh
    
    Returns:
        tuple: (answer_text, sources_list)
    """
    # ==================================================================
    # Bước 1: Bóc tách câu hỏi phức tạp
    # ==================================================================
    rewrite_prompt = (
        "Bạn là một hệ thống phân tách ngôn ngữ. Hệ thống này được thiết kế ĐỘC QUYỀN cho "
        "'Trường Cao đẳng Kỹ thuật Cao Thắng'.\n"
        "Nhiệm vụ của bạn là tách câu hỏi phức tạp của người dùng thành một danh sách (array) "
        "các câu hỏi đơn lẻ để hệ thống RAG tìm kiếm.\n"
        "QUY TẮC TỐI THƯỢNG:\n"
        "1. MẶC ĐỊNH NGỮ CẢNH: Bất cứ khi nào người dùng dùng các từ như 'trường', 'nhà trường', "
        "'trường mình', 'trường đó', 'ở đây', bạn BẮT BUỘC phải thay thế cụm từ đó bằng "
        "'Trường Cao đẳng Kỹ thuật Cao Thắng' trong câu hỏi đầu ra.\n"
        "2. GIỮ NGUYÊN Ý NGHĨA: Tuyệt đối không được lược bỏ hoặc bỏ qua các câu hỏi mang "
        "tính chất lịch sử, vĩ nhân hoặc danh nhân.\n"
        "3. BẮT BUỘC trả về ĐÚNG định dạng JSON mảng (bắt đầu bằng [ và kết thúc bằng ]).\n"
        "4. TUYỆT ĐỐI KHÔNG thêm bất kỳ văn bản giải thích nào khác ngoài JSON.\n\n"
        "VÍ DỤ:\n"
        "- Input: Điểm chuẩn của trường là bao nhiêu? Có những ai nổi tiếng từng học ở đây?\n"
        '- Output: ["Điểm chuẩn của trường Cao đẳng Kỹ thuật Cao Thắng là bao nhiêu?", '
        '"Có những người nổi tiếng nào từng học tại trường Cao đẳng Kỹ thuật Cao Thắng?"]\n\n'
        f"- Input: {prompt}\n"
        "- Output:"
    )

    try:
        optimized_res = llm.invoke(rewrite_prompt).content.strip()
        # Loại bỏ markdown code block nếu có
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
        answer = llm.invoke(synthesis_prompt).content.strip()
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
