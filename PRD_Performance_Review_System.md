# Product Requirements Document (PRD)
## GI Performance Review and Enhancement (PRE) System

**Version:** 1.0
**Date:** October 2, 2025
**Product:** GI-Pre-Dev System

---

## 1. Product Overview

### 1.1 Purpose
The GI Performance Review and Enhancement (PRE) System is a comprehensive web-based platform designed to manage organizational performance planning, execution tracking, continuous improvement initiatives, and review processes. The system enables organizations to create annual and quarterly plans, track key performance indicators (KPIs), manage improvement projects, conduct review meetings, and maintain accountability through action item tracking.

### 1.2 Target Users
- **Administrators**: System-wide configuration and user management
- **Coordinators**: Organization-level oversight and coordination
- **Team Managers**: Team leadership and performance monitoring
- **Team Members**: Individual contributors executing plans and actions
- **General Users**: View and update assigned tasks and actions

### 1.3 Key Business Value
- Centralized planning and execution tracking
- Real-time visibility into financial and operational performance
- Structured improvement project management
- Systematic review and accountability mechanisms
- Data-driven decision-making through metrics tracking
- Audit trail for all changes and updates

---

## 2. User Roles and Permissions

### 2.1 Admin
**Capabilities:**
- Full system access
- Create and manage organizations
- Create and manage users across all organizations
- Assign user roles
- Configure system-wide settings
- Impersonate users for support purposes
- View all audit trails

### 2.2 Coordinator
**Capabilities:**
- Manage organization-specific data
- Create and manage teams within their organization
- Assign team managers
- Upload annual and quarterly plans
- View all teams' performance data within their organization
- Cannot access other organizations' data

### 2.3 General User (Team Manager)
**Capabilities:**
- Manage their own team(s)
- Upload quarterly plans and improvement projects
- Create and assign actions to team members
- Conduct review meetings
- Track team performance metrics (FPI, GPI, PPI)
- Create and resolve issues
- View and update data for teams they manage

### 2.4 General User (Team Member)
**Capabilities:**
- View team plans and metrics
- Update assigned actions and tasks
- Participate in review meetings
- Report issues
- View team dashboards
- Cannot manage team settings or create new actions

---

## 3. Core Modules

### 3.1 Accounts Module

#### 3.1.1 User Management
**FR-ACC-001: User Registration and Authentication**
- System shall support email-based authentication
- Users must provide first name, last name, email, and mobile number
- Passwords must meet security requirements (min 8 chars, complexity rules)
- First login forces password change
- Support username and email login

**FR-ACC-002: User Roles**
- Three roles: Admin, Coordinator, General
- Role determines access permissions throughout system
- Users can belong to one organization (except Admin)

**FR-ACC-003: User Profile Management**
- Users can update their profile information
- Change password functionality
- View activity history

**FR-ACC-004: Impersonation**
- Admins can impersonate any user for support
- Impersonation is logged in audit trail
- Clear indication when impersonating
- Easy switch back to admin account

#### 3.1.2 Audit Trail
**FR-ACC-005: Activity Logging**
- System automatically logs all create, update, delete operations
- Audit records include: user, action, model, object ID, changes (JSON), timestamp, IP address
- Impersonated actions show both admin and impersonated user
- Audit trail is immutable and viewable by admins

---

### 3.2 Organizations Module

#### 3.2.1 Organization Management
**FR-ORG-001: Organization CRUD**
- Admins can create, view, update, and deactivate organizations
- Organization has name and active status
- Organizations can be deactivated but not deleted (data retention)

**FR-ORG-002: Organization Coordinators**
- Multiple coordinators can be assigned to one organization
- Coordinators have management access to organization data
- Active/inactive status for coordinator assignments

#### 3.2.2 Team Management
**FR-ORG-003: Team CRUD**
- Coordinators and admins can create teams within organizations
- Each team has: name, manager, active status
- Team names must be unique within an organization
- Teams belong to exactly one organization

**FR-ORG-004: Team Membership**
- Users can be added as team members
- One user can be member of multiple teams
- Team members can be active or inactive
- Track join date for members

**FR-ORG-005: Team Manager Assignment**
- Each team has exactly one manager
- Manager must be a user within the same organization
- Manager can manage their team's plans, actions, and reviews

---

### 3.3 Plans Module

#### 3.3.1 Financial Year Management
**FR-PLN-001: Financial Year Setup**
- System supports multiple financial years
- Each FY has: year label (e.g., "FY 25-26"), start date, end date
- Financial years cannot overlap
- Used as basis for all planning

#### 3.3.2 Annual Planning
**FR-PLN-002: Annual Plan Upload**
- Teams upload Excel file containing annual goals
- One annual plan per team per financial year
- Upload processes FPI, GPI, and PPI data from Excel
- Upload status tracking (successful/failed) with error logs
- Parse and store:
  - FPI parameters with quarterly goals
  - GPI parameters with quarterly goals
  - PPI projects with quarterly milestones

**FR-PLN-003: Annual Plan Data Structure**
- **FPI (Financial Performance Indicators):**
  - Main heads: Revenue, Variable Cost, Operating Expenses, Other Expenses
  - Sub-heads under each main head
  - Responsible user assignment
  - Annual goal and Q1-Q4 breakdown

- **GPI (Growth Performance Indicators):**
  - Parameter name and unit of measure
  - Tracking type: Weekly or Monthly
  - Indicator type: Goal or Progress
  - Responsible user assignment
  - Annual goal and Q1-Q4 breakdown

- **PPI (Project Performance Indicators):**
  - Project name and responsible user
  - Annual goal description
  - Q1-Q4 milestone descriptions

#### 3.3.3 Quarterly Planning
**FR-PLN-004: Quarterly Plan Upload**
- Teams upload Excel file for each quarter (Q1-Q4)
- One quarterly plan per team per quarter per FY
- More detailed breakdown than annual plan
- Upload processes:
  - FPI parameters with monthly budgets (3 months)
  - GPI parameters with weekly/monthly milestones
  - PPI projects with tasks assigned by week

**FR-PLN-005: Quarterly Plan Data Structure**
- **FPI Parameters:**
  - Link to annual FPI or standalone
  - Quarter goal and 3-month budget breakdown
  - Month 1, Month 2, Month 3 budgets
  - Tracking fields: last month actual, last month goal, current month plan
  - Explanation field for variances

- **GPI Parameters:**
  - Link to annual GPI or standalone
  - Quarter goal
  - Weekly milestones (up to 13 weeks) or Monthly milestones (3 months)
  - Tracking fields: last period actual, last period goal, current period plan
  - Explanation field for variances

- **PPI Projects:**
  - Link to annual PPI or standalone
  - Project details: name, completion criteria, responsible user, start/end dates
  - Steps description
  - Weekly tasks (Week 1-13): task description, assigned user, completion status

#### 3.3.4 Plan Visualization
**FR-PLN-006: Plan Dashboards**
- View annual plan summary for team
- Drill down into quarterly plans
- View FPI, GPI, PPI in separate tabs
- Filter by responsible user
- Export plan data to Excel/PDF

---

### 3.4 Implement Module

#### 3.4.1 Action Management
**FR-IMP-001: Action Creation**
- Actions can be created from multiple sources:
  - Manual entry
  - PPI tasks (from quarterly plan)
  - Improvement tasks
  - Review meeting action items
  - Issue resolution actions
- Required fields: action description, priority, assigned to, original due date
- Optional fields: team, challenge, comments, revised due date
- Actions can have parent-child relationships (sub-actions)

**FR-IMP-002: Action Status Workflow**
- Status options: Not Started, In Progress, At Risk, Danger, Done, Completed, Rejected
- Status changes create history records
- Assignee receives notifications on status changes
- Manager can reject actions with rejection reason

**FR-IMP-003: Action Updates**
- Assignee can update: status, challenge, comments, revised due date
- Cannot change: action description, original due date, assigned to (only manager can)
- All updates create history records
- Comments support markdown formatting

**FR-IMP-004: Action Reassignment**
- Managers can reassign actions to other team members
- Reassignment requires reason/comment
- Original and new assignee are notified
- Reassignment logged in history

#### 3.4.2 My To-Do Dashboard
**FR-IMP-005: Personal Action View**
- User sees all actions assigned to them across all teams
- Group by: status, priority, due date
- Quick filters: overdue, due this week, due this month
- Color coding: red (overdue), orange (due soon), green (on track)
- Update status inline
- Add comments and challenges

#### 3.4.3 Numbers Tracking
**FR-IMP-006: FPI/GPI Tracking**
- Weekly and monthly tracking forms for FPI and GPI parameters
- Pre-populate budget values from quarterly plan
- Enter actual vs plan values
- Calculate variance automatically
- Comments for explaining variances
- Historical tracking view showing trends

#### 3.4.4 Project Status Tracking
**FR-IMP-007: PPI Project Updates**
- Weekly status updates for PPI projects
- Update fields: status, completion %, revised due date, challenge, comments
- Status history maintained
- Manager dashboard shows all projects' current status
- Alert when projects move to At Risk or Danger status

#### 3.4.5 Issue Management
**FR-IMP-008: Issue Creation and Tracking**
- Users can create issues for their team
- Issue fields: title, description, priority (high/medium/low), required by date
- Issue status: Open, Resolved, On Hold, Dropped, Escalated
- Issues can be escalated to parent/related teams
- Issues can have multiple related actions
- Issue resolution tracked with comments
- Previous status saved when escalating or putting on hold

**FR-IMP-009: Issue Dashboard**
- View all team issues
- Filter by status, priority, assigned team
- Quick actions: add action to issue, change status, escalate
- Track resolution progress (actions completed / total actions)
- Visual indicators for priority and overdue issues

---

### 3.5 Reviews Module

#### 3.5.1 Review Meeting Management
**FR-REV-001: Review Meeting Creation**
- Managers create review meetings for their teams
- Meeting types: Daily, Weekly, Monthly
- Meeting details: type, date/time, financial year, quarter, week/month number
- Participants can be selected (team members)
- Meeting status: Draft, Finalized

**FR-REV-002: Review Meeting Conduct**
- During review, capture:
  - Review notes (general observations with title and content)
  - Decisions (numbered D1, D2, etc.)
  - Action items (with assignee, team, priority, due date, parameter links)
  - Parameter discussions (link to FPI, GPI, or PPI)
- Real-time updates (AJAX)
- Auto-save functionality
- Warning on unsaved changes

#### 3.5.2 Review Notes
**FR-REV-003: Review Notes Management**
- Add, edit, delete review notes
- Each note has: title, content, creator, timestamp
- Notes can be reordered (move up/down/top/bottom)
- Confirmation dialog on cancel with unsaved changes
- Notes displayed chronologically

#### 3.5.3 Review Decisions
**FR-REV-004: Decision Tracking**
- Record decisions made during review
- Auto-numbered sequentially (D1, D2, D3...)
- Edit and delete decisions
- Renumbering when decisions deleted
- Reorder decisions
- Export decisions to PDF/Word or copy to clipboard
- Confirmation dialog on cancel with unsaved changes

#### 3.5.4 Action Items from Reviews
**FR-REV-005: Review Action Items**
- Create action items during review meeting
- Link action items to:
  - Specific FPI parameters
  - Specific GPI parameters
  - Specific PPI projects
- Assign to team member or different team
- Set priority and due date
- Action items automatically flow to Implement module
- Track which review meeting generated each action

#### 3.5.5 Review Tabs and Views
**FR-REV-006: FPI Review Tab**
- Display all FPI parameters for the quarter
- Show: budget, plan, actual, variance
- Click on row to add action items
- Show existing action items for each parameter
- Filter by main head, responsible user
- Visual indicators for negative variances

**FR-REV-007: GPI Review Tab**
- Display all GPI parameters for the quarter
- Show weekly or monthly tracking data
- Click on row to add action items
- Show existing action items for each parameter
- Filter by tracking type, responsible user

**FR-REV-008: PPI Review Tab**
- Display all PPI projects for the quarter
- Show project details, status, completion %
- View weekly tasks and completion status
- Click on row or task to add action items
- Show existing action items for each project/task
- Filter by status, responsible user

**FR-REV-009: Issues Review Tab**
- Display all team issues
- Show status, priority, related actions
- Add action items for issues
- Update issue status
- Escalate issues
- Filter by status, priority

#### 3.5.6 Review Meeting Finalization
**FR-REV-010: Meeting Finalization**
- Manager can finalize review meeting
- Finalization locks notes, decisions, and action items
- Finalized by user and timestamp recorded
- Generate PDF summary of meeting
- Email summary to participants

---

### 3.6 Improve Module

#### 3.6.1 Improvement Project Upload
**FR-IMP-010: Improvement Upload**
- Similar to quarterly plan upload but for improvement initiatives
- Upload Excel file with improvement projects
- One upload per team per quarter per FY
- Upload processing creates:
  - Improvement projects
  - Weekly tasks for each project
- Track upload status and errors

#### 3.6.2 Improvement Project Management
**FR-IMP-011: Improvement Projects**
- Project structure identical to PPI projects:
  - Name, completion criteria, responsible user
  - Start date, end date
  - Steps description
  - Status (On Track, At Risk, Danger, Completed, On Hold)
- Weekly tasks with assignees
- Status history tracking

#### 3.6.3 Improvement Dashboard
**FR-IMP-012: Improvement Tracking**
- View all improvement projects for team
- Update project status and completion %
- Update task completion
- Create actions from tasks
- Filter by status, responsible user, quarter
- Export improvement data

---

## 4. System Architecture

### 4.1 Technology Stack
- **Framework**: Django 4.x (Python web framework)
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Frontend**: Bootstrap 5, jQuery, vanilla JavaScript
- **Forms**: Crispy Forms with Bootstrap 5
- **File Uploads**: Django file handling for Excel uploads
- **Authentication**: Django auth with custom email backend
- **Static Files**: Whitenoise for serving static files

### 4.2 Application Structure
```
pre_system/
├── accounts/          # User management, authentication, audit trail
├── organizations/     # Organizations, teams, team members
├── plans/            # Financial years, annual/quarterly plans, FPI/GPI/PPI
├── implement/        # Actions, issues, numbers tracking, project status
├── reviews/          # Review meetings, notes, decisions, action items
├── improve/          # Improvement uploads and projects
├── api/              # REST API endpoints
└── templates/        # HTML templates
```

### 4.3 Data Model Relationships
```
Organization (1) ---> (N) Team
Team (1) ---> (N) TeamMember (N) <--- (1) User
Team (1) ---> (N) AnnualPlan (N) <--- (1) FinancialYear
Team (1) ---> (N) QuarterlyPlan (N) <--- (1) FinancialYear
QuarterlyPlan (1) ---> (N) FPIParameter
QuarterlyPlan (1) ---> (N) GPIParameter
QuarterlyPlan (1) ---> (N) PPIProject
PPIProject (1) ---> (N) PPITask
Team (1) ---> (N) Action
Team (1) ---> (N) Issue
Team (1) ---> (N) ReviewMeeting
ReviewMeeting (1) ---> (N) ReviewNote
ReviewMeeting (1) ---> (N) ReviewDecision
ReviewMeeting (1) ---> (N) ReviewActionItem
Team (1) ---> (N) ImprovementUpload
ImprovementUpload (1) ---> (N) ImprovementProject
ImprovementProject (1) ---> (N) ImprovementTask
```

---

## 5. Non-Functional Requirements

### 5.1 Performance
**NFR-001**: Page load time < 3 seconds for 90% of requests
**NFR-002**: Support up to 1000 concurrent users
**NFR-003**: Database queries optimized with select_related and prefetch_related
**NFR-004**: File uploads up to 25MB supported

### 5.2 Security
**NFR-005**: All passwords hashed using Django's PBKDF2 algorithm
**NFR-006**: CSRF protection on all forms
**NFR-007**: XSS protection through template auto-escaping
**NFR-008**: Login required for all views except login/register
**NFR-009**: Role-based access control enforced at view level
**NFR-010**: Audit trail for all data modifications
**NFR-011**: Secure session management with configurable timeout

### 5.3 Usability
**NFR-012**: Responsive design working on desktop, tablet, mobile
**NFR-013**: Intuitive navigation with breadcrumbs
**NFR-014**: Consistent UI/UX across all modules
**NFR-015**: Confirmation dialogs for destructive actions
**NFR-016**: Inline help text for complex fields
**NFR-017**: Error messages clear and actionable
**NFR-018**: Warning for unsaved changes

### 5.4 Reliability
**NFR-019**: 99% uptime for production system
**NFR-020**: Automated database backups daily
**NFR-021**: Transaction management for data consistency
**NFR-022**: Graceful error handling with user-friendly messages

### 5.5 Maintainability
**NFR-023**: Code follows PEP 8 style guide
**NFR-024**: Modular architecture with clear separation of concerns
**NFR-025**: Database migrations for all schema changes
**NFR-026**: Logging for debugging and monitoring

### 5.6 Scalability
**NFR-027**: Horizontal scaling supported via load balancing
**NFR-028**: Database connection pooling
**NFR-029**: Static files served via CDN in production
**NFR-030**: Caching strategy for frequently accessed data

---

## 6. Integration Points

### 6.1 File Upload/Processing
- Excel file parsing using pandas/openpyxl
- Validation of uploaded data
- Error reporting for invalid data
- Rollback on upload failure

### 6.2 Email Notifications
- Email backend configured (console for dev, SMTP for prod)
- Notifications for:
  - Action assignments
  - Action status changes
  - Issue escalations
  - Review meeting summaries
  - Overdue items

### 6.3 Export Functionality
- Export to Excel: plans, action lists, issue lists
- Export to PDF: review summaries, reports
- Copy to clipboard: decisions, notes

### 6.4 API Endpoints
- RESTful API for external integrations
- JSON response format
- Authentication via token or session
- Rate limiting for API calls

---

## 7. User Workflows

### 7.1 Plan Creation Workflow
1. Coordinator creates financial year
2. Team managers prepare annual plan Excel file
3. Upload annual plan via web interface
4. System validates and parses data
5. View parsed data in plan dashboard
6. Quarterly plan upload for each quarter
7. System links quarterly to annual parameters
8. Quarterly plans drive weekly/monthly tracking

### 7.2 Review Meeting Workflow
1. Manager creates review meeting
2. Select participants
3. Review FPI/GPI/PPI tabs with actual vs plan data
4. Add notes for key observations
5. Record decisions made
6. Create action items for follow-ups
7. Link action items to specific parameters/projects
8. Assign action items to team members
9. Finalize meeting
10. System sends summary to participants

### 7.3 Action Execution Workflow
1. Team member views My To-Do dashboard
2. Select action to update
3. Change status, add comments, update challenge
4. If blocked, revise due date with reason
5. Manager reviews action status in team dashboard
6. Manager provides feedback or reassigns if needed
7. Mark action as completed when done
8. Manager verifies completion

### 7.4 Issue Resolution Workflow
1. Team member creates issue
2. Set priority and required by date
3. Manager reviews issue in dashboard
4. Create action items to resolve issue
5. Assign actions to team members
6. Track action completion
7. Update issue status as progress made
8. Escalate to parent team if cannot resolve
9. Mark issue as resolved when all actions completed

---

## 8. Data Requirements

### 8.1 Master Data
- Organizations
- Users
- Teams and memberships
- Financial years

### 8.2 Reference Data
- Status choices (actions, projects, issues)
- Priority levels
- Review meeting types
- Main heads for FPI

### 8.3 Transactional Data
- Plans (annual and quarterly)
- Parameters (FPI, GPI, PPI) and their tracking data
- Actions and action history
- Issues
- Review meetings, notes, decisions, action items
- Improvement projects and tasks
- Audit trails

### 8.4 Data Retention
- All historical data retained indefinitely
- Soft deletes for entities (is_active flag)
- Audit trail immutable
- Regular backups to external storage

---

## 9. Business Rules

### 9.1 Planning Rules
- BR-001: One annual plan per team per financial year
- BR-002: One quarterly plan per team per quarter per financial year
- BR-003: Quarterly plan data must align with financial year quarters
- BR-004: Parameters in quarterly plan should reference annual plan parameters
- BR-005: Responsible users must be members of the team

### 9.2 Action Rules
- BR-006: Actions cannot be deleted, only marked as rejected
- BR-007: Only assignee or manager can update action status
- BR-008: Completed actions cannot be reopened
- BR-009: Revised due date must be after original due date
- BR-010: Sub-actions inherit parent action's team

### 9.3 Review Meeting Rules
- BR-011: Only team manager can create review meetings
- BR-012: Review meetings can only be finalized once
- BR-013: Finalized review meetings cannot be edited
- BR-014: Decisions are auto-numbered sequentially per meeting
- BR-015: Action items from review must have assignee and due date

### 9.4 Access Control Rules
- BR-016: Users can only access teams they are member of or manage
- BR-017: Coordinators can access all teams in their organization
- BR-018: Admins can access all data across all organizations
- BR-019: Impersonation is only available to admins
- BR-020: Team managers can only assign actions to their team members

---

## 10. Success Metrics

### 10.1 Usage Metrics
- Number of active users per month
- Number of plans uploaded per quarter
- Number of review meetings conducted per week
- Number of actions created and completed per month

### 10.2 Performance Metrics
- Plan completion rate (actual vs planned)
- Action completion rate
- On-time action completion percentage
- Issue resolution time

### 10.3 Quality Metrics
- Data accuracy (upload errors / total uploads)
- User satisfaction score
- System uptime percentage
- Page load time metrics

---

## 11. Future Enhancements (Out of Scope for v1)

### 11.1 Advanced Analytics
- Trend analysis for FPI/GPI parameters
- Predictive analytics for project delays
- Performance dashboards with charts
- Comparative analysis across teams

### 11.2 Mobile Application
- Native mobile app for iOS and Android
- Offline mode for data entry
- Push notifications

### 11.3 Advanced Collaboration
- Real-time collaborative editing of review notes
- Chat functionality within teams
- Document attachments to actions and issues
- Calendar integration for review meetings

### 11.4 Workflow Automation
- Automatic action creation based on rules
- Escalation workflows for overdue items
- Approval workflows for plan uploads
- Reminder emails for upcoming due dates

### 11.5 External Integrations
- Integration with accounting systems for FPI data
- Integration with project management tools
- Single Sign-On (SSO) with corporate directories
- API for third-party tools

---

## Appendix A: Glossary

**FPI**: Financial Performance Indicators - financial metrics like revenue, costs
**GPI**: Growth Performance Indicators - growth metrics tracked weekly or monthly
**PPI**: Project Performance Indicators - strategic projects tracked by tasks
**FY**: Financial Year
**Q1-Q4**: Quarters 1 through 4 within a financial year
**YTD**: Year To Date
**Action**: A task or to-do item assigned to a user
**Issue**: A problem or blocker that needs resolution
**Review Meeting**: Structured meeting to review performance and make decisions

---

## Appendix B: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Oct 2, 2025 | System Analysis | Initial PRD based on codebase analysis |

