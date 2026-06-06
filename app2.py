import streamlit as st
import streamlit.components.v1 as components
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
<<<<<<< Updated upstream
st.set_page_config(page_title="Tư Vấn Tuyển Sinh AI", page_icon="🎓")
st.title("🤖 AI Tư Vấn Tuyển Sinh")
st.info("Hệ thống RAG đã được tích hợp giao diện Web.")

set_llm_cache(SQLiteCache(database_path=".langchain.db"))
=======
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
>>>>>>> Stashed changes

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

<<<<<<< Updated upstream
# Gọi hàm khởi tạo
chain = setup_rag_system()

if chain is None:
    st.error("❌ Không tìm thấy file data.txt. Vui lòng kiểm tra lại!")
    st.stop()

# --- XỬ LÝ LỊCH SỬ CHAT (Để web giống ChatGPT) ---
=======

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
>>>>>>> Stashed changes
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_ts" not in st.session_state:
    st.session_state.last_ts = 0

<<<<<<< Updated upstream
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
=======
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
>>>>>>> Stashed changes
