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

// Due Date Filter Function for My To Do
function applyDueDateFilter() {
    // Get all filter checkboxes
    const checkboxes = [
        document.getElementById('filterOverdue'),
        document.getElementById('filterCurrentWeek'),
        document.getElementById('filterNextWeek'),
        document.getElementById('filterLater')
    ];

    // Check if any checkbox exists (we're on the right page)
    if (!checkboxes[0]) return;

    // Get selected filters
    const selectedFilters = checkboxes
        .filter(cb => cb && cb.checked)
        .map(cb => cb.value);

    // Store the active tab before reload
    localStorage.setItem('activeImplementTab', 'my-todo-tab');

    // Build URL with selected filters
    const url = new URL(window.location.href);
    // Remove any existing hash to avoid conflicts
    url.hash = '';

    if (selectedFilters.length > 0) {
        url.searchParams.set('due_date_filter', selectedFilters.join(','));
    } else {
        url.searchParams.delete('due_date_filter');
    }

    // Reload page with new filters
    window.location.href = url.toString();
}

// Parameter Actions Popup (for My Numbers)
function openParameterActions(paramType, paramId, weekNumber, monthNumber) {
    console.log(`Opening parameter actions for ${paramType} ID: ${paramId}, week: ${weekNumber}, month: ${monthNumber}`);

    // Store current parameter context with week/month
    window.currentParameterContext = {
        type: paramType,
        id: paramId,
        weekNumber: weekNumber,
        monthNumber: monthNumber
    };

    // Build query parameters
    let queryParams = `parameter_type=${paramType}&parameter_id=${paramId}`;
    if (weekNumber) queryParams += `&week_number=${weekNumber}`;
    if (monthNumber) queryParams += `&month_number=${monthNumber}`;

    // Fetch actions for this parameter
    fetch(`/api/parameter-actions/?${queryParams}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showParameterActionsModal(data.actions, data.parameter_name, paramType, paramId);
        } else {
            showNotification('Failed to load actions: ' + (data.message || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error loading parameter actions:', error);
        showNotification('Error loading actions', 'danger');
    });
}

function showParameterActionsModal(actions, parameterName, paramType, paramId) {
    // Calculate summary statistics
    const total = actions.length;
    const highPriority = actions.filter(a => a.priority === 'high').length;
    const completed = actions.filter(a => a.status === 'completed' || a.status === 'done').length;

    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="parameterActionsModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-tasks me-2"></i>Action Items - ${parameterName}
                            <span class="badge bg-secondary ms-2">${total} item${total !== 1 ? 's' : ''}</span>
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <div class="row flex-grow-1 g-2">
                                <div class="col-md-4">
                                    <div class="card text-center border-primary">
                                        <div class="card-body py-2">
                                            <h6 class="card-title mb-1 text-primary">${total}</h6>
                                            <small class="text-muted">Total Actions</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card text-center border-danger">
                                        <div class="card-body py-2">
                                            <h6 class="card-title mb-1 text-danger">${highPriority}</h6>
                                            <small class="text-muted">High Priority</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <div class="card text-center border-success">
                                        <div class="card-body py-2">
                                            <h6 class="card-title mb-1 text-success">${completed}</h6>
                                            <small class="text-muted">Completed</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <button class="btn btn-success ms-3" onclick="addParameterAction('${paramType}', ${paramId})">
                                <i class="fas fa-plus me-2"></i>Add Action
                            </button>
                        </div>

                        ${actions.length === 0 ?
                            `<div class="text-center py-5">
                                <i class="fas fa-clipboard-list fa-3x text-muted mb-3"></i>
                                <h6 class="text-muted mb-3">No Action Items for ${parameterName}</h6>
                                <p class="text-muted mb-3">No action items have been created for this parameter yet.</p>
                                <button class="btn btn-outline-primary" onclick="addParameterAction('${paramType}', ${paramId})">
                                    <i class="fas fa-plus me-2"></i>Add First Action Item
                                </button>
                            </div>` :
                            `<div class="card">
                                <div class="card-header">
                                    <h6 class="mb-0">Current Action Items</h6>
                                </div>
                                <div class="card-body p-0">
                                    <div class="table-responsive">
                                        <table class="table table-hover mb-0">
                                            <thead class="table-light">
                                                <tr>
                                                    <th style="width: 5%">S.No</th>
                                                    <th style="width: 35%">Action</th>
                                                    <th style="width: 12%">Priority</th>
                                                    <th style="width: 18%">Assigned To</th>
                                                    <th style="width: 15%">Due Date</th>
                                                    <th style="width: 12%">Status</th>
                                                    <th style="width: 8%">Edit</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${actions.map((action, index) => `
                                                    <tr class="${action.priority === 'high' ? 'table-warning' : ''}">
                                                        <td>
                                                            <span class="badge bg-secondary">${index + 1}</span>
                                                        </td>
                                                        <td>
                                                            <div>
                                                                <strong>${action.description.length > 80 ? action.description.substring(0, 80) + '...' : action.description}</strong>
                                                            </div>
                                                        </td>
                                                        <td>
                                                            <span class="badge bg-${getPriorityBadgeClass(action.priority)}">${action.priority_display}</span>
                                                        </td>
                                                        <td>
                                                            <div class="d-flex align-items-center">
                                                                <i class="fas fa-user me-1"></i>
                                                                <small>${action.assigned_to_name}</small>
                                                            </div>
                                                        </td>
                                                        <td>${action.due_date || '-'}</td>
                                                        <td>
                                                            <span class="badge bg-${getStatusBadgeClass(action.status)}">${action.status_display}</span>
                                                        </td>
                                                        <td>
                                                            <button class="btn btn-sm btn-outline-primary" onclick="editAction(${action.id})"
                                                                    data-bs-toggle="tooltip" title="Edit Action">
                                                                <i class="fas fa-edit"></i>
                                                            </button>
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>`
                        }

                        <!-- Inline Add Action Form (Initially Hidden) -->
                        <div class="mt-3" id="parameterActionFormContainer" style="display: none;">
                            <div class="card">
                                <div class="card-header bg-success text-white">
                                    <h6 class="mb-0">
                                        <i class="fas fa-plus me-2"></i>Add New Action for ${parameterName}
                                    </h6>
                                </div>
                                <div class="card-body">
                                    <form id="parameterActionForm" onsubmit="saveParameterAction(event, '${paramType}', ${paramId})">
                                        <div class="row g-3">
                                            <div class="col-12">
                                                <label for="paramActionDescription" class="form-label">Action Required <span class="text-danger">*</span></label>
                                                <textarea class="form-control" id="paramActionDescription" name="action" rows="3"
                                                          placeholder="Describe what needs to be done for ${parameterName}..." required></textarea>
                                            </div>

                                            <div class="col-md-4">
                                                <label for="paramActionTeam" class="form-label">Team <span class="text-danger">*</span></label>
                                                <select class="form-select" id="paramActionTeam" name="team_id" required onchange="loadTeamMembers(this.value, 'paramActionAssignedTo')">
                                                    <option value="">Select Team</option>
                                                </select>
                                            </div>

                                            <div class="col-md-4">
                                                <label for="paramActionPriority" class="form-label">Priority <span class="text-danger">*</span></label>
                                                <select class="form-select" id="paramActionPriority" name="priority" required>
                                                    <option value="">Select Priority</option>
                                                    <option value="high">High</option>
                                                    <option value="medium" selected>Medium</option>
                                                    <option value="low">Low</option>
                                                </select>
                                            </div>

                                            <div class="col-md-4">
                                                <label for="paramActionDueDate" class="form-label">Due Date <span class="text-danger">*</span></label>
                                                <input type="date" class="form-control" id="paramActionDueDate" name="original_due_date" required>
                                            </div>

                                            <div class="col-md-12">
                                                <label for="paramActionAssignedTo" class="form-label">Assigned To <span class="text-danger">*</span></label>
                                                <select class="form-select" id="paramActionAssignedTo" name="assigned_to" required>
                                                    <option value="">Select Team First</option>
                                                </select>
                                            </div>

                                            <div class="col-12">
                                                <label for="paramActionComments" class="form-label">Comments/Notes</label>
                                                <textarea class="form-control" id="paramActionComments" name="comments" rows="2"
                                                          placeholder="Additional context or notes..."></textarea>
                                            </div>
                                        </div>

                                        <div class="d-flex gap-2 mt-3">
                                            <button type="submit" class="btn btn-primary">
                                                <i class="fas fa-save me-2"></i>Save Action
                                            </button>
                                            <button type="button" class="btn btn-secondary" onclick="cancelParameterActionForm()">
                                                <i class="fas fa-times me-2"></i>Cancel
                                            </button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('parameterActionsModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('parameterActionsModal'));
    modal.show();

    // Load teams for the form
    loadTeamsForParameterAction();
}

function loadTeamsForParameterAction() {
    fetch('/api/user-teams/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const teamSelect = document.getElementById('paramActionTeam');
            if (teamSelect) {
                teamSelect.innerHTML = '<option value="">Select Team</option>';
                data.teams.forEach(team => {
                    teamSelect.innerHTML += `<option value="${team.id}">${team.name}</option>`;
                });
            }
        }
    })
    .catch(error => {
        console.error('Error loading teams:', error);
    });
}

function loadTeamMembers(teamId, selectId) {
    if (!teamId) {
        document.getElementById(selectId).innerHTML = '<option value="">Select Team First</option>';
        return;
    }

    fetch(`/api/team-members/${teamId}/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const memberSelect = document.getElementById(selectId);
            memberSelect.innerHTML = '<option value="">Select Person</option>';
            data.members.forEach(member => {
                memberSelect.innerHTML += `<option value="${member.id}">${member.name}</option>`;
            });
        }
    })
    .catch(error => {
        console.error('Error loading team members:', error);
    });
}

function addParameterAction(paramType, paramId) {
    // Show the inline form
    document.getElementById('parameterActionFormContainer').style.display = 'block';
    document.getElementById('paramActionDescription').focus();
}

function cancelParameterActionForm() {
    document.getElementById('parameterActionFormContainer').style.display = 'none';
    document.getElementById('parameterActionForm').reset();
}

function saveParameterAction(event, paramType, paramId) {
    event.preventDefault();

    const formData = new FormData(event.target);

    // Add parameter context and source
    formData.append('parameter_type', paramType);
    formData.append('parameter_id', paramId);
    formData.append('source', 'manual');

    // Add week/month context if available
    if (window.currentParameterContext) {
        if (window.currentParameterContext.weekNumber) {
            formData.append('week_number', window.currentParameterContext.weekNumber);
        }
        if (window.currentParameterContext.monthNumber) {
            formData.append('month_number', window.currentParameterContext.monthNumber);
        }
    }

    const saveBtn = event.target.querySelector('button[type="submit"]');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';

    fetch('/api/create-action/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reset form and hide it
            cancelParameterActionForm();

            // Reload the parameter actions to show the new action
            if (window.currentParameterContext) {
                openParameterActions(window.currentParameterContext.type, window.currentParameterContext.id);
            }

            showNotification('Action created successfully', 'success');
        } else {
            showNotification('Error: ' + (data.error || 'Failed to create action'), 'danger');
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save me-2"></i>Save Action';
        }
    })
    .catch(error => {
        console.error('Error saving action:', error);
        showNotification('Error saving action', 'danger');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save me-2"></i>Save Action';
    });
}

function getStatusBadgeClass(status) {
    const statusClasses = {
        'not_started': 'secondary',
        'in_progress': 'primary',
        'completed': 'success',
        'done': 'success',
        'on_hold': 'warning',
        'cancelled': 'dark',
        'at_risk': 'warning',
        'danger': 'danger',
        'overdue': 'danger',
        'carry_forward': 'info',
        'rejected': 'secondary'
    };
    return statusClasses[status] || 'secondary';
}

function getPriorityBadgeClass(priority) {
    const priorityClasses = {
        'high': 'danger',
        'medium': 'warning',
        'low': 'info'
    };
    return priorityClasses[priority] || 'secondary';
}

// Parameter Issues Popup (for My Numbers)
function openParameterIssues(paramType, paramId, weekNumber, monthNumber) {
    console.log(`Opening parameter issues for ${paramType} ID: ${paramId}, week: ${weekNumber}, month: ${monthNumber}`);

    // Store current parameter context with week/month
    window.currentParameterContext = {
        type: paramType,
        id: paramId,
        weekNumber: weekNumber,
        monthNumber: monthNumber
    };

    // Build query parameters
    let queryParams = `parameter_type=${paramType}&parameter_id=${paramId}`;
    if (weekNumber) queryParams += `&week_number=${weekNumber}`;
    if (monthNumber) queryParams += `&month_number=${monthNumber}`;

    // Fetch issues for this parameter
    fetch(`/api/parameter-issues/?${queryParams}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showParameterIssuesModal(data.issues, data.parameter_name, paramType, paramId);
        } else {
            showNotification('Failed to load issues: ' + (data.message || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error loading parameter issues:', error);
        showNotification('Error loading issues', 'danger');
    });
}

function showParameterIssuesModal(issues, parameterName, paramType, paramId) {
    // Calculate summary statistics
    const total = issues.length;
    const open = issues.filter(i => i.status === 'open').length;
    const inProgress = issues.filter(i => i.status === 'in_progress').length;
    const resolved = issues.filter(i => i.status === 'resolved').length;

    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="parameterIssuesModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle me-2"></i>Issues - ${parameterName}
                            <span class="badge bg-secondary ms-2">${total} issue${total !== 1 ? 's' : ''}</span>
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <div class="row flex-grow-1 g-2">
                                <div class="col-md-3">
                                    <div class="card text-center border-primary">
                                        <div class="card-body py-2">
                                            <h6 class="card-title mb-1 text-primary">${total}</h6>
                                            <small class="text-muted">Total Issues</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center border-danger">
                                        <div class="card-body py-2">
                                            <h6 class="card-title mb-1 text-danger">${open}</h6>
                                            <small class="text-muted">Open</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center border-warning">
                                        <div class="card-body py-2">
                                            <h6 class="card-title mb-1 text-warning">${inProgress}</h6>
                                            <small class="text-muted">In Progress</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card text-center border-success">
                                        <div class="card-body py-2">
                                            <h6 class="card-title mb-1 text-success">${resolved}</h6>
                                            <small class="text-muted">Resolved</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <button class="btn btn-danger ms-3" onclick="addParameterIssue('${paramType}', ${paramId})">
                                <i class="fas fa-plus me-2"></i>Add Issue
                            </button>
                        </div>

                        ${issues.length === 0 ?
                            `<div class="text-center py-5">
                                <i class="fas fa-check-circle fa-3x text-success mb-3"></i>
                                <h6 class="text-muted mb-3">No Issues for ${parameterName}</h6>
                                <p class="text-muted mb-3">No issues have been reported for this parameter yet.</p>
                                <button class="btn btn-outline-danger" onclick="addParameterIssue('${paramType}', ${paramId})">
                                    <i class="fas fa-plus me-2"></i>Report First Issue
                                </button>
                            </div>` :
                            `<div class="card">
                                <div class="card-header">
                                    <h6 class="mb-0">Current Issues</h6>
                                </div>
                                <div class="card-body p-0">
                                    <div class="table-responsive">
                                        <table class="table table-hover mb-0">
                                            <thead class="table-light">
                                                <tr>
                                                    <th style="width: 5%">S.No</th>
                                                    <th style="width: 20%">Issue Title</th>
                                                    <th style="width: 25%">Description</th>
                                                    <th style="width: 10%">Priority</th>
                                                    <th style="width: 12%">Required By</th>
                                                    <th style="width: 15%">Team</th>
                                                    <th style="width: 10%">Status</th>
                                                    <th style="width: 8%">Edit</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${issues.map((issue, index) => `
                                                    <tr class="${issue.priority === 'high' ? 'table-danger' : issue.status === 'open' ? 'table-warning' : ''}">
                                                        <td>
                                                            <span class="badge bg-secondary">${index + 1}</span>
                                                        </td>
                                                        <td>
                                                            <strong>${issue.title || '-'}</strong>
                                                        </td>
                                                        <td>
                                                            <small>${issue.description ? (issue.description.length > 50 ? issue.description.substring(0, 50) + '...' : issue.description) : '-'}</small>
                                                        </td>
                                                        <td>
                                                            <span class="badge bg-${getPriorityBadgeClass(issue.priority)}">${issue.priority_display || '-'}</span>
                                                        </td>
                                                        <td>
                                                            <small>${issue.required_by || '-'}</small>
                                                        </td>
                                                        <td>
                                                            <small>${issue.team_name || 'Unassigned'}</small>
                                                        </td>
                                                        <td>
                                                            <span class="badge bg-${getIssueStatusBadgeClass(issue.status)}">${issue.status_display}</span>
                                                        </td>
                                                        <td>
                                                            <button class="btn btn-sm btn-outline-primary" onclick="editIssue(${issue.id})"
                                                                    data-bs-toggle="tooltip" title="Edit Issue">
                                                                <i class="fas fa-edit"></i>
                                                            </button>
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>`
                        }

                        <!-- Inline Add Issue Form (Initially Hidden) -->
                        <div class="mt-3" id="parameterIssueFormContainer" style="display: none;">
                            <div class="card">
                                <div class="card-header bg-warning">
                                    <h6 class="mb-0">
                                        <i class="fas fa-exclamation-triangle me-2"></i>New Issue for ${parameterName}
                                    </h6>
                                </div>
                                <div class="card-body">
                                    <form id="parameterIssueForm" onsubmit="saveParameterIssue(event, '${paramType}', ${paramId})">
                                        <div class="mb-3">
                                            <label for="paramIssueTitle" class="form-label">Issue Title <span class="text-danger">*</span></label>
                                            <input type="text" class="form-control" id="paramIssueTitle" name="title" required
                                                   placeholder="Brief description of the issue">
                                        </div>

                                        <div class="mb-3">
                                            <label for="paramIssueDescription" class="form-label">Description</label>
                                            <textarea class="form-control" id="paramIssueDescription" name="description" rows="3"
                                                      placeholder="Optional detailed description"></textarea>
                                        </div>

                                        <div class="row">
                                            <div class="col-md-6">
                                                <div class="mb-3">
                                                    <label for="paramIssuePriority" class="form-label">Priority</label>
                                                    <select class="form-control" id="paramIssuePriority" name="priority">
                                                        <option value="">Select</option>
                                                        <option value="high">High</option>
                                                        <option value="medium">Medium</option>
                                                        <option value="low">Low</option>
                                                    </select>
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <div class="mb-3">
                                                    <label for="paramIssueRequiredBy" class="form-label">Required to be resolved by</label>
                                                    <input type="date" class="form-control" id="paramIssueRequiredBy" name="required_by">
                                                </div>
                                            </div>
                                        </div>

                                        <div class="mb-3">
                                            <label for="paramIssueTeam" class="form-label">Team for which the issue has to be added <span class="text-danger">*</span></label>
                                            <select class="form-control" id="paramIssueTeam" name="team" required>
                                                <option value="">Select</option>
                                            </select>
                                            <div class="form-text">Teams where you are a member or in charge</div>
                                        </div>

                                        <div class="d-flex gap-2 mt-3">
                                            <button type="submit" class="btn btn-warning">
                                                <i class="fas fa-save me-2"></i>Save
                                            </button>
                                            <button type="button" class="btn btn-secondary" onclick="cancelParameterIssueForm()">
                                                Cancel
                                            </button>
                                        </div>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove existing modal if present
    const existingModal = document.getElementById('parameterIssuesModal');
    if (existingModal) {
        existingModal.remove();
    }

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHtml);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('parameterIssuesModal'));
    modal.show();

    // Load teams for the form
    loadTeamsForParameterIssue();
}

function loadTeamsForParameterIssue() {
    fetch('/api/issue-teams/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const teamSelect = document.getElementById('paramIssueTeam');
            if (teamSelect) {
                teamSelect.innerHTML = '<option value="">Select Team</option>';
                data.teams.forEach(team => {
                    teamSelect.innerHTML += `<option value="${team.id}">${team.name}</option>`;
                });
            }
        }
    })
    .catch(error => {
        console.error('Error loading teams:', error);
    });
}

function addParameterIssue(paramType, paramId) {
    // Show the inline form
    document.getElementById('parameterIssueFormContainer').style.display = 'block';
    document.getElementById('paramIssueTitle').focus();
}

function cancelParameterIssueForm() {
    document.getElementById('parameterIssueFormContainer').style.display = 'none';
    document.getElementById('parameterIssueForm').reset();
}

function saveParameterIssue(event, paramType, paramId) {
    event.preventDefault();

    const formData = new FormData(event.target);

    // Add parameter context
    formData.append('parameter_type', paramType);
    formData.append('parameter_id', paramId);

    // Add week/month context if available
    if (window.currentParameterContext) {
        if (window.currentParameterContext.weekNumber) {
            formData.append('week_number', window.currentParameterContext.weekNumber);
        }
        if (window.currentParameterContext.monthNumber) {
            formData.append('month_number', window.currentParameterContext.monthNumber);
        }
    }

    const saveBtn = event.target.querySelector('button[type="submit"]');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';

    fetch('/api/create-issue/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reset form and hide it
            cancelParameterIssueForm();

            // Reload the parameter issues to show the new issue
            if (window.currentParameterContext) {
                openParameterIssues(window.currentParameterContext.type, window.currentParameterContext.id);
            }

            showNotification('Issue created successfully', 'success');
        } else {
            showNotification('Error: ' + (data.error || 'Failed to create issue'), 'danger');
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-save me-2"></i>Save Issue';
        }
    })
    .catch(error => {
        console.error('Error saving issue:', error);
        showNotification('Error saving issue', 'danger');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save me-2"></i>Save Issue';
    });
}

function getIssueStatusBadgeClass(status) {
    const statusClasses = {
        'open': 'danger',
        'resolved': 'success',
        'on_hold': 'warning',
        'dropped': 'secondary',
        'escalated': 'info'
    };
    return statusClasses[status] || 'secondary';
}

// Project Actions and Issues functions
function openProjectActions(projectId, projectType) {
    window.currentProjectContext = {
        id: projectId,
        type: projectType
    };

    let queryParams = `project_id=${projectId}&project_type=${projectType}`;

    fetch(`/api/project-actions/?${queryParams}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success === false) {
            showNotification('Failed to load project actions: ' + (data.error || 'Unknown error'), 'danger');
            return;
        }
        if (!data.actions) {
            data.actions = [];
        }
        showProjectActionsModal(data, projectId, projectType);
    })
    .catch(error => {
        console.error('Error fetching project actions:', error);
        showNotification('Failed to load project actions: ' + error.message, 'danger');
    });
}

function openProjectIssues(projectId, projectType) {
    window.currentProjectContext = {
        id: projectId,
        type: projectType
    };

    let queryParams = `project_id=${projectId}&project_type=${projectType}`;

    fetch(`/api/project-issues/?${queryParams}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success === false) {
            showNotification('Failed to load project issues: ' + (data.error || 'Unknown error'), 'danger');
            return;
        }
        if (!data.issues) {
            data.issues = [];
        }
        showProjectIssuesModal(data, projectId, projectType);
    })
    .catch(error => {
        console.error('Error fetching project issues:', error);
        showNotification('Failed to load project issues: ' + error.message, 'danger');
    });
}

function openActionIssues(actionId) {
    window.currentActionContext = {
        id: actionId
    };

    fetch(`/api/action-issues/?action_id=${actionId}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success === false) {
            showNotification('Failed to load action issues: ' + (data.error || 'Unknown error'), 'danger');
            return;
        }
        if (!data.issues) {
            data.issues = [];
        }
        showActionIssuesModal(data, actionId);
    })
    .catch(error => {
        console.error('Error fetching action issues:', error);
        showNotification('Failed to load action issues: ' + error.message, 'danger');
    });
}

function showProjectActionsModal(data, projectId, projectType) {
    const modalHtml = `
        <div class="modal fade" id="projectActionsModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-plus-circle me-2"></i>Action Items for ${projectType} Project
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-12">
                                <div class="alert alert-info">
                                    <strong>Total Actions:</strong> ${data.actions.length}
                                </div>
                            </div>
                        </div>

                        <div class="table-responsive mb-3">
                            <table class="table table-bordered table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>S.No</th>
                                        <th>Action</th>
                                        <th>Priority</th>
                                        <th>Assigned To</th>
                                        <th>Due Date</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="projectActionsTableBody">
                                    ${data.actions.length > 0 ? data.actions.map((action, index) => `
                                        <tr>
                                            <td>${index + 1}</td>
                                            <td>${action.action}</td>
                                            <td><span class="badge bg-${action.priority === 'high' ? 'danger' : action.priority === 'medium' ? 'warning' : 'secondary'}">${action.priority_display}</span></td>
                                            <td>${action.assigned_to_name}</td>
                                            <td>${action.original_due_date || '-'}</td>
                                            <td><span class="badge bg-${action.status === 'completed' ? 'success' : action.status === 'in_progress' ? 'primary' : 'secondary'}">${action.status_display}</span></td>
                                            <td>
                                                <button class="btn btn-sm btn-outline-primary" onclick="editAction(${action.id})">
                                                    <i class="fas fa-edit"></i>
                                                </button>
                                            </td>
                                        </tr>
                                    `).join('') : '<tr><td colspan="7" class="text-center text-muted">No action items found</td></tr>'}
                                </tbody>
                            </table>
                        </div>

                        <div class="border-top pt-3">
                            <h6>Add New Action Item</h6>
                            <form id="projectActionForm" onsubmit="saveProjectAction(event, ${projectId}, '${projectType}')">
                                <div class="row mb-2">
                                    <div class="col-md-12">
                                        <input type="text" class="form-control" name="action" placeholder="Action description" required>
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <div class="col-md-3">
                                        <select class="form-select" name="team" id="projectActionTeamSelect" onchange="loadMembersForProjectAction(this.value)" required>
                                            <option value="">Select Team</option>
                                        </select>
                                    </div>
                                    <div class="col-md-3">
                                        <select class="form-select" name="assigned_to" id="projectActionMemberSelect" required>
                                            <option value="">Select Member</option>
                                        </select>
                                    </div>
                                    <div class="col-md-2">
                                        <select class="form-select" name="priority" required>
                                            <option value="">Priority</option>
                                            <option value="low">Low</option>
                                            <option value="medium">Medium</option>
                                            <option value="high">High</option>
                                        </select>
                                    </div>
                                    <div class="col-md-2">
                                        <input type="date" class="form-control" name="due_date" required>
                                    </div>
                                    <div class="col-md-2">
                                        <button type="submit" class="btn btn-primary w-100">
                                            <i class="fas fa-save me-1"></i>Save
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('projectActionsModal').innerHTML = modalHtml;
    loadTeamsForProjectAction();
    const modal = new bootstrap.Modal(document.querySelector('#projectActionsModal .modal'));
    modal.show();
}

function loadTeamsForProjectAction() {
    fetch('/api/user-teams/')
    .then(response => response.json())
    .then(data => {
        const select = document.getElementById('projectActionTeamSelect');
        if (select) {
            data.teams.forEach(team => {
                const option = document.createElement('option');
                option.value = team.id;
                option.textContent = team.name;
                select.appendChild(option);
            });
        }
    })
    .catch(error => console.error('Error loading teams:', error));
}

function loadMembersForProjectAction(teamId) {
    if (!teamId) {
        document.getElementById('projectActionMemberSelect').innerHTML = '<option value="">Select Member</option>';
        return;
    }

    fetch(`/api/team-members/${teamId}/`)
    .then(response => response.json())
    .then(data => {
        const select = document.getElementById('projectActionMemberSelect');
        select.innerHTML = '<option value="">Select Member</option>';
        if (data.success && data.members) {
            data.members.forEach(member => {
                const option = document.createElement('option');
                option.value = member.id;
                option.textContent = member.name;
                select.appendChild(option);
            });
        }
    })
    .catch(error => console.error('Error loading members:', error));
}

function showProjectIssuesModal(data, projectId, projectType) {
    const modalHtml = `
        <div class="modal fade" id="projectIssuesModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle me-2"></i>Issues for ${projectType} Project
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-12">
                                <div class="alert alert-info">
                                    <strong>Total Issues:</strong> ${data.issues.length}
                                </div>
                            </div>
                        </div>

                        <div class="table-responsive mb-3">
                            <table class="table table-bordered table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>S.No</th>
                                        <th>Issue Title</th>
                                        <th>Description</th>
                                        <th>Priority</th>
                                        <th>Required By</th>
                                        <th>Team</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="projectIssuesTableBody">
                                    ${data.issues.length > 0 ? data.issues.map((issue, index) => `
                                        <tr>
                                            <td>${index + 1}</td>
                                            <td>${issue.title}</td>
                                            <td>${issue.description || '-'}</td>
                                            <td><span class="badge bg-${issue.priority === 'high' ? 'danger' : issue.priority === 'medium' ? 'warning' : 'secondary'}">${issue.priority_display}</span></td>
                                            <td>${issue.required_by || '-'}</td>
                                            <td>${issue.team_name}</td>
                                            <td><span class="badge bg-${getIssueStatusBadgeClass(issue.status)}">${issue.status_display}</span></td>
                                            <td>
                                                <button class="btn btn-sm btn-outline-primary" onclick="editIssue(${issue.id})">
                                                    <i class="fas fa-edit"></i>
                                                </button>
                                            </td>
                                        </tr>
                                    `).join('') : '<tr><td colspan="8" class="text-center text-muted">No issues found</td></tr>'}
                                </tbody>
                            </table>
                        </div>

                        <div class="border-top pt-3">
                            <h6>Add New Issue</h6>
                            <form id="projectIssueForm" onsubmit="saveProjectIssue(event, ${projectId}, '${projectType}')">
                                <div class="row">
                                    <div class="col-md-3 mb-2">
                                        <input type="text" class="form-control" name="title" placeholder="Issue title" required>
                                    </div>
                                    <div class="col-md-3 mb-2">
                                        <input type="text" class="form-control" name="description" placeholder="Description">
                                    </div>
                                    <div class="col-md-2 mb-2">
                                        <select class="form-select" name="priority" required>
                                            <option value="">Priority</option>
                                            <option value="low">Low</option>
                                            <option value="medium">Medium</option>
                                            <option value="high">High</option>
                                        </select>
                                    </div>
                                    <div class="col-md-2 mb-2">
                                        <input type="date" class="form-control" name="required_by">
                                    </div>
                                    <div class="col-md-2 mb-2">
                                        <button type="submit" class="btn btn-danger w-100">
                                            <i class="fas fa-save me-1"></i>Save
                                        </button>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-4 mb-2">
                                        <select class="form-select" name="team" id="projectIssueTeamSelect" required>
                                            <option value="">Select Team</option>
                                        </select>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('projectIssuesModal').innerHTML = modalHtml;
    loadTeamsForProjectIssue();
    const modal = new bootstrap.Modal(document.querySelector('#projectIssuesModal .modal'));
    modal.show();
}

function showActionIssuesModal(data, actionId) {
    const modalHtml = `
        <div class="modal fade" id="actionIssuesModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-danger text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-exclamation-triangle me-2"></i>Issues for Action Item
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-12">
                                <div class="alert alert-info">
                                    <strong>Total Issues:</strong> ${data.issues.length}
                                </div>
                            </div>
                        </div>

                        <div class="table-responsive mb-3">
                            <table class="table table-bordered table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>S.No</th>
                                        <th>Issue Title</th>
                                        <th>Description</th>
                                        <th>Priority</th>
                                        <th>Required By</th>
                                        <th>Team</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="actionIssuesTableBody">
                                    ${data.issues.length > 0 ? data.issues.map((issue, index) => `
                                        <tr>
                                            <td>${index + 1}</td>
                                            <td>${issue.title}</td>
                                            <td>${issue.description || '-'}</td>
                                            <td><span class="badge bg-${issue.priority === 'high' ? 'danger' : issue.priority === 'medium' ? 'warning' : 'secondary'}">${issue.priority_display}</span></td>
                                            <td>${issue.required_by || '-'}</td>
                                            <td>${issue.team_name}</td>
                                            <td><span class="badge bg-${getIssueStatusBadgeClass(issue.status)}">${issue.status_display}</span></td>
                                            <td>
                                                <button class="btn btn-sm btn-outline-primary" onclick="editIssue(${issue.id})">
                                                    <i class="fas fa-edit"></i>
                                                </button>
                                            </td>
                                        </tr>
                                    `).join('') : '<tr><td colspan="8" class="text-center text-muted">No issues found</td></tr>'}
                                </tbody>
                            </table>
                        </div>

                        <div class="border-top pt-3">
                            <h6>Add New Issue</h6>
                            <form id="actionIssueForm" onsubmit="saveActionIssue(event, ${actionId})">
                                <div class="row">
                                    <div class="col-md-3 mb-2">
                                        <input type="text" class="form-control" name="title" placeholder="Issue title" required>
                                    </div>
                                    <div class="col-md-3 mb-2">
                                        <input type="text" class="form-control" name="description" placeholder="Description">
                                    </div>
                                    <div class="col-md-2 mb-2">
                                        <select class="form-select" name="priority" required>
                                            <option value="">Priority</option>
                                            <option value="low">Low</option>
                                            <option value="medium">Medium</option>
                                            <option value="high">High</option>
                                        </select>
                                    </div>
                                    <div class="col-md-2 mb-2">
                                        <input type="date" class="form-control" name="required_by">
                                    </div>
                                    <div class="col-md-2 mb-2">
                                        <button type="submit" class="btn btn-danger w-100">
                                            <i class="fas fa-save me-1"></i>Save
                                        </button>
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-4 mb-2">
                                        <select class="form-select" name="team" id="actionIssueTeamSelect" required>
                                            <option value="">Select Team</option>
                                        </select>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('actionIssuesModal').innerHTML = modalHtml;
    loadTeamsForActionIssue();
    const modal = new bootstrap.Modal(document.querySelector('#actionIssuesModal .modal'));
    modal.show();
}

function saveProjectAction(event, projectId, projectType) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    formData.append('project_id', projectId);
    formData.append('project_type', projectType);

    fetch('/api/create-action/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            form.reset();
            refreshProjectActionsTable(projectId, projectType);
            showNotification('Action created successfully', 'success');
        } else {
            showNotification('Error: ' + (data.error || 'Failed to create action'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving action:', error);
        showNotification('Error saving action', 'danger');
    });
}

function refreshProjectActionsTable(projectId, projectType) {
    fetch(`/api/project-actions/?project_id=${projectId}&project_type=${projectType}`, {
        method: 'GET',
        headers: {'X-CSRFToken': getCookie('csrftoken')}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.actions) {
            const tbody = document.getElementById('projectActionsTableBody');
            if (tbody) {
                tbody.innerHTML = data.actions.length > 0 ? data.actions.map((action, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${action.action}</td>
                        <td><span class="badge bg-${action.priority === 'high' ? 'danger' : action.priority === 'medium' ? 'warning' : 'secondary'}">${action.priority_display}</span></td>
                        <td>${action.assigned_to_name}</td>
                        <td>${action.original_due_date || '-'}</td>
                        <td><span class="badge bg-${action.status === 'completed' ? 'success' : action.status === 'in_progress' ? 'primary' : 'secondary'}">${action.status_display}</span></td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="editAction(${action.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                        </td>
                    </tr>
                `).join('') : '<tr><td colspan="7" class="text-center text-muted">No action items found</td></tr>';

                // Update count
                const alertDiv = document.querySelector('#projectActionsModal .alert-info strong');
                if (alertDiv) {
                    alertDiv.nextSibling.textContent = ` ${data.actions.length}`;
                }
            }
        }
    })
    .catch(error => console.error('Error refreshing actions:', error));
}

function saveProjectIssue(event, projectId, projectType) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    formData.append('project_id', projectId);
    formData.append('project_type', projectType);

    fetch('/api/create-issue/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            form.reset();
            refreshProjectIssuesTable(projectId, projectType);
            showNotification('Issue created successfully', 'success');
        } else {
            showNotification('Error: ' + (data.error || 'Failed to create issue'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving issue:', error);
        showNotification('Error saving issue', 'danger');
    });
}

function refreshProjectIssuesTable(projectId, projectType) {
    fetch(`/api/project-issues/?project_id=${projectId}&project_type=${projectType}`, {
        method: 'GET',
        headers: {'X-CSRFToken': getCookie('csrftoken')}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.issues) {
            const tbody = document.getElementById('projectIssuesTableBody');
            if (tbody) {
                tbody.innerHTML = data.issues.length > 0 ? data.issues.map((issue, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${issue.title}</td>
                        <td>${issue.description}</td>
                        <td><span class="badge bg-${issue.priority === 'high' ? 'danger' : issue.priority === 'medium' ? 'warning' : 'secondary'}">${issue.priority_display}</span></td>
                        <td>${issue.required_by || '-'}</td>
                        <td>${issue.team_name}</td>
                        <td><span class="badge bg-${issue.status === 'resolved' ? 'success' : issue.status === 'in_progress' ? 'primary' : 'secondary'}">${issue.status_display}</span></td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="editIssue(${issue.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                        </td>
                    </tr>
                `).join('') : '<tr><td colspan="8" class="text-center text-muted">No issues found</td></tr>';

                // Update count
                const alertDiv = document.querySelector('#projectIssuesModal .alert-info strong');
                if (alertDiv) {
                    alertDiv.nextSibling.textContent = ` ${data.issues.length}`;
                }
            }
        }
    })
    .catch(error => console.error('Error refreshing issues:', error));
}

function saveActionIssue(event, actionId) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    formData.append('action_id', actionId);

    fetch('/api/create-issue/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            form.reset();
            refreshActionIssuesTable(actionId);
            showNotification('Issue created successfully', 'success');
        } else {
            showNotification('Error: ' + (data.error || 'Failed to create issue'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving issue:', error);
        showNotification('Error saving issue', 'danger');
    });
}

function refreshActionIssuesTable(actionId) {
    fetch(`/api/action-issues/?action_id=${actionId}`, {
        method: 'GET',
        headers: {'X-CSRFToken': getCookie('csrftoken')}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.issues) {
            const tbody = document.getElementById('actionIssuesTableBody');
            if (tbody) {
                tbody.innerHTML = data.issues.length > 0 ? data.issues.map((issue, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${issue.title}</td>
                        <td>${issue.description}</td>
                        <td><span class="badge bg-${issue.priority === 'high' ? 'danger' : issue.priority === 'medium' ? 'warning' : 'secondary'}">${issue.priority_display}</span></td>
                        <td>${issue.required_by || '-'}</td>
                        <td>${issue.team_name}</td>
                        <td><span class="badge bg-${issue.status === 'resolved' ? 'success' : issue.status === 'in_progress' ? 'primary' : 'secondary'}">${issue.status_display}</span></td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="editIssue(${issue.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                        </td>
                    </tr>
                `).join('') : '<tr><td colspan="8" class="text-center text-muted">No issues found</td></tr>';

                // Update count
                const alertDiv = document.querySelector('#actionIssuesModal .alert-info strong');
                if (alertDiv) {
                    alertDiv.nextSibling.textContent = ` ${data.issues.length}`;
                }
            }
        }
    })
    .catch(error => console.error('Error refreshing issues:', error));
}

function loadTeamsForProjectIssue() {
    fetch('/api/issue-teams/')
    .then(response => response.json())
    .then(data => {
        const select = document.getElementById('projectIssueTeamSelect');
        if (select) {
            data.teams.forEach(team => {
                const option = document.createElement('option');
                option.value = team.id;
                option.textContent = team.name;
                select.appendChild(option);
            });
        }
    })
    .catch(error => console.error('Error loading teams:', error));
}

function loadTeamsForActionIssue() {
    fetch('/api/issue-teams/')
    .then(response => response.json())
    .then(data => {
        const select = document.getElementById('actionIssueTeamSelect');
        if (select) {
            data.teams.forEach(team => {
                const option = document.createElement('option');
                option.value = team.id;
                option.textContent = team.name;
                select.appendChild(option);
            });
        }
    })
    .catch(error => console.error('Error loading teams:', error));
}

// Action Actions (additional actions for an action item)
function openActionActions(actionId) {
    window.currentParentActionContext = {
        id: actionId
    };

    fetch(`/api/action-actions/?action_id=${actionId}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success === false) {
            showNotification('Failed to load action items: ' + (data.error || 'Unknown error'), 'danger');
            return;
        }
        if (!data.actions) {
            data.actions = [];
        }
        showActionActionsModal(data, actionId);
    })
    .catch(error => {
        console.error('Error fetching action actions:', error);
        showNotification('Failed to load action items: ' + error.message, 'danger');
    });
}

function showActionActionsModal(data, actionId) {
    const modalHtml = `
        <div class="modal fade" id="actionActionsModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-plus-circle me-2"></i>Action Items for Action
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-12">
                                <div class="alert alert-info">
                                    <strong>Total Actions:</strong> ${data.actions.length}
                                </div>
                            </div>
                        </div>

                        <div class="table-responsive mb-3">
                            <table class="table table-bordered table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>S.No</th>
                                        <th>Action</th>
                                        <th>Priority</th>
                                        <th>Assigned To</th>
                                        <th>Due Date</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="actionActionsTableBody">
                                    ${data.actions.length > 0 ? data.actions.map((action, index) => `
                                        <tr>
                                            <td>${index + 1}</td>
                                            <td>${action.action}</td>
                                            <td><span class="badge bg-${action.priority === 'high' ? 'danger' : action.priority === 'medium' ? 'warning' : 'secondary'}">${action.priority_display}</span></td>
                                            <td>${action.assigned_to_name}</td>
                                            <td>${action.original_due_date || '-'}</td>
                                            <td><span class="badge bg-${action.status === 'completed' ? 'success' : action.status === 'in_progress' ? 'primary' : 'secondary'}">${action.status_display}</span></td>
                                            <td>
                                                <button class="btn btn-sm btn-outline-primary" onclick="editAction(${action.id})">
                                                    <i class="fas fa-edit"></i>
                                                </button>
                                            </td>
                                        </tr>
                                    `).join('') : '<tr><td colspan="7" class="text-center text-muted">No action items found</td></tr>'}
                                </tbody>
                            </table>
                        </div>

                        <div class="border-top pt-3">
                            <h6>Add New Action Item</h6>
                            <form id="actionActionForm" onsubmit="saveActionAction(event, ${actionId})">
                                <div class="row mb-2">
                                    <div class="col-md-12">
                                        <input type="text" class="form-control" name="action" placeholder="Action description" required>
                                    </div>
                                </div>
                                <div class="row mb-2">
                                    <div class="col-md-3">
                                        <select class="form-select" name="team" id="actionActionTeamSelect" onchange="loadMembersForActionAction(this.value)" required>
                                            <option value="">Select Team</option>
                                        </select>
                                    </div>
                                    <div class="col-md-3">
                                        <select class="form-select" name="assigned_to" id="actionActionMemberSelect" required>
                                            <option value="">Select Member</option>
                                        </select>
                                    </div>
                                    <div class="col-md-2">
                                        <select class="form-select" name="priority" required>
                                            <option value="">Priority</option>
                                            <option value="low">Low</option>
                                            <option value="medium">Medium</option>
                                            <option value="high">High</option>
                                        </select>
                                    </div>
                                    <div class="col-md-2">
                                        <input type="date" class="form-control" name="due_date" required>
                                    </div>
                                    <div class="col-md-2">
                                        <button type="submit" class="btn btn-primary w-100">
                                            <i class="fas fa-save me-1"></i>Save
                                        </button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.getElementById('actionActionsModal').innerHTML = modalHtml;
    loadTeamsForActionAction();
    const modal = new bootstrap.Modal(document.querySelector('#actionActionsModal .modal'));
    modal.show();
}

function loadTeamsForActionAction() {
    fetch('/api/user-teams/')
    .then(response => response.json())
    .then(data => {
        const select = document.getElementById('actionActionTeamSelect');
        if (select) {
            data.teams.forEach(team => {
                const option = document.createElement('option');
                option.value = team.id;
                option.textContent = team.name;
                select.appendChild(option);
            });
        }
    })
    .catch(error => console.error('Error loading teams:', error));
}

function loadMembersForActionAction(teamId) {
    if (!teamId) {
        document.getElementById('actionActionMemberSelect').innerHTML = '<option value="">Select Member</option>';
        return;
    }

    fetch(`/api/team-members/${teamId}/`)
    .then(response => response.json())
    .then(data => {
        const select = document.getElementById('actionActionMemberSelect');
        select.innerHTML = '<option value="">Select Member</option>';
        if (data.success && data.members) {
            data.members.forEach(member => {
                const option = document.createElement('option');
                option.value = member.id;
                option.textContent = member.name;
                select.appendChild(option);
            });
        }
    })
    .catch(error => console.error('Error loading members:', error));
}

function saveActionAction(event, actionId) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    formData.append('parent_action_id', actionId);

    fetch('/api/create-action/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            form.reset();
            refreshActionActionsTable(actionId);
            showNotification('Action created successfully', 'success');
        } else {
            showNotification('Error: ' + (data.error || 'Failed to create action'), 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving action:', error);
        showNotification('Error saving action', 'danger');
    });
}

function refreshActionActionsTable(actionId) {
    fetch(`/api/action-actions/?action_id=${actionId}`, {
        method: 'GET',
        headers: {'X-CSRFToken': getCookie('csrftoken')}
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.actions) {
            const tbody = document.getElementById('actionActionsTableBody');
            if (tbody) {
                tbody.innerHTML = data.actions.length > 0 ? data.actions.map((action, index) => `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${action.action}</td>
                        <td><span class="badge bg-${action.priority === 'high' ? 'danger' : action.priority === 'medium' ? 'warning' : 'secondary'}">${action.priority_display}</span></td>
                        <td>${action.assigned_to_name}</td>
                        <td>${action.original_due_date || '-'}</td>
                        <td><span class="badge bg-${action.status === 'completed' ? 'success' : action.status === 'in_progress' ? 'primary' : 'secondary'}">${action.status_display}</span></td>
                        <td>
                            <button class="btn btn-sm btn-outline-primary" onclick="editAction(${action.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                        </td>
                    </tr>
                `).join('') : '<tr><td colspan="7" class="text-center text-muted">No action items found</td></tr>';

                // Update count
                const alertDiv = document.querySelector('#actionActionsModal .alert-info strong');
                if (alertDiv) {
                    alertDiv.nextSibling.textContent = ` ${data.actions.length}`;
                }
            }
        }
    })
    .catch(error => console.error('Error refreshing actions:', error));
}