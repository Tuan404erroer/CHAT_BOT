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

# --- HÀM KHỞI TẠO HỆ THỐNG (Gom từ code cũ của bạn) ---
@st.cache_resource # Quan trọng: Giúp nạp dữ liệu 1 lần duy nhất, cực nhanh
def setup_rag_system():
    # 1. Cấu hình Key (Nhớ thay Key mới của bạn vào đây)
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("Chưa cấu hình API Key trong Secrets!")

    # 2. Khởi tạo Embedding & LLM (Phần này tốn thời gian nên cần cache)
    model_name = "paraphrase-multilingual-MiniLM-L12-v2"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    llm = ChatGoogleGenerativeAI(model="models/gemini-flash-latest", temperature=0.3)

    # 3. Xử lý dữ liệu từ file data.txt
    file_path = "data.txt"
    if not os.path.exists(file_path):
        return None
        
    persist_directory = "./chroma_db"
    if os.path.exists(persist_directory):
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
        )
    else:
        with open(file_path, "r", encoding="utf-8") as handle:
            raw_data = json.load(handle)
        if not isinstance(raw_data, list):
            raw_data = [raw_data]
        docs = []
        for item in raw_data:
            if not isinstance(item, dict):
                continue
            content = (
                f"ten_nganh: {item.get('ten_nganh', '')}\n"
                f"ma_nganh: {item.get('ma_nganh', '')}\n"
                f"chuyen_nganh: {item.get('chuyen_nganh', '')}\n"
                f"muc_tieu_dao_tao: {item.get('muc_tieu_dao_tao', '')}\n"
                f"chuan_dau_ra: {item.get('chuan_dau_ra', '')}\n"
                f"vi_tri_viec_lam: {item.get('vi_tri_viec_lam', '')}\n"
            )
            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "id": item.get("id"),
                        "ten_nganh": item.get("ten_nganh", ""),
                        "ma_nganh": item.get("ma_nganh", ""),
                    },
                )
            )
        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=persist_directory,
        )
    
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 2}),
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT},
    )
    return qa_chain

# Gọi hàm khởi tạo
chain = setup_rag_system()

if chain is None:
    st.error("❌ Không tìm thấy file data.txt. Vui lòng kiểm tra lại!")
    st.stop()

# --- XỬ LÝ LỊCH SỬ CHAT (Để web giống ChatGPT) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lại các câu chat trước đó
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- PHẦN NHẬP CÂU HỎI ---
if prompt := st.chat_input("Bạn muốn hỏi gì về kỳ tuyển sinh năm nay?"):
    # 1. Hiển thị câu hỏi của bạn
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Xử lý câu trả lời từ hệ thống RAG
    with st.chat_message("assistant"):
        with st.spinner("AI đang tra cứu tài liệu..."):
            # Thay cho việc chạy terminal, ta gọi chain ở đây
            response = chain.invoke({"query": prompt})
            answer = response["result"]
            
            st.markdown(answer)
            
            # Hiển thị nguồn (optional - giống như code terminal của bạn)
            with st.expander("Nguồn tài liệu tham khảo"):
                for doc in response["source_documents"]:
                    st.write(f"- {doc.page_content[:200]}...")

    # 3. Lưu lại câu trả lời vào lịch sử
    st.session_state.messages.append({"role": "assistant", "content": answer})