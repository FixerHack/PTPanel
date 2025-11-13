#!/usr/bin/env python3
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from config import config

logger = logging.getLogger('ptpanel')

def setup_environment():
    if not os.path.exists('.env'):
        logger.warning("⚠️  .env file not found. Using default configuration.")
    
    try:
        from core.database import db_manager
        db_manager.get_session().execute("SELECT 1")
        logger.info("✅ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    
    return True

def main():
    try:
        logger.info("🚀 Starting PTPanel - Telegram Research Framework")
        
        if not setup_environment():
            sys.exit(1)
        
        app = create_app()
        
        print("\n" + "="*50)
        print("🛡️  PTPanel - Telegram Research Framework")
        print("="*50)
        print(f"📍 Local URL: http://{config.server.host}:{config.server.port}")
        print(f"🔐 Admin panel: http://{config.server.host}:{config.server.port}/admin")
        print(f"⚡ Debug mode: {config.server.debug}")
        print("="*50 + "\n")
        
        app.run(
            host=config.server.host,
            port=config.server.port,
            debug=config.server.debug
        )
        
    except KeyboardInterrupt:
        logger.info("👋 PTPanel stopped by user")
    except Exception as e:
        logger.error(f"💥 PTPanel failed to start: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()