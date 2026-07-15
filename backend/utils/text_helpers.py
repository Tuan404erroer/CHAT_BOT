"""
Tiện ích xử lý text và JSON data.
Chuyển đổi cấu trúc JSON thành văn bản phẳng cho RAG indexing.
"""
import json
from utils.file_helpers import parse_multiple_json


def flatten_json_to_text(data):
    """Chuyển đổi cấu trúc JSON lồng nhau thành văn bản phẳng dễ đọc.
    
    Ví dụ:
        {"ten_nganh": "CNTT", "hoc_phi": 5000000}
        -> "Ten nganh: CNTT\nHoc phi: 5000000"
    """
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


def load_json_items(path):
    """Load danh sách items từ file JSON.
    
    Hỗ trợ:
    - File JSON chuẩn (object hoặc array)
    - File chứa nhiều JSON objects nối tiếp
    - File text thuần (trả về [text])
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw_data = json.load(handle)
    except json.JSONDecodeError:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                raw_text = handle.read()
        except Exception:
            return []
        parsed = parse_multiple_json(raw_text)
        if parsed:
            return parsed
        if raw_text.strip():
            return [raw_text]
        return []
    except Exception:
        return []

    if isinstance(raw_data, list):
        return raw_data
    return [raw_data]
