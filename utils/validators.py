import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))

def validate_proxy_config(proxy_config: dict) -> bool:
    """Validate proxy configuration"""
    required_fields = ['type', 'host', 'port']
    
    if not isinstance(proxy_config, dict):
        return False
    
    for field in required_fields:
        if field not in proxy_config:
            return False
    
    if proxy_config['type'] not in ['socks5', 'http', 'https']:
        return False
    
    try:
        port = int(proxy_config['port'])
        if not (1 <= port <= 65535):
            return False
    except (ValueError, TypeError):
        return False
    
    return True

def validate_session_string(session_string: str) -> bool:
    """Validate Telegram session string format"""
    if not session_string or len(session_string) < 10:
        return False
    
    try:
        import base64
        base64.b64decode(session_string + '===')
        return True
    except:
        return False

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal"""
    import os
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\-_.]', '_', filename)
    return filename