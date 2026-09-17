/* Mbugani Luxe Adventures - Custom Unfold Admin JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize custom functionality
    initializeMbuganiAdmin();
    
    // Add travel-themed enhancements
    enhanceTravelInterface();
    
    // Initialize form enhancements
    enhanceForms();
    
    // Add responsive behavior
    handleResponsiveNavigation();
});

function initializeMbuganiAdmin() {
    console.log('Mbugani Luxe Adventures Admin Interface Initialized');
    
    // Add fade-in animation to main content
    const mainContent = document.querySelector('.main-content');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }
    
    // Add slide-in animation to sidebar
    const sidebar = document.querySelector('.unfold-sidebar');
    if (sidebar) {
        sidebar.classList.add('slide-in-left');
    }
}

function enhanceTravelInterface() {
    // Add travel-themed icons to navigation items
    const navItems = {
        'Destinations': 'fas fa-map-marker-alt',
        'Packages': 'fas fa-suitcase-rolling',
        'Accommodations': 'fas fa-hotel',
        'Travel Modes': 'fas fa-plane',
        'Blog Posts': 'fas fa-blog',
        'Categories': 'fas fa-tags'
    };
    
    Object.entries(navItems).forEach(([text, iconClass]) => {
        const navLink = Array.from(document.querySelectorAll('.nav-link')).find(
            link => link.textContent.trim().includes(text)
        );
        
        if (navLink && !navLink.querySelector('i')) {
            const icon = document.createElement('i');
            icon.className = `${iconClass} travel-icon me-2`;
            navLink.insertBefore(icon, navLink.firstChild);
        }
    });
    
    // Add status indicators for packages
    enhancePackageStatus();
    
    // Add destination type indicators
    enhanceDestinationTypes();
}

function enhancePackageStatus() {
    const statusElements = document.querySelectorAll('[data-status]');
    statusElements.forEach(element => {
        const status = element.getAttribute('data-status');
        element.classList.add(`package-status-${status.toLowerCase()}`);
    });
}

function enhanceDestinationTypes() {
    const typeElements = document.querySelectorAll('[data-destination-type]');
    typeElements.forEach(element => {
        const type = element.getAttribute('data-destination-type');
        element.classList.add(`destination-type-${type.toLowerCase()}`);
    });
}

function enhanceForms() {
    // Add enhanced styling to form fields
    const formFields = document.querySelectorAll('.form-control, .form-select');
    formFields.forEach(field => {
        const wrapper = field.closest('.field-wrapper') || field.parentElement;
        
        // Add focus enhancement
        field.addEventListener('focus', function() {
            wrapper.classList.add('field-focused');
        });
        
        field.addEventListener('blur', function() {
            wrapper.classList.remove('field-focused');
        });
    });
    
    // Enhance image upload fields
    enhanceImageUploads();
    
    // Add form validation enhancements
    enhanceFormValidation();
}

function enhanceImageUploads() {
    const imageInputs = document.querySelectorAll('input[type="file"]');
    imageInputs.forEach(input => {
        if (input.accept && input.accept.includes('image')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'image-upload-wrapper';
            
            const label = document.createElement('label');
            label.innerHTML = `
                <i class="fas fa-cloud-upload-alt fa-2x mb-2 d-block"></i>
                <span>Click to upload image or drag and drop</span>
            `;
            label.appendChild(input.cloneNode(true));
            
            wrapper.appendChild(label);
            input.parentNode.replaceChild(wrapper, input);
            
            // Add drag and drop functionality
            addDragDropToImageUpload(wrapper);
        }
    });
}

function addDragDropToImageUpload(wrapper) {
    const input = wrapper.querySelector('input[type="file"]');
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        wrapper.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        wrapper.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        wrapper.addEventListener(eventName, unhighlight, false);
    });
    
    wrapper.addEventListener('drop', handleDrop, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        wrapper.classList.add('drag-over');
    }
    
    function unhighlight() {
        wrapper.classList.remove('drag-over');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            input.files = files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
}

function enhanceFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showValidationMessage('Please fill in all required fields.');
            }
        });
    });
}

function handleResponsiveNavigation() {
    const toggleBtn = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('.unfold-sidebar');
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(e) {
            if (window.innerWidth <= 768 && 
                !sidebar.contains(e.target) && 
                !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('show');
            }
        });
    }
}

function showValidationMessage(message) {
    // Create or update validation message
    let messageEl = document.querySelector('.validation-message');
    if (!messageEl) {
        messageEl = document.createElement('div');
        messageEl.className = 'alert alert-error validation-message';
        document.querySelector('form').insertBefore(messageEl, document.querySelector('form').firstChild);
    }
    
    messageEl.textContent = message;
    messageEl.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageEl.style.display = 'none';
    }, 5000);
}

function showSuccessMessage(message) {
    const messageEl = document.createElement('div');
    messageEl.className = 'alert alert-success';
    messageEl.textContent = message;
    
    document.body.insertBefore(messageEl, document.body.firstChild);
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        messageEl.remove();
    }, 3000);
}

// Utility functions for admin interface
window.MbuganiAdmin = {
    showLoading: function(element) {
        const spinner = document.createElement('div');
        spinner.className = 'loading-spinner';
        element.appendChild(spinner);
    },
    
    hideLoading: function(element) {
        const spinner = element.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
    },
    
    showSuccess: showSuccessMessage,
    
    showError: function(message) {
        showValidationMessage(message);
    }
};

// Initialize tooltips and popovers if Bootstrap is available
if (typeof bootstrap !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Initialize popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    });
}
