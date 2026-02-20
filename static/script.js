// Blood Bank Pro - Professional JavaScript
class BloodBankSystem {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeComponents();
        this.setupRealTimeUpdates();
        this.initializeNotifications();
    }

    setupEventListeners() {
        // Form validations
        this.setupFormValidations();
        
        // Interactive elements
        this.setupInteractiveElements();
        
        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
        
        // Search functionality
        this.setupSearch();
    }

    initializeComponents() {
        // Initialize tooltips
        this.initTooltips();
        
        // Initialize modals
        this.initModals();
        
        // Initialize date pickers
        this.initDatePickers();
        
        // Initialize charts
        this.initCharts();
    }

    setupRealTimeUpdates() {
        // Update time every second
        setInterval(this.updateDateTime, 1000);
        
        // Check for notifications every 30 seconds
        setInterval(this.checkNotifications, 30000);
        
        // Update dashboard stats every minute
        setInterval(this.updateDashboardStats, 60000);
    }

    initializeNotifications() {
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
        
        // Setup WebSocket for real-time updates
        this.setupWebSocket();
    }

    // Tooltip System
    initTooltips() {
        const tooltips = document.querySelectorAll('[data-tooltip]');
        tooltips.forEach(element => {
            element.addEventListener('mouseenter', this.showTooltip);
            element.addEventListener('mouseleave', this.hideTooltip);
        });
    }

    showTooltip(event) {
        const tooltipText = this.dataset.tooltip;
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = tooltipText;
        
        document.body.appendChild(tooltip);
        
        const rect = this.getBoundingClientRect();
        tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
        tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;
        
        this.tooltipElement = tooltip;
    }

    hideTooltip() {
        if (this.tooltipElement) {
            this.tooltipElement.remove();
            this.tooltipElement = null;
        }
    }

    // Modal System
    initModals() {
        // Close modal on ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
        
        // Close modal on background click
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                e.target.remove();
            }
        });
    }

    showModal(title, content, buttons = []) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <h3 class="text-xl font-bold mb-4">${title}</h3>
                <div class="modal-content">${content}</div>
                ${buttons.length ? `
                    <div class="form-actions">
                        ${buttons.map(btn => `
                            <button class="btn btn-${btn.type}" onclick="${btn.onclick}">
                                ${btn.icon ? `<i class="${btn.icon}"></i>` : ''}
                                ${btn.text}
                            </button>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
        
        document.body.appendChild(modal);
        return modal;
    }

    closeAllModals() {
        document.querySelectorAll('.modal-overlay').forEach(modal => modal.remove());
    }

    // Form Validation
    setupFormValidations() {
        const forms = document.querySelectorAll('form[needs-validation]');
        forms.forEach(form => {
            form.addEventListener('submit', this.validateForm);
            
            // Real-time validation
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('input', this.validateInput);
                input.addEventListener('blur', this.validateInput);
            });
        });
    }

    validateForm(e) {
        const form = e.target;
        let isValid = true;
        
        const inputs = form.querySelectorAll('[required]');
        inputs.forEach(input => {
            if (!this.validateInput.call(input)) {
                isValid = false;
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            this.showNotification('Please fill all required fields correctly.', 'error');
        }
    }

    validateInput() {
        const input = this;
        const value = input.value.trim();
        const errorDiv = input.parentElement.querySelector('.error-message') || 
                         document.createElement('div');
        
        errorDiv.className = 'error-message text-sm text-error mt-1';
        
        let isValid = true;
        let message = '';
        
        // Check required
        if (input.required && !value) {
            isValid = false;
            message = 'This field is required';
        }
        
        // Check email
        else if (input.type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                message = 'Please enter a valid email address';
            }
        }
        
        // Check phone
        else if (input.type === 'tel' && value) {
            const phoneRegex = /^[0-9]{10}$/;
            if (!phoneRegex.test(value.replace(/\D/g, ''))) {
                isValid = false;
                message = 'Please enter a valid 10-digit phone number';
            }
        }
        
        // Check date
        else if (input.type === 'date' && value) {
            const date = new Date(value);
            if (date > new Date()) {
                isValid = false;
                message = 'Date cannot be in the future';
            }
        }
        
        // Update UI
        if (!isValid) {
            input.classList.add('border-error');
            errorDiv.textContent = message;
            if (!input.parentElement.contains(errorDiv)) {
                input.parentElement.appendChild(errorDiv);
            }
        } else {
            input.classList.remove('border-error');
            errorDiv.remove();
        }
        
        return isValid;
    }

    // Date Pickers
    initDatePickers() {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        const today = new Date().toISOString().split('T')[0];
        
        dateInputs.forEach(input => {
            // Set max date to today for DOB
            if (input.name === 'dob' || input.id === 'dob') {
                input.max = today;
            }
            
            // Add date formatting
            input.addEventListener('change', function() {
                if (this.value) {
                    const date = new Date(this.value);
                    const formatted = date.toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    });
                    
                    // Show formatted date
                    const helper = document.createElement('small');
                    helper.className = 'date-helper text-sm text-muted mt-1 block';
                    helper.textContent = formatted;
                    
                    const existingHelper = this.parentElement.querySelector('.date-helper');
                    if (existingHelper) existingHelper.remove();
                    
                    this.parentElement.appendChild(helper);
                }
            });
        });
    }

    // Charts
    initCharts() {
        // Initialize any charts on the page
        const chartContainers = document.querySelectorAll('[data-chart]');
        chartContainers.forEach(container => {
            const type = container.dataset.chart;
            this.renderChart(container, type);
        });
    }

    renderChart(container, type) {
        // Chart rendering logic
        // You can integrate Chart.js or any other chart library here
        console.log(`Rendering ${type} chart in`, container);
    }

    // Search System
    setupSearch() {
        const searchInputs = document.querySelectorAll('.search-input');
        searchInputs.forEach(input => {
            input.addEventListener('input', this.debounce(this.performSearch, 300));
        });
    }

    performSearch(event) {
        const searchTerm = event.target.value.toLowerCase();
        const tableId = event.target.dataset.searchTable;
        
        if (!tableId) return;
        
        const table = document.getElementById(tableId);
        if (!table) return;
        
        const rows = table.querySelectorAll('tbody tr');
        let visibleCount = 0;
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const isVisible = text.includes(searchTerm);
            row.style.display = isVisible ? '' : 'none';
            
            if (isVisible) {
                visibleCount++;
                row.classList.add('search-highlight');
                setTimeout(() => row.classList.remove('search-highlight'), 1000);
            }
        });
        
        // Update results count
        const countElement = table.parentElement.querySelector('.results-count');
        if (countElement) {
            countElement.textContent = `${visibleCount} results found`;
        }
    }

    // Notification System
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${this.getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add to page
        const container = document.querySelector('.notification-container') || 
                          this.createNotificationContainer();
        container.appendChild(notification);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
        
        // Browser notification
        if (Notification.permission === 'granted') {
            new Notification('Blood Bank System', {
                body: message,
                icon: '/static/favicon.ico'
            });
        }
    }

    getNotificationIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    createNotificationContainer() {
        const container = document.createElement('div');
        container.className = 'notification-container fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
        return container;
    }

    // Utility Functions
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    updateDateTime() {
        const now = new Date();
        const timeElements = document.querySelectorAll('.live-time');
        const dateElements = document.querySelectorAll('.live-date');
        
        const timeString = now.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const dateString = now.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        timeElements.forEach(el => el.textContent = timeString);
        dateElements.forEach(el => el.textContent = dateString);
    }

    // WebSocket for real-time updates
    setupWebSocket() {
        // Implement WebSocket connection for real-time features
        // This is a placeholder for WebSocket implementation
        console.log('WebSocket setup placeholder');
    }

    // Export Data
    exportToCSV(data, filename) {
        const csvContent = "data:text/csv;charset=utf-8," + data;
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // Print Functionality
    printElement(elementId) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const originalContents = document.body.innerHTML;
        const printContents = element.innerHTML;
        
        document.body.innerHTML = `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Print Document</title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    @media print {
                        .no-print { display: none !important; }
                    }
                </style>
            </head>
            <body>
                ${printContents}
            </body>
            </html>
        `;
        
        window.print();
        document.body.innerHTML = originalContents;
        location.reload();
    }
}

// Initialize the system
window.BloodBankSystem = new BloodBankSystem();

// Additional global utilities
window.copyToClipboard = function(text) {
    navigator.clipboard.writeText(text).then(
        () => BloodBankSystem.showNotification('Copied to clipboard!', 'success'),
        () => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            BloodBankSystem.showNotification('Copied to clipboard!', 'success');
        }
    );
};

window.confirmAction = function(message, callback) {
    const modal = BloodBankSystem.showModal(
        'Confirm Action',
        `<p class="mb-4">${message}</p>`,
        [
            {
                text: 'Cancel',
                type: 'secondary',
                onclick: 'this.closest(\'.modal-overlay\').remove()'
            },
            {
                text: 'Confirm',
                type: 'danger',
                onclick: `() => { ${callback.toString()}(); this.closest('.modal-overlay').remove(); }`
            }
        ]
    );
};

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add CSS for notifications
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            background: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 0.75rem;
            animation: slideIn 0.3s ease;
            min-width: 300px;
            border-left: 4px solid #2979ff;
        }
        
        .notification-success {
            border-left-color: #00c853;
        }
        
        .notification-error {
            border-left-color: #ff1744;
        }
        
        .notification-warning {
            border-left-color: #ff9100;
        }
        
        .notification-close {
            margin-left: auto;
            background: none;
            border: none;
            color: #666;
            cursor: pointer;
            padding: 0.25rem;
        }
        
        .search-highlight {
            animation: highlight 1s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(100%);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        @keyframes highlight {
            0% { background-color: rgba(229, 57, 53, 0.2); }
            100% { background-color: transparent; }
        }
    `;
    document.head.appendChild(style);
});
// Enhanced Add Donor Page Functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeAddDonorPage();
});

function initializeAddDonorPage() {
    // Set max date for date of birth (must be at least 18 years ago)
    const dobInput = document.querySelector('input[name="dob"]');
    if (dobInput) {
        const today = new Date();
        const minDate = new Date(today.getFullYear() - 65, today.getMonth(), today.getDate());
        const maxDate = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());
        
        dobInput.min = minDate.toISOString().split('T')[0];
        dobInput.max = maxDate.toISOString().split('T')[0];
        
        // Add date picker enhancement
        dobInput.addEventListener('change', function() {
            calculateAge(this.value);
            updateEligibilityIndicator(this.value);
        });
    }
    
    // Set max date for donation date (cannot be in future)
    const donationDateInput = document.querySelector('input[name="donation_date"]');
    if (donationDateInput) {
        const today = new Date().toISOString().split('T')[0];
        donationDateInput.max = today;
    }
    
    // Phone number formatting
    const phoneInput = document.querySelector('input[name="phone"]');
    if (phoneInput) {
        phoneInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 10) value = value.substring(0, 10);
            
            // Format as (XXX) XXX-XXXX
            if (value.length > 3 && value.length <= 6) {
                value = `(${value.substring(0,3)}) ${value.substring(3)}`;
            } else if (value.length > 6) {
                value = `(${value.substring(0,3)}) ${value.substring(3,6)}-${value.substring(6)}`;
            }
            
            e.target.value = value;
        });
    }
    
    // Form validation
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                showFormErrors();
            } else {
                showLoadingState();
            }
        });
    }
    
    // Real-time validation
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('blur', validateInput);
        input.addEventListener('input', clearError);
    });
}

// Enhanced Age Calculator with Visual Indicator
function calculateAge(dob) {
    if (!dob) return null;
    
    const birthDate = new Date(dob);
    const today = new Date();
    
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    
    // Update age display
    const ageDisplay = document.querySelector('.age-display');
    if (!ageDisplay) {
        const dobGroup = document.querySelector('input[name="dob"]').closest('.form-group');
        const display = document.createElement('div');
        display.className = 'age-display';
        display.style.cssText = `
            margin-top: 10px;
            padding: 10px;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
        `;
        dobGroup.appendChild(display);
    }
    
    const display = document.querySelector('.age-display');
    const isEligible = age >= 18 && age <= 65;
    
    display.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 18px;">${isEligible ? '✅' : '❌'}</span>
            <span>
                <strong>Age:</strong> ${age} years
                <br>
                <small style="font-weight: ${isEligible ? '500' : '600'}; color: ${isEligible ? '#2e7d32' : '#e53935'}">
                    ${isEligible ? 'Eligible to donate' : 'Not eligible (must be 18-65 years)'}
                </small>
            </span>
        </div>
    `;
    
    display.style.background = isEligible ? 'rgba(104, 211, 145, 0.1)' : 'rgba(229, 57, 53, 0.1)';
    display.style.border = `2px solid ${isEligible ? '#68d391' : '#e53935'}`;
    
    // Show eligibility alert
    if (!isEligible) {
        showEligibilityAlert(age);
    }
    
    return { age, isEligible };
}

function showEligibilityAlert(age) {
    const alert = document.createElement('div');
    alert.className = 'eligibility-alert';
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #e53935, #ff5252);
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        box-shadow: 0 10px 25px rgba(229, 57, 53, 0.3);
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 15px;
        animation: slideInDown 0.5s ease;
    `;
    
    let message = '';
    if (age < 18) {
        message = `Age ${age}: Too young to donate. Minimum age is 18 years.`;
    } else if (age > 65) {
        message = `Age ${age}: Too old to donate. Maximum age is 65 years.`;
    }
    
    alert.innerHTML = `
        <i class="fas fa-exclamation-triangle" style="font-size: 24px;"></i>
        <div>
            <strong>Donation Eligibility</strong>
            <div style="font-size: 14px; opacity: 0.9;">${message}</div>
        </div>
        <button onclick="this.parentElement.remove()" style="margin-left: auto; background: none; border: none; color: white; cursor: pointer;">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alert.parentElement) {
            alert.style.animation = 'slideOutUp 0.5s ease';
            setTimeout(() => alert.remove(), 500);
        }
    }, 5000);
}

// Form Validation Functions
function validateForm() {
    let isValid = true;
    const requiredFields = document.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!validateInput.call(field)) {
            isValid = false;
        }
    });
    
    return isValid;
}

function validateInput() {
    const input = this;
    const value = input.value.trim();
    let isValid = true;
    let errorMessage = '';
    
    // Remove existing error
    clearError.call(input);
    
    // Check required
    if (input.required && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Check email
    else if (input.type === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    // Check phone
    else if (input.type === 'tel' && value) {
        const phoneRegex = /^\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$/;
        if (!phoneRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid 10-digit phone number';
        }
    }
    
    // Check date (not in future for DOB)
    else if (input.type === 'date' && value) {
        const date = new Date(value);
        const today = new Date();
        if (input.name === 'dob' && date > today) {
            isValid = false;
            errorMessage = 'Date of birth cannot be in the future';
        }
        if (input.name === 'donation_date' && date > today) {
            isValid = false;
            errorMessage = 'Donation date cannot be in the future';
        }
    }
    
    // Show error if invalid
    if (!isValid) {
        showError(input, errorMessage);
    } else {
        showSuccess(input);
    }
    
    return isValid;
}

function showError(input, message) {
    input.style.borderColor = '#e53935';
    input.style.background = 'rgba(229, 57, 53, 0.05)';
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        color: #e53935;
        font-size: 0.85rem;
        margin-top: 5px;
        display: flex;
        align-items: center;
        gap: 5px;
    `;
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    input.parentElement.appendChild(errorDiv);
}

function showSuccess(input) {
    input.style.borderColor = '#68d391';
    input.style.background = 'rgba(104, 211, 145, 0.05)';
    
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.style.cssText = `
        color: #68d391;
        font-size: 0.85rem;
        margin-top: 5px;
        display: flex;
        align-items: center;
        gap: 5px;
    `;
    successDiv.innerHTML = `<i class="fas fa-check-circle"></i> Valid`;
    
    input.parentElement.appendChild(successDiv);
}

function clearError() {
    this.style.borderColor = '';
    this.style.background = '';
    
    const errorDiv = this.parentElement.querySelector('.error-message');
    if (errorDiv) errorDiv.remove();
    
    const successDiv = this.parentElement.querySelector('.success-message');
    if (successDiv) successDiv.remove();
}

function showFormErrors() {
    const firstError = document.querySelector('.error-message');
    if (firstError) {
        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Add shake animation to form
        const form = document.querySelector('.form-container');
        form.style.animation = 'shake 0.5s ease';
        setTimeout(() => form.style.animation = '', 500);
    }
}

function showLoadingState() {
    const submitBtn = document.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    submitBtn.innerHTML = `
        <div class="spinner" style="
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        "></div>
        Processing...
    `;
    submitBtn.disabled = true;
}

// Enhanced toggle donation with animation
function toggleDonation() {
    const fields = document.getElementById('donationFields');
    const checkbox = document.getElementById('make_donation');
    
    if (checkbox.checked) {
        fields.style.display = 'block';
        // Animate in
        fields.style.animation = 'slideDown 0.5s ease';
        
        // Show donation info
        showDonationInfo();
    } else {
        // Animate out
        fields.style.animation = 'slideUp 0.5s ease';
        setTimeout(() => {
            fields.style.display = 'none';
        }, 500);
    }
}

function showDonationInfo() {
    const infoDiv = document.createElement('div');
    infoDiv.className = 'donation-info';
    infoDiv.style.cssText = `
        background: rgba(33, 150, 243, 0.1);
        border-left: 4px solid #2196f3;
        padding: 15px;
        margin-top: 15px;
        border-radius: 8px;
        font-size: 0.9rem;
        color: #1565c0;
    `;
    infoDiv.innerHTML = `
        <strong><i class="fas fa-info-circle"></i> Donation Information:</strong>
        <ul style="margin: 10px 0 0 20px;">
            <li>Standard donation is 1 unit (≈450ml)</li>
            <li>Double donation (2 units) requires special eligibility</li>
            <li>Blood expires after 42 days</li>
            <li>Donors must wait 56 days between donations</li>
        </ul>
    `;
    
    const existingInfo = document.querySelector('.donation-info');
    if (existingInfo) existingInfo.remove();
    
    document.getElementById('donationFields').appendChild(infoDiv);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
        20%, 40%, 60%, 80% { transform: translateX(5px); }
    }
    
    @keyframes slideInDown {
        from {
            transform: translate(-50%, -100%);
            opacity: 0;
        }
        to {
            transform: translate(-50%, 0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutUp {
        from {
            transform: translate(-50%, 0);
            opacity: 1;
        }
        to {
            transform: translate(-50%, -100%);
            opacity: 0;
        }
    }
    
    @keyframes slideUp {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-20px);
        }
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
// Password visibility toggle function
function togglePasswordVisibility(inputId) {
    const passwordInput = document.getElementById(inputId);
    if (!passwordInput) return;
    
    const toggleButton = passwordInput.nextElementSibling;
    const icon = toggleButton.querySelector('i');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize password toggle buttons with event listeners
    initializePasswordToggles();
    
    // Your existing initialization code...
    if (window.BloodBankSystem) {
        window.BloodBankSystem.init();
    }
});


// ============================================
// EXPORT FUNCTIONALITY
// ============================================

// Export to CSV
function exportToCSV(data, filename = 'export') {
    return new Promise((resolve, reject) => {
        try {
            if (!data || data.length === 0) {
                showDownloadNotification('No data to export', 'error');
                reject('No data');
                return;
            }

            // Get headers from first object
            const headers = Object.keys(data[0]);
            
            // Convert to CSV
            const csvContent = [
                headers.join(','),
                ...data.map(row => headers.map(header => {
                    let cell = row[header] || '';
                    // Escape quotes and wrap in quotes if contains comma
                    if (cell.toString().includes(',')) {
                        cell = `"${cell.toString().replace(/"/g, '""')}"`;
                    }
                    return cell;
                }).join(','))
            ].join('\n');

            // Create and trigger download
            const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            link.setAttribute('href', url);
            link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            showDownloadNotification('CSV file downloaded successfully!', 'success');
            resolve();
        } catch (error) {
            showDownloadNotification('Error exporting to CSV', 'error');
            reject(error);
        }
    });
}

// Export to Excel (XLS)
function exportToExcel(data, filename = 'export', title = 'Data Export') {
    return new Promise((resolve, reject) => {
        try {
            if (!data || data.length === 0) {
                showDownloadNotification('No data to export', 'error');
                reject('No data');
                return;
            }

            // Get headers
            const headers = Object.keys(data[0]);
            
            // Create HTML table
            let html = `
                <html>
                <head>
                    <title>${title}</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 20px; }
                        h2 { color: #e53935; }
                        table { border-collapse: collapse; width: 100%; }
                        th { background: #e53935; color: white; padding: 10px; }
                        td { padding: 8px; border: 1px solid #ddd; }
                        tr:nth-child(even) { background: #f9f9f9; }
                    </style>
                </head>
                <body>
                    <h2>${title}</h2>
                    <p>Generated on: ${new Date().toLocaleString()}</p>
                    <table>
                        <thead>
                            <tr>
                                ${headers.map(h => `<th>${h.replace(/_/g, ' ').toUpperCase()}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            // Add data rows
            data.forEach(row => {
                html += '<tr>';
                headers.forEach(header => {
                    html += `<td>${row[header] || ''}</td>`;
                });
                html += '</tr>';
            });
            
            html += `
                        </tbody>
                    </table>
                    <p><strong>Total Records:</strong> ${data.length}</p>
                </body>
                </html>
            `;

            // Create and trigger download
            const blob = new Blob([html], { type: 'application/vnd.ms-excel' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            link.setAttribute('href', url);
            link.setAttribute('download', `${filename}_${new Date().toISOString().split('T')[0]}.xls`);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            showDownloadNotification('Excel file downloaded successfully!', 'success');
            resolve();
        } catch (error) {
            showDownloadNotification('Error exporting to Excel', 'error');
            reject(error);
        }
    });
}

// Export to PDF (using browser print)
function exportToPDF(elementId, filename = 'export') {
    const element = document.getElementById(elementId);
    if (!element) {
        showDownloadNotification('Element not found', 'error');
        return;
    }
    
    // Store original title
    const originalTitle = document.title;
    document.title = filename;
    
    // Trigger print
    window.print();
    
    // Restore title
    document.title = originalTitle;
    
    showDownloadNotification('Print dialog opened', 'success');
}

// Copy to clipboard
function copyToClipboard(data, headers = null) {
    return new Promise((resolve, reject) => {
        try {
            if (!data || data.length === 0) {
                showDownloadNotification('No data to copy', 'error');
                reject('No data');
                return;
            }

            // Use provided headers or get from data
            const cols = headers || Object.keys(data[0]);
            
            // Create tab-separated text
            let text = cols.join('\t') + '\n';
            
            data.forEach(row => {
                const rowData = cols.map(col => row[col] || '').join('\t');
                text += rowData + '\n';
            });

            // Copy to clipboard
            navigator.clipboard.writeText(text).then(
                () => {
                    showDownloadNotification('Data copied to clipboard!', 'success');
                    resolve();
                },
                () => {
                    // Fallback for older browsers
                    const textarea = document.createElement('textarea');
                    textarea.value = text;
                    textarea.style.position = 'fixed';
                    textarea.style.opacity = '0';
                    document.body.appendChild(textarea);
                    textarea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textarea);
                    showDownloadNotification('Data copied to clipboard!', 'success');
                    resolve();
                }
            );
        } catch (error) {
            showDownloadNotification('Error copying to clipboard', 'error');
            reject(error);
        }
    });
}

// Download notification
function showDownloadNotification(message, type = 'success') {
    // Remove existing notification
    const existing = document.querySelector('.download-notification');
    if (existing) existing.remove();
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `download-notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <div class="download-notification-content">
            <div class="download-notification-title">
                ${type === 'success' ? 'Download Successful' : 'Download Failed'}
            </div>
            <div class="download-notification-message">${message}</div>
        </div>
        <button class="download-notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 3000);
}

// Format data for export
function prepareExportData(donors) {
    return donors.map(donor => ({
        'Donor ID': donor.donor_id,
        'Name': donor.name,
        'Age': donor.age,
        'Gender': donor.gender,
        'Blood Group': donor.blood_group,
        'City': donor.city,
        'Phone': donor.phone,
        'Email': donor.email || 'N/A',
        'Last Donation': donor.last_donation_date || 'Never',
        'Eligible': donor.eligible ? 'Yes' : 'No',
        'Status': donor.status || 'Active'
    }));
}

// Add loading state to button
function setButtonLoading(button, isLoading) {
    if (isLoading) {
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = `<span class="download-spinner"></span> Processing...`;
        button.disabled = true;
    } else {
        button.innerHTML = button.dataset.originalText || button.innerHTML;
        button.disabled = false;
    }
}

// Slide animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

function editDonation(button) {
    const donationId = button.dataset.id;
    const donationDate = button.dataset.date;
    const units = button.dataset.units;
    const testResult = button.dataset.result;
    const notes = button.dataset.notes;
    
    currentDonationId = donationId;
    
    // Set form values
    document.getElementById('edit_donation_id').value = donationId;
    document.getElementById('edit_donation_date').value = donationDate;
    document.getElementById('edit_units_donated').value = units;
    document.getElementById('edit_test_result').value = testResult;
    document.getElementById('edit_notes').value = notes;
    
    // Show modal
    document.getElementById('editModal').style.display = 'flex';
}
