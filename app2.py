import streamlit as st
import streamlit.components.v1 as components
import os
import json
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever

# --- BỘ GỘP HYBRID RETRIEVER TỰ ĐỊNH NGHĨA (SỬA LỖI MODULE RETRIEVERS) ---
from typing import Any, List
from langchain_core.retrievers import BaseRetriever

class CustomHybridRetriever(BaseRetriever):
    vector_retriever: Any
    bm25_retriever: Any
    
    def _get_relevant_documents(self, query: str, *, run_manager=None) -> List[Document]:
        # Gọi song song cả bộ tìm kiếm Vector và Từ khóa chính xác
        docs_vector = self.vector_retriever.invoke(query)
        docs_bm25 = self.bm25_retriever.invoke(query)
        
        # Gộp chung kết quả và loại bỏ các tài liệu trùng nội dung
        seen = set()
        combined = []
        for doc in docs_bm25 + docs_vector:
            if doc.page_content not in seen:
                combined.append(doc)
                seen.add(doc.page_content)
        return combined

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Tư Vấn Tuyển Sinh AI", page_icon="🎓", layout="wide")

# Ẩn toàn bộ UI mặc định của Streamlit — chỉ hiển thị custom component
st.markdown("""
<style>
    #MainMenu, footer, header,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stHeader"] { display: none !important; }

    .stApp { overflow: hidden; }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        padding: 0 !important;
        max-width: 100% !important;
        overflow: hidden;
    }

    /* Đưa iframe component chiếm full viewport */
    [data-testid="stCustomComponentV1"],
    [data-testid="stCustomComponentV1"] > div,
    [data-testid="stCustomComponentV1"] iframe {
        position: fixed !important;
        top: 0 !important; left: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        border: none !important;
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# --- KHAI BÁO CUSTOM COMPONENT ---
parent_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(parent_dir, "frontend")
_chat_component = components.declare_component("chat_ui", path=frontend_dir)

# --- PROMPT TỔNG ---
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

# --- HÀM KHỞI TẠO HỆ THỐNG ---
@st.cache_resource
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
                st.warning(f"Không đọc được file {path}: {exc}")
                return []
            parsed = parse_multiple_json(raw_text)
            if parsed:
                return parsed
            if raw_text.strip():
                return [raw_text]
            return []
        except Exception as exc:
            st.warning(f"Không đọc được file {path}: {exc}")
            return []
        if isinstance(raw_data, list):
            return raw_data
        return [raw_data]

    def build_documents(source_files):
        docs = []
        
        def flatten_json_to_text(data):
            if isinstance(data, dict):
                parts = []
                for k, v in data.items():
                    clean_key = str(k).replace("_", " ").capitalize()
                    parts.append(f"{clean_key}: {flatten_json_to_text(v)}")
                return "\n".join(parts)
            elif isinstance(data, list):
                return "\n".join([f"- {flatten_json_to_text(item)}" for item in data])
            else:
                return str(data).strip()

        for path in source_files:
            filename = os.path.basename(path)
            
            if filename == "diem-chuan.json":
                for item in load_json_items(path):
                    if isinstance(item, dict) and "nganh" in item and "diem_chuan" in item:
                        diem_chuan_lines = []
                        for year, values in item["diem_chuan"].items():
                            diem_chuan_lines.append(f"  {year}: xet_hoc_ba={values.get('xet_hoc_ba')}, thi_thpt_quoc_gia={values.get('thi_thpt_quoc_gia')}, thi_danh_gia_nang_luc={values.get('thi_danh_gia_nang_luc')}")
                        content = f"Nganh: {item['nganh']}\nDiem chuan:\n" + "\n".join(diem_chuan_lines)
                        metadata = {
                            "nganh": item["nganh"],
                            "source_file": filename
                        }
                        docs.append(Document(page_content=content, metadata=metadata))
                continue
            
            for item in load_json_items(path):
                content = flatten_json_to_text(item)
                metadata = {"source_file": filename}
                if isinstance(item, dict):
                    if "id" in item: metadata["id"] = item["id"]
                    if "nganh" in item: metadata["nganh"] = item.get("nganh", "")
                    if "ma_nganh" in item: metadata["ma_nganh"] = item.get("ma_nganh", "")
                    if "ten_nganh" in item: metadata["ten_nganh"] = item.get("ten_nganh", "")
                
                docs.append(Document(page_content=content, metadata=metadata))
                
        return docs

    source_files = collect_source_files()
    if not source_files:
        return None

    docs = build_documents(source_files)
    if not docs:
        return None
    
    # -------------------------------------------------------------
    # BỘ MÁY TÌM KIẾM CẢI TIẾN HYBRID SEARCH
    # -------------------------------------------------------------
    
    # 1. VECTOR SEARCH (Tìm theo ngữ nghĩa)
    vectorstore = Chroma.from_documents(documents=docs, embedding=embeddings)
    chroma_retriever_all = vectorstore.as_retriever(search_kwargs={"k": 7})
    retriever_diem_chuan = vectorstore.as_retriever(
        search_kwargs={"k": 10, "filter": {"source_file": "diem-chuan.json"}}
    )
    
    # 2. BM25 SEARCH (Tìm theo từ khóa chính xác)
    bm25_retriever_all = BM25Retriever.from_documents(docs)
    bm25_retriever_all.k = 7
    
    # 3. KẾT HỢP SONG KIẾM HỢP BÍCH (Sử dụng Bộ gộp tự định nghĩa)
    ensemble_retriever_all = CustomHybridRetriever(
        vector_retriever=chroma_retriever_all,
        bm25_retriever=bm25_retriever_all
    )

    qa_chain_all = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=ensemble_retriever_all,  
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


# --- HÀM XỬ LÝ CÂU HỎI QUA RAG PIPELINE ---
def process_query(prompt, qa_chain_all, qa_chain_diem_chuan, llm):
    """Xử lý câu hỏi người dùng qua pipeline RAG đầy đủ:
    1. Bóc tách câu hỏi phức tạp thành các ý đơn lẻ
    2. Truy vấn từng ý qua Hybrid Search
    3. Tổng hợp kết quả thành câu trả lời hoàn chỉnh
    """
    # Bước 1: Bóc tách câu hỏi
    rewrite_prompt = (
        "Bạn là một hệ thống phân tách ngôn ngữ. Nhiệm vụ của bạn là tách câu hỏi phức tạp của người dùng thành một danh sách (array) các câu hỏi đơn lẻ.\n"
        "QUY TẮC TỐI THƯỢNG:\n"
        "1. BẮT BUỘC trả về ĐÚNG định dạng JSON mảng (bắt đầu bằng [ và kết thúc bằng ]).\n"
        "2. TUYỆT ĐỐI KHÔNG thêm bất kỳ văn bản, lời chào, hay giải thích nào khác ngoài JSON.\n\n"
        "VÍ DỤ 1:\n"
        "- Input: Cao Thắng sử dụng phương thức gì để xét tuyển , toán có được nhân 2 không?\n"
        '- Output: ["Trường Cao Thắng sử dụng phương thức xét tuyển nào?", "Môn Toán có được nhân hệ số 2 khi xét tuyển không?"]\n\n'
        f"- Input: {prompt}\n"
        "- Output:"
    )
    
    try:
        optimized_res = llm.invoke(rewrite_prompt).content.strip()
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

    # Bước 2: Truy vấn từng ý
    sub_answers = []
    all_source_documents = []
    
    for sub_query in sub_queries:
        sub_query_lower = sub_query.lower()
        try:
            if "điểm chuẩn" in sub_query_lower or "diem chuan" in sub_query_lower:
                res = qa_chain_diem_chuan.invoke({"query": sub_query})
            else:
                res = qa_chain_all.invoke({"query": sub_query})
                
            sub_answers.append(res['result'])
            
            if "source_documents" in res:
                all_source_documents.extend(res["source_documents"])
        except Exception as e:
            sub_answers.append(f"(Lỗi khi quét ý '{sub_query}': {e})")

    # Bước 3: Tổng hợp kết quả
    sub_answers_text = "\n\n".join(sub_answers)
    synthesis_prompt = (
        "Bạn là một chuyên gia tư vấn tuyển sinh chuyên nghiệp, cẩn trọng và tận tâm.\n"
        "Nhiệm vụ: Hãy gộp các thông tin câu trả lời đơn lẻ dưới đây thành một văn bản tư vấn hoàn chỉnh.\n"
        "QUY TẮC CỐT LÕI (NGHIÊM NGẶT):\n"
        "1. TUYỆT ĐỐI KHÔNG ĐƯỢC LƯỢC BỎ, rút gọn, hoặc làm mất bất kỳ thông tin chi tiết, con số, điều kiện hay phương thức nào có trong dữ liệu cung cấp.\n"
        "2. Có bao nhiêu ý hỏi, bao nhiêu phương thức xét tuyển ở dữ liệu gốc thì phải giữ lại TRỌN VẸN toàn bộ, không được tự ý gộp hay xóa bớt.\n"
        "3. Trình bày rõ ràng bằng các đề mục, số thứ tự (1, 2, 3...) hoặc gạch đầu dòng để thí sinh dễ đọc. Chỉ sửa lại câu từ cho mượt mà, không làm giảm lượng thông tin.\n\n"
        f"Dữ liệu gốc BẮT BUỘC phải giữ nguyên chi tiết:\n{sub_answers_text}\n\n"
        "Câu trả lời tư vấn đầy đủ và chi tiết nhất:"
    )
    
    try:
        answer = llm.invoke(synthesis_prompt).content.strip()
    except Exception:
        answer = "\n\n".join(sub_answers)

    # Bước 4: Chuẩn bị nguồn tài liệu
    sources = []
    seen_docs = set()
    for doc in all_source_documents:
        if doc.page_content not in seen_docs:
            sources.append(doc.page_content[:200] + "...")
            seen_docs.add(doc.page_content)

    return answer, sources


# --- KHỞI TẠO VÀ CHẠY ỨNG DỤNG ---
chains = setup_rag_system()
if chains is None:
    st.error("❌ Không tìm thấy file dữ liệu hợp lệ. Vui lòng kiểm tra lại!")
    st.stop()
qa_chain_all, qa_chain_diem_chuan, llm = chains

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_ts" not in st.session_state:
    st.session_state.last_ts = 0

# --- RENDER COMPONENT & XỬ LÝ ---
user_input = _chat_component(
    messages=json.dumps(st.session_state.messages, ensure_ascii=False),
    key="chat",
    default=None
)

# Khi nhận được tin nhắn mới từ frontend
if user_input is not None:
    ts = user_input.get("timestamp", 0)
    
    if ts != st.session_state.last_ts:
        st.session_state.last_ts = ts
        query = user_input.get("message", "")
        
        # Lưu tin nhắn user
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Xử lý qua RAG pipeline
        answer, sources = process_query(query, qa_chain_all, qa_chain_diem_chuan, llm)
        
        # Lưu tin nhắn assistant
        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources
        })
        
        # Rerun để gửi kết quả xuống frontend
        st.rerun()
