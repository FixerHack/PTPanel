# core/qr_manager.py
import asyncio
import logging
import secrets
from base64 import urlsafe_b64encode
from datetime import datetime

logger = logging.getLogger(__name__)

class QRManager:
    """Менеджер для QR авторизації"""
    
    def __init__(self):
        self.active_sessions = {}  # session_id -> дані сесії
        logger.info("QRManager initialized")
    
    def generate_qr_session(self):
        """Генерація нової QR сесії"""
        try:
            # Генеруємо унікальний токен
            token = secrets.token_urlsafe(32)
            session_id = secrets.token_urlsafe(16)
            
            # Створюємо дані сесії
            session_data = {
                'session_id': session_id,
                'token': token,
                'status': 'waiting',  # waiting, authorized, expired
                'created_at': datetime.utcnow(),
                'account_data': None
            }
            
            # Зберігаємо сесію
            self.active_sessions[session_id] = session_data
            
            # Створюємо QR код для Telegram
            qr_token = urlsafe_b64encode(token.encode()).decode('utf-8')
            qr_data = f"tg://login?token={qr_token}"
            
            logger.info(f"Generated QR session: {session_id}")
            
            return {
                'session_id': session_id,
                'qr_data': qr_data,
                'token': token
            }
            
        except Exception as e:
            logger.error(f"QR session generation error: {e}")
            raise
    
    def check_session_status(self, session_id):
        """Перевірка статусу сесії"""
        if session_id not in self.active_sessions:
            return {'status': 'expired', 'message': 'Сесія не знайдена або прострочена'}
        
        session = self.active_sessions[session_id]
        
        # Перевіряємо чи не прострочена сесія (30 хвилин)
        time_diff = datetime.utcnow() - session['created_at']
        if time_diff.total_seconds() > 1800:  # 30 хвилин
            session['status'] = 'expired'
            return {'status': 'expired', 'message': 'QR код прострочено'}
        
        return {
            'status': session['status'],
            'session_id': session_id,
            'account_data': session.get('account_data')
        }
    
    def authorize_session(self, session_id, account_data):
        """Авторизація сесії після сканування QR"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['status'] = 'authorized'
            self.active_sessions[session_id]['account_data'] = account_data
            logger.info(f"Session authorized: {session_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Очищення прострочених сесій"""
        expired_keys = []
        for session_id, session in self.active_sessions.items():
            time_diff = datetime.utcnow() - session['created_at']
            if time_diff.total_seconds() > 1800:  # 30 хвилин
                expired_keys.append(session_id)
        
        for key in expired_keys:
            del self.active_sessions[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired sessions")

# Глобальний екземпляр
qr_manager = QRManager()