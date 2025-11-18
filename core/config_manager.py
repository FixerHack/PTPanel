# core/config_manager.py - ПОВНА ВИПРАВЛЕНА ВЕРСІЯ
import logging
import json
import os
from typing import Dict, Any, Optional
from core.database import db_manager
from models.db_models import UserConfig, Admin
from core.security import encryption_manager
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self):
        self.default_configs = {
            'telegram': {
                'api_id': '',
                'api_hash': '',
                'phone_number': ''
            },
            'server': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': True
            },
            'bots': {
                'webapp_token': '',
                'classic_token': '',
                'multitool_token': '',
                'admin_token': ''
            },
            'additional': {
                'ngrok_auth_token': '',
                'ngrok_domain': ''
            }
        }
    
    def save_user_config(self, admin_id: int, config_type: str, config_data: Dict[str, Any]) -> bool:
        """Зберегти налаштування користувача"""
        try:
            db_session = db_manager.get_session()
            
            # Шифруємо чутливі дані для БД
            encrypted_data = self._encrypt_sensitive_data(config_type, config_data)
            
            # Перевіряємо чи існує запис
            config = db_session.query(UserConfig).filter_by(
                admin_id=admin_id, 
                config_type=config_type
            ).first()
            
            if config:
                config.config_data = encrypted_data
                config.updated_at = datetime.utcnow()
            else:
                config = UserConfig(
                    admin_id=admin_id,
                    config_type=config_type,
                    config_data=encrypted_data
                )
                db_session.add(config)
            
            db_session.commit()
            
            # Зберігаємо в JSON файл (читабельну версію без шифрування)
            self._save_to_json(admin_id, config_type, config_data)
            
            logger.info(f"Config saved for admin {admin_id}, type: {config_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            db_session.rollback()
            return False
        finally:
            db_session.close()
    
    def load_user_config(self, admin_id: int, config_type: str) -> Dict[str, Any]:
        """Завантажити налаштування користувача"""
        try:
            db_session = db_manager.get_session()
            
            config = db_session.query(UserConfig).filter_by(
                admin_id=admin_id, 
                config_type=config_type
            ).first()
            
            if config:
                # Розшифровуємо дані
                decrypted_data = self._decrypt_sensitive_data(config_type, config.config_data)
                return decrypted_data
            else:
                # Повертаємо дефолтні налаштування
                return self.default_configs.get(config_type, {})
                
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self.default_configs.get(config_type, {})
        finally:
            db_session.close()
    
    def migrate_from_env(self, admin_id: int) -> bool:
        """Міграція даних з .env файлу в БД"""
        try:
            # Telegram налаштування
            telegram_config = {
                'api_id': os.getenv('API_ID', ''),
                'api_hash': os.getenv('API_HASH', ''),
                'phone_number': os.getenv('PHONE_NUMBER', '')
            }
            self.save_user_config(admin_id, 'telegram', telegram_config)
            
            # Server налаштування
            server_config = {
                'host': os.getenv('HOST', '0.0.0.0'),
                'port': int(os.getenv('PORT', '5000')),
                'debug': os.getenv('DEBUG', 'False').lower() == 'true'
            }
            self.save_user_config(admin_id, 'server', server_config)
            
            # Bot tokens
            bots_config = {
                'webapp_token': os.getenv('BOT_WEBAPP_TOKEN', ''),
                'classic_token': os.getenv('BOT_CLASSIC_TOKEN', ''),
                'multitool_token': os.getenv('BOT_MULTITOOL_TOKEN', ''),
                'admin_token': os.getenv('BOT_ADMIN_TOKEN', '')
            }
            self.save_user_config(admin_id, 'bots', bots_config)
            
            # Additional налаштування
            additional_config = {
                'ngrok_auth_token': os.getenv('NGROK_AUTH_TOKEN', ''),
                'ngrok_domain': os.getenv('NGROK_DOMAIN', '')
            }
            self.save_user_config(admin_id, 'additional', additional_config)
            
            logger.info(f"Migration completed for admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def _encrypt_sensitive_data(self, config_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Шифрування чутливих даних для БД"""
        encrypted_data = data.copy()
        
        if config_type == 'telegram':
            if data.get('api_hash'):
                encrypted_data['api_hash'] = encryption_manager.encrypt_data(data['api_hash'])
        
        elif config_type == 'bots':
            for key in ['webapp_token', 'classic_token', 'multitool_token', 'admin_token']:
                if data.get(key):
                    encrypted_data[key] = encryption_manager.encrypt_data(data[key])
        
        elif config_type == 'additional':
            if data.get('ngrok_auth_token'):
                encrypted_data['ngrok_auth_token'] = encryption_manager.encrypt_data(data['ngrok_auth_token'])
        
        return encrypted_data
    
    def _decrypt_sensitive_data(self, config_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Розшифрування чутливих даних з БД"""
        decrypted_data = data.copy()
        
        if config_type == 'telegram':
            if data.get('api_hash'):
                try:
                    decrypted_data['api_hash'] = encryption_manager.decrypt_data(data['api_hash'])
                except:
                    decrypted_data['api_hash'] = data['api_hash']  # Якщо не зашифровано
        
        elif config_type == 'bots':
            for key in ['webapp_token', 'classic_token', 'multitool_token', 'admin_token']:
                if data.get(key):
                    try:
                        decrypted_data[key] = encryption_manager.decrypt_data(data[key])
                    except:
                        decrypted_data[key] = data[key]  # Якщо не зашифровано
        
        elif config_type == 'additional':
            if data.get('ngrok_auth_token'):
                try:
                    decrypted_data['ngrok_auth_token'] = encryption_manager.decrypt_data(data['ngrok_auth_token'])
                except:
                    decrypted_data['ngrok_auth_token'] = data['ngrok_auth_token']
        
        return decrypted_data
    
    def _save_to_json(self, admin_id: int, config_type: str, data: Dict[str, Any]):
        """Збереження в JSON файл для бекапу (читабельна версія)"""
        try:
            # Отримуємо username адміна
            db_session = db_manager.get_session()
            admin = db_session.query(Admin).filter(Admin.id == admin_id).first()
            username = admin.username if admin else f"admin_{admin_id}"
            db_session.close()
            
            # Створюємо папку з username
            config_dir = f"configs/users/{username}"
            os.makedirs(config_dir, exist_ok=True)
            
            file_path = f"{config_dir}/{config_type}.json"
            
            # Зберігаємо оригінальні дані (без шифрування)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"JSON config saved: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save JSON config: {e}")

# Глобальний екземпляр
config_manager = ConfigManager()