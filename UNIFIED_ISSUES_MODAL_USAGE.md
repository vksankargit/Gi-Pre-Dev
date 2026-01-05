# Unified Issues Modal - Usage Guide

## Overview
The Unified Issues Modal provides a consistent interface for viewing and creating issues from any location in the application. The modal displays:
1. An inline form to create new issues
2. A grid showing existing issues for the current context
3. Dynamic source tracking based on where it was opened from

## Files Created
1. `templates/includes/unified_issues_modal.html` - Modal template
2. `static/js/unified_issues_modal.js` - JavaScript handler
3. `api/views.py` - Added `UnifiedIssuesAPIView` class
4. `api/urls.py` - Added `/api/unified-issues/` endpoint

## How to Use

### 1. Include the Modal and Script in Your Template

```django
{% load static %}

<!-- At the bottom of your template, include the modal -->
{% include 'includes/unified_issues_modal.html' %}

<!-- Include the JavaScript file -->
<script src="{% static 'js/unified_issues_modal.js' %}"></script>
```

### 2. Call the Modal from Your Code

Use the `openUnifiedIssuesModal(context)` function with the appropriate context object.

## Context Object Structure

```javascript
{
    location: 'implement' | 'review',  // Required
    screen: 'my_numbers' | 'my_projects' | 'my_todo' | 'gpi' | 'ppi',  // Optional
    level: 'screen' | 'item',  // Required
    period: 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'adhoc' | 'manual',  // Optional
    periodNumber: number,  // Optional (week/month/quarter number)
    itemType: 'gpi' | 'ppi' | 'action',  // Optional (for item level)
    itemId: number,  // Optional (for item level)
    itemName: string,  // Optional (for display)
    teamId: number,  // Optional
    meetingId: number,  // Optional (for review context)
    reviewDate: string,  // Optional (for review context)
    actionSource: string  // Optional (for My To Do action level)
}
```

## Implementation Examples

### 1. Implement - My Numbers (Top of Page, Weekly)

**Source**: `Implement + Week {number}`

```javascript
function openMyNumbersWeeklyIssues() {
    openUnifiedIssuesModal({
        location: 'implement',
        screen: 'my_numbers',
        level: 'screen',
        period: 'weekly',
        periodNumber: {{ selected_week }}  // Django template variable
    });
}
```

**Button**:
```html
<button class="btn btn-danger" onclick="openMyNumbersWeeklyIssues()">
    <i class="fas fa-exclamation-triangle me-2"></i>Issues
</button>
```

### 2. Implement - My Numbers (Top of Page, Monthly)

**Source**: `Implement + Month {number}`

```javascript
function openMyNumbersMonthlyIssues() {
    openUnifiedIssuesModal({
        location: 'implement',
        screen: 'my_numbers',
        level: 'screen',
        period: 'monthly',
        periodNumber: {{ selected_month }}  // Django template variable
    });
}
```

### 3. Implement - My Projects (Top of Page)

**Source**: `Implement + Quarter {number}`

```javascript
function openMyProjectsIssues() {
    openUnifiedIssuesModal({
        location: 'implement',
        screen: 'my_projects',
        level: 'screen',
        period: 'quarterly',
        periodNumber: {{ current_quarter_num }}  // Django template variable
    });
}
```

### 4. Implement - My To Do (Top of Page)

**Source**: `Implement + Manual`

```javascript
function openMyTodoIssues() {
    openUnifiedIssuesModal({
        location: 'implement',
        screen: 'my_todo',
        level: 'screen',
        period: 'manual'
    });
}
```

### 5. Implement - My Numbers at GPI Item Level

**Source**: `Implement + Week {number} + {GPI Name}`

```javascript
// Weekly GPI
function openWeeklyGPIIssues(gpiId, gpiName) {
    openUnifiedIssuesModal({
        location: 'implement',
        level: 'item',
        period: 'weekly',
        periodNumber: {{ selected_week }},
        itemType: 'gpi',
        itemId: gpiId,
        itemName: gpiName
    });
}

// Monthly GPI
function openMonthlyGPIIssues(gpiId, gpiName) {
    openUnifiedIssuesModal({
        location: 'implement',
        level: 'item',
        period: 'monthly',
        periodNumber: {{ selected_month }},
        itemType: 'gpi',
        itemId: gpiId,
        itemName: gpiName
    });
}
```

**Button (in table row)**:
```html
<button class="btn btn-outline-danger btn-sm"
        onclick="openWeeklyGPIIssues(${gpi.id}, '${gpi.name}')"
        title="Issues">
    <i class="fas fa-exclamation-triangle"></i>
</button>
```

### 6. Implement - My Projects at Project Level

**Source**: `Implement + Quarter {number} + {PPI Name}`

```javascript
function openProjectIssues(projectId, projectName) {
    openUnifiedIssuesModal({
        location: 'implement',
        level: 'item',
        period: 'quarterly',
        periodNumber: {{ current_quarter_num }},
        itemType: 'ppi',
        itemId: projectId,
        itemName: projectName
    });
}
```

### 7. Implement - My To Do at Action Level

**Source**: `Implement + {Source} + {Action Name}`

```javascript
function openActionIssues(actionId, actionName, actionSource) {
    openUnifiedIssuesModal({
        location: 'implement',
        level: 'item',
        period: 'manual',
        itemType: 'action',
        itemId: actionId,
        itemName: actionName,
        actionSource: actionSource  // This will be added to the source string
    });
}
```

### 8. Review Meeting (Top of Page)

**Source**: `Review + {Cadence} ({Week/Month/Quarter/Year}) {Date}`

```javascript
function openReviewIssues() {
    const meeting = {{ meeting|safe }};  // Django context
    openUnifiedIssuesModal({
        location: 'review',
        level: 'screen',
        period: '{{ meeting.review_type }}',  // 'weekly', 'monthly', 'quarterly', 'yearly', 'adhoc'
        periodNumber: {{ meeting.week_number|default:'null' }},  // For weekly/monthly/quarterly
        meetingId: {{ meeting.pk }},
        teamId: {{ meeting.team.id }},
        reviewDate: '{{ meeting.review_date|date:"M d, Y" }}'
    });
}
```

### 9. Review - GPI Tab at Item Level

**Source**: `Review + Week {number} + {GPI Name}` or `Review + Month {number} + {GPI Name}` etc.

```javascript
// Weekly GPI
function openReviewWeeklyGPIIssues(gpiId, gpiName, weekNumber) {
    openUnifiedIssuesModal({
        location: 'review',
        level: 'item',
        period: 'weekly',
        periodNumber: weekNumber,
        itemType: 'gpi',
        itemId: gpiId,
        itemName: gpiName,
        meetingId: {{ meeting.pk }},
        teamId: {{ meeting.team.id }}
    });
}

// Monthly GPI
function openReviewMonthlyGPIIssues(gpiId, gpiName, monthNumber) {
    openUnifiedIssuesModal({
        location: 'review',
        level: 'item',
        period: 'monthly',
        periodNumber: monthNumber,
        itemType: 'gpi',
        itemId: gpiId,
        itemName: gpiName,
        meetingId: {{ meeting.pk }},
        teamId: {{ meeting.team.id }}
    });
}

// Quarterly GPI
function openReviewQuarterlyGPIIssues(gpiId, gpiName, quarterNumber) {
    openUnifiedIssuesModal({
        location: 'review',
        level: 'item',
        period: 'quarterly',
        periodNumber: quarterNumber,
        itemType: 'gpi',
        itemId: gpiId,
        itemName: gpiName,
        meetingId: {{ meeting.pk }},
        teamId: {{ meeting.team.id }}
    });
}

// Annual GPI
function openReviewAnnualGPIIssues(gpiId, gpiName) {
    openUnifiedIssuesModal({
        location: 'review',
        level: 'item',
        period: 'yearly',
        itemType: 'gpi',
        itemId: gpiId,
        itemName: gpiName,
        meetingId: {{ meeting.pk }},
        teamId: {{ meeting.team.id }}
    });
}
```

### 10. Review - PPI Tab at Item Level

**Source**: `Review + Quarter {number} + {PPI Name}`

```javascript
function openReviewPPIIssues(projectId, projectName, quarterNumber) {
    openUnifiedIssuesModal({
        location: 'review',
        level: 'item',
        period: 'quarterly',
        periodNumber: quarterNumber,
        itemType: 'ppi',
        itemId: projectId,
        itemName: projectName,
        meetingId: {{ meeting.pk }},
        teamId: {{ meeting.team.id }}
    });
}
```

## Source String Examples

Based on the context object, the modal automatically generates source strings:

| Location | Context | Source String |
|----------|---------|---------------|
| Implement - My Numbers Weekly | Week 5 | `Implement + Week 5` |
| Implement - My Numbers Monthly | Month 2 | `Implement + Month 2` |
| Implement - My Projects | Quarter 3 | `Implement + Quarter 3` |
| Implement - My To Do | Manual | `Implement + Manual` |
| Implement - GPI Item (Weekly) | Week 5, GPI "Sales" | `Implement + Week 5 + Sales` |
| Implement - GPI Item (Monthly) | Month 2, GPI "Sales" | `Implement + Month 2 + Sales` |
| Implement - PPI Item | Quarter 3, PPI "New Product" | `Implement + Quarter 3 + New Product` |
| Implement - Action Item | Action "Fix bug" from "Project X" | `Implement + Manual + Project X + Fix bug` |
| Review - Weekly Meeting | Week 5, Jan 30 2025 | `Review + Week 5 (Jan 30, 2025)` |
| Review - Monthly Meeting | Month 2, Feb 28 2025 | `Review + Month 2 (Feb 28, 2025)` |
| Review - Quarterly Meeting | Quarter 3, Sep 30 2025 | `Review + Quarter 3 (Sep 30, 2025)` |
| Review - GPI Item (Weekly) | Week 5, GPI "Sales" | `Review + Week 5 + Sales` |
| Review - PPI Item | Quarter 3, PPI "New Product" | `Review + Quarter 3 + New Product` |

## Migration from Existing Modals

The unified modal can replace:
1. `new_issue_modal.html` (simple creation modal)
2. JavaScript-generated issue modals in `main.js`
3. Server-rendered issue popups

Benefits of the unified approach:
- Consistent UI/UX across all locations
- Single source of truth for issue creation
- Automatic source tracking
- Shows both creation form and existing issues
- Easier to maintain and update

## Next Steps

To fully implement this across your application:

1. Update `templates/base.html` to include the modal and script globally
2. Replace existing issue button handlers with unified modal calls
3. Test each location to ensure correct source tracking
4. Remove old modal files once migration is complete
