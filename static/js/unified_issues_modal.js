/**
 * Unified Issues Modal - JavaScript Handler
 * This modal can be called from any location in the application with dynamic source tracking
 */

// Global variable to store current context
window.unifiedIssuesContext = null;

/**
 * Open the unified issues modal with source information
 * @param {Object} context - Context object containing source information
 *
 * Context object structure:
 * {
 *   location: 'implement' | 'review',
 *   screen: 'my_numbers' | 'my_projects' | 'my_todo' | 'gpi' | 'ppi',
 *   level: 'screen' | 'item',
 *   period: 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'adhoc',
 *   periodNumber: number (week/month/quarter number),
 *   itemType: 'gpi' | 'ppi' | 'action',
 *   itemId: number,
 *   itemName: string,
 *   teamId: number,
 *   meetingId: number (for review context),
 *   reviewDate: string (for review context)
 * }
 */
function openUnifiedIssuesModal(context) {
    console.log('🔵 Opening Unified Issues Modal with context:', context);

    // Store context globally
    window.unifiedIssuesContext = context;

    // Build source display string
    const sourceDisplay = buildSourceDisplay(context);
    document.getElementById('issuesSourceDisplay').textContent = sourceDisplay;

    // Build source string for API
    const sourceString = buildSourceString(context);
    document.getElementById('issuesModalSource').value = sourceString;

    // Populate team dropdown
    populateUnifiedIssueTeams();

    // Reset the form
    resetUnifiedIssueForm();

    // Load existing issues
    loadExistingIssues(context);

    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('unifiedIssuesModal'));
    modal.show();
}

/**
 * Build human-readable source display string
 */
function buildSourceDisplay(context) {
    const parts = [];

    // Location
    parts.push(context.location === 'implement' ? 'Implement' : 'Review');

    // Period information
    if (context.period === 'weekly' && context.periodNumber) {
        parts.push(`Week ${context.periodNumber}`);
    } else if (context.period === 'monthly' && context.periodNumber) {
        parts.push(`Month ${context.periodNumber}`);
    } else if (context.period === 'quarterly' && context.periodNumber) {
        parts.push(`Quarter ${context.periodNumber}`);
    } else if (context.period === 'yearly') {
        parts.push('Annual');
    } else if (context.period === 'adhoc') {
        parts.push('Ad-hoc');
    }

    // Review specific info
    if (context.location === 'review' && context.reviewDate) {
        parts.push(`(${context.reviewDate})`);
    }

    // Item level info
    if (context.level === 'item' && context.itemName) {
        parts.push(`- ${context.itemName}`);
    }

    // Screen level info
    if (context.level === 'screen') {
        if (context.screen === 'my_numbers') {
            parts.push('- My Numbers');
        } else if (context.screen === 'my_projects') {
            parts.push('- My Projects');
        } else if (context.screen === 'my_todo') {
            parts.push('- My To Do');
        }
    }

    return parts.join(' ');
}

/**
 * Build source string for API storage
 */
function buildSourceString(context) {
    const parts = [];

    // Location
    parts.push(context.location === 'implement' ? 'Implement' : 'Review');

    // Period
    if (context.period === 'weekly' && context.periodNumber) {
        parts.push(`Week ${context.periodNumber}`);
    } else if (context.period === 'monthly' && context.periodNumber) {
        parts.push(`Month ${context.periodNumber}`);
    } else if (context.period === 'quarterly' && context.periodNumber) {
        parts.push(`Quarter ${context.periodNumber}`);
    } else if (context.period === 'yearly') {
        parts.push('Annual');
    } else if (context.period === 'adhoc') {
        parts.push('Ad-hoc');
    } else if (context.period === 'manual') {
        parts.push('Manual');
    }

    // Item name
    if (context.level === 'item' && context.itemName) {
        parts.push(context.itemName);
    }

    // Action source (for My To Do item level)
    if (context.itemType === 'action' && context.actionSource) {
        parts.push(context.actionSource);
    }

    return parts.join(' + ');
}

/**
 * Populate team dropdown for unified issues modal
 */
function populateUnifiedIssueTeams() {
    const teamSelect = document.getElementById('unifiedIssueTeam');
    if (!teamSelect) return;

    // Clear existing options except the first one
    teamSelect.innerHTML = '<option value="">Select</option>';

    // Fetch teams
    fetch('/api/user-teams/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.teams) {
            data.teams.forEach(team => {
                const option = document.createElement('option');
                option.value = team.id;
                option.textContent = team.name;
                teamSelect.appendChild(option);
            });

            // Pre-select team if provided in context
            if (window.unifiedIssuesContext && window.unifiedIssuesContext.teamId) {
                teamSelect.value = window.unifiedIssuesContext.teamId;
            }
        }
    })
    .catch(error => {
        console.error('Error loading teams:', error);
    });
}

/**
 * Load existing issues based on context
 */
function loadExistingIssues(context) {
    const tbody = document.getElementById('issuesTableBody');
    const spinner = document.getElementById('issuesLoadingSpinner');

    // Show loading spinner
    if (spinner) {
        tbody.innerHTML = `
            <tr id="issuesLoadingSpinner">
                <td colspan="8" class="text-center py-4">
                    <i class="fas fa-spinner fa-spin fa-2x text-muted"></i>
                    <p class="text-muted mt-2">Loading issues...</p>
                </td>
            </tr>
        `;
    }

    // Build query parameters based on context
    let endpoint = '/api/unified-issues/';
    const params = new URLSearchParams();

    params.append('location', context.location);
    params.append('level', context.level);

    if (context.screen) params.append('screen', context.screen);
    if (context.period) params.append('period', context.period);
    if (context.periodNumber) params.append('period_number', context.periodNumber);
    if (context.itemType) params.append('item_type', context.itemType);
    if (context.itemId) params.append('item_id', context.itemId);
    if (context.teamId) params.append('team_id', context.teamId);
    if (context.meetingId) params.append('meeting_id', context.meetingId);

    endpoint += '?' + params.toString();

    console.log('🔍 Fetching issues from:', endpoint);

    fetch(endpoint, {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('📡 Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('📊 Response data:', data);
        if (data.success) {
            renderIssuesGrid(data.issues);
        } else {
            console.error('❌ API returned success=false:', data.error);
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-4">
                        <i class="fas fa-exclamation-triangle fa-2x text-danger"></i>
                        <p class="text-danger mt-2">Error loading issues: ${data.error || 'Unknown error'}</p>
                    </td>
                </tr>
            `;
        }
    })
    .catch(error => {
        console.error('❌ Error loading issues:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-4">
                    <i class="fas fa-exclamation-triangle fa-2x text-danger"></i>
                    <p class="text-danger mt-2">Error loading issues: ${error.message}</p>
                </td>
            </tr>
        `;
    });
}

/**
 * Render issues in the grid (matching GPI modal style)
 */
function renderIssuesGrid(issues) {
    const tbody = document.getElementById('issuesTableBody');
    const countSpan = document.getElementById('issuesTotalCount');

    // Update count
    if (countSpan) {
        countSpan.textContent = issues.length;
    }

    if (issues.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-muted">No issues found</td>
            </tr>
        `;
        return;
    }

    // Build table rows
    let html = '';
    issues.forEach((issue, index) => {
        const priorityBadge = issue.priority ?
            `<span class="badge bg-${getPriorityBadgeClass(issue.priority)}">${issue.priority_display || issue.priority}</span>` :
            '-';

        const statusBadge = `<span class="badge bg-${getIssueStatusBadgeClass(issue.status)}">${issue.status_display || issue.status}</span>`;

        const requiredBy = issue.required_by || '-';
        const description = issue.description ? (issue.description.length > 50 ? issue.description.substring(0, 50) + '...' : issue.description) : '-';

        html += `
            <tr>
                <td>${index + 1}</td>
                <td>${issue.title || '-'}</td>
                <td>${description}</td>
                <td>${priorityBadge}</td>
                <td>${requiredBy}</td>
                <td>${issue.team_name || 'Unassigned'}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="editIssue(${issue.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

/**
 * Helper function to get priority badge class
 */
function getPriorityBadgeClass(priority) {
    if (priority === 'high') return 'danger';
    if (priority === 'medium') return 'warning';
    return 'secondary';
}

/**
 * Helper function to get issue status badge class
 */
function getIssueStatusBadgeClass(status) {
    if (status === 'resolved') return 'success';
    if (status === 'open') return 'secondary';
    if (status === 'acknowledged') return 'info';
    if (status === 'parked') return 'warning';
    return 'danger';
}

/**
 * Placeholder edit function (can be implemented later)
 */
function editIssue(issueId) {
    alert(`Edit issue ${issueId} - Feature coming soon`);
}

/**
 * Reset the unified issue form
 */
function resetUnifiedIssueForm() {
    const form = document.getElementById('unifiedIssueForm');
    if (form) {
        form.reset();
    }

    // Clear error and success messages
    const errorDiv = document.getElementById('unifiedIssueFormError');
    const successDiv = document.getElementById('unifiedIssueFormSuccess');
    if (errorDiv) errorDiv.classList.add('d-none');
    if (successDiv) successDiv.classList.add('d-none');

    // Clear validation states
    document.querySelectorAll('#unifiedIssueForm .is-invalid').forEach(el => {
        el.classList.remove('is-invalid');
    });
}

/**
 * Add another issue (allows adding multiple issues without closing modal)
 */
function addAnotherIssue() {
    const form = document.getElementById('unifiedIssueForm');
    const formData = new FormData(form);

    // Add source information
    const source = document.getElementById('issuesModalSource').value;
    formData.append('source', source);

    // Add context information for parameter linking
    if (window.unifiedIssuesContext) {
        const ctx = window.unifiedIssuesContext;

        if (ctx.itemType && ctx.itemId) {
            formData.append('parameter_type', ctx.itemType);
            formData.append('parameter_id', ctx.itemId);
        }

        if (ctx.periodNumber) {
            if (ctx.period === 'weekly') {
                formData.append('week_number', ctx.periodNumber);
            } else if (ctx.period === 'monthly') {
                formData.append('month_number', ctx.periodNumber);
            }
        }

        // Add review meeting ID if from review location
        if (ctx.location === 'review' && ctx.meetingId) {
            formData.append('meeting_id', ctx.meetingId);
        }
    }

    // Clear previous errors
    document.getElementById('unifiedIssueFormError').classList.add('d-none');
    document.getElementById('unifiedIssueFormSuccess').classList.add('d-none');

    // Validate required fields
    const title = document.getElementById('unifiedIssueTitle').value.trim();
    const team = document.getElementById('unifiedIssueTeam').value;

    if (!title) {
        showUnifiedIssueError('Issue title is required');
        document.getElementById('unifiedIssueTitle').classList.add('is-invalid');
        return;
    }

    if (!team) {
        showUnifiedIssueError('Team is required');
        document.getElementById('unifiedIssueTeam').classList.add('is-invalid');
        return;
    }

    // Disable add button
    const addBtn = document.getElementById('addMoreIssueBtn');
    const originalHTML = addBtn.innerHTML;
    addBtn.disabled = true;
    addBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Adding...';

    // Submit to API
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
            showUnifiedIssueSuccess('Issue added successfully! Add another or close the modal.');
            resetUnifiedIssueForm();

            // Reload issues grid to show the new issue
            if (window.unifiedIssuesContext) {
                loadExistingIssues(window.unifiedIssuesContext);
            }

            // Auto-hide success message after 3 seconds
            setTimeout(() => {
                document.getElementById('unifiedIssueFormSuccess').classList.add('d-none');
            }, 3000);
        } else {
            showUnifiedIssueError(data.error || 'Error creating issue');
        }
    })
    .catch(error => {
        console.error('Error saving issue:', error);
        showUnifiedIssueError('Network error. Please try again.');
    })
    .finally(() => {
        // Re-enable add button
        addBtn.disabled = false;
        addBtn.innerHTML = originalHTML;
    });
}

/**
 * Show error message
 */
function showUnifiedIssueError(message) {
    const errorDiv = document.getElementById('unifiedIssueFormError');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('d-none');
    }
}

/**
 * Show success message
 */
function showUnifiedIssueSuccess(message) {
    const successDiv = document.getElementById('unifiedIssueFormSuccess');
    if (successDiv) {
        successDiv.textContent = message;
        successDiv.classList.remove('d-none');

        // Auto-hide after 3 seconds
        setTimeout(() => {
            successDiv.classList.add('d-none');
        }, 3000);
    }
}

/**
 * Helper function to get CSRF token
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

// Make functions globally available
window.openUnifiedIssuesModal = openUnifiedIssuesModal;
window.resetUnifiedIssueForm = resetUnifiedIssueForm;
window.saveUnifiedIssue = saveUnifiedIssue;
