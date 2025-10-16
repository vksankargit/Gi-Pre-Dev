# Test Plan
## GI Performance Review and Enhancement (PRE) System

**Version:** 1.0
**Date:** October 2, 2025
**Product:** GI-Pre-Dev System

---

## 1. Test Strategy

### 1.1 Testing Approach
This test plan employs a comprehensive testing strategy covering:
- **Unit Testing**: Testing individual components (models, views, forms)
- **Integration Testing**: Testing workflows across multiple components
- **User Interface Testing**: Testing user interactions and UI behavior
- **Security Testing**: Testing authentication, authorization, and data protection
- **Performance Testing**: Testing system under load
- **Regression Testing**: Ensuring existing functionality remains intact

### 1.2 Test Levels
- **Level 1 - Unit Tests**: Automated tests for models, utilities, forms
- **Level 2 - Integration Tests**: Automated tests for multi-component workflows
- **Level 3 - System Tests**: Manual/automated end-to-end user scenarios
- **Level 4 - User Acceptance Tests**: Manual tests by stakeholders

### 1.3 Test Environment Requirements
- **Development Environment**: Local Django dev server, SQLite database
- **Staging Environment**: Production-like setup with PostgreSQL
- **Test Data**: Sample organizations, users, teams, plans, actions
- **Test Users**: Admin, Coordinator, Team Manager, Team Member accounts

---

## 2. Test Scope

### 2.1 In Scope
- All functional requirements from PRD
- User authentication and authorization
- CRUD operations for all entities
- File upload and processing
- Review meeting workflows
- Action and issue management
- Dashboard and reporting
- Data validation and error handling
- UI responsiveness and usability
- Security and access control

### 2.2 Out of Scope
- Third-party integrations (future enhancement)
- Mobile app testing (future enhancement)
- Advanced analytics (future enhancement)
- Performance testing beyond 100 concurrent users
- Load testing for massive data volumes (>1M records)

---

## 3. Test Cases by Module

## 3.1 Accounts Module

### Authentication Tests

**TC-ACC-001: User Login with Email**
- **Priority**: High
- **Pre-conditions**: User account exists with email and password
- **Steps**:
  1. Navigate to login page
  2. Enter valid email address
  3. Enter valid password
  4. Click Login button
- **Expected**: User successfully logged in, redirected to dashboard
- **Test Data**: user@example.com / password123

**TC-ACC-002: User Login with Username**
- **Priority**: High
- **Pre-conditions**: User account exists
- **Steps**:
  1. Navigate to login page
  2. Enter valid username
  3. Enter valid password
  4. Click Login button
- **Expected**: User successfully logged in, redirected to dashboard

**TC-ACC-003: Login with Invalid Credentials**
- **Priority**: High
- **Pre-conditions**: None
- **Steps**:
  1. Navigate to login page
  2. Enter invalid email/username
  3. Enter password
  4. Click Login
- **Expected**: Error message displayed, user remains on login page

**TC-ACC-004: First Login Password Change**
- **Priority**: Medium
- **Pre-conditions**: New user account with is_first_login=True
- **Steps**:
  1. Login with credentials
  2. Verify redirect to password change page
  3. Enter current password
  4. Enter new password
  5. Confirm new password
  6. Submit
- **Expected**: Password changed, is_first_login set to False, redirected to dashboard

**TC-ACC-005: Logout Functionality**
- **Priority**: High
- **Pre-conditions**: User is logged in
- **Steps**:
  1. Click Logout button/link
- **Expected**: User logged out, session cleared, redirected to login page

### User Management Tests

**TC-ACC-006: Create Admin User**
- **Priority**: High
- **Pre-conditions**: Logged in as admin
- **Steps**:
  1. Navigate to user management
  2. Click Create User
  3. Enter: first name, last name, email, mobile, username
  4. Select role: Admin
  5. Submit
- **Expected**: User created with admin role, no organization required

**TC-ACC-007: Create Coordinator User**
- **Priority**: High
- **Pre-conditions**: Logged in as admin, organization exists
- **Steps**:
  1. Create user with role=Coordinator
  2. Assign to organization
  3. Submit
- **Expected**: User created with coordinator role, assigned to organization

**TC-ACC-008: Create General User**
- **Priority**: High
- **Pre-conditions**: Logged in as admin or coordinator, organization exists
- **Steps**:
  1. Create user with role=General
  2. Assign to organization
  3. Submit
- **Expected**: User created, assigned to organization

**TC-ACC-009: Update User Profile**
- **Priority**: Medium
- **Pre-conditions**: Logged in as user
- **Steps**:
  1. Navigate to profile page
  2. Update first name, last name, mobile number
  3. Submit
- **Expected**: Profile updated successfully, changes reflected

**TC-ACC-010: Change Password**
- **Priority**: High
- **Pre-conditions**: Logged in as user
- **Steps**:
  1. Navigate to change password page
  2. Enter current password
  3. Enter new password (meets requirements)
  4. Confirm new password
  5. Submit
- **Expected**: Password changed, success message shown

**TC-ACC-011: Password Complexity Validation**
- **Priority**: High
- **Pre-conditions**: On password change page
- **Steps**:
  1. Enter weak password (e.g., "123")
  2. Submit
- **Expected**: Validation error, password not changed

### Impersonation Tests

**TC-ACC-012: Admin Impersonate User**
- **Priority**: High
- **Pre-conditions**: Logged in as admin, target user exists
- **Steps**:
  1. Navigate to user list
  2. Click Impersonate button for target user
- **Expected**: Admin now viewing as target user, impersonation indicator shown

**TC-ACC-013: Stop Impersonation**
- **Priority**: High
- **Pre-conditions**: Admin is impersonating a user
- **Steps**:
  1. Click Stop Impersonation button
- **Expected**: Admin returned to own account

**TC-ACC-014: Non-Admin Cannot Impersonate**
- **Priority**: High
- **Pre-conditions**: Logged in as coordinator or general user
- **Steps**:
  1. Attempt to access impersonate URL directly
- **Expected**: Access denied, error message

### Audit Trail Tests

**TC-ACC-015: Audit Trail Created on User Create**
- **Priority**: Medium
- **Pre-conditions**: Admin logged in
- **Steps**:
  1. Create new user
  2. Check audit trail
- **Expected**: Audit record created with action=CREATE, model=User, user=admin

**TC-ACC-016: Audit Trail for Impersonated Actions**
- **Priority**: Medium
- **Pre-conditions**: Admin impersonating user
- **Steps**:
  1. Perform action (e.g., create team)
  2. Check audit trail
- **Expected**: Audit record shows both admin and impersonated user

**TC-ACC-017: Audit Trail Immutability**
- **Priority**: Medium
- **Pre-conditions**: Audit records exist
- **Steps**:
  1. Attempt to edit audit trail record via admin interface
- **Expected**: Cannot edit or delete audit trail records

---

## 3.2 Organizations Module

### Organization Management Tests

**TC-ORG-001: Create Organization**
- **Priority**: High
- **Pre-conditions**: Logged in as admin
- **Steps**:
  1. Navigate to organizations
  2. Click Create Organization
  3. Enter organization name
  4. Set is_active=True
  5. Submit
- **Expected**: Organization created successfully

**TC-ORG-002: Duplicate Organization Name**
- **Priority**: High
- **Pre-conditions**: Organization "Acme Corp" exists
- **Steps**:
  1. Attempt to create organization with name "Acme Corp"
  2. Submit
- **Expected**: Validation error, organization not created

**TC-ORG-003: Update Organization**
- **Priority**: Medium
- **Pre-conditions**: Organization exists
- **Steps**:
  1. Select organization
  2. Update name
  3. Submit
- **Expected**: Organization updated

**TC-ORG-004: Deactivate Organization**
- **Priority**: Medium
- **Pre-conditions**: Organization exists
- **Steps**:
  1. Select organization
  2. Set is_active=False
  3. Submit
- **Expected**: Organization deactivated, not visible in active org list

**TC-ORG-005: View Organization List**
- **Priority**: High
- **Pre-conditions**: Multiple organizations exist
- **Steps**:
  1. Navigate to organizations list
- **Expected**: All active organizations displayed, ordered by name

### Coordinator Assignment Tests

**TC-ORG-006: Assign Coordinator to Organization**
- **Priority**: High
- **Pre-conditions**: Organization exists, coordinator user exists
- **Steps**:
  1. Select organization
  2. Click Add Coordinator
  3. Select coordinator user
  4. Submit
- **Expected**: Coordinator assigned, has access to organization data

**TC-ORG-007: Remove Coordinator from Organization**
- **Priority**: Medium
- **Pre-conditions**: Coordinator assigned to organization
- **Steps**:
  1. Select organization
  2. Remove coordinator
- **Expected**: Coordinator removed, no longer has organization access

**TC-ORG-008: Multiple Coordinators for Organization**
- **Priority**: Medium
- **Pre-conditions**: Organization exists, multiple coordinator users exist
- **Steps**:
  1. Assign Coordinator 1
  2. Assign Coordinator 2
  3. Verify both have access
- **Expected**: Multiple coordinators can manage same organization

### Team Management Tests

**TC-ORG-009: Create Team**
- **Priority**: High
- **Pre-conditions**: Organization exists, manager user exists
- **Steps**:
  1. Navigate to teams
  2. Click Create Team
  3. Enter team name
  4. Select organization
  5. Select manager
  6. Submit
- **Expected**: Team created successfully

**TC-ORG-010: Duplicate Team Name in Same Organization**
- **Priority**: High
- **Pre-conditions**: Team "Sales" exists in Org A
- **Steps**:
  1. Attempt to create another team "Sales" in Org A
  2. Submit
- **Expected**: Validation error, team not created

**TC-ORG-011: Same Team Name in Different Organizations**
- **Priority**: Medium
- **Pre-conditions**: Org A and Org B exist
- **Steps**:
  1. Create team "Sales" in Org A
  2. Create team "Sales" in Org B
- **Expected**: Both teams created successfully (unique constraint is org+name)

**TC-ORG-012: Update Team Manager**
- **Priority**: High
- **Pre-conditions**: Team exists, new manager user exists
- **Steps**:
  1. Select team
  2. Change manager to different user
  3. Submit
- **Expected**: Manager updated, new manager has team access

**TC-ORG-013: Deactivate Team**
- **Priority**: Medium
- **Pre-conditions**: Team exists
- **Steps**:
  1. Select team
  2. Set is_active=False
  3. Submit
- **Expected**: Team deactivated, not visible in active team list

### Team Membership Tests

**TC-ORG-014: Add Team Member**
- **Priority**: High
- **Pre-conditions**: Team exists, user exists
- **Steps**:
  1. Select team
  2. Click Add Member
  3. Select user
  4. Submit
- **Expected**: User added as team member, join date recorded

**TC-ORG-015: Remove Team Member**
- **Priority**: Medium
- **Pre-conditions**: User is team member
- **Steps**:
  1. Select team
  2. Remove member
- **Expected**: Member removed from team

**TC-ORG-016: User Member of Multiple Teams**
- **Priority**: Medium
- **Pre-conditions**: Multiple teams exist, user exists
- **Steps**:
  1. Add user to Team A
  2. Add same user to Team B
- **Expected**: User is member of both teams

**TC-ORG-017: Deactivate Team Member**
- **Priority**: Low
- **Pre-conditions**: User is active team member
- **Steps**:
  1. Set team membership is_active=False
- **Expected**: Member still in team but inactive

---

## 3.3 Plans Module

### Financial Year Management Tests

**TC-PLN-001: Create Financial Year**
- **Priority**: High
- **Pre-conditions**: Logged in as admin
- **Steps**:
  1. Navigate to financial years
  2. Click Create FY
  3. Enter year label "FY 25-26"
  4. Set start date: 2025-04-01
  5. Set end date: 2026-03-31
  6. Submit
- **Expected**: Financial year created

**TC-PLN-002: Duplicate Financial Year**
- **Priority**: High
- **Pre-conditions**: FY "FY 25-26" exists
- **Steps**:
  1. Attempt to create another "FY 25-26"
  2. Submit
- **Expected**: Validation error

**TC-PLN-003: Overlapping Financial Years**
- **Priority**: Medium
- **Pre-conditions**: FY 25-26 (Apr 2025 - Mar 2026) exists
- **Steps**:
  1. Attempt to create FY with dates overlapping existing FY
  2. Submit
- **Expected**: Validation error or warning

### Annual Plan Upload Tests

**TC-PLN-004: Upload Valid Annual Plan**
- **Priority**: High
- **Pre-conditions**: Team exists, FY exists, valid Excel file prepared
- **Steps**:
  1. Navigate to plans upload
  2. Select team
  3. Select financial year
  4. Upload Excel file
  5. Submit
- **Expected**: File uploaded, status=successful, FPI/GPI/PPI parameters created

**TC-PLN-005: Upload Invalid Annual Plan**
- **Priority**: High
- **Pre-conditions**: Team exists, FY exists, invalid Excel file (missing columns)
- **Steps**:
  1. Upload invalid Excel file
  2. Submit
- **Expected**: Upload status=failed, error log populated with details

**TC-PLN-006: Duplicate Annual Plan Upload**
- **Priority**: High
- **Pre-conditions**: Annual plan already uploaded for Team A, FY 25-26
- **Steps**:
  1. Attempt to upload another annual plan for same team and FY
  2. Submit
- **Expected**: Validation error or replacement confirmation

**TC-PLN-007: Annual Plan FPI Parameters Created**
- **Priority**: High
- **Pre-conditions**: Valid annual plan uploaded
- **Steps**:
  1. View FPI parameters for annual plan
- **Expected**: All FPI rows from Excel created with correct main head, sub head, annual goal, Q1-Q4 goals

**TC-PLN-008: Annual Plan GPI Parameters Created**
- **Priority**: High
- **Pre-conditions**: Valid annual plan uploaded
- **Steps**:
  1. View GPI parameters for annual plan
- **Expected**: All GPI rows from Excel created with correct name, type, annual goal, Q1-Q4 goals

**TC-PLN-009: Annual Plan PPI Projects Created**
- **Priority**: High
- **Pre-conditions**: Valid annual plan uploaded
- **Steps**:
  1. View PPI projects for annual plan
- **Expected**: All PPI rows from Excel created with correct project name, Q1-Q4 milestones

### Quarterly Plan Upload Tests

**TC-PLN-010: Upload Valid Quarterly Plan**
- **Priority**: High
- **Pre-conditions**: Team exists, FY exists, valid Excel file
- **Steps**:
  1. Navigate to quarterly plan upload
  2. Select team, FY, quarter (Q1)
  3. Upload Excel file
  4. Submit
- **Expected**: File uploaded, status=successful, FPI/GPI/PPI data created

**TC-PLN-011: Quarterly Plan FPI with Monthly Budgets**
- **Priority**: High
- **Pre-conditions**: Quarterly plan uploaded
- **Steps**:
  1. View FPI parameter
  2. Check month1_budget, month2_budget, month3_budget
- **Expected**: Monthly budgets match Excel data

**TC-PLN-012: Quarterly Plan GPI with Weekly Milestones**
- **Priority**: High
- **Pre-conditions**: Quarterly plan with weekly GPI uploaded
- **Steps**:
  1. View GPI parameter
  2. Check milestones (weeks 1-13)
- **Expected**: 13 milestone records created with budget values

**TC-PLN-013: Quarterly Plan GPI with Monthly Milestones**
- **Priority**: High
- **Pre-conditions**: Quarterly plan with monthly GPI uploaded
- **Steps**:
  1. View GPI parameter
  2. Check milestones (months 1-3)
- **Expected**: 3 milestone records created with budget values

**TC-PLN-014: Quarterly Plan PPI with Tasks**
- **Priority**: High
- **Pre-conditions**: Quarterly plan uploaded
- **Steps**:
  1. View PPI project
  2. Check tasks
- **Expected**: Tasks created for each week with description and assignee

**TC-PLN-015: Duplicate Quarterly Plan Upload**
- **Priority**: High
- **Pre-conditions**: Q1 plan uploaded for Team A, FY 25-26
- **Steps**:
  1. Attempt to upload another Q1 plan for same team and FY
- **Expected**: Validation error or replacement confirmation

### Plan Dashboard Tests

**TC-PLN-016: View Annual Plan Dashboard**
- **Priority**: High
- **Pre-conditions**: Annual plan uploaded for team
- **Steps**:
  1. Navigate to plans dashboard
  2. Select team
  3. Select annual plan
- **Expected**: Dashboard displays FPI, GPI, PPI tabs with annual data

**TC-PLN-017: View Quarterly Plan Dashboard**
- **Priority**: High
- **Pre-conditions**: Quarterly plan uploaded
- **Steps**:
  1. Navigate to plans dashboard
  2. Select team, FY, quarter
- **Expected**: Dashboard displays quarterly plan data with monthly/weekly details

**TC-PLN-018: Filter FPI by Main Head**
- **Priority**: Medium
- **Pre-conditions**: Multiple FPI parameters exist
- **Steps**:
  1. View FPI tab
  2. Apply filter: main_head=Revenue
- **Expected**: Only revenue FPI parameters displayed

**TC-PLN-019: Filter by Responsible User**
- **Priority**: Medium
- **Pre-conditions**: Parameters assigned to multiple users
- **Steps**:
  1. Select responsible user from filter
- **Expected**: Only parameters for selected user displayed

**TC-PLN-020: Export Plan to Excel**
- **Priority**: Low
- **Pre-conditions**: Plan exists
- **Steps**:
  1. View plan dashboard
  2. Click Export to Excel
- **Expected**: Excel file downloaded with plan data

---

## 3.4 Implement Module

### Action Management Tests

**TC-IMP-001: Create Manual Action**
- **Priority**: High
- **Pre-conditions**: Team exists, user is team manager
- **Steps**:
  1. Navigate to actions
  2. Click Create Action
  3. Enter action description
  4. Select priority: High
  5. Select assigned to: team member
  6. Set original due date
  7. Submit
- **Expected**: Action created with status=Not Started, source=manual

**TC-IMP-002: Create Action from PPI Task**
- **Priority**: High
- **Pre-conditions**: PPI task exists
- **Steps**:
  1. View PPI project details
  2. Click Add Action for specific task
  3. Action pre-populated with task description
  4. Assign to user
  5. Submit
- **Expected**: Action created with source=ppi, linked to PPI task

**TC-IMP-003: Create Action from Review Meeting**
- **Priority**: High
- **Pre-conditions**: Review meeting in progress
- **Steps**:
  1. In review meeting, click Add Action Item
  2. Enter description
  3. Assign to team member
  4. Set due date
  5. Submit
- **Expected**: Action created with source=review, linked to review meeting

**TC-IMP-004: Create Action for Issue**
- **Priority**: High
- **Pre-conditions**: Issue exists
- **Steps**:
  1. View issue details
  2. Click Add Action
  3. Enter action description
  4. Assign and set due date
  5. Submit
- **Expected**: Action created with source=issue, linked to issue

**TC-IMP-005: Update Action Status**
- **Priority**: High
- **Pre-conditions**: Action assigned to user
- **Steps**:
  1. User views My To-Do
  2. Select action
  3. Change status from Not Started to In Progress
  4. Add comments
  5. Submit
- **Expected**: Action status updated, history record created

**TC-IMP-006: Mark Action as Completed**
- **Priority**: High
- **Pre-conditions**: Action in progress
- **Steps**:
  1. Select action
  2. Change status to Completed
  3. Add completion comments
  4. Submit
- **Expected**: Action marked completed, completion timestamp recorded

**TC-IMP-007: Revise Action Due Date**
- **Priority**: High
- **Pre-conditions**: Action exists, user is assignee
- **Steps**:
  1. Select action
  2. Set revised due date (after original due date)
  3. Add challenge explaining delay
  4. Submit
- **Expected**: Revised due date saved, challenge recorded in history

**TC-IMP-008: Reject Action**
- **Priority**: Medium
- **Pre-conditions**: Action exists, user is manager
- **Steps**:
  1. Select action
  2. Change status to Rejected
  3. Enter rejection reason
  4. Submit
- **Expected**: Action status=Rejected, rejection reason saved

**TC-IMP-009: Reassign Action**
- **Priority**: High
- **Pre-conditions**: Action assigned to User A, User B exists in team
- **Steps**:
  1. Manager selects action
  2. Click Reassign
  3. Select User B
  4. Enter reassignment reason
  5. Submit
- **Expected**: Action now assigned to User B, history shows reassignment

**TC-IMP-010: Create Sub-Action**
- **Priority**: Medium
- **Pre-conditions**: Parent action exists
- **Steps**:
  1. View parent action
  2. Click Add Sub-Action
  3. Enter sub-action details
  4. Submit
- **Expected**: Sub-action created, linked to parent action

**TC-IMP-011: View Action History**
- **Priority**: Medium
- **Pre-conditions**: Action with multiple status changes exists
- **Steps**:
  1. View action details
  2. Click History tab
- **Expected**: All status changes, comments, updates displayed chronologically

### My To-Do Dashboard Tests

**TC-IMP-012: View My To-Do Dashboard**
- **Priority**: High
- **Pre-conditions**: User has assigned actions
- **Steps**:
  1. Navigate to My To-Do
- **Expected**: All actions assigned to user displayed, grouped by status

**TC-IMP-013: Filter Overdue Actions**
- **Priority**: High
- **Pre-conditions**: Some actions are overdue
- **Steps**:
  1. Click Overdue filter
- **Expected**: Only actions with due date < today displayed in red

**TC-IMP-014: Filter Actions Due This Week**
- **Priority**: Medium
- **Pre-conditions**: Actions with various due dates
- **Steps**:
  1. Click Due This Week filter
- **Expected**: Only actions due within next 7 days displayed

**TC-IMP-015: Update Action Inline**
- **Priority**: High
- **Pre-conditions**: On My To-Do dashboard
- **Steps**:
  1. Select action
  2. Update status dropdown inline
  3. Auto-save
- **Expected**: Status updated without full page reload

**TC-IMP-016: Add Comment to Action**
- **Priority**: Medium
- **Pre-conditions**: On action details
- **Steps**:
  1. Enter comment in text area
  2. Submit
- **Expected**: Comment added with timestamp and user

### Numbers Tracking Tests

**TC-IMP-017: Enter Weekly GPI Actual**
- **Priority**: High
- **Pre-conditions**: Weekly GPI parameter exists for current week
- **Steps**:
  1. Navigate to Numbers Tracking
  2. Select week
  3. View GPI parameters
  4. Enter last_week_actual value
  5. Enter current_week_plan value
  6. Add comments explaining variance
  7. Submit
- **Expected**: Values saved, variance calculated and displayed

**TC-IMP-018: Enter Monthly FPI Actual**
- **Priority**: High
- **Pre-conditions**: Monthly FPI parameter exists
- **Steps**:
  1. Navigate to Numbers Tracking
  2. Select month
  3. View FPI parameters
  4. Enter last_month_actual
  5. Enter current_month_plan
  6. Submit
- **Expected**: Values saved, variance from budget shown

**TC-IMP-019: View Numbers Tracking History**
- **Priority**: Medium
- **Pre-conditions**: Multiple weeks/months of data entered
- **Steps**:
  1. View numbers tracking for parameter
  2. Select date range
- **Expected**: Historical trend displayed, chart/graph shown

### Project Status Tracking Tests

**TC-IMP-020: Update PPI Project Status**
- **Priority**: High
- **Pre-conditions**: PPI project exists
- **Steps**:
  1. Navigate to project status
  2. Select project
  3. Update status to At Risk
  4. Set completion percentage: 45%
  5. Enter challenge description
  6. Submit
- **Expected**: Project status updated, history record created

**TC-IMP-021: Revise Project Due Date**
- **Priority**: High
- **Pre-conditions**: Project exists
- **Steps**:
  1. Select project
  2. Set revised due date
  3. Enter reason for delay
  4. Submit
- **Expected**: Revised due date saved, challenge recorded

**TC-IMP-022: Complete Project**
- **Priority**: High
- **Pre-conditions**: Project exists
- **Steps**:
  1. Update status to Completed
  2. Set completion percentage: 100%
  3. Add completion comments
  4. Submit
- **Expected**: Project marked completed, all tasks should be completed

**TC-IMP-023: Project Status Alert**
- **Priority**: Medium
- **Pre-conditions**: Project moved to Danger status
- **Steps**:
  1. Update project to Danger
  2. Submit
- **Expected**: Manager notified via email/notification

### Issue Management Tests

**TC-IMP-024: Create Issue**
- **Priority**: High
- **Pre-conditions**: User is team member
- **Steps**:
  1. Navigate to Issues
  2. Click Create Issue
  3. Enter title: "Printer not working"
  4. Enter description
  5. Set priority: High
  6. Set required by date
  7. Select team
  8. Submit
- **Expected**: Issue created with status=Open

**TC-IMP-025: View Issue Dashboard**
- **Priority**: High
- **Pre-conditions**: Multiple issues exist
- **Steps**:
  1. Navigate to Issue Dashboard
- **Expected**: All team issues displayed with status, priority, assigned team

**TC-IMP-026: Filter Issues by Status**
- **Priority**: Medium
- **Pre-conditions**: Issues with various statuses
- **Steps**:
  1. Select filter: Status=Open
- **Expected**: Only open issues displayed

**TC-IMP-027: Add Action to Issue**
- **Priority**: High
- **Pre-conditions**: Issue exists
- **Steps**:
  1. View issue details
  2. Click Add Action
  3. Create action
  4. Submit
- **Expected**: Action created and linked to issue

**TC-IMP-028: Resolve Issue**
- **Priority**: High
- **Pre-conditions**: Issue exists with all actions completed
- **Steps**:
  1. Change issue status to Resolved
  2. Add resolution comments
  3. Submit
- **Expected**: Issue status=Resolved, resolution timestamp recorded

**TC-IMP-029: Escalate Issue**
- **Priority**: High
- **Pre-conditions**: Issue exists, parent team exists
- **Steps**:
  1. View issue
  2. Click Escalate
  3. Select parent team
  4. Enter escalation reason
  5. Submit
- **Expected**: Issue status=Escalated, assigned to parent team, previous status saved

**TC-IMP-030: Put Issue on Hold**
- **Priority**: Medium
- **Pre-conditions**: Issue status=Open
- **Steps**:
  1. Change status to On Hold
  2. Enter reason
  3. Submit
- **Expected**: Issue on hold, previous status saved

**TC-IMP-031: Drop Issue**
- **Priority**: Medium
- **Pre-conditions**: Issue exists
- **Steps**:
  1. Change status to Dropped
  2. Enter reason
  3. Submit
- **Expected**: Issue status=Dropped

**TC-IMP-032: Issue Resolution Progress**
- **Priority**: Medium
- **Pre-conditions**: Issue with 5 actions, 3 completed
- **Steps**:
  1. View issue
- **Expected**: Progress shown as "3 of 5 actions completed (60%)"

---

## 3.5 Reviews Module

### Review Meeting Management Tests

**TC-REV-001: Create Weekly Review Meeting**
- **Priority**: High
- **Pre-conditions**: User is team manager
- **Steps**:
  1. Navigate to Reviews
  2. Click Create Review Meeting
  3. Select type: Weekly
  4. Set date and time
  5. Select financial year and quarter
  6. Set week number
  7. Select participants
  8. Submit
- **Expected**: Review meeting created with status=Draft

**TC-REV-002: Create Monthly Review Meeting**
- **Priority**: High
- **Pre-conditions**: User is team manager
- **Steps**:
  1. Create review meeting, type=Monthly
  2. Set month number
  3. Submit
- **Expected**: Monthly review created

**TC-REV-003: Add Review Participants**
- **Priority**: Medium
- **Pre-conditions**: Review meeting created
- **Steps**:
  1. Edit review meeting
  2. Select team members as participants
  3. Submit
- **Expected**: Participants added to review

### Review Notes Tests

**TC-REV-004: Add Review Note**
- **Priority**: High
- **Pre-conditions**: Review meeting exists
- **Steps**:
  1. Open review meeting
  2. Click Add Note
  3. Enter title
  4. Enter content
  5. Submit
- **Expected**: Note added with creator and timestamp

**TC-REV-005: Edit Review Note**
- **Priority**: High
- **Pre-conditions**: Review note exists
- **Steps**:
  1. Click Edit on note
  2. Update title and content
  3. Save
- **Expected**: Note updated

**TC-REV-006: Delete Review Note**
- **Priority**: Medium
- **Pre-conditions**: Review note exists
- **Steps**:
  1. Click Delete on note
  2. Confirm deletion
- **Expected**: Note deleted

**TC-REV-007: Reorder Review Notes**
- **Priority**: Low
- **Pre-conditions**: Multiple notes exist
- **Steps**:
  1. Click Move Up/Down on note
  2. Verify new order
- **Expected**: Notes reordered

**TC-REV-008: Cancel Add Note with Warning**
- **Priority**: Medium
- **Pre-conditions**: Adding new note with data entered
- **Steps**:
  1. Click Add Note
  2. Enter title and content
  3. Click Cancel
- **Expected**: Warning dialog: "You will lose the data entered. Do you wish to continue?"

**TC-REV-009: Cancel Edit Note with Warning**
- **Priority**: Medium
- **Pre-conditions**: Editing note with changes
- **Steps**:
  1. Edit note content
  2. Click Cancel
- **Expected**: Warning dialog displayed

### Review Decisions Tests

**TC-REV-010: Add Review Decision**
- **Priority**: High
- **Pre-conditions**: Review meeting exists
- **Steps**:
  1. Click Add Decision
  2. Enter decision text
  3. Submit
- **Expected**: Decision added with serial number D1

**TC-REV-011: Decision Auto-Numbering**
- **Priority**: High
- **Pre-conditions**: Review with 3 decisions
- **Steps**:
  1. Add 4th decision
- **Expected**: Decision numbered D4

**TC-REV-012: Edit Decision**
- **Priority**: High
- **Pre-conditions**: Decision exists
- **Steps**:
  1. Click Edit on decision
  2. Update decision text
  3. Save
- **Expected**: Decision updated

**TC-REV-013: Delete Decision with Renumbering**
- **Priority**: High
- **Pre-conditions**: 5 decisions exist (D1-D5)
- **Steps**:
  1. Delete decision D3
  2. Confirm
- **Expected**: Decision deleted, D4 becomes D3, D5 becomes D4

**TC-REV-014: Reorder Decisions**
- **Priority**: Medium
- **Pre-conditions**: Multiple decisions exist
- **Steps**:
  1. Move decision D2 to top
- **Expected**: Decision moved, renumbered to D1, others shifted

**TC-REV-015: Export Decisions to PDF**
- **Priority**: Low
- **Pre-conditions**: Decisions exist
- **Steps**:
  1. Click Export to PDF
- **Expected**: PDF file generated with all decisions

**TC-REV-016: Copy Decisions to Clipboard**
- **Priority**: Low
- **Pre-conditions**: Decisions exist
- **Steps**:
  1. Click Copy to Clipboard
- **Expected**: Decisions copied in formatted text

**TC-REV-017: Cancel Add Decision with Warning**
- **Priority**: Medium
- **Pre-conditions**: Adding decision with content entered
- **Steps**:
  1. Enter decision text
  2. Click Cancel
- **Expected**: Warning dialog displayed

### Review Action Items Tests

**TC-REV-018: Add Action Item in Review**
- **Priority**: High
- **Pre-conditions**: Review meeting in progress
- **Steps**:
  1. Navigate to FPI tab
  2. Click on FPI parameter row
  3. Action item popup opens
  4. Enter action description
  5. Assign to team member
  6. Set due date and priority
  7. Submit
- **Expected**: Action item created, linked to FPI parameter and review meeting

**TC-REV-019: Link Action to GPI Parameter**
- **Priority**: High
- **Pre-conditions**: Review meeting, GPI parameter exists
- **Steps**:
  1. Navigate to GPI tab
  2. Click Add Action for GPI parameter
  3. Create action
- **Expected**: Action created with parameter_type=gpi, parameter_id set

**TC-REV-020: Link Action to PPI Project**
- **Priority**: High
- **Pre-conditions**: Review meeting, PPI project exists
- **Steps**:
  1. Navigate to PPI tab
  2. Click on project row
  3. Create action
- **Expected**: Action linked to PPI project

**TC-REV-021: Assign Action to Different Team**
- **Priority**: High
- **Pre-conditions**: Review meeting, multiple teams exist
- **Steps**:
  1. Create action item
  2. Select assigned_to_team (different from review meeting team)
  3. Select team member from that team
  4. Submit
- **Expected**: Action assigned to other team member

### Review Tab Tests

**TC-REV-022: View FPI Tab in Review**
- **Priority**: High
- **Pre-conditions**: Review meeting with quarterly plan
- **Steps**:
  1. Open review meeting
  2. Click FPI tab
- **Expected**: All FPI parameters displayed with budget, plan, actual, variance

**TC-REV-023: View GPI Tab in Review**
- **Priority**: High
- **Pre-conditions**: Review meeting with quarterly plan
- **Steps**:
  1. Open review meeting
  2. Click GPI tab
- **Expected**: All GPI parameters displayed with tracking data

**TC-REV-024: View PPI Tab in Review**
- **Priority**: High
- **Pre-conditions**: Review meeting with quarterly plan
- **Steps**:
  1. Open review meeting
  2. Click PPI tab
- **Expected**: All PPI projects displayed with tasks and status

**TC-REV-025: View Issues Tab in Review**
- **Priority**: High
- **Pre-conditions**: Review meeting, team issues exist
- **Steps**:
  1. Open review meeting
  2. Click Issues tab
- **Expected**: All team issues displayed with status and actions

**TC-REV-026: Click FPI Row Opens Action Popup**
- **Priority**: High
- **Pre-conditions**: Review meeting, FPI data exists
- **Steps**:
  1. In FPI tab, click on any cell in FPI row
- **Expected**: Action item popup opens, pre-populated with FPI parameter context

**TC-REV-027: Click PPI Task Opens Action Popup**
- **Priority**: High
- **Pre-conditions**: Review meeting, PPI tasks exist
- **Steps**:
  1. In PPI tab, click on task row
- **Expected**: Action popup opens with task context

**TC-REV-028: Filter FPI by Responsible User in Review**
- **Priority**: Medium
- **Pre-conditions**: Multiple FPI parameters with different owners
- **Steps**:
  1. In FPI tab, select responsible user filter
- **Expected**: Only FPI parameters for selected user shown

### Review Finalization Tests

**TC-REV-029: Finalize Review Meeting**
- **Priority**: High
- **Pre-conditions**: Review meeting with notes and decisions
- **Steps**:
  1. Click Finalize Meeting
  2. Confirm
- **Expected**: Meeting status=Finalized, finalized_by and finalized_at set

**TC-REV-030: Cannot Edit Finalized Review**
- **Priority**: High
- **Pre-conditions**: Review meeting finalized
- **Steps**:
  1. Attempt to add note or decision
- **Expected**: Error message, editing disabled

**TC-REV-031: Generate Review Summary PDF**
- **Priority**: Medium
- **Pre-conditions**: Review finalized
- **Steps**:
  1. Click Generate Summary
- **Expected**: PDF generated with all notes, decisions, action items

**TC-REV-032: Email Review Summary**
- **Priority**: Low
- **Pre-conditions**: Review finalized with participants
- **Steps**:
  1. Click Send Summary
- **Expected**: Email sent to all participants with PDF attachment

---

## 3.6 Improve Module

### Improvement Upload Tests

**TC-IMP-033: Upload Improvement Projects**
- **Priority**: High
- **Pre-conditions**: Team exists, FY and quarter selected
- **Steps**:
  1. Navigate to Improve Upload
  2. Select team, FY, Q1
  3. Upload Excel file with improvement projects
  4. Submit
- **Expected**: Upload successful, improvement projects and tasks created

**TC-IMP-034: Improvement Upload Error Handling**
- **Priority**: High
- **Pre-conditions**: Invalid Excel file
- **Steps**:
  1. Upload invalid file
  2. Submit
- **Expected**: Upload status=failed, error log shows specific errors

**TC-IMP-035: View Improvement Projects**
- **Priority**: High
- **Pre-conditions**: Improvement upload successful
- **Steps**:
  1. Navigate to Improve Dashboard
  2. Select quarter
- **Expected**: All improvement projects displayed

### Improvement Project Management Tests

**TC-IMP-036: Update Improvement Project Status**
- **Priority**: High
- **Pre-conditions**: Improvement project exists
- **Steps**:
  1. Select project
  2. Update status, completion %, comments
  3. Submit
- **Expected**: Project status updated, history created

**TC-IMP-037: Complete Improvement Task**
- **Priority**: High
- **Pre-conditions**: Improvement task exists
- **Steps**:
  1. Select task
  2. Mark as completed
- **Expected**: Task marked complete, completion timestamp set

**TC-IMP-038: Create Action from Improvement Task**
- **Priority**: High
- **Pre-conditions**: Improvement task exists
- **Steps**:
  1. View task
  2. Click Create Action
  3. Action pre-populated
  4. Submit
- **Expected**: Action created with source=improvement, linked to task

**TC-IMP-039: Filter Improvement Projects by Status**
- **Priority**: Medium
- **Pre-conditions**: Projects with various statuses
- **Steps**:
  1. Select status filter: At Risk
- **Expected**: Only at-risk projects displayed

**TC-IMP-040: View Improvement Project History**
- **Priority**: Medium
- **Pre-conditions**: Project with status updates
- **Steps**:
  1. View project
  2. Click History
- **Expected**: All status changes displayed chronologically

---

## 4. Integration Test Scenarios

### Scenario 1: End-to-End Plan Upload and Review

**TC-INT-001: Complete Plan to Review Workflow**
- **Priority**: High
- **Pre-conditions**: Team setup complete
- **Steps**:
  1. Admin creates FY 25-26
  2. Coordinator uploads annual plan for Team A
  3. System processes annual plan (FPI, GPI, PPI created)
  4. Coordinator uploads Q1 quarterly plan
  5. System processes quarterly plan with monthly/weekly details
  6. Week 1: Manager enters actual values for GPI parameters
  7. Week 1: Manager conducts weekly review meeting
  8. During review, creates action items for variances
  9. Manager finalizes review
  10. Team members see action items in My To-Do
- **Expected**: Complete workflow successful, data flows correctly from upload to action assignment

### Scenario 2: Issue Creation and Resolution

**TC-INT-002: Issue Lifecycle**
- **Priority**: High
- **Pre-conditions**: Team exists
- **Steps**:
  1. Team member creates issue
  2. Manager views issue in dashboard
  3. Manager creates 3 action items for issue resolution
  4. Assigns actions to different team members
  5. Team members update action status as they work
  6. All 3 actions marked completed
  7. Manager resolves issue
- **Expected**: Issue status flows correctly, actions linked, resolution tracked

### Scenario 3: Project Tracking Across Quarter

**TC-INT-003: PPI Project Tracking**
- **Priority**: High
- **Pre-conditions**: Quarterly plan uploaded with PPI project
- **Steps**:
  1. Week 1: Manager updates project status to On Track
  2. Week 2: Task assigned for week 2 marked complete
  3. Week 5: Project moved to At Risk due to delay
  4. Week 6: Manager creates action items during review
  5. Week 10: Revised due date set
  6. Week 13: Project completed
- **Expected**: Project status history maintained, tasks tracked, completion recorded

### Scenario 4: Multi-Team Escalation

**TC-INT-004: Issue Escalation Workflow**
- **Priority**: Medium
- **Pre-conditions**: Parent team and child team exist
- **Steps**:
  1. Child team member creates issue
  2. Child team manager cannot resolve
  3. Issue escalated to parent team
  4. Parent team manager assigns action to parent team member
  5. Action completed
  6. Issue resolved
- **Expected**: Escalation works, issue visible to both teams, resolution tracked

---

## 5. Security Test Cases

### Authentication Tests

**TC-SEC-001: Unauthorized Access to Protected Page**
- **Priority**: High
- **Steps**:
  1. Open browser (not logged in)
  2. Navigate to /implement/actions/
- **Expected**: Redirected to login page

**TC-SEC-002: Session Timeout**
- **Priority**: Medium
- **Steps**:
  1. Login
  2. Wait for session timeout (configurable, e.g., 30 min)
  3. Attempt to access page
- **Expected**: Session expired, redirected to login

**TC-SEC-003: CSRF Protection**
- **Priority**: High
- **Steps**:
  1. Attempt POST request without CSRF token
- **Expected**: Request rejected with 403 Forbidden

**TC-SEC-004: SQL Injection Prevention**
- **Priority**: High
- **Steps**:
  1. Enter SQL injection payload in search field: `' OR '1'='1`
  2. Submit
- **Expected**: Input sanitized, no SQL injection

**TC-SEC-005: XSS Prevention**
- **Priority**: High
- **Steps**:
  1. Enter XSS payload in text field: `<script>alert('XSS')</script>`
  2. Save
  3. View page
- **Expected**: Script tag escaped and displayed as text

### Authorization Tests

**TC-SEC-006: Coordinator Cannot Access Other Organization**
- **Priority**: High
- **Pre-conditions**: Coordinator for Org A
- **Steps**:
  1. Attempt to access Org B team URL directly
- **Expected**: Access denied

**TC-SEC-007: Team Member Cannot Access Other Team**
- **Priority**: High
- **Pre-conditions**: User is member of Team A only
- **Steps**:
  1. Attempt to access Team B actions URL
- **Expected**: Access denied

**TC-SEC-008: General User Cannot Impersonate**
- **Priority**: High
- **Pre-conditions**: Logged in as general user
- **Steps**:
  1. Attempt to access impersonate URL
- **Expected**: Access denied, 403 error

**TC-SEC-009: Non-Manager Cannot Create Review Meeting**
- **Priority**: High
- **Pre-conditions**: User is team member (not manager)
- **Steps**:
  1. Attempt to create review meeting
- **Expected**: Access denied

**TC-SEC-010: User Cannot Edit Others' Actions**
- **Priority**: High
- **Pre-conditions**: Action assigned to User A
- **Steps**:
  1. User B attempts to edit User A's action
- **Expected**: Permission denied

### Data Validation Tests

**TC-SEC-011: File Upload Size Limit**
- **Priority**: Medium
- **Steps**:
  1. Attempt to upload file > 25MB
- **Expected**: Error message, file rejected

**TC-SEC-012: File Upload Type Validation**
- **Priority**: Medium
- **Steps**:
  1. Attempt to upload .exe file as plan
- **Expected**: File type rejected

**TC-SEC-013: Email Format Validation**
- **Priority**: Medium
- **Steps**:
  1. Enter invalid email: "notanemail"
  2. Submit user form
- **Expected**: Validation error

**TC-SEC-014: Password Strength Enforcement**
- **Priority**: High
- **Steps**:
  1. Attempt to set password: "123"
- **Expected**: Error: password must be at least 8 characters

**TC-SEC-015: Date Range Validation**
- **Priority**: Medium
- **Steps**:
  1. Set project end date before start date
  2. Submit
- **Expected**: Validation error

---

## 6. Performance Test Cases

**TC-PERF-001: Page Load Time**
- **Priority**: High
- **Steps**:
  1. Measure page load time for dashboard
  2. Repeat for other major pages
- **Expected**: < 3 seconds for 90% of requests

**TC-PERF-002: Concurrent User Load**
- **Priority**: Medium
- **Steps**:
  1. Simulate 100 concurrent users
  2. Each user performs typical workflows
- **Expected**: System remains responsive, error rate < 1%

**TC-PERF-003: Large File Upload**
- **Priority**: Medium
- **Steps**:
  1. Upload 20MB Excel file
  2. Measure processing time
- **Expected**: Upload completes within 60 seconds

**TC-PERF-004: Large Dataset Query**
- **Priority**: Medium
- **Steps**:
  1. Query database with 10,000+ records
  2. Measure response time
- **Expected**: Query completes within 5 seconds

**TC-PERF-005: Dashboard with Large Data**
- **Priority**: Medium
- **Steps**:
  1. Load dashboard with 500+ actions
  2. Measure render time
- **Expected**: Page loads within 5 seconds

---

## 7. UI/UX Test Cases

**TC-UI-001: Responsive Design - Mobile**
- **Priority**: High
- **Steps**:
  1. Access application on mobile device (320px width)
  2. Navigate through major pages
- **Expected**: All pages render correctly, content accessible

**TC-UI-002: Responsive Design - Tablet**
- **Priority**: High
- **Steps**:
  1. Access on tablet (768px width)
- **Expected**: Proper layout, no horizontal scroll

**TC-UI-003: Breadcrumb Navigation**
- **Priority**: Medium
- **Steps**:
  1. Navigate: Dashboard > Teams > Team A > Actions
  2. Check breadcrumbs
- **Expected**: Breadcrumbs show correct path, clickable

**TC-UI-004: Form Validation Messages**
- **Priority**: High
- **Steps**:
  1. Submit form with required field empty
- **Expected**: Clear error message next to field

**TC-UI-005: Success Messages**
- **Priority**: Medium
- **Steps**:
  1. Create new team
- **Expected**: Green success message: "Team created successfully"

**TC-UI-006: Confirmation Dialogs**
- **Priority**: High
- **Steps**:
  1. Click Delete on action
- **Expected**: Confirmation dialog: "Are you sure?"

**TC-UI-007: Loading Indicators**
- **Priority**: Medium
- **Steps**:
  1. Upload large file
- **Expected**: Loading spinner shown during processing

**TC-UI-008: Tooltips and Help Text**
- **Priority**: Low
- **Steps**:
  1. Hover over info icon next to complex field
- **Expected**: Tooltip with helpful explanation

**TC-UI-009: Color Coding for Priority**
- **Priority**: Medium
- **Steps**:
  1. View action list with various priorities
- **Expected**: High=red, Medium=orange, Low=green

**TC-UI-010: Overdue Visual Indicator**
- **Priority**: High
- **Steps**:
  1. View action with due date in past
- **Expected**: Action highlighted in red, "OVERDUE" label

---

## 8. Regression Test Suite

After any code changes, run these critical path tests:

### Critical Path Tests

**TC-REG-001: Login**
- Login with valid credentials

**TC-REG-002: Create Team**
- Admin creates new team

**TC-REG-003: Upload Quarterly Plan**
- Upload valid quarterly plan Excel

**TC-REG-004: Create Action**
- Manager creates action for team member

**TC-REG-005: Update Action Status**
- Team member updates action status

**TC-REG-006: Conduct Review Meeting**
- Manager creates and conducts review, adds notes and decisions

**TC-REG-007: Create Issue**
- Team member creates issue

**TC-REG-008: View My To-Do**
- User views their to-do dashboard

**TC-REG-009: Enter Numbers**
- Update FPI/GPI actual values

**TC-REG-010: Update Project Status**
- Update PPI project status

---

## 9. Test Data Requirements

### Master Data
- **Organizations**: 3 orgs (Acme Corp, Beta Inc, Gamma LLC)
- **Users**: 20 users across various roles
  - 2 Admins
  - 3 Coordinators (1-2 per org)
  - 15 General users
- **Teams**: 10 teams across organizations
- **Financial Years**: 3 FYs (FY 24-25, FY 25-26, FY 26-27)

### Transactional Data
- **Annual Plans**: 5 annual plans
- **Quarterly Plans**: 15 quarterly plans (various quarters)
- **FPI Parameters**: 100 parameters
- **GPI Parameters**: 80 parameters
- **PPI Projects**: 50 projects
- **PPITasks**: 500 tasks
- **Actions**: 200 actions in various statuses
- **Issues**: 30 issues in various statuses
- **Review Meetings**: 20 review meetings
- **Improvement Projects**: 25 improvement projects

### Test Files
- **Valid Annual Plan Excel**: Sample with all required sheets
- **Valid Quarterly Plan Excel**: Sample with all required sheets
- **Invalid Excel Files**: Missing columns, wrong data types
- **Large Excel File**: 20MB file for performance testing

---

## 10. Test Metrics

### Metrics to Track

**Test Coverage**
- Unit test coverage: Target 80%
- Integration test coverage: Target 70%
- Manual test case execution: Target 100% for critical paths

**Defect Metrics**
- Defects found per module
- Defect severity distribution
- Defect resolution time
- Defect leakage (found in production)

**Quality Metrics**
- Test pass rate: Target > 95%
- Test execution time
- Automated vs manual test ratio

**Performance Metrics**
- Average page load time
- API response time
- Database query performance

---

## 11. Entry and Exit Criteria

### Entry Criteria for Testing
- Code complete and deployed to test environment
- Test environment setup complete
- Test data prepared
- Test cases reviewed and approved

### Exit Criteria for Testing
- 100% of critical path tests passed
- > 95% of all test cases passed
- All severity 1 (critical) defects resolved
- All severity 2 (major) defects resolved or have workarounds
- Test coverage targets met
- Performance metrics meet requirements
- User acceptance testing completed and signed off

---

## 12. Test Schedule

**Week 1-2: Unit Testing**
- Models, forms, utilities
- 80% code coverage target

**Week 3-4: Integration Testing**
- Workflow testing
- Cross-module integration

**Week 5-6: System Testing**
- End-to-end scenarios
- UI/UX testing
- Security testing

**Week 7: Performance Testing**
- Load testing
- Stress testing

**Week 8: User Acceptance Testing**
- Stakeholder testing
- Production readiness verification

**Ongoing: Regression Testing**
- After each code change
- Before each release

---

## 13. Defect Management

### Severity Levels

**Severity 1 - Critical**
- System crash or data loss
- Security vulnerability
- Cannot login
- Cannot upload plans
- Fix within 24 hours

**Severity 2 - Major**
- Major feature broken
- Workaround available
- Data incorrect
- Fix within 1 week

**Severity 3 - Minor**
- Minor feature issue
- UI glitch
- Fix within 2 weeks

**Severity 4 - Cosmetic**
- Formatting issue
- Typo
- Fix as time permits

### Defect Reporting
- Use issue tracking system (e.g., Jira, GitHub Issues)
- Include: Test Case ID, Steps to Reproduce, Expected vs Actual, Screenshots, Environment
- Assign to development team
- Track status: Open, In Progress, Fixed, Verified, Closed

---

## 14. Tools and Resources

### Testing Tools
- **Unit Testing**: Django TestCase, pytest
- **Integration Testing**: Django Client, Selenium
- **Load Testing**: Apache JMeter, Locust
- **Code Coverage**: coverage.py
- **Database**: SQLite (dev), PostgreSQL (staging/prod)
- **Browser Testing**: Chrome, Firefox, Safari, Edge
- **Mobile Testing**: Chrome DevTools, BrowserStack

### Test Environment
- **Dev**: http://localhost:8000
- **Staging**: https://staging.pre-system.com
- **Production**: https://pre-system.com

### Test Accounts
- admin@test.com / TestAdmin123!
- coordinator@test.com / TestCoord123!
- manager@test.com / TestManager123!
- member@test.com / TestMember123!

---

## 15. Risks and Mitigation

### Risk 1: Insufficient Test Data
- **Mitigation**: Create automated test data generation scripts

### Risk 2: Environment Downtime
- **Mitigation**: Maintain local dev environment as backup

### Risk 3: Tight Timeline
- **Mitigation**: Prioritize critical path tests, automate where possible

### Risk 4: Changing Requirements
- **Mitigation**: Maintain traceability matrix, update test cases promptly

---

## Appendix A: Test Case Template

```
Test Case ID: TC-[MODULE]-[NUMBER]
Title: [Brief description]
Priority: High/Medium/Low
Module: [Accounts/Organizations/Plans/Implement/Reviews/Improve]
Test Type: Functional/Integration/Security/Performance/UI

Pre-conditions:
- [List all pre-conditions]

Test Steps:
1. [Step 1]
2. [Step 2]
3. [Step 3]

Test Data:
- [Data required]

Expected Result:
- [What should happen]

Actual Result:
- [What actually happened - filled during execution]

Status: Pass/Fail/Blocked
Executed By: [Tester name]
Execution Date: [Date]
Notes: [Any additional notes]
```

---

## Appendix B: Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Oct 2, 2025 | System Analysis | Initial test plan based on codebase analysis |

