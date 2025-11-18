#!/usr/bin/env python3
"""
Запуск адмін бота - простий синхронний запуск
"""
import logging
import sys
import os

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - ADMIN_BOT - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/admin_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Головна функція запуску"""
    try:
        # Додаємо шлях для імпортів
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from bots.admin_bot import AdminBot, find_admin_token
        
        logger.info("🎯 Starting PTPanel Admin Bot...")
        
        # Отримуємо токен конкретно з BOT_ADMIN_TOKEN
        token = find_admin_token()
        if not token:
            logger.error("❌ No valid BOT_ADMIN_TOKEN found")
            return
        
        # Створюємо та запускаємо бота
        bot = AdminBot(token)
        bot.start_bot()
        
    except KeyboardInterrupt:
        logger.info("⏹️ Admin Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Admin Bot crashed: {e}")

if __name__ == "__main__":
    main()