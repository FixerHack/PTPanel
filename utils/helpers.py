import os
import json
import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)

def generate_unique_id() -> str:
    """Generate unique ID for clients"""
    return datetime.now().strftime("%Y%m%d%H%M%S%f")

def save_uploaded_file(file, upload_dir: str, filename: str = None) -> str:
    """Save uploaded file to directory"""
    try:
        os.makedirs(upload_dir, exist_ok=True)
        
        if not filename:
            filename = f"{generate_unique_id()}_{file.filename}"
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        logger.info(f"File saved: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise

def read_json_file(file_path: str) -> Dict[str, Any]:
    """Read JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read JSON file {file_path}: {e}")
        return {}

def write_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """Write data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to write JSON file {file_path}: {e}")
        return False

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Failed to get file size {file_path}: {e}")
        return 0

def format_file_size(size_bytes: int) -> str:
    """Format file size to human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    import re
    pattern = r'^\+?[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone))

def get_client_ip(request) -> str:
    """Get client IP address from request"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr