// ==================== NAVIGATION ====================

// Toggle Navigation Panel
function toggleNavPanel() {
    document.body.classList.toggle('nav-collapsed');
    
    // Save state to localStorage
    const isCollapsed = document.body.classList.contains('nav-collapsed');
    localStorage.setItem('navCollapsed', isCollapsed);
}

// ==================== FORM VALIDATION ====================

// Validate Raffle Numbers
function validateRaffle(raffleInput) {
    const errorDiv = document.getElementById('raffleError');
    
    if (!errorDiv) return true;
    
    if (!raffleInput || raffleInput.trim() === '') {
        errorDiv.classList.add('d-none');
        return true; // Raffle is optional
    }

    const numbers = raffleInput.split(',').map(n => n.trim()).filter(n => n !== '');
    
    // Check if at least 10 numbers
    if (numbers.length < 10) {
        errorDiv.textContent = 'Please enter at least 10 numbers.';
        errorDiv.classList.remove('d-none');
        return false;
    }

    // Validate each number
    for (let num of numbers) {
        const n = parseInt(num);
        if (isNaN(n) || n < 1 || n > 100) {
            errorDiv.textContent = `Invalid number: "${num}". Please enter numbers between 1 and 100.`;
            errorDiv.classList.remove('d-none');
            return false;
        }
    }

    errorDiv.classList.add('d-none');
    return true;
}

// Form Validation and Submission (Survey)
function validateAndSubmit(event) {
    event.preventDefault();
    
    const form = document.getElementById('surveyForm');
    const alertDiv = document.getElementById('formAlert');
    
    if (!form || !alertDiv) return false;
    
    // Reset alert
    alertDiv.classList.add('d-none');
    alertDiv.classList.remove('alert-success', 'alert-danger');

    // Validate raffle
    const raffleInput = document.getElementById('raffle');
    if (raffleInput && !validateRaffle(raffleInput.value)) {
        return false;
    }

    // If all validation passes
    if (form.checkValidity()) {
        // Show success message
        alertDiv.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i><strong>Success!</strong> Your survey has been submitted successfully. Thank you for your feedback!';
        alertDiv.classList.remove('d-none');
        alertDiv.classList.add('alert-success');
        
        // Scroll to top to show alert
        window.scrollTo({ top: 0, behavior: 'smooth' });
        
        // Reset form after delay
        setTimeout(() => {
            form.reset();
            // Reset date to today
            const surveyDate = document.getElementById('surveyDate');
            if (surveyDate) {
                const today = new Date().toISOString().split('T')[0];
                surveyDate.value = today;
            }
        }, 3000);
        
        return false;
    } else {
        // Show error message
        alertDiv.innerHTML = '<i class="bi bi-exclamation-triangle-fill me-2"></i><strong>Error!</strong> Please fill in all required fields correctly.';
        alertDiv.classList.remove('d-none');
        alertDiv.classList.add('alert-danger');
        
        // Trigger browser's built-in validation
        form.reportValidity();
        return false;
    }
}

// Reset Form
function resetForm() {
    const form = document.getElementById('surveyForm');
    const alertDiv = document.getElementById('formAlert');
    const raffleError = document.getElementById('raffleError');
    
    if (form) form.reset();
    if (alertDiv) alertDiv.classList.add('d-none');
    if (raffleError) raffleError.classList.add('d-none');
    
    // Reset date to today
    const surveyDate = document.getElementById('surveyDate');
    if (surveyDate) {
        const today = new Date().toISOString().split('T')[0];
        surveyDate.value = today;
    }
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function() {
    // Restore nav panel state from localStorage
    const isCollapsed = localStorage.getItem('navCollapsed') === 'true';
    if (isCollapsed || window.innerWidth < 992) {
        document.body.classList.add('nav-collapsed');
    }

    // Handle responsive nav panel on resize
    window.addEventListener('resize', function() {
        if (window.innerWidth < 992) {
            document.body.classList.add('nav-collapsed');
        }
    });

    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Close nav panel when clicking outside on mobile
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 992) {
            const navPanel = document.getElementById('navPanel');
            const iconBar = document.querySelector('.icon-bar');
            const menuToggle = document.querySelector('.menu-toggle');
            
            if (navPanel && !navPanel.contains(e.target) && 
                !iconBar.contains(e.target) && 
                !menuToggle.contains(e.target)) {
                document.body.classList.add('nav-collapsed');
            }
        }
    });

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

// ==================== UTILITY FUNCTIONS ====================

// Format phone number
function formatPhoneNumber(input) {
    const cleaned = ('' + input.value).replace(/\D/g, '');
    const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
    if (match) {
        input.value = '(' + match[1] + ') ' + match[2] + '-' + match[3];
    }
}

// Debounce function for search/input
function debounce(func, wait) {
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
