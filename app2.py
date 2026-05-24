import streamlit as st
import os
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Tư Vấn Tuyển Sinh AI", page_icon="🎓")
st.title("🤖 AI Tư Vấn Tuyển Sinh")
st.info("Hệ thống RAG tự động duyệt/quét lại toàn bộ file dữ liệu trực tiếp trên RAM mỗi khi đặt câu hỏi.")

# --- PROMPT TỔNG: ĐÃ THÊM LƯU Ý TƯ DUY BẮC CẦU ---
PROMPT = PromptTemplate(
    template=(
        "Bạn là chuyên gia tư vấn tuyển sinh thông minh.\n"
        "Sử dụng các thông tin được cung cấp dưới đây để trả lời câu hỏi.\n\n"
        "LƯU Ý TƯ DUY:\n"
        "1. Nếu thông tin của một ngành cụ thể không ghi rõ chuẩn ngoại ngữ/tin học, nhưng trong tài liệu có quy định chung về ngoại ngữ/tin học tốt nghiệp của toàn trường, hãy áp dụng quy định chung đó để trả lời cho ngành được hỏi.\n"
        "2. Trả lời chi tiết, mạch lạc nếu có thông tin. Nếu là câu hỏi chung không có trong tài liệu, được phép tự trả lời ngắn dưới 50 từ. Nếu không biết thì nói không biết, không tự bịa thông tin.\n\n"
        "Thông tin tài liệu:\n{context}\n\n"
        "Câu hỏi của thí sinh: {question}\n"
        "Câu trả lời:"
    ),
    input_variables=["context", "question"],
)

# --- HÀM KHỞI TẠO HỆ THỐNG (CHẠY THUẦN TRÊN RAM) ---
def setup_rag_system():
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("Chưa cấu hình API Key trong Secrets!")

    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0.3)

    def collect_source_files():
        candidates = []
        for entry in os.listdir("."):
            if entry.lower().endswith(".json") and os.path.isfile(entry):
                candidates.append(entry)
        return sorted(set(candidates))

    def parse_multiple_json(text):
        decoder = json.JSONDecoder()
        index = 0
        results = []
        length = len(text)
        while index < length:
            while index < length and text[index].isspace():
                index += 1
            if index >= length:
                break
            try:
                value, next_index = decoder.raw_decode(text, index)
            except json.JSONDecodeError:
                break
            if isinstance(value, list):
                results.extend(value)
            else:
                results.append(value)
            index = next_index
        return results

    def load_json_items(path):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw_data = json.load(handle)
        except json.JSONDecodeError:
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    raw_text = handle.read()
            except Exception as exc:
                st.warning(f"Khong doc duoc file {path}: {exc}")
                return []
            parsed = parse_multiple_json(raw_text)
            if parsed:
                return parsed
            if raw_text.strip():
                return [raw_text]
            return []
        except Exception as exc:
            st.warning(f"Khong doc duoc file {path}: {exc}")
            return []
        if isinstance(raw_data, list):
            return raw_data
        return [raw_data]

    def build_documents(source_files):
        docs = []
        for path in source_files:
            filename = os.path.basename(path)
            if filename == "diem-chuan.json":
                for item in load_json_items(path):
                    if isinstance(item, dict) and "nganh" in item and "diem_chuan" in item:
                        diem_chuan_lines = []
                        for year, values in item["diem_chuan"].items():
                            diem_chuan_lines.append(f"  {year}: xet_hoc_ba={values.get('xet_hoc_ba')}, thi_thpt_quoc_gia={values.get('thi_thpt_quoc_gia')}, thi_danh_gia_nang_luc={values.get('thi_danh_gia_nang_luc')}")
                        content = f"nganh: {item['nganh']}\ndiem_chuan:\n" + "\n".join(diem_chuan_lines)
                        metadata = {
                            "nganh": item["nganh"],
                            "source_file": filename
                        }
                        docs.append(Document(page_content=content, metadata=metadata))
                continue
            for item in load_json_items(path):
                if isinstance(item, dict) and any(
                    key in item
                    for key in [
                        "ten_nganh",
                        "ma_nganh",
                        "chuyen_nganh",
                        "muc_tieu_dao_tao",
                        "chuan_dau_ra",
                        "vi_tri_viec_lam",
                    ]
                ):
                    content = (
                        f"ten_nganh: {item.get('ten_nganh', '')}\n"
                        f"ma_nganh: {item.get('ma_nganh', '')}\n"
                        f"chuyen_nganh: {item.get('chuyen_nganh', '')}\n"
                        f"muc_tieu_dao_tao: {item.get('muc_tieu_dao_tao', '')}\n"
                        f"chuan_dau_ra: {item.get('chuan_dau_ra', '')}\n"
                        f"vi_tri_viec_lam: {item.get('vi_tri_viec_lam', '')}\n"
                    )
                    metadata = {
                        "id": item.get("id"),
                        "ten_nganh": item.get("ten_nganh", ""),
                        "ma_nganh": item.get("ma_nganh", ""),
                        "source_file": filename
                    }
                else:
                    if isinstance(item, str):
                        content = item
                    else:
                        content = json.dumps(item, ensure_ascii=False, indent=2)
                    metadata = {"source_file": filename}
                docs.append(Document(page_content=content, metadata=metadata))
        return docs

    source_files = collect_source_files()
    if not source_files:
        return None

    docs = build_documents(source_files)
    if not docs:
        return None
    
    # KHÔNG TRUYỀN persist_directory -> Chroma tự biết chỉ hoạt động trên RAM
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings
    )
    
    retriever_all = vectorstore.as_retriever(search_kwargs={"k": 10})
    retriever_diem_chuan = vectorstore.as_retriever(
        search_kwargs={"k": 10, "filter": {"source_file": "diem-chuan.json"}}
    )
    qa_chain_all = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever_all,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT},
    )
    qa_chain_diem_chuan = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever_diem_chuan,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT},
    )
    return qa_chain_all, qa_chain_diem_chuan, llm


# --- XỬ LÝ LỊCH SỬ CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- PHẦN NHẬP CÂU HỎI ---
if prompt := st.chat_input("Bạn muốn hỏi gì về kỳ tuyển sinh năm nay?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Đang quét trực tiếp tệp tin và dựng lại không gian ngữ nghĩa trên RAM..."):
            
            # GỌI LẠI HÀM KHỞI TẠO TẠI ĐÂY: Mỗi khi hỏi, hệ thống sẽ quét sạch và nạp lại file JSON mới nhất
            chains = setup_rag_system()
            
            if chains is None:
                st.error("❌ Không tìm thấy file dữ liệu hợp lệ. Vui lòng kiểm tra lại!")
                st.stop()

            qa_chain_all, qa_chain_diem_chuan, llm = chains
            prompt_lower = prompt.lower()
            
            if "điểm chuẩn" in prompt_lower or "diem chuan" in prompt_lower:
                response = qa_chain_diem_chuan.invoke({"query": prompt})
            else:
                # BỘ TRÍCH XUẤT Ý ĐỊNH SIÊU CẤP (ÉP BUỘC BẰNG VÍ DỤ - FEW-SHOT)
                rewrite_prompt = (
                    "Bạn là một cỗ máy trích xuất từ khóa (Search Engine Optimizer) cho database nhà trường.\n"
                    "Nhiệm vụ: Chuyển câu hỏi thành 1 CỤM TỪ KHÓA NGẮN GỌN (tối đa 5 từ) mang tính học thuật.\n"
                    "QUY TẮC TỐI THƯỢNG:\n"
                    "1. TUYỆT ĐỐI XÓA BỎ: 'Cao Thắng', 'trường', 'sinh viên', 'em', 'có', 'không', 'ạ', 'bắt buộc'.\n"
                    "2. CHỈ TRẢ VỀ TỪ KHÓA, không trả lời thành câu.\n\n"
                    "VÍ DỤ BẮT BUỘC PHẢI HỌC THEO:\n"
                    "- Input: Cao Thắng có yêu cầu đầu ra nào về tiếng anh bắt buộc cho sinh viên\n"
                    "- Output: chuẩn đầu ra tiếng anh\n"
                    "- Input: Học cơ khí ở trường mình bao lâu thì ra trường\n"
                    "- Output: thời gian đào tạo cơ khí\n"
                    "- Input: Ngành ô tô ra làm nghề gì shop\n"
                    "- Output: vị trí việc làm ô tô\n\n"
                    f"- Input: {prompt}\n"
                    "- Output:"
                )
                
                try:
                    optimized_query = llm.invoke(rewrite_prompt).content.strip()
                except Exception:
                    optimized_query = prompt
                
                response = qa_chain_all.invoke({"query": optimized_query})
            
            answer = response["result"]
            st.markdown(answer)

            # Hiển thị nguồn
            with st.expander("Nguồn tài liệu tham khảo"):
                for doc in response["source_documents"]:
                    st.write(f"- {doc.page_content[:200]}...")

            # DEBUG
            with st.expander("DEBUG"):
                if "optimized_query" in locals():
                    st.info(f"🔑 **Query sau khi trích xuất ý định:** {optimized_query}")
                for doc in response["source_documents"]:
                    st.write(doc.metadata)
                    st.write(doc.page_content)

    st.session_state.messages.append({"role": "assistant", "content": answer})