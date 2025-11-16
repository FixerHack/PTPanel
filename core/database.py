# core/database.py
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from config import config

logger = logging.getLogger(__name__)

# Імпортуємо Base з моделей
from models.db_models import Base

class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self):
        self.engine = create_engine(
            config.db.url,
            pool_size=config.db.pool_size,
            max_overflow=config.db.max_overflow,
            echo=config.db.echo
        )
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
    
    def get_session(self):
        """Get database session"""
        return self.Session()
    
    def create_tables(self):
        """Create all tables"""
        logger.info("Creating database tables...")
        try:
            # Тест підключення
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            
            # Створення таблиць
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def close_session(self):
        """Close database session"""
        self.Session.remove()

# Global database instance
db_manager = DatabaseManager()

def init_db(app=None):
    """Initialize database for Flask app"""
    if app:
        @app.teardown_appcontext
        def shutdown_session(exception=None):
            db_manager.close_session()
    
    return db_manager