"""
Service quản lý System Prompts.
Đọc/ghi file prompts.json cho RAG pipeline.
"""
from models.constants import SYSTEM_PROMPT_FILE, DEFAULT_PROMPTS
from utils.file_helpers import safe_read_json, safe_write_json


def get_system_prompts():
    """Lấy toàn bộ dictionary các prompt từ file cấu hình."""
    data = safe_read_json(SYSTEM_PROMPT_FILE, default=None)
    if data is None:
        return DEFAULT_PROMPTS.copy()
    return data


def get_system_prompt(prompt_key="DEFAULT"):
    """Lấy nội dung text của 1 prompt cụ thể (mặc định lấy DEFAULT)."""
    prompts = get_system_prompts()
    if prompt_key in prompts:
        return prompts[prompt_key]["content"]
    return DEFAULT_PROMPTS["DEFAULT"]["content"]


def save_system_prompts(prompts_dict):
    """Lưu toàn bộ dictionary prompts ra file."""
    return safe_write_json(SYSTEM_PROMPT_FILE, prompts_dict)
