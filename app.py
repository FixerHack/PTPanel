import os
import logging
from flask import Flask, render_template
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    from config import config
    app.config.from_object(config.server)
    app.config['APP_NAME'] = "PTPanel"
    
    from core.database import init_db
    init_db(app)
    
    @app.route('/')
    def index():
        return render_template('index.html', app_name="PTPanel")
    
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'PTPanel'}
    
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