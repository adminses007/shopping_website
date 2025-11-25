// 修改密码功能（支持所有用户）
(function() {
    'use strict';
    
    // 密码管理模块
    const PasswordManager = {
        modal: null,
        isSubmitting: false,
        timeoutId: null,
        
        // 初始化
        init: function() {
            this.initModal();
            this.bindEvents();
            this.initPasswordValidation();
        },
        
        // 初始化模态框
        initModal: function() {
            const modalElement = document.getElementById('changePasswordModal');
            if (!modalElement) return;
            
            if (typeof bootstrap === 'undefined' || !bootstrap.Modal) {
                console.error('Bootstrap Modal is not available');
                return;
            }
            
            try {
                this.modal = new bootstrap.Modal(modalElement, {
                    backdrop: true,
                    keyboard: true,
                    focus: true
                });
            } catch (e) {
                console.error('Error initializing modal:', e);
                this.modal = { element: modalElement };
            }
        },
        
        // 绑定事件
        bindEvents: function() {
            const self = this;
            const modalElement = document.getElementById('changePasswordModal');
            if (!modalElement) return;
            
            // 模态框内按钮事件
            modalElement.addEventListener('click', function(e) {
                // 取消按钮
                if (e.target.closest('#cancel-change-password-btn')) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.closeModal();
                    return false;
                }
                
                // 关闭按钮
                if (e.target.closest('#modal-close-btn')) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.closeModal();
                    return false;
                }
                
                // 提交按钮
                if (e.target.closest('#confirm-change-password-btn')) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.submitPassword();
                    return false;
                }
                
                // 密码显示/隐藏按钮
                const toggleBtn = e.target.closest('[id^="toggle-"]');
                if (toggleBtn) {
                    e.preventDefault();
                    e.stopPropagation();
                    const btnId = toggleBtn.id;
                    if (btnId === 'toggle-old-password') {
                        self.togglePasswordVisibility('old-password', 'old-password-eye-icon');
                    } else if (btnId === 'toggle-new-password') {
                        self.togglePasswordVisibility('new-password', 'new-password-eye-icon');
                    } else if (btnId === 'toggle-confirm-password') {
                        self.togglePasswordVisibility('confirm-new-password', 'confirm-password-eye-icon');
                    }
                    return false;
                }
            });
            
            // 表单提交事件
            const form = document.getElementById('change-password-form');
            if (form) {
                form.addEventListener('submit', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    self.submitPassword();
                    return false;
                });
            }
            
            // 模态框关闭时清理
            modalElement.addEventListener('hidden.bs.modal', function() {
                self.resetForm();
            });
        },
        
        // 切换密码可见性
        togglePasswordVisibility: function(inputId, iconId) {
            const input = document.getElementById(inputId);
            const icon = document.getElementById(iconId);
            if (input && icon) {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                icon.classList.toggle('fa-eye');
                icon.classList.toggle('fa-eye-slash');
            }
        },
        
        // 初始化密码验证
        initPasswordValidation: function() {
            const newPasswordInput = document.getElementById('new-password');
            const confirmPasswordInput = document.getElementById('confirm-new-password');
            
            if (newPasswordInput) {
                newPasswordInput.addEventListener('input', this.validatePasswordStrength.bind(this));
                newPasswordInput.addEventListener('blur', this.validatePasswordStrength.bind(this));
            }
            
            if (confirmPasswordInput) {
                confirmPasswordInput.addEventListener('input', this.validatePasswordMatch.bind(this));
                confirmPasswordInput.addEventListener('blur', this.validatePasswordMatch.bind(this));
            }
        },
        
        // 验证密码强度
        validatePasswordStrength: function() {
            const input = document.getElementById('new-password');
            const strengthDiv = document.getElementById('password-strength');
            const strengthBar = document.getElementById('strength-bar');
            const strengthText = document.getElementById('strength-text');
            
            if (!input || !strengthDiv || !strengthBar || !strengthText) return;
            
            const password = input.value;
            
            if (password.length === 0) {
                strengthDiv.style.display = 'none';
                return;
            }
            
            strengthDiv.style.display = 'block';
            
            let strength = 0;
            let text = '';
            let color = '';
            
            if (password.length >= 6) strength += 25;
            if (password.length >= 8) strength += 25;
            if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength += 25;
            if (/\d/.test(password)) strength += 15;
            if (/[^a-zA-Z0-9]/.test(password)) strength += 10;
            
            if (strength < 40) {
                text = 'weak';
                color = 'bg-danger';
            } else if (strength < 70) {
                text = 'medium';
                color = 'bg-warning';
            } else {
                text = 'powerful';
                color = 'bg-success';
            }
            
            strengthBar.style.width = strength + '%';
            strengthBar.className = 'progress-bar ' + color;
            strengthText.textContent = 'Password strength: ' + text;
        },
        
        // 验证密码匹配
        validatePasswordMatch: function() {
            const newPassword = document.getElementById('new-password');
            const confirmPassword = document.getElementById('confirm-new-password');
            const matchDiv = document.getElementById('confirm-password-match');
            const feedback = document.getElementById('confirm-password-feedback');
            
            if (!newPassword || !confirmPassword) return;
            
            const newPwd = newPassword.value;
            const confirmPwd = confirmPassword.value;
            
            if (confirmPwd.length === 0) {
                if (matchDiv) matchDiv.style.display = 'none';
                if (feedback) feedback.textContent = '';
                confirmPassword.classList.remove('is-valid', 'is-invalid');
                return;
            }
            
            if (newPwd === confirmPwd) {
                confirmPassword.classList.remove('is-invalid');
                confirmPassword.classList.add('is-valid');
                if (matchDiv) matchDiv.style.display = 'block';
                if (feedback) feedback.textContent = '';
            } else {
                confirmPassword.classList.remove('is-valid');
                confirmPassword.classList.add('is-invalid');
                if (matchDiv) matchDiv.style.display = 'none';
                if (feedback) feedback.textContent = 'Password mismatch';
            }
        },
        
        // 显示错误消息
        showError: function(message) {
            const errorDiv = document.getElementById('password-error-message');
            const errorText = document.getElementById('error-text');
            if (errorDiv && errorText) {
                errorText.textContent = message;
                errorDiv.classList.remove('d-none');
                clearTimeout(this.timeoutId);
                this.timeoutId = setTimeout(function() {
                    errorDiv.classList.add('d-none');
                }, 3000);
            }
        },
        
        // 隐藏错误消息
        hideError: function() {
            const errorDiv = document.getElementById('password-error-message');
            if (errorDiv) {
                errorDiv.classList.add('d-none');
            }
        },
        
        // 打开模态框
        openModal: function() {
            if (this.isSubmitting) return;
            
            this.hideError();
            this.resetForm();
            
            const modalElement = document.getElementById('changePasswordModal');
            if (!modalElement) return;
            
            try {
                // 确保按钮可点击
                const buttons = modalElement.querySelectorAll('button');
                buttons.forEach(function(btn) {
                    btn.style.pointerEvents = 'auto';
                    btn.style.cursor = 'pointer';
                    btn.style.zIndex = '9999';
                    btn.disabled = false;
                    btn.classList.remove('disabled');
                });
                
                // 监听模态框显示完成事件
                const shownHandler = function() {
                    const buttons = modalElement.querySelectorAll('button');
                    buttons.forEach(function(btn) {
                        btn.style.pointerEvents = 'auto';
                        btn.style.cursor = 'pointer';
                        btn.style.zIndex = '99999';
                        btn.disabled = false;
                        btn.classList.remove('disabled');
                    });
                    modalElement.removeEventListener('shown.bs.modal', shownHandler);
                };
                modalElement.addEventListener('shown.bs.modal', shownHandler, { once: true });
                
                if (this.modal && typeof this.modal.show === 'function') {
                    this.modal.show();
                } else if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    const modal = bootstrap.Modal.getInstance(modalElement) || 
                                 new bootstrap.Modal(modalElement, {
                                     backdrop: true,
                                     keyboard: true,
                                     focus: true
                                 });
                    this.modal = modal;
                    modal.show();
                } else {
                    // 降级：直接显示
                    modalElement.classList.add('show');
                    modalElement.style.display = 'block';
                    document.body.classList.add('modal-open');
                    const backdrop = document.createElement('div');
                    backdrop.className = 'modal-backdrop fade show';
                    backdrop.style.zIndex = '1040';
                    document.body.appendChild(backdrop);
                    setTimeout(shownHandler, 50);
                }
                
                // 聚焦到第一个输入框
                setTimeout(function() {
                    const firstInput = document.getElementById('old-password');
                    if (firstInput) {
                        firstInput.focus();
                    }
                }, 300);
            } catch (e) {
                console.error('Error opening modal:', e);
                this.showError('Unable to open dialog box, please refresh the page and try again.');
            }
        },
        
        // 关闭模态框
        closeModal: function() {
            const modalElement = document.getElementById('changePasswordModal');
            if (!modalElement) return;
            
            try {
                if (this.modal && typeof this.modal.hide === 'function') {
                    this.modal.hide();
                } else if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
                    const modal = bootstrap.Modal.getInstance(modalElement);
                    if (modal) {
                        modal.hide();
                    } else {
                        this.forceCloseModal();
                    }
                } else {
                    this.forceCloseModal();
                }
            } catch (e) {
                console.error('Error closing modal:', e);
                this.forceCloseModal();
            }
            
            this.resetForm();
        },
        
        // 强制关闭模态框
        forceCloseModal: function() {
            const modalElement = document.getElementById('changePasswordModal');
            if (modalElement) {
                modalElement.classList.remove('show');
                modalElement.style.display = 'none';
            }
            document.body.classList.remove('modal-open');
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(function(backdrop) {
                backdrop.remove();
            });
        },
        
        // 重置表单
        resetForm: function() {
            const form = document.getElementById('change-password-form');
            if (form) {
                form.reset();
            }
            
            const inputs = ['old-password', 'new-password', 'confirm-new-password'];
            inputs.forEach(function(id) {
                const input = document.getElementById(id);
                if (input) {
                    input.classList.remove('is-valid', 'is-invalid');
                    if (input.type === 'text') {
                        input.type = 'password';
                    }
                }
            });
            
            const strengthDiv = document.getElementById('password-strength');
            if (strengthDiv) {
                strengthDiv.style.display = 'none';
            }
            
            const matchDiv = document.getElementById('confirm-password-match');
            if (matchDiv) {
                matchDiv.style.display = 'none';
            }
            
            this.setButtonState(false);
            this.hideError();
        },
        
        // 设置按钮状态
        setButtonState: function(disabled) {
            const submitBtn = document.getElementById('confirm-change-password-btn');
            const cancelBtn = document.getElementById('cancel-change-password-btn');
            const submitText = document.getElementById('submit-btn-text');
            
            if (submitBtn) {
                submitBtn.disabled = disabled;
            }
            if (cancelBtn) {
                cancelBtn.disabled = disabled;
            }
            
            if (submitText) {
                submitText.textContent = disabled ? 'Changing...' : 'change password';
            }
            
            if (submitBtn) {
                if (disabled) {
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span id="submit-btn-text">Changing...</span>';
                } else {
                    submitBtn.innerHTML = '<i class="fas fa-save"></i> <span id="submit-btn-text">change password</span>';
                }
            }
        },
        
        // 验证表单
        validateForm: function() {
            const userIdEl = document.getElementById('change-password-user-id');
            const oldPasswordEl = document.getElementById('old-password');
            const newPasswordEl = document.getElementById('new-password');
            const confirmPasswordEl = document.getElementById('confirm-new-password');
            
            if (!userIdEl || !oldPasswordEl || !newPasswordEl || !confirmPasswordEl) {
                this.showError('Form elements missing, please refresh the page');
                return false;
            }
            
            const userId = parseInt(userIdEl.value);
            const oldPassword = oldPasswordEl.value.trim();
            const newPassword = newPasswordEl.value.trim();
            const confirmPassword = confirmPasswordEl.value.trim();
            
            if (!userId || userId <= 0) {
                this.showError('Invalid user ID');
                return false;
            }
            
            if (!oldPassword) {
                this.showError('Please enter the current password');
                oldPasswordEl.classList.add('is-invalid');
                oldPasswordEl.focus();
                return false;
            }
            
            if (!newPassword) {
                this.showError('Please enter the new password');
                newPasswordEl.classList.add('is-invalid');
                newPasswordEl.focus();
                return false;
            }
            
            if (newPassword.length < 6) {
                this.showError('The new password must be at least 6 characters');
                newPasswordEl.classList.add('is-invalid');
                newPasswordEl.focus();
                return false;
            }
            
            if (!confirmPassword) {
                this.showError('Please confirm the new password');
                confirmPasswordEl.classList.add('is-invalid');
                confirmPasswordEl.focus();
                return false;
            }
            
            if (newPassword !== confirmPassword) {
                this.showError('The two passwords do not match');
                confirmPasswordEl.classList.add('is-invalid');
                confirmPasswordEl.focus();
                return false;
            }
            
            if (oldPassword === newPassword) {
                this.showError('The new password must be different from the current password');
                newPasswordEl.classList.add('is-invalid');
                newPasswordEl.focus();
                return false;
            }
            
            return true;
        },
        
        // 提交密码更改
        submitPassword: function() {
            if (this.isSubmitting) {
                return false;
            }
            
            this.hideError();
            
            if (!this.validateForm()) {
                return false;
            }
            
            const userIdEl = document.getElementById('change-password-user-id');
            const oldPasswordEl = document.getElementById('old-password');
            const newPasswordEl = document.getElementById('new-password');
            
            const userId = parseInt(userIdEl.value);
            const oldPassword = oldPasswordEl.value.trim();
            const newPassword = newPasswordEl.value.trim();
            
            this.isSubmitting = true;
            this.setButtonState(true);
            
            const timeoutPromise = new Promise(function(_, reject) {
                setTimeout(function() {
                    reject(new Error('Request timeout, please check the network connection'));
                }, 30000);
            });
            
            // 使用通用密码修改接口（支持所有用户）
            const fetchPromise = fetch('/change_password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: userId,
                    old_password: oldPassword,
                    new_password: newPassword
                })
            });
            
            Promise.race([fetchPromise, timeoutPromise])
                .then(function(response) {
                    if (!response || !response.ok) {
                        throw new Error('Network request failed');
                    }
                    return response.json();
                })
                .then(function(data) {
                    if (data.success) {
                            showMessage(data.message || 'Password changed successfully', 'success');
                        setTimeout(function() {
                            PasswordManager.closeModal();
                        }, 500);
                    } else {
                        PasswordManager.showError(data.message || 'Password change failed');
                        PasswordManager.setButtonState(false);
                        PasswordManager.isSubmitting = false;
                    }
                })
                .catch(function(error) {
                    console.error('Error:', error);
                    const errorMsg = error.message || 'Operation failed, please try again later.';
                    PasswordManager.showError(errorMsg);
                    PasswordManager.setButtonState(false);
                    PasswordManager.isSubmitting = false;
                });
            
            return false;
        }
    };
    
    // 全局函数：打开修改密码模态框
    window.openChangePasswordModal = function() {
        PasswordManager.openModal();
    };
    
    // 页面加载完成后初始化
    function initializePasswordManager() {
        PasswordManager.init();
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializePasswordManager);
    } else {
        initializePasswordManager();
    }
})();

