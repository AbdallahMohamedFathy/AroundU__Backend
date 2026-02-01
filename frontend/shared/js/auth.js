// Authentication Helper Functions

// Check if user is logged in
function isLoggedIn() {
    return localStorage.getItem('access_token') !== null;
}

// Redirect to login if not authenticated
function requireAuth() {
    if (!isLoggedIn()) {
        window.location.href = 'index.html';
        return false;
    }
    return true;
}

// Get current user from localStorage
function getCurrentUser() {
    const userStr = localStorage.getItem('current_user');
    return userStr ? JSON.parse(userStr) : null;
}

// Save current user to localStorage
function saveCurrentUser(user) {
    localStorage.setItem('current_user', JSON.stringify(user));
}

// Clear user data and logout
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('current_user');
    window.location.href = 'index.html';
}

// Show success message
function showSuccess(message) {
    showMessage(message, 'success');
}

// Show error message
function showError(message) {
    showMessage(message, 'error');
}

// Show message helper
function showMessage(message, type = 'info') {
    // Remove existing messages
    const existing = document.querySelector('.message-toast');
    if (existing) {
        existing.remove();
    }

    // Create message element
    const messageEl = document.createElement('div');
    messageEl.className = `message-toast ${type}`;
    messageEl.textContent = message;
    document.body.appendChild(messageEl);

    // Auto remove after 3 seconds
    setTimeout(() => {
        messageEl.classList.add('fade-out');
        setTimeout(() => messageEl.remove(), 300);
    }, 3000);
}

// Show loading state
function showLoading(button) {
    button.disabled = true;
    button.dataset.originalText = button.textContent;
    button.innerHTML = '<span class="spinner"></span> Loading...';
}

// Hide loading state
function hideLoading(button) {
    button.disabled = false;
    button.textContent = button.dataset.originalText;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

// Validate email
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}
