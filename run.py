#!/usr/bin/env python3
"""
PTPanel Main Entry Point
"""
import os
import sys
import logging
from sqlalchemy import text  # ← ДОДАЙТЕ ЦЕЙ ІМПОРТ

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from config import config

# Setup logging
logger = logging.getLogger('ptpanel')

def setup_environment():
    """Setup application environment"""
    # Check if .env file exists
    if not os.path.exists('.env'):
        logger.warning("⚠️  .env file not found. Using default configuration.")
    
    # Check database connection
    try:
        from core.database import db_manager
        
        session = db_manager.get_session()
        session.execute(text("SELECT 1"))  # ← ВИПРАВЛЕНА ЛІНІЯ
        session.close()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main application entry point for PTPanel"""
    try:
        logger.info("🚀 Starting PTPanel - Telegram Research Framework")
        
        # Setup environment
        if not setup_environment():
            sys.exit(1)
        
        # Create Flask app
        app = create_app()
        
        # Display startup information
        print("\n" + "="*50)
        print("🛡️  PTPanel - Telegram Research Framework")
        print("="*50)
        print(f"📍 Local URL: http://{config.server.host}:{config.server.port}")
        print(f"🔐 Admin panel: http://{config.server.host}:{config.server.port}/admin")
        print(f"⚡ Debug mode: {config.server.debug}")
        print("="*50 + "\n")
        
        # Start the Flask application
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
