"""
Tiện ích đọc/ghi file an toàn.
Cung cấp các hàm helper để thao tác với file JSON mà không bị crash.
"""
import json
from pathlib import Path


def safe_read_json(path, default=None):
    """Đọc file JSON an toàn, trả về default nếu file không tồn tại hoặc lỗi parse."""
    path = Path(path)
    if default is None:
        default = {}
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def safe_write_json(path, data):
    """Ghi dữ liệu ra file JSON an toàn, tự tạo thư mục cha nếu chưa có."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False


def parse_multiple_json(text):
    """Parse nhiều JSON objects/arrays nối tiếp nhau trong một chuỗi text.
    
    Hữu ích khi file chứa nhiều JSON objects không được bọc trong array.
    """
    decoder = json.JSONDecoder()
    index = 0
    results = []
    length = len(text)
    while index < length:
        # Bỏ qua khoảng trắng
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
