#!/usr/bin/env python3
"""
PTPanel Classic Bot - Запуск з окремої папки
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
    format='%(asctime)s - CLASSIC_BOT - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/classic_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Головна функція запуску Classic бота"""
    try:
        logger.info("🎯 Starting PTPanel Classic Bot from run_files...")
        
        # Отримуємо токен з конфігурації
        from config import config
        config.refresh_telegram_config(1)
        
        if not config.telegram.bot_tokens or len(config.telegram.bot_tokens) < 3:
            logger.error("❌ Classic bot token not available")
            return
        
        # Використовуємо третій токен (classic бот)
        token = config.telegram.bot_tokens[2]
        
        # Тут буде запуск Classic бота
        logger.info(f"🤖 Classic Bot would start with token: {token[:10]}...")
        logger.info("⚠️ Classic Bot implementation pending...")
        
        # Заглушка - просто чекаємо
        import time
        while True:
            time.sleep(10)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Classic Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Classic Bot crashed: {e}")

if __name__ == "__main__":
    main()