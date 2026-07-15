"""
Custom Hybrid Retriever: Kết hợp Vector Search + BM25 Keyword Search.
Gộp kết quả từ 2 bộ tìm kiếm và loại trùng lặp.
"""
from typing import Any, List
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document


class CustomHybridRetriever(BaseRetriever):
    """Bộ gộp Hybrid Retriever tự định nghĩa.
    
    Kết hợp song song:
    - Vector Retriever (tìm theo ngữ nghĩa)
    - BM25 Retriever (tìm theo từ khóa chính xác)
    """
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
