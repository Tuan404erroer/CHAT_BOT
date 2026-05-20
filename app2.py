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
try:
    from langchain.globals import set_llm_cache
except Exception:
    from langchain_core.globals import set_llm_cache
try:
    from langchain.cache import SQLiteCache
except Exception:
    from langchain_community.cache import SQLiteCache

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Tư Vấn Tuyển Sinh AI", page_icon="🎓")
st.title("🤖 AI Tư Vấn Tuyển Sinh")
st.info("Hệ thống RAG đã được tích hợp giao diện Web.")

set_llm_cache(SQLiteCache(database_path=".langchain.db"))

PROMPT = PromptTemplate(
    template=(
        "Ban la chuyen gia tu van tuyen sinh. "
        "Su dung thong tin duoi day de tra loi. "
        "Neu cau hoi nam trong thong tin duoc cung cap, hay tra loi chi tiet. "
        "Neu cau hoi la cau hoi chung (tu van nghe nghiep, gioi tinh, dinh huong) "
        "KHONG co trong thong tin, ban DUOC PHEP tu tra loi nhung bat buoc RẤT NGAN "
        "(duoi 50 tu). Neu khong biet, hay noi khong biet, dung tuong tuong.\n\n"
        "Thong tin:\n{context}\n\n"
        "Cau hoi: {question}\n"
        "Cau tra loi:"
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

    def build_manifest(source_files):
        manifest = []
        for path in source_files:
            try:
                stat = os.stat(path)
            except OSError:
                continue
            manifest.append(
                {
                    "path": path,
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                }
            )
        return sorted(manifest, key=lambda item: item["path"])

    source_files = collect_source_files()
    if not source_files:
        return None

    persist_directory = "./chroma_db"
    manifest_path = os.path.join(persist_directory, "_sources.json")
    current_manifest = build_manifest(source_files)
    use_existing = False

    if os.path.exists(persist_directory) and os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as handle:
                saved_manifest = json.load(handle)
            if saved_manifest == current_manifest:
                use_existing = True
        except Exception:
            use_existing = False

    if use_existing:
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
        )
    else:
        docs = build_documents(source_files)
        if not docs:
            return None
        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=persist_directory,
        )
        os.makedirs(persist_directory, exist_ok=True)
        with open(manifest_path, "w", encoding="utf-8") as handle:
            json.dump(current_manifest, handle, ensure_ascii=False, indent=2)
    
    # ĐÃ SỬA LẦN 2: Tăng k lên 8 để mở rộng vùng tìm kiếm, tránh bị lọt thông tin
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

# Gọi hàm khởi tạo
chains = setup_rag_system()

if chains is None:
    st.error("❌ Không tìm thấy file dữ liệu hợp lệ. Vui lòng kiểm tra lại!")
    st.stop()

qa_chain_all, qa_chain_diem_chuan, llm = chains

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
        with st.spinner("AI đang tra cứu tài liệu..."):
            prompt_lower = prompt.lower()
            
            if "điểm chuẩn" in prompt_lower or "diem chuan" in prompt_lower:
                response = qa_chain_diem_chuan.invoke({"query": prompt})
            else:
                # ĐÃ SỬA LẦN 2: Prompt xịn hơn, cấm đưa tên trường vào để tránh nhiễu
                rewrite_prompt = (
                    f"Bạn là chuyên gia tối ưu từ khóa tìm kiếm cho hệ thống RAG.\n"
                    f"Nhiệm vụ: Chuyển câu hỏi của người dùng thành 1 câu truy vấn ngắn gọn sát với dữ liệu giáo dục.\n"
                    f"QUY TẮC QUAN TRỌNG:\n"
                    f"1. TUYỆT ĐỐI KHÔNG đưa tên trường (VD: Cao Thắng, trường mình, ở đây) vào câu truy vấn vì toàn bộ DB đã mặc định là của trường này. Thêm tên trường sẽ làm nhiễu công cụ tìm kiếm.\n"
                    f"2. Chuyển các từ đồng nghĩa (VD: 'tốt nghiệp', 'hoàn thành khóa học', 'bao lâu') thành từ khóa chuẩn (VD: 'thời gian đào tạo', 'số năm học').\n"
                    f"Câu hỏi gốc: {prompt}\n"
                    f"Câu truy vấn tối ưu (Chỉ trả về câu mới, không giải thích):"
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
                    st.info(f"🔑 **Query sau khi tối ưu:** {optimized_query}")
                for doc in response["source_documents"]:
                    st.write(doc.metadata)
                    st.write(doc.page_content)

    st.session_state.messages.append({"role": "assistant", "content": answer})