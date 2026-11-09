/**
 * Authentication — Login & Register Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // If already logged in, redirect to dashboard
    const token = localStorage.getItem('auth_token');
    if (token) {
        window.location.href = '/dashboard.html';
        return;
    }

    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const showRegisterBtn = document.getElementById('show-register');
    const showLoginBtn = document.getElementById('show-login');
    const loginCard = document.getElementById('login-card');
    const registerCard = document.getElementById('register-card');

    // Toggle between login and register
    if (showRegisterBtn) {
        showRegisterBtn.addEventListener('click', (e) => {
            e.preventDefault();
            loginCard.classList.add('hidden');
            registerCard.classList.remove('hidden');
        });
    }

    if (showLoginBtn) {
        showLoginBtn.addEventListener('click', (e) => {
            e.preventDefault();
            registerCard.classList.add('hidden');
            loginCard.classList.remove('hidden');
        });
    }

    // Login handler
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('login-username').value.trim();
            const password = document.getElementById('login-password').value;
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            const btnText = submitBtn.innerHTML;

            if (!username || !password) {
                showToast('Please enter username and password', 'warning');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span> Signing in...';

            const result = await api.login(username, password);

            if (result && result.status === 'success') {
                localStorage.setItem('auth_token', result.token);
                localStorage.setItem('user', JSON.stringify(result.user));
                showToast('Login successful! Redirecting...', 'success');
                setTimeout(() => {
                    window.location.href = '/dashboard.html';
                }, 500);
            } else {
                showToast(result?.message || 'Login failed', 'error');
                submitBtn.disabled = false;
                submitBtn.innerHTML = btnText;
            }
        });
    }

    // Register handler
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const full_name = document.getElementById('reg-fullname').value.trim();
            const username = document.getElementById('reg-username').value.trim();
            const email = document.getElementById('reg-email').value.trim();
            const password = document.getElementById('reg-password').value;
            const submitBtn = registerForm.querySelector('button[type="submit"]');
            const btnText = submitBtn.innerHTML;

            if (!full_name || !username || !email || !password) {
                showToast('Please fill in all fields', 'warning');
                return;
            }

            if (password.length < 6) {
                showToast('Password must be at least 6 characters', 'warning');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span> Creating account...';

            const result = await api.register({ full_name, username, email, password });

            if (result && result.status === 'success') {
                showToast('Account created! Please login.', 'success');
                registerCard.classList.add('hidden');
                loginCard.classList.remove('hidden');
            } else {
                showToast(result?.message || 'Registration failed', 'error');
            }

            submitBtn.disabled = false;
            submitBtn.innerHTML = btnText;
        });
    }
});
