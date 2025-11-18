#!/usr/bin/env python3
"""
PTPanel WebApp Bot - Запуск з окремої папки
"""
import sys
import os
import logging

# Додаємо кореневу папку проекту в шлях
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - WEBAPP_BOT - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/webapp_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Головна функція запуску WebApp бота"""
    try:
        logger.info("🎯 Starting PTPanel WebApp Bot from run_files...")
        
        # Отримуємо токен з конфігурації
        from config import config
        config.refresh_telegram_config(1)
        
        if not config.telegram.bot_tokens or len(config.telegram.bot_tokens) < 2:
            logger.error("❌ WebApp bot token not available")
            return
        
        # Використовуємо другий токен (webapp бот)
        token = config.telegram.bot_tokens[1]
        
        # Тут буде запуск WebApp бота
        logger.info(f"🤖 WebApp Bot would start with token: {token[:10]}...")
        logger.info("⚠️ WebApp Bot implementation pending...")
        
        # Заглушка - просто чекаємо
        import time
        while True:
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("⏹️ WebApp Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 WebApp Bot crashed: {e}")

if __name__ == "__main__":
    main()