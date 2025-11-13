import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from config import config

logger = logging.getLogger(__name__)

# Імпортуй Base з моделей
from models.db_models import Base

class DatabaseManager:
    """Manager for database operations"""
    
    def __init__(self):
        self.engine = create_engine(
            config.db.url,
            pool_size=config.db.pool_size,
            max_overflow=config.db.max_overflow,
            echo=False  # Вимкнути SQL логування
        )
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)
    
    def get_session(self):
        return self.Session()
    
    def create_tables(self):
        """Create all tables"""
        print("🔄 Creating database tables...")
        try:
            # Простий тест підключення
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            
            # Створення таблиць
            Base.metadata.create_all(bind=self.engine)
            print("✅ Tables created successfully")
            logger.info("Database tables created successfully")
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def close_session(self):
        self.Session.remove()

# Global database instance
db_manager = DatabaseManager()

def init_db(app=None):
    if app:
        @app.teardown_appcontext
        def shutdown_session(exception=None):
            db_manager.close_session()
    
    return db_manager