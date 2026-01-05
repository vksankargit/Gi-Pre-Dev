/**
 * New Review Form - JavaScript for dynamic interactions
 * Handles: Team selection, Cadence/Ad-Hoc toggle, Period selection, Auto-fill, Participants, Warnings
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const teamSelect = document.getElementById('team');
    const meetingTypeDisplay = document.getElementById('meeting_type_display');
    const cadenceDisplayContainer = document.getElementById('cadence_display_container');
    const cadenceDisplay = document.getElementById('cadence_display');
    const reviewTypeHidden = document.getElementById('review_type');
    const participantsList = document.getElementById('participantsList');

    // Meeting category radio buttons
    const cadenceMeetingRadio = document.getElementById('cadence_meeting');
    const adhocMeetingRadio = document.getElementById('adhoc_meeting');
    const isAdhocHidden = document.getElementById('is_adhoc');

    // Period selection elements
    const periodSelectionContainer = document.getElementById('period_selection_container');
    const weekSelection = document.getElementById('week_selection');
    const monthSelection = document.getElementById('month_selection');
    const quarterSelection = document.getElementById('quarter_selection');
    const yearSelection = document.getElementById('year_selection');

    const selectedWeekSelect = document.getElementById('selected_week');
    const selectedMonthSelect = document.getElementById('selected_month');
    const selectedQuarterSelect = document.getElementById('selected_quarter');
    const selectedYearSelect = document.getElementById('selected_year');

    // Date/time inputs
    const reviewDateInput = document.getElementById('review_date');
    const reviewTimeInput = document.getElementById('review_time');

    // Warning message
    const pendingReviewWarning = document.getElementById('pending_review_warning');
    const pendingReviewMessage = document.getElementById('pending_review_message');

    // Current selected team data
    let currentTeamData = null;

    // Set default date to today and time to current hour
    const today = new Date().toISOString().split('T')[0];
    reviewDateInput.value = today;

    const now = new Date();
    const currentTime = now.getHours().toString().padStart(2, '0') + ':00';
    reviewTimeInput.value = currentTime;

    // Initialize cadence display on page load (since Cadence is selected by default)
    if (cadenceMeetingRadio.checked) {
        cadenceDisplayContainer.style.display = 'block';
    }

    /**
     * Handle team selection change
     */
    teamSelect.addEventListener('change', function() {
        const teamId = parseInt(this.value);

        if (!teamId) {
            resetForm();
            return;
        }

        // Find team data
        currentTeamData = teamsData.find(t => t.id === teamId);

        if (!currentTeamData) {
            console.error('Team data not found for team ID:', teamId);
            return;
        }

        // Update meeting type display
        meetingTypeDisplay.value = currentTeamData.meeting_type || 'N/A';

        // Update cadence display
        if (currentTeamData.cadence) {
            const cadenceText = currentTeamData.cadence.charAt(0).toUpperCase() + currentTeamData.cadence.slice(1);
            cadenceDisplay.value = cadenceText;

            // Auto-fill review_type from cadence
            reviewTypeHidden.value = currentTeamData.cadence;
        } else {
            cadenceDisplay.value = 'No cadence set';
            reviewTypeHidden.value = 'weekly'; // Default fallback
        }

        // Load team members for participants
        loadTeamMembers(teamId);

        // Update period selections if cadence meeting
        if (cadenceMeetingRadio.checked && currentTeamData.cadence) {
            updatePeriodSelections();
        }

        // Auto-fill time from team meeting time
        if (currentTeamData.meeting_time) {
            reviewTimeInput.value = currentTeamData.meeting_time;
        }
    });

    /**
     * Handle cadence/ad-hoc radio button changes
     */
    cadenceMeetingRadio.addEventListener('change', function() {
        if (this.checked) {
            isAdhocHidden.value = 'false';
            cadenceDisplayContainer.style.display = 'block';

            if (currentTeamData && currentTeamData.cadence) {
                periodSelectionContainer.style.display = 'block';
                updatePeriodSelections();
            }
        }
    });

    adhocMeetingRadio.addEventListener('change', function() {
        if (this.checked) {
            isAdhocHidden.value = 'true';
            cadenceDisplayContainer.style.display = 'none';
            periodSelectionContainer.style.display = 'none';

            // Hide all period selections
            weekSelection.style.display = 'none';
            monthSelection.style.display = 'none';
            quarterSelection.style.display = 'none';
            yearSelection.style.display = 'none';
        }
    });

    /**
     * Update period selections based on team cadence
     */
    function updatePeriodSelections() {
        if (!currentTeamData || !currentTeamData.cadence) {
            return;
        }

        // Show the period selection container
        periodSelectionContainer.style.display = 'block';

        // Hide all period selections first
        weekSelection.style.display = 'none';
        monthSelection.style.display = 'none';
        quarterSelection.style.display = 'none';
        yearSelection.style.display = 'none';

        // Show appropriate selection based on cadence
        switch (currentTeamData.cadence) {
            case 'weekly':
                weekSelection.style.display = 'block';
                loadAvailableWeeks();
                break;
            case 'monthly':
                monthSelection.style.display = 'block';
                loadAvailableMonths();
                break;
            case 'quarterly':
                quarterSelection.style.display = 'block';
                loadAvailableQuarters();
                break;
            case 'annually':
                yearSelection.style.display = 'block';
                loadAvailableYears();
                break;
        }
    }

    /**
     * Load available weeks (from last review to current week)
     */
    function loadAvailableWeeks() {
        const teamId = parseInt(teamSelect.value);
        console.log('Loading weeks for team:', teamId);

        // Fetch available weeks from backend
        fetch(`/api/available-periods/?team_id=${teamId}&period_type=week`)
            .then(response => {
                console.log('Week API response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Week API data:', data);
                selectedWeekSelect.innerHTML = '<option value="">Select Week</option>';

                if (data.success && data.periods && data.periods.length > 0) {
                    console.log(`Adding ${data.periods.length} weeks with ISO numbers`);
                    data.periods.forEach(period => {
                        const option = document.createElement('option');
                        option.value = period.number;
                        option.textContent = `Week ${period.number} (${period.date_range})`;
                        selectedWeekSelect.appendChild(option);
                    });
                } else {
                    console.warn('No periods in response, using fallback');
                    // Fallback: generate weeks 1-13 (one quarter)
                    for (let i = 1; i <= 13; i++) {
                        const option = document.createElement('option');
                        option.value = i;
                        option.textContent = `Week ${i}`;
                        selectedWeekSelect.appendChild(option);
                    }
                }
            })
            .catch(error => {
                console.error('Error loading weeks:', error);
                // Fallback
                for (let i = 1; i <= 13; i++) {
                    const option = document.createElement('option');
                    option.value = i;
                    option.textContent = `Week ${i}`;
                    selectedWeekSelect.appendChild(option);
                }
            });
    }

    /**
     * Load available months (from last review to current month)
     */
    function loadAvailableMonths() {
        const teamId = parseInt(teamSelect.value);

        fetch(`/api/available-periods/?team_id=${teamId}&period_type=month`)
            .then(response => response.json())
            .then(data => {
                selectedMonthSelect.innerHTML = '<option value="">Select Month</option>';

                if (data.success && data.periods && data.periods.length > 0) {
                    data.periods.forEach(period => {
                        const option = document.createElement('option');
                        option.value = period.number;
                        option.textContent = `Month ${period.number} (${period.name})`;
                        selectedMonthSelect.appendChild(option);
                    });
                } else {
                    // Fallback: generate months 1-3 (one quarter)
                    const monthNames = ['Month 1', 'Month 2', 'Month 3'];
                    for (let i = 1; i <= 3; i++) {
                        const option = document.createElement('option');
                        option.value = i;
                        option.textContent = monthNames[i - 1];
                        selectedMonthSelect.appendChild(option);
                    }
                }
            })
            .catch(error => {
                console.error('Error loading months:', error);
                // Fallback
                const monthNames = ['Month 1', 'Month 2', 'Month 3'];
                for (let i = 1; i <= 3; i++) {
                    const option = document.createElement('option');
                    option.value = i;
                    option.textContent = monthNames[i - 1];
                    selectedMonthSelect.appendChild(option);
                }
            });
    }

    /**
     * Load available quarters
     */
    function loadAvailableQuarters() {
        selectedQuarterSelect.innerHTML = '<option value="">Select Quarter</option>';

        const quarters = [
            { value: 1, label: 'Q1 (Apr-Jun)' },
            { value: 2, label: 'Q2 (Jul-Sep)' },
            { value: 3, label: 'Q3 (Oct-Dec)' },
            { value: 4, label: 'Q4 (Jan-Mar)' }
        ];

        quarters.forEach(quarter => {
            const option = document.createElement('option');
            option.value = quarter.value;
            option.textContent = quarter.label;
            selectedQuarterSelect.appendChild(option);
        });
    }

    /**
     * Load available years
     */
    function loadAvailableYears() {
        selectedYearSelect.innerHTML = '<option value="">Select Year</option>';

        const currentYear = new Date().getFullYear();
        for (let year = currentYear - 2; year <= currentYear + 2; year++) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = `FY ${year % 100}-${(year + 1) % 100}`;
            selectedYearSelect.appendChild(option);
        }
    }

    /**
     * Load team members for participants selection
     */
    function loadTeamMembers(teamId) {
        participantsList.innerHTML = '<div class="text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Loading team members...</div>';

        fetch(`/api/team-members/${teamId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.members && data.members.length > 0) {
                    let html = '';
                    data.members.forEach(member => {
                        html += `
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="participants"
                                       value="${member.id}" id="participant_${member.id}" checked>
                                <label class="form-check-label" for="participant_${member.id}">
                                    ${member.name} (${member.email})
                                </label>
                            </div>
                        `;
                    });
                    participantsList.innerHTML = html;
                } else if (data.success) {
                    participantsList.innerHTML = '<div class="text-muted">No team members found</div>';
                } else {
                    participantsList.innerHTML = `<div class="text-danger">${data.error || 'Error loading team members'}</div>`;
                }
            })
            .catch(error => {
                console.error('Error loading team members:', error);
                participantsList.innerHTML = '<div class="text-danger">Error loading team members</div>';
            });
    }

    /**
     * Check for pending reviews when creating a future review
     */
    function checkPendingReviews() {
        const teamId = parseInt(teamSelect.value);
        const reviewDate = reviewDateInput.value;

        if (!teamId || !reviewDate) {
            pendingReviewWarning.style.display = 'none';
            return;
        }

        const selectedDate = new Date(reviewDate);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        // Only check if creating a future review
        if (selectedDate <= today) {
            pendingReviewWarning.style.display = 'none';
            return;
        }

        // Check for pending reviews
        fetch(`/api/check-pending-reviews/?team_id=${teamId}&date=${reviewDate}`)
            .then(response => response.json())
            .then(data => {
                if (data.has_pending) {
                    pendingReviewMessage.textContent = data.message;
                    pendingReviewWarning.style.display = 'block';
                } else {
                    pendingReviewWarning.style.display = 'none';
                }
            })
            .catch(error => {
                console.error('Error checking pending reviews:', error);
            });
    }

    // Check for pending reviews when date or team changes
    reviewDateInput.addEventListener('change', checkPendingReviews);
    teamSelect.addEventListener('change', checkPendingReviews);

    /**
     * Reset form to initial state
     */
    function resetForm() {
        meetingTypeDisplay.value = '';
        cadenceDisplay.value = '';
        cadenceDisplayContainer.style.display = 'none';
        periodSelectionContainer.style.display = 'none';
        participantsList.innerHTML = '<div class="text-muted">Please select a team first</div>';
        pendingReviewWarning.style.display = 'none';
        currentTeamData = null;
    }

    /**
     * Form validation before submission
     */
    document.getElementById('newReviewForm').addEventListener('submit', function(e) {
        const team = teamSelect.value;
        const reviewDate = reviewDateInput.value;
        const reviewTime = reviewTimeInput.value;
        const managerName = document.getElementById('manager_name').value.trim();

        if (!team || !reviewDate || !reviewTime || !managerName) {
            e.preventDefault();
            alert('Please fill in all required fields.');
            return false;
        }

        // Validate period selection for cadence meetings
        if (cadenceMeetingRadio.checked && currentTeamData && currentTeamData.cadence) {
            let periodSelected = false;

            switch (currentTeamData.cadence) {
                case 'weekly':
                    periodSelected = selectedWeekSelect.value !== '';
                    if (!periodSelected) {
                        e.preventDefault();
                        alert('Please select a week for this weekly cadence meeting.');
                        return false;
                    }
                    break;
                case 'monthly':
                    periodSelected = selectedMonthSelect.value !== '';
                    if (!periodSelected) {
                        e.preventDefault();
                        alert('Please select a month for this monthly cadence meeting.');
                        return false;
                    }
                    break;
                case 'quarterly':
                    periodSelected = selectedQuarterSelect.value !== '';
                    if (!periodSelected) {
                        e.preventDefault();
                        alert('Please select a quarter for this quarterly cadence meeting.');
                        return false;
                    }
                    break;
                case 'annually':
                    periodSelected = selectedYearSelect.value !== '';
                    if (!periodSelected) {
                        e.preventDefault();
                        alert('Please select a year for this annual cadence meeting.');
                        return false;
                    }
                    break;
            }
        }

        // Check if date is not in the past (with confirmation)
        const selectedDateTime = new Date(reviewDate + 'T' + reviewTime);
        const now = new Date();

        if (selectedDateTime < now) {
            const confirmPast = confirm('The selected date and time is in the past. Do you want to continue?');
            if (!confirmPast) {
                e.preventDefault();
                return false;
            }
        }
    });
});
