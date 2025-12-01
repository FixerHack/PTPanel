// static/js/devices.js
class DevicesManager {
    constructor() {
        this.currentAccountId = null;
    }

    // Завантаження списку акаунтів
    loadAccounts() {
        fetch('/admin/api/accounts')
            .then(response => response.json())
            .then(data => {
                this.displayAccounts(data.accounts);
            })
            .catch(error => {
                console.error('Помилка завантаження акаунтів:', error);
                this.showNoAccountsMessage();
            });
    }

    // Відображення акаунтів в таблиці
    displayAccounts(accounts) {
        const tableBody = document.getElementById('accountsList');
        const countBadge = document.getElementById('accountsCount');
        
        if (!accounts || accounts.length === 0) {
            this.showNoAccountsMessage();
            return;
        }

        // Оновлюємо кількість
        countBadge.textContent = `${accounts.length} акаунтів`;

        // Очищаємо таблицю
        tableBody.innerHTML = '';

        // Додаємо кожен акаунт
        accounts.forEach(account => {
            const row = this.createAccountRow(account);
            tableBody.appendChild(row);
        });

        // Ховаємо повідомлення "немає акаунтів"
        document.getElementById('noAccountsMessage').style.display = 'none';
        document.getElementById('accountsTable').style.display = 'table';
    }

    // Створення рядка для акаунта
    createAccountRow(account) {
        const row = document.createElement('tr');
        
        // Форматуємо дату
        const lastActivity = account.last_activity 
            ? new Date(account.last_activity).toLocaleString('uk-UA')
            : 'Немає';
        
        // Статус
        const statusBadge = account.is_authorized 
            ? '<span class="badge bg-success">Активний</span>'
            : '<span class="badge bg-warning">Не авторизовано</span>';
        
        row.innerHTML = `
            <td>${account.id}</td>
            <td>${account.phone || 'Н/Д'}</td>
            <td>${statusBadge}</td>
            <td>${account.app_id || 'Н/Д'}</td>
            <td>${lastActivity}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="devicesManager.showAccountActions(${account.id}, '${account.phone || ''}')">
                        <i class="fas fa-cog"></i>
                    </button>
                    <button class="btn btn-outline-success" onclick="devicesManager.testAccount(${account.id})">
                        <i class="fas fa-wifi"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="devicesManager.deleteAccount(${account.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        return row;
    }

    showNoAccountsMessage() {
        document.getElementById('loadingRow').style.display = 'none';
        document.getElementById('accountsTable').style.display = 'none';
        document.getElementById('noAccountsMessage').style.display = 'block';
        document.getElementById('accountsCount').textContent = '0 акаунтів';
    }

    // Додавання через номер телефону
    addAccountByPhone() {
        const form = document.getElementById('phoneForm');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        
        const btn = document.getElementById('phoneSubmitBtn');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Обробка...';
        btn.disabled = true;

        fetch('/admin/api/add_account/phone', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                if (result.requires_code) {
                    // Потрібен код
                    document.getElementById('codeSection').style.display = 'block';
                    document.getElementById('phoneSubmitBtn').innerHTML = '<i class="fas fa-key"></i> Ввести код';
                    this.showAlert('Введіть код з Telegram', 'info', 'phoneStatus');
                } else if (result.requires_password) {
                    // Потрібен пароль 2FA
                    document.getElementById('passwordSection').style.display = 'block';
                    document.getElementById('phoneSubmitBtn').innerHTML = '<i class="fas fa-lock"></i> Ввести пароль';
                    this.showAlert('Введіть пароль двофакторної авторизації', 'info', 'phoneStatus');
                } else {
                    // Успішно додано
                    this.showAlert('Акаунт успішно додано!', 'success', 'phoneStatus');
                    setTimeout(() => {
                        bootstrap.Modal.getInstance(document.getElementById('phoneModal')).hide();
                        this.loadAccounts();
                    }, 2000);
                }
            } else {
                this.showAlert(`Помилка: ${result.error}`, 'danger', 'phoneStatus');
            }
        })
        .catch(error => {
            this.showAlert(`Помилка: ${error}`, 'danger', 'phoneStatus');
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        });
    }

    // Додавання через Tdata
    addAccountByTdata() {
        const form = document.getElementById('tdataForm');
        const formData = new FormData(form);
        
        fetch('/admin/api/add_account/tdata', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.showAlert('Tdata архів успішно оброблено!', 'success', 'tdataStatus');
                setTimeout(() => {
                    bootstrap.Modal.getInstance(document.getElementById('tdataModal')).hide();
                    this.loadAccounts();
                }, 2000);
            } else {
                this.showAlert(`Помилка: ${result.error}`, 'danger', 'tdataStatus');
            }
        })
        .catch(error => {
            this.showAlert(`Помилка: ${error}`, 'danger', 'tdataStatus');
        });
    }

    // Додавання через Session файл
    addAccountBySession() {
        const form = document.getElementById('sessionForm');
        const formData = new FormData(form);
        
        fetch('/admin/api/add_account/session', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.showAlert('Session файл успішно завантажено!', 'success', 'sessionStatus');
                setTimeout(() => {
                    bootstrap.Modal.getInstance(document.getElementById('sessionModal')).hide();
                    this.loadAccounts();
                }, 2000);
            } else {
                this.showAlert(`Помилка: ${result.error}`, 'danger', 'sessionStatus');
            }
        })
        .catch(error => {
            this.showAlert(`Помилка: ${error}`, 'danger', 'sessionStatus');
        });
    }

    // Показ модального вікна дій з акаунтом
    showAccountActions(accountId, phone) {
        this.currentAccountId = accountId;
        document.getElementById('accountPhone').textContent = phone || `ID: ${accountId}`;
        
        const modal = new bootstrap.Modal(document.getElementById('accountActionsModal'));
        modal.show();
    }

    // Тестування підключення
    testAccount(accountId) {
        fetch(`/admin/api/account/${accountId}/test`)
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    this.showAlert('Підключення успішне!', 'success');
                } else {
                    this.showAlert(`Помилка підключення: ${result.error}`, 'danger');
                }
            })
            .catch(error => {
                this.showAlert(`Помилка: ${error}`, 'danger');
            });
    }

    // Видалення акаунта
    deleteAccount(accountId) {
        if (!confirm('Видалити цей акаунт? Цю дію не можна скасувати.')) {
            return;
        }

        fetch(`/admin/api/account/${accountId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                this.showAlert('Акаунт видалено', 'success');
                this.loadAccounts();
                // Закриваємо модальне вікно дій якщо відкрите
                const actionsModal = bootstrap.Modal.getInstance(document.getElementById('accountActionsModal'));
                if (actionsModal) actionsModal.hide();
            } else {
                this.showAlert(`Помилка: ${result.error}`, 'danger');
            }
        })
        .catch(error => {
            this.showAlert(`Помилка: ${error}`, 'danger');
        });
    }

    // Утиліти
    showAlert(message, type, containerId = null) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        if (containerId) {
            const container = document.getElementById(containerId);
            container.innerHTML = '';
            container.appendChild(alertDiv);
        } else {
            const mainContent = document.querySelector('.main-content');
            mainContent.insertBefore(alertDiv, mainContent.firstChild);
        }
        
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Глобальний екземпляр
let devicesManager = new DevicesManager();

// Глобальні функції для HTML
function loadAccounts() {
    devicesManager.loadAccounts();
}

function showAccountActions(accountId, phone) {
    devicesManager.showAccountActions(accountId, phone);
}

function testAccount(accountId) {
    devicesManager.testAccount(accountId);
}

function deleteAccount(accountId) {
    devicesManager.deleteAccount(accountId);
}