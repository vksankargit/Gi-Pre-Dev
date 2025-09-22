/**
 * Common JavaScript functionality for New Issue and New Action modals
 * Used across all screens in the PRE system
 */

// Global variables
let userTeams = [];
let currentModal = null;

// Initialize modal functionality
document.addEventListener('DOMContentLoaded', function() {
    loadUserTeams();
    setupModalEventHandlers();
});

/**
 * Load user's teams from the server
 */
function loadUserTeams() {
    console.log('Loading user teams from API...');
    fetch('/api/user-teams/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('API response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('API response data:', data);
        if (data.success) {
            userTeams = data.teams;
            console.log('User teams loaded:', userTeams.length, 'teams');
            populateTeamDropdowns();
        } else {
            console.error('API returned error:', data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error loading user teams:', error);
    });
}

/**
 * Populate team dropdowns in both modals
 */
function populateTeamDropdowns() {
    console.log('Populating team dropdowns with', userTeams.length, 'teams');
    const issueTeamSelect = document.getElementById('issueTeam');
    const actionTeamSelect = document.getElementById('actionTeam');

    if (issueTeamSelect) {
        issueTeamSelect.innerHTML = '<option value="">Select</option>';
        userTeams.forEach(team => {
            console.log('Adding team to issue dropdown:', team.name);
            issueTeamSelect.innerHTML += `<option value="${team.id}">${team.name}</option>`;
        });
        console.log('Issue team dropdown now has', issueTeamSelect.options.length, 'options');
    } else {
        console.error('Issue team select element not found');
    }

    if (actionTeamSelect) {
        actionTeamSelect.innerHTML = '<option value="">Select</option>';
        userTeams.forEach(team => {
            actionTeamSelect.innerHTML += `<option value="${team.id}">${team.name}</option>`;
        });
        console.log('Action team dropdown now has', actionTeamSelect.options.length, 'options');
    } else {
        console.error('Action team select element not found');
    }
}

/**
 * Setup event handlers for modals
 */
function setupModalEventHandlers() {
    // Issue modal save button
    const saveIssueBtn = document.getElementById('saveIssueBtn');
    if (saveIssueBtn) {
        saveIssueBtn.addEventListener('click', saveIssue);
    }

    // Action modal save button
    const saveActionBtn = document.getElementById('saveActionBtn');
    if (saveActionBtn) {
        saveActionBtn.addEventListener('click', saveAction);
    }

    // Action team selection to load members
    const actionTeamSelect = document.getElementById('actionTeam');
    if (actionTeamSelect) {
        actionTeamSelect.addEventListener('change', loadTeamMembers);
    }

    // Modal cancel confirmation
    setupCancelConfirmation();
}

/**
 * Load team members when a team is selected for action
 */
function loadTeamMembers() {
    const teamId = document.getElementById('actionTeam').value;
    const memberSelect = document.getElementById('actionMember');

    if (!teamId) {
        memberSelect.innerHTML = '<option value="">Select</option>';
        return;
    }

    fetch(`/api/team-members/${teamId}/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            memberSelect.innerHTML = '<option value="">Select</option>';
            data.members.forEach(member => {
                memberSelect.innerHTML += `<option value="${member.id}">${member.name}</option>`;
            });
        }
    })
    .catch(error => {
        console.error('Error loading team members:', error);
    });
}

/**
 * Open the New Issue modal
 */
function openNewIssueModal() {
    resetIssueForm();
    currentModal = new bootstrap.Modal(document.getElementById('newIssueModal'));
    currentModal.show();
}

/**
 * Open the New Action modal
 */
function openNewActionModal() {
    resetActionForm();
    currentModal = new bootstrap.Modal(document.getElementById('newActionModal'));
    currentModal.show();
}

/**
 * Save new issue
 */
function saveIssue() {
    const form = document.getElementById('newIssueForm');
    const formData = new FormData(form);

    // Clear previous errors
    clearFormErrors('issue');

    // Validate required fields
    const title = document.getElementById('issueTitle').value.trim();
    const team = document.getElementById('issueTeam').value;

    if (!title) {
        showFieldError('issueTitle', 'Issue title is required');
        return;
    }

    if (!team) {
        showFieldError('issueTeam', 'Please select a team');
        return;
    }

    // Disable save button
    const saveBtn = document.getElementById('saveIssueBtn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';

    fetch('/api/create-issue/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage('Issue created successfully!', 'issue');
            setTimeout(() => {
                currentModal.hide();
                // Refresh the page or update the relevant section
                location.reload();
            }, 1500);
        } else {
            showErrorMessage(data.error || 'Error creating issue', 'issue');
        }
    })
    .catch(error => {
        console.error('Error saving issue:', error);
        showErrorMessage('Network error. Please try again.', 'issue');
    })
    .finally(() => {
        // Re-enable save button
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save me-2"></i>Save';
    });
}

/**
 * Save new action
 */
function saveAction() {
    const form = document.getElementById('newActionForm');
    const formData = new FormData(form);

    // Clear previous errors
    clearFormErrors('action');

    // Validate required fields
    const action = document.getElementById('actionTitle').value.trim();
    const team = document.getElementById('actionTeam').value;
    const assignedTo = document.getElementById('actionMember').value;

    if (!action) {
        showFieldError('actionTitle', 'Action is required');
        return;
    }

    if (!team) {
        showFieldError('actionTeam', 'Please select a team');
        return;
    }

    if (!assignedTo) {
        showFieldError('actionMember', 'Please select a member');
        return;
    }

    // Disable save button
    const saveBtn = document.getElementById('saveActionBtn');
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';

    fetch('/api/create-action/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccessMessage('Action created successfully!', 'action');
            setTimeout(() => {
                currentModal.hide();
                // Refresh the page or update the relevant section
                location.reload();
            }, 1500);
        } else {
            showErrorMessage(data.error || 'Error creating action', 'action');
        }
    })
    .catch(error => {
        console.error('Error saving action:', error);
        showErrorMessage('Network error. Please try again.', 'action');
    })
    .finally(() => {
        // Re-enable save button
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="fas fa-save me-2"></i>Save';
    });
}

/**
 * Reset issue form
 */
function resetIssueForm() {
    document.getElementById('newIssueForm').reset();
    clearFormErrors('issue');
}

/**
 * Reset action form
 */
function resetActionForm() {
    document.getElementById('newActionForm').reset();
    document.getElementById('actionMember').innerHTML = '<option value="">Select</option>';
    clearFormErrors('action');
}

/**
 * Clear form errors
 */
function clearFormErrors(formType) {
    const errorDiv = document.getElementById(`${formType}FormError`);
    const successDiv = document.getElementById(`${formType}FormSuccess`);

    if (errorDiv) errorDiv.classList.add('d-none');
    if (successDiv) successDiv.classList.add('d-none');

    // Clear field-specific errors
    const errorElements = document.querySelectorAll(`#${formType}TitleError, #${formType}TeamError, #${formType}MemberError`);
    errorElements.forEach(el => el.textContent = '');

    // Remove invalid classes
    const inputs = document.querySelectorAll(`#new${formType.charAt(0).toUpperCase() + formType.slice(1)}Form .form-control`);
    inputs.forEach(input => input.classList.remove('is-invalid'));
}

/**
 * Show field-specific error
 */
function showFieldError(fieldId, message) {
    const field = document.getElementById(fieldId);
    const errorElement = document.getElementById(`${fieldId}Error`);

    if (field) field.classList.add('is-invalid');
    if (errorElement) errorElement.textContent = message;
}

/**
 * Show error message
 */
function showErrorMessage(message, formType) {
    const errorDiv = document.getElementById(`${formType}FormError`);
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('d-none');
    }
}

/**
 * Show success message
 */
function showSuccessMessage(message, formType) {
    const successDiv = document.getElementById(`${formType}FormSuccess`);
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.classList.remove('d-none');
    }
}

/**
 * Setup cancel confirmation
 */
function setupCancelConfirmation() {
    // Add confirmation for cancel buttons
    const modals = ['newIssueModal', 'newActionModal'];

    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (modal) {
            const cancelBtn = modal.querySelector('[data-bs-dismiss="modal"]');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', function(e) {
                    const formId = modalId.replace('Modal', 'Form');
                    const form = document.getElementById(formId);

                    if (form && isFormDirty(form)) {
                        e.preventDefault();
                        if (confirm('You will lose the data entered. Do you wish to continue?')) {
                            currentModal.hide();
                        }
                    }
                });
            }
        }
    });
}

/**
 * Check if form has been modified
 */
function isFormDirty(form) {
    const inputs = form.querySelectorAll('input, textarea, select');
    for (let input of inputs) {
        if (input.value && input.value.trim() !== '') {
            return true;
        }
    }
    return false;
}

/**
 * Get CSRF token from cookies
 */
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

// Expose global functions for compatibility with existing code
window.createIssue = openNewIssueModal;
window.addAction = openNewActionModal;
window.openNewIssueModal = openNewIssueModal;
window.openNewActionModal = openNewActionModal;