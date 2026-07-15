"""
Service khởi tạo và quản lý RAG (Retrieval-Augmented Generation) pipeline.
Bao gồm: load models, tạo vector store, hybrid retriever, QA chains.
"""
import os
import uuid
import hashlib

import streamlit as st
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_community.retrievers import BM25Retriever

from models.constants import (
    EMBEDDING_MODEL_NAME, LLM_MODEL_NAME, LLM_TEMPERATURE,
    KNOWLEDGE_CONFIG_FILE, KNOWLEDGE_DIR,
)
from models.retrievers import CustomHybridRetriever
from services.prompt_service import get_system_prompt
from services.knowledge_service import collect_source_files, build_documents


# ==============================================================================
# GLOBAL CACHE (Streamlit cache_resource)
# ==============================================================================

@st.cache_resource
def get_global_rag_cache():
    """Cache toàn cục cho RAG system, chia sẻ giữa các session."""
    return {"hash": None, "chains": None}


@st.cache_resource
def load_models():
    """Load embedding model và LLM, cache để tái sử dụng.
    
    Returns:
        tuple: (embeddings, llm)
    """
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
    else:
        st.error("Chưa cấu hình API Key trong Secrets!")

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    llm = ChatGoogleGenerativeAI(
        model=LLM_MODEL_NAME, temperature=LLM_TEMPERATURE
    )
    return embeddings, llm


# ==============================================================================
# RAG SYSTEM SETUP
# ==============================================================================

def get_rag_hash():
    """Tính hash MD5 từ cấu hình knowledge để phát hiện thay đổi."""
    hash_str = ""

    if KNOWLEDGE_CONFIG_FILE.exists():
        try:
            with open(KNOWLEDGE_CONFIG_FILE, "r", encoding="utf-8") as f:
                hash_str += f.read()
        except Exception:
            pass

    # Hash thời gian sửa đổi file trong thư mục knowledge
    if KNOWLEDGE_DIR.exists():
        for entry in os.listdir(KNOWLEDGE_DIR):
            full_path = KNOWLEDGE_DIR / entry
            if entry.lower().endswith((".json", ".txt")) and full_path.is_file():
                hash_str += f"{entry}_{os.path.getmtime(full_path)}"

    return hashlib.md5(hash_str.encode()).hexdigest()


def setup_rag_system(config_hash=None):
    """Khởi tạo toàn bộ RAG pipeline: embeddings, vector store, chains.
    
    Sử dụng Hybrid Search = Vector (ChromaDB) + BM25 (keyword).
    
    Returns:
        tuple: (qa_chain_all, qa_chain_diem_chuan, llm) hoặc None nếu lỗi
    """
    cache = get_global_rag_cache()
    if cache["hash"] == config_hash and cache["chains"] is not None:
        return cache["chains"]

    embeddings, llm = load_models()

    source_files = collect_source_files()
    if not source_files:
        cache["chains"] = None
        cache["hash"] = config_hash
        return None

    docs = build_documents(source_files)
    if not docs:
        cache["chains"] = None
        cache["hash"] = config_hash
        return None

    # 1. VECTOR SEARCH (Tìm theo ngữ nghĩa)
    collection_name = f"rag_{config_hash}_{uuid.uuid4().hex[:8]}"
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=collection_name,
    )
    chroma_retriever_all = vectorstore.as_retriever(search_kwargs={"k": 7})
    retriever_diem_chuan = vectorstore.as_retriever(
        search_kwargs={"k": 10, "filter": {"source_file": "diem-chuan.json"}}
    )

    # 2. BM25 SEARCH (Tìm theo từ khóa chính xác)
    bm25_retriever_all = BM25Retriever.from_documents(docs)
    bm25_retriever_all.k = 7

    # 3. KẾT HỢP SONG KIẾM HỢP BÍCH (Hybrid Search)
    ensemble_retriever_all = CustomHybridRetriever(
        vector_retriever=chroma_retriever_all,
        bm25_retriever=bm25_retriever_all,
    )

    current_date_str = datetime.now().strftime("%d/%m/%Y")

    prompt_all = PromptTemplate(
        template=get_system_prompt("DEFAULT"),
        input_variables=["context", "question"],
        partial_variables={"current_date": current_date_str},
    )

    prompt_diem_chuan = PromptTemplate(
        template=get_system_prompt("DIEM_CHUAN"),
        input_variables=["context", "question"],
        partial_variables={"current_date": current_date_str},
    )

    qa_chain_all = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=ensemble_retriever_all,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt_all},
    )

    qa_chain_diem_chuan = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever_diem_chuan,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt_diem_chuan},
    )

    cache["chains"] = (qa_chain_all, qa_chain_diem_chuan, llm)
    cache["hash"] = config_hash
    return cache["chains"]


def ensure_rag_system():
    """Đảm bảo RAG system đã khởi tạo và cập nhật theo config hiện tại.
    
    Returns:
        tuple: (qa_chain_all, qa_chain_diem_chuan, llm)
    """
    rag_hash = get_rag_hash()

    if (
        not st.session_state.get("rag_initialized")
        or st.session_state.get("current_rag_hash") != rag_hash
    ):
        with st.spinner("🔄 Đang cập nhật hệ thống AI..."):
            chips = setup_rag_system(rag_hash)
            if chips is None:
                st.error("❌ Không tìm thấy file dữ liệu hợp lệ. Vui lòng kiểm tra lại!")
                st.stop()
            st.session_state.qa_chain_all = chips[0]
            st.session_state.qa_chain_diem_chuan = chips[1]
            st.session_state.llm = chips[2]
            st.session_state.rag_initialized = True
            st.session_state.current_rag_hash = rag_hash

    return (
        st.session_state.qa_chain_all,
        st.session_state.qa_chain_diem_chuan,
        st.session_state.llm,
    )
