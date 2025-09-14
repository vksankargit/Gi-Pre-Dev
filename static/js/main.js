// Main JavaScript for PRE System

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-save functionality
    setupAutoSave();
    
    // Grid functionality
    setupGridSorting();
    setupGridFiltering();
    
    // Form enhancements
    setupFormValidation();
    
    // Number formatting
    setupNumberFormatting();
});

// Auto-save functionality
function setupAutoSave() {
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    
    autoSaveForms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        let saveTimeout;
        
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                clearTimeout(saveTimeout);
                saveTimeout = setTimeout(() => {
                    autoSaveForm(form);
                }, 2000); // Save after 2 seconds of inactivity
            });
        });
    });
}

function autoSaveForm(form) {
    const formData = new FormData(form);
    const url = form.dataset.autoSaveUrl || form.action;
    
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Changes saved automatically', 'success');
        }
    })
    .catch(error => {
        console.error('Auto-save error:', error);
    });
}

// Grid sorting functionality
function setupGridSorting() {
    const sortableHeaders = document.querySelectorAll('.sortable-column');
    
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const table = this.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const columnIndex = Array.from(this.parentNode.children).indexOf(this);
            
            const currentSort = this.dataset.sort || 'none';
            let newSort = 'asc';
            
            if (currentSort === 'asc') {
                newSort = 'desc';
            } else if (currentSort === 'desc') {
                newSort = 'none';
            }
            
            // Reset all other column sorts
            sortableHeaders.forEach(h => {
                if (h !== this) {
                    h.dataset.sort = 'none';
                    h.querySelector('.sort-icon').innerHTML = '<i class="fas fa-sort"></i>';
                }
            });
            
            this.dataset.sort = newSort;
            
            if (newSort === 'none') {
                this.querySelector('.sort-icon').innerHTML = '<i class="fas fa-sort"></i>';
                // Reset to original order (could be enhanced to store original order)
                return;
            }
            
            // Update sort icon
            const icon = newSort === 'asc' ? 'fa-sort-up' : 'fa-sort-down';
            this.querySelector('.sort-icon').innerHTML = `<i class="fas ${icon}"></i>`;
            
            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.cells[columnIndex].textContent.trim();
                const bValue = b.cells[columnIndex].textContent.trim();
                
                // Try to parse as numbers
                const aNum = parseFloat(aValue.replace(/[,$]/g, ''));
                const bNum = parseFloat(bValue.replace(/[,$]/g, ''));
                
                let comparison = 0;
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    comparison = aNum - bNum;
                } else {
                    comparison = aValue.localeCompare(bValue);
                }
                
                return newSort === 'asc' ? comparison : -comparison;
            });
            
            // Reorder table rows
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// Grid filtering functionality
function setupGridFiltering() {
    const filterButtons = document.querySelectorAll('.filter-toggle');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const dropdown = this.nextElementSibling;
            
            // Close other dropdowns
            document.querySelectorAll('.filter-content').forEach(content => {
                if (content !== dropdown) {
                    content.parentElement.classList.remove('show');
                }
            });
            
            dropdown.parentElement.classList.toggle('show');
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function() {
        document.querySelectorAll('.filter-dropdown').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    });
    
    // Prevent dropdown from closing when clicking inside
    document.querySelectorAll('.filter-content').forEach(content => {
        content.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });
    
    // Apply filters
    const applyFilterButtons = document.querySelectorAll('.apply-filter');
    applyFilterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filterContent = this.closest('.filter-content');
            const columnIndex = parseInt(filterContent.dataset.column);
            const table = filterContent.closest('.grid-container').querySelector('table');
            
            applyColumnFilter(table, columnIndex, filterContent);
            filterContent.parentElement.classList.remove('show');
        });
    });
}

function applyColumnFilter(table, columnIndex, filterContent) {
    const tbody = table.querySelector('tbody');
    const rows = tbody.querySelectorAll('tr');
    const checkboxes = filterContent.querySelectorAll('input[type="checkbox"]:checked');
    const selectedValues = Array.from(checkboxes).map(cb => cb.value);
    
    rows.forEach(row => {
        const cellValue = row.cells[columnIndex].textContent.trim();
        const shouldShow = selectedValues.length === 0 || selectedValues.includes(cellValue);
        row.style.display = shouldShow ? '' : 'none';
    });
}

// Form validation enhancements
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        });
    });
}

// Number formatting
function setupNumberFormatting() {
    const numberFields = document.querySelectorAll('.number-field input');
    
    numberFields.forEach(field => {
        field.addEventListener('blur', function() {
            const value = parseFloat(this.value.replace(/[,$]/g, ''));
            if (!isNaN(value)) {
                this.value = formatNumber(value);
            }
        });
    });
}

function formatNumber(num) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num);
}

// Utility functions
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    const firstChild = container.firstElementChild;
    container.insertBefore(alertDiv, firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Confirmation dialogs
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Loading states
function showLoading(element) {
    element.classList.add('loading');
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border spinner-border-sm spinner-overlay';
    spinner.setAttribute('role', 'status');
    element.style.position = 'relative';
    element.appendChild(spinner);
}

function hideLoading(element) {
    element.classList.remove('loading');
    const spinner = element.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

// Dynamic form handling
function addFormRow(templateSelector, containerSelector) {
    const template = document.querySelector(templateSelector);
    const container = document.querySelector(containerSelector);
    
    if (template && container) {
        const clone = template.cloneNode(true);
        clone.style.display = '';
        container.appendChild(clone);
        
        // Update form indices if needed
        updateFormIndices(container);
    }
}

function removeFormRow(button) {
    const row = button.closest('.form-row');
    if (row) {
        row.remove();
        updateFormIndices(row.closest('.form-container'));
    }
}

function updateFormIndices(container) {
    const rows = container.querySelectorAll('.form-row');
    rows.forEach((row, index) => {
        const inputs = row.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.name) {
                input.name = input.name.replace(/\d+/, index);
            }
            if (input.id) {
                input.id = input.id.replace(/\d+/, index);
            }
        });
    });
}