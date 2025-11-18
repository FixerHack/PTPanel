#!/usr/bin/env python3
"""
PTPanel Multitool Bot - Запуск з окремої папки
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
    format='%(asctime)s - MULTITOOL_BOT - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/multitool_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Головна функція запуску Multitool бота"""
    try:
        logger.info("🎯 Starting PTPanel Multitool Bot from run_files...")
        
        # Отримуємо токен з конфігурації
        from config import config
        config.refresh_telegram_config(1)
        
        if not config.telegram.bot_tokens or len(config.telegram.bot_tokens) < 4:
            logger.error("❌ Multitool bot token not available")
            return
        
        # Використовуємо четвертий токен (multitool бот)
        token = config.telegram.bot_tokens[3]
        
        # Тут буде запуск Multitool бота
        logger.info(f"🤖 Multitool Bot would start with token: {token[:10]}...")
        logger.info("⚠️ Multitool Bot implementation pending...")
        
        # Заглушка - просто чекаємо
        import time
        while True:
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Multitool Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Multitool Bot crashed: {e}")

if __name__ == "__main__":
    main()