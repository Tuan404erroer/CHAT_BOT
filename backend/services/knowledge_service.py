"""
Service quản lý file tri thức (Knowledge Base).
CRUD file trong data/knowledge/ và đồng bộ knowledge_config.json.
"""
import os
import json
from datetime import datetime
from langchain_core.documents import Document

from models.constants import (
    KNOWLEDGE_DIR, KNOWLEDGE_CONFIG_FILE, EXCLUDED_FILES
)
from utils.file_helpers import safe_read_json, safe_write_json
from utils.text_helpers import flatten_json_to_text, load_json_items


def collect_source_files():
    """Quét thư mục knowledge/ và trả về danh sách file được bật (enabled).
    
    Returns:
        list[Path]: Danh sách đường dẫn tuyệt đối đến các file tri thức.
    """
    knowledge_config = safe_read_json(KNOWLEDGE_CONFIG_FILE, default={})
    candidates = []

    if not KNOWLEDGE_DIR.exists():
        return candidates

    for entry in os.listdir(KNOWLEDGE_DIR):
        full_path = KNOWLEDGE_DIR / entry
        if (
            entry.lower().endswith((".json", ".txt"))
            and full_path.is_file()
            and entry not in EXCLUDED_FILES
        ):
            cfg = knowledge_config.get(entry, {})
            if cfg.get("enabled", True):
                candidates.append(str(full_path))

    return sorted(set(candidates))


def build_documents(source_files):
    """Xây dựng danh sách Document từ các file tri thức cho RAG indexing.
    
    Xử lý đặc biệt cho file diem-chuan.json (cấu trúc điểm chuẩn).
    """
    docs = []

    for path in source_files:
        filename = os.path.basename(path)

        # Xử lý đặc biệt cho file điểm chuẩn
        if filename == "diem-chuan.json":
            for item in load_json_items(path):
                if isinstance(item, dict) and "nganh" in item and "diem_chuan" in item:
                    diem_chuan_lines = []
                    for year, values in item["diem_chuan"].items():
                        parts = [f"{k}={v}" for k, v in values.items()]
                        diem_chuan_lines.append(f"  {year}: " + ", ".join(parts))
                    content = f"Nganh: {item['nganh']}\nDiem chuan:\n" + "\n".join(diem_chuan_lines)
                    metadata = {
                        "nganh": item["nganh"],
                        "source_file": filename,
                        "original_json": json.dumps(item, ensure_ascii=False, indent=2),
                    }
                    docs.append(Document(page_content=content, metadata=metadata))
            continue

        # Xử lý chung cho các file khác
        for item in load_json_items(path):
            content = flatten_json_to_text(item)
            metadata = {
                "source_file": filename,
                "original_json": (
                    json.dumps(item, ensure_ascii=False, indent=2)
                    if isinstance(item, (dict, list))
                    else str(item)
                ),
            }
            if isinstance(item, dict):
                if "id" in item:
                    metadata["id"] = item["id"]
                if "nganh" in item:
                    metadata["nganh"] = item.get("nganh", "")
                if "ma_nganh" in item:
                    metadata["ma_nganh"] = item.get("ma_nganh", "")
                if "ten_nganh" in item:
                    metadata["ten_nganh"] = item.get("ten_nganh", "")

            docs.append(Document(page_content=content, metadata=metadata))

    return docs


def update_knowledge_status(filename, enabled):
    """Cập nhật trạng thái enabled/disabled của một file tri thức."""
    knowledge_config = safe_read_json(KNOWLEDGE_CONFIG_FILE, default={})
    if filename in knowledge_config:
        knowledge_config[filename]["enabled"] = enabled
        safe_write_json(KNOWLEDGE_CONFIG_FILE, knowledge_config)


def delete_knowledge_file(filename):
    """Xóa một file tri thức và cập nhật config tương ứng."""
    # Xóa file vật lý
    file_path = KNOWLEDGE_DIR / filename
    if file_path.exists():
        os.remove(file_path)

    # Xóa khỏi config
    knowledge_config = safe_read_json(KNOWLEDGE_CONFIG_FILE, default={})
    if filename in knowledge_config:
        del knowledge_config[filename]
        safe_write_json(KNOWLEDGE_CONFIG_FILE, knowledge_config)


def upload_knowledge_file(filename, content):
    """Tải lên (tạo mới) một file tri thức và thêm vào config."""
    if not filename or not content:
        return False
    if not filename.lower().endswith((".json", ".txt")):
        return False

    # Tạo thư mục nếu chưa có
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    # Ghi file
    file_path = KNOWLEDGE_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Cập nhật config
    knowledge_config = safe_read_json(KNOWLEDGE_CONFIG_FILE, default={})
    knowledge_config[filename] = {
        "enabled": True,
        "description": "File tải lên từ Admin",
        "uploaded_at": datetime.now().isoformat(),
    }
    safe_write_json(KNOWLEDGE_CONFIG_FILE, knowledge_config)
    return True
