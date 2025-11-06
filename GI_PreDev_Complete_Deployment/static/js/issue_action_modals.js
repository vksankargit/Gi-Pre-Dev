/**
 * Common JavaScript functionality for New Issue and New Action modals
 * Used across all screens in the PRE system
 */

// Global variables
let userTeams = []; // For actions - teams where user is manager
let issueTeams = []; // For issues - teams where user is manager or member
window.currentModal = null; // Make it explicitly global so other scripts can access it

// Initialize modal functionality
document.addEventListener('DOMContentLoaded', function() {
    // Only load teams if we're on a page that needs modals
    console.log('🔍 DEBUG: Checking for modal elements...');
    console.log('🔍 DEBUG: newActionModal exists?', !!document.getElementById('newActionModal'));
    console.log('🔍 DEBUG: newIssueModal exists?', !!document.getElementById('newIssueModal'));

    if (document.getElementById('newIssueModal') || document.getElementById('newActionModal')) {
        console.log('Modal elements detected, loading teams...');
        // Load teams for both modals if both exist
        if (document.getElementById('newActionModal')) {
            console.log('🔍 DEBUG: About to call loadUserTeams()');
            loadUserTeams(); // For action modal - manager only
        } else {
            console.log('🔍 DEBUG: newActionModal NOT found, skipping loadUserTeams()');
        }
        if (document.getElementById('newIssueModal')) {
            loadIssueTeams(); // For issue modal - manager or member
        }
    } else {
        console.log('No modal elements found, skipping teams API call');
    }
    setupModalEventHandlers();
});

/**
 * Load user's teams from the server (for Add Action modal - manager only)
 */
function loadUserTeams() {
    console.log('Loading user teams (manager only) from API...');
    fetch('/api/user-teams/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('API response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('API response data:', data);
        if (data.success) {
            userTeams = data.teams;
            console.log('User teams loaded:', userTeams.length, 'teams');
            populateActionTeamDropdown();
        } else {
            console.error('API returned error:', data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error loading user teams:', error);
        // Gracefully handle the error by using empty teams array
        userTeams = [];
        console.log('Continuing with empty teams array...');
    });
}

/**
 * Load teams for issue creation (manager or member)
 */
function loadIssueTeams() {
    console.log('Loading issue teams (manager or member) from API...');
    fetch('/api/issue-teams/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('API response status:', response.status);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('API response data:', data);
        if (data.success) {
            issueTeams = data.teams;
            console.log('Issue teams loaded:', issueTeams.length, 'teams');
            populateIssueTeamDropdown();
        } else {
            console.error('API returned error:', data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error loading issue teams:', error);
        // Gracefully handle the error by using empty teams array
        issueTeams = [];
        console.log('Continuing with empty teams array...');
    });
}

/**
 * Populate issue team dropdown
 */
function populateIssueTeamDropdown() {
    const issueTeamSelect = document.getElementById('issueTeam');

    if (issueTeamSelect) {
        issueTeamSelect.innerHTML = '<option value="">Select</option>';
        issueTeams.forEach(team => {
            issueTeamSelect.innerHTML += `<option value="${team.id}">${team.name}</option>`;
        });
    }
}

/**
 * Populate action team dropdown
 */
function populateActionTeamDropdown() {
    console.log('🔍 DEBUG: populateActionTeamDropdown called');
    const actionTeamSelect = document.getElementById('actionTeam');
    console.log('🔍 DEBUG: actionTeamSelect element:', actionTeamSelect);
    console.log('🔍 DEBUG: userTeams array:', userTeams);

    if (actionTeamSelect) {
        actionTeamSelect.innerHTML = '<option value="">Select</option>';
        userTeams.forEach(team => {
            actionTeamSelect.innerHTML += `<option value="${team.id}">${team.name}</option>`;
        });
        console.log('🔍 DEBUG: actionTeam dropdown populated with', userTeams.length, 'teams');
        console.log('🔍 DEBUG: actionTeam dropdown HTML:', actionTeamSelect.innerHTML);
    } else {
        console.log('❌ DEBUG: actionTeamSelect element NOT FOUND!');
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
        console.log('🔍 DEBUG: Attaching change event listener to actionTeam');
        actionTeamSelect.addEventListener('change', function(event) {
            console.log('🔍 DEBUG: Team dropdown changed!');
            console.log('🔍 DEBUG: Event target value:', event.target.value);
            console.log('🔍 DEBUG: actionTeamSelect.value:', actionTeamSelect.value);
            loadActionModalTeamMembers();
        });
    } else {
        console.log('❌ DEBUG: actionTeamSelect not found during setupModalEventHandlers');
    }

    // Modal cancel confirmation
    setupCancelConfirmation();
}

/**
 * Load team members when a team is selected for action modal
 * (Renamed to avoid collision with main.js loadTeamMembers)
 */
function loadActionModalTeamMembers() {
    console.log('🔍 DEBUG: loadActionModalTeamMembers called');
    const actionTeamSelect = document.getElementById('actionTeam');
    const memberSelect = document.getElementById('actionMember');

    console.log('🔍 DEBUG: actionTeamSelect:', actionTeamSelect);
    console.log('🔍 DEBUG: memberSelect:', memberSelect);

    if (!actionTeamSelect || !memberSelect) {
        console.log('❌ DEBUG: Missing actionTeamSelect or memberSelect - returning early');
        return;
    }

    const teamId = actionTeamSelect.value;
    console.log('🔍 DEBUG: Selected teamId:', teamId);

    if (!teamId) {
        console.log('❌ DEBUG: No teamId selected - clearing member dropdown');
        memberSelect.innerHTML = '<option value="">Select</option>';
        return;
    }

    console.log('✅ DEBUG: Making API call to /api/team-members/' + teamId + '/');

    fetch(`/api/team-members/${teamId}/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        console.log('📡 DEBUG: API response received, status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('📦 DEBUG: API data:', data);
        if (data.success) {
            memberSelect.innerHTML = '<option value="">Select</option>';
            data.members.forEach(member => {
                memberSelect.innerHTML += `<option value="${member.id}">${member.name}</option>`;
            });
            console.log('✅ DEBUG: Member dropdown populated with', data.members.length, 'members');
        } else {
            console.log('❌ DEBUG: API returned success=false, error:', data.error);
        }
    })
    .catch(error => {
        console.error('❌ Error loading team members:', error);
    });
}

/**
 * Open the New Issue modal
 */
function openNewIssueModal() {
    resetIssueForm();
    window.currentModal = new bootstrap.Modal(document.getElementById('newIssueModal'));
    window.currentModal.show();
}

/**
 * Open the New Action modal
 */
function openNewActionModal() {
    console.log('🔍 DEBUG: openNewActionModal called');

    // Populate the team dropdown when modal opens (in case it wasn't populated on page load)
    // MUST be done BEFORE resetActionForm() to ensure teams are available after reset
    console.log('🔍 DEBUG: Populating action team dropdown on modal open');
    populateActionTeamDropdown();

    // Reset form AFTER populating teams
    resetActionForm();

    // Debug: Check what's in the dropdown after reset
    const actionTeamSelect = document.getElementById('actionTeam');
    if (actionTeamSelect) {
        console.log('🔍 DEBUG: Team dropdown HTML after reset:', actionTeamSelect.innerHTML);
        console.log('🔍 DEBUG: Team dropdown options count:', actionTeamSelect.options.length);
    }

    window.currentModal = new bootstrap.Modal(document.getElementById('newActionModal'));
    window.currentModal.show();
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
                if (window.currentModal) {
                    window.currentModal.hide();
                }
                // Refresh page to show new issue in lists
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
                if (window.currentModal) {
                    window.currentModal.hide();
                }
                // Refresh page to show new action in lists
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
    // Store current team dropdown HTML before reset
    const actionTeamSelect = document.getElementById('actionTeam');
    const teamDropdownHTML = actionTeamSelect ? actionTeamSelect.innerHTML : '';

    // Reset the form
    document.getElementById('newActionForm').reset();

    // Restore team dropdown HTML (so teams don't get cleared)
    if (actionTeamSelect && teamDropdownHTML) {
        actionTeamSelect.innerHTML = teamDropdownHTML;
    }

    // Clear member dropdown
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
    console.log('🔧 Setting up cancel confirmation - removing data-bs-dismiss attributes');
    // Add confirmation for cancel buttons - expanded to cover all form modals
    const modals = [
        'newIssueModal',
        'newActionModal',
        'subActionModal',
        'addCoordinatorModal',
        'editCoordinatorModal',
        'editActionModal',
        'editProjectModal'
    ];

    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (modal) {
            // Find all buttons that would normally dismiss the modal
            const dismissButtons = modal.querySelectorAll('[data-bs-dismiss="modal"], .btn-close');
            console.log(`🔧 Found ${dismissButtons.length} dismiss buttons in ${modalId}`);

            dismissButtons.forEach((btn, index) => {
                // Skip if button already has onclick handlers (avoid conflicts)
                if (btn.hasAttribute('onclick')) {
                    console.log(`🔧 Skipping button ${index + 1} - already has onclick handler`);
                    return;
                }

                // Remove the data-bs-dismiss attribute to prevent automatic closing
                btn.removeAttribute('data-bs-dismiss');
                console.log(`🔧 Removed data-bs-dismiss from button ${index + 1}`);

                btn.addEventListener('click', function(e) {
                    console.log('🔍 Manual close handler triggered');
                    e.preventDefault();
                    e.stopImmediatePropagation();

                    const formId = modalId.replace('Modal', 'Form');
                    const form = document.getElementById(formId);

                    if (form && isFormDirty(form)) {
                        console.log('🔍 Form is dirty, showing confirm dialog');
                        const userWantsToClose = confirm('You will lose the data entered. Do you wish to continue?');
                        console.log('🔍 User wants to close:', userWantsToClose);

                        if (userWantsToClose) {
                            console.log('🔍 User confirmed - closing modal manually');
                            const modalInstance = bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal);
                            modalInstance.hide();
                        } else {
                            console.log('🔍 User cancelled - modal should stay open');
                            return false;
                        }
                    } else {
                        console.log('🔍 Form not dirty - closing modal normally');
                        const modalInstance = bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal);
                        modalInstance.hide();
                    }
                });
            });
        }
    });
}

/**
 * Check if form has been modified
 */
function isFormDirty(form) {
    const inputs = form.querySelectorAll('input, textarea, select');
    for (let input of inputs) {
        const value = input.value ? input.value.trim() : '';
        if (value !== '' && input.name !== 'csrfmiddlewaretoken') {
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

/**
 * Open issue modal for a specific parameter (GPI/FPI)
 * @param {string} paramType - 'gpi' or 'fpi'
 * @param {number} paramId - ID of the parameter
 */
function openNewIssueModalForParameter(paramType, paramId) {
    console.log(`Opening issue modal for ${paramType} parameter ${paramId}`);

    // Populate the hidden fields in the form
    document.getElementById('issueParameterType').value = paramType;
    document.getElementById('issueParameterId').value = paramId;

    // Open the regular issue modal
    openNewIssueModal();
}

/**
 * Open action modal for a specific parameter (GPI/FPI)
 * @param {string} paramType - 'gpi' or 'fpi'
 * @param {number} paramId - ID of the parameter
 */
function openNewActionModalForParameter(paramType, paramId) {
    console.log(`Opening action modal for ${paramType} parameter ${paramId}`);

    // Populate the hidden fields in the form
    document.getElementById('actionParameterType').value = paramType;
    document.getElementById('actionParameterId').value = paramId;

    // Open the regular action modal
    openNewActionModal();
}

// Expose global functions for compatibility with existing code
window.createIssue = openNewIssueModal;
window.addAction = openNewActionModal;
window.openNewIssueModal = openNewIssueModal;
window.openNewActionModal = openNewActionModal;
window.openNewIssueModalForParameter = openNewIssueModalForParameter;
window.openNewActionModalForParameter = openNewActionModalForParameter;