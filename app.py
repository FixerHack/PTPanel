import os
import logging
from flask import Flask, render_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Application factory function for PTPanel"""
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config.server)
    
    # Додаємо SECRET_KEY для сесій
    app.config['SECRET_KEY'] = config.server.secret_key
    app.config['APP_NAME'] = "PTPanel"

    # Після реєстрації admin_bp
    from web.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize extensions
    from core.database import init_db
    init_db(app)
    
    # Register blueprints
    from web.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Basic routes
    @app.route('/')
    def index():
        return render_template('index.html', app_name="PTPanel")
    
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'PTPanel'}
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html', app_name="PTPanel"), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html', app_name="PTPanel"), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    logger.info(f"Starting PTPanel on {config.server.host}:{config.server.port}")
    app.run(
        host=config.server.host,
        port=config.server.port,
        debug=config.server.debug
    )