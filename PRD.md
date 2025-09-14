**Introduction**

PRE is a review tool which can be used to conduct periodic review meetings for any team. In order to conduct the review, the pre-requisite is a plan and regular progress data. As a result of the review, actions will be decided and these need to be tracked. Review meetings will also be used to address any issues faced by the team members.

**Technical details**

The system has to be developed using Python and Django with SQLite for the Dev environment and Postgres for the Stage and Production environments. The application should be made mobile friendly.

All grids in the system should have sort and filter functionality on all columns by default except for column which contains action buttons. Both these functionalities should be presented as buttons on each grid column. Sort functionality should be capable of multi-column sort with ascending and descending options. Filter functionality should have all features similar to Excel column filter.

All Numeric fields in the system will always have 2 decimals and comma positions should be as per the regional settings.

All dropdowns in the system should have a facility to search if the list is long.

**Model details**

The user roles could be either of: admin, coordinator, general. There will be one user called admin whose role will be admin. The user called “admin” will have the ability to define new organizations and their coordinators. Coordinators will have the ability to define the General users and Teams of an organization. Coordinator users can access the entire data for one or more designated organizations by impersonating a General user of an organization.

A Team comprises of a Team Manager and one or more Team Members. General users can be Team Managers for multiple teams and could be Members of multiple teams. The access of data in the system depends on the team membership.

Plans could be Annual Plans and Quarterly Plans. Both these types of plans lay out the Financial Performance Indicators (FPI), Goal Performance Indicators (GPI) and Project Performance Indicators (PPI). While FPI & GPI specify numeric goals, PPI specifies action milestones. These plans will be uploaded into the system in Excel format.

FPI consists of 4 heads viz., Revenue, Variable Costs, Operating Expenses and Other Expenses. Each of these can be bifurcated into sub-heads and these will be defined in the Annual Plan FPI sheet. The plans will specify the main heads, sub-heads and total lines and lines having sub-heads will indicate the main head against each of them. So, when the import is done, only the lines with the sub-heads having specified main head will be imported.  In Quarterly Plan, Responsible User will also be indicated in FPI, GPI and PPI sheets against each line. The Responsible User will be the mail ID of the user.

Annual Plan specifies the annual goals with quarter wise estimates whereas the Quarterly Plan specifies the quarter goals bifurcated into either weekly or monthly milestones. FPI will be bifurcated into monthly milestones, GPI can be weekly or monthly and PPI will be only weekly bifurcation in the Quarterly Plan.

In PPI, the weekly milestones against each project may contain multiple tasks. These tasks will be converted into separate To Do items in the system. The initial assignee for each of the actions will be the Responsible User who can reassign the actions to other members.

**Audit Trail**

A complete audit trail is required to know who & when each of the data has been updated in the system. In case the coordinator acts as a user and updates any data, the audit trail must indicate this as well.

# **Login**

The login screen will ask the user for the email ID and password. This screen will have a Forgot Password link and a Sign In button. The Forgot Password link will be enabled after the email ID has been entered. On click of the Sign In button, if the user is logging in for the first time, the user will be forced to change the password and then the home page for the user will be displayed; else, if this is not the first log in by the user, the home page for the user will be opened.

# **Dashboard**

This is a placeholder for future dashboard. All reports will be accessible from this dashboard. The Dashboard will be the landing page after login.

Depending on the type of user, the menu options will be displayed in the side bar. In all cases, at the bottom of the side bar, there will be Sign Out button, the name of the logged in user and the version number of the software. In case the user is “admin”, the menu options will be Dashboard, Manage Organizations and Change Password. If the type of user is Coordinator, the menu options will be Dashboard, Login As, Change Password, Manage Users and Manage Teams. If the type of user is General, the menu options will be Dashboard, Plan, Implement, Review, Improve and Change Password.

# **Manage Organizations**

This screen will display the list of organizations defined in the system in a grid with the following columns: Organization Name, Action. Under Action column, it will have buttons for: Edit, Inactivate/Reactivate, View Coordinators. Edit screen will enable change of organization name and a grid displaying coordinator information with the columns name of coordinator, mobile number, the email ID, Action. In the Action column, it will have buttons to edit & inactivate/reactivate the coordinator. At the top of the grid, it will have a button to add New Coordinator with the required information of name, mobile number and email ID.

At the top of the screen, there will be a New Organization button to capture the name and a grid to display the coordinator information with the columns name of coordinator, mobile number, the email ID, Action. In the Action column, it will have buttons to edit & delete the coordinator. At the top of the grid, it will have a button to add New Coordinator with the required information of name, mobile number and email ID.

# **Login As**

Login As will be an option using which the Coordinator can impersonate a specific General user of a specific organization. When the Coordinator users impersonate another user, there will be an additional option of My Login in the sidebar that will take the system back to the original screen of the Coordinator.

On click of this option, the system will display a list of organizations identified for the Coordinator who has logged in. Once the organization is selected, it will display a list of General users in the selected organization. And then have a Log In button.

On click of the Log In button, the screen of the selected General user will be displayed and all actions allowed for the General user can be done by the coordinator. However, in the audit trail, the coordinator name will be logged in along with the General user name.

# **Change Password**

Ask for the old password. And then ask for the new password with a reconfirmation of the same. Use any standard password requirement for strong passwords. On click of Ok, the Dashboard screen to be opened. On click of Cancel, show the Login screen again.

# **Manage Users**

This screen will have a grid with the following columns: User name, Mobile Number, Email ID and Action. Action column will have action buttons for Edit and Inactivate/Reactivate. On Inactivate, the system should prompt for bulk transfer of pending assigned activities to another user.

At the top of the screen, there will be a button to add a new user. Email ID has to be unique across the system.

# **Manage Teams**

The screen will have a grid with the following columns: Team name, Team manager, Action. Action column will have action buttons for Edit, Inactivate/Reactivate, View Members. Edit will enable to change the Team name, Team manager and the Team members. If Team member is removed from a Team, all activities assigned to the member as part of the team will have to be bulk transferred to another member of the team.

At the top of the screen, there will be a button to add a new Team. Team Manager and, at least, one Team Member is mandatory.

# **Plan**

This screen will have two tabs viz., Upload Annual Plan and Upload Quarterly Plan.

***Tab: Upload Annual Plan***

This tab will capture the Team (dropdown of teams whose manager is the logged in user), Plan Year (dropdown of financial years in the form of FY 25-26), a button to browse for a file to upload and a button to Upload. There will also be buttons to Download Template, Create Issue, Add Action and View History of uploads.

The Download Template will always be enabled. On click of this button, the blank template for the Annual Plan will be downloaded.

Once the Team, Plan Year & File Selection is done, the Upload button will be enabled.

The Plan Year dropdown will be populated with current financial year and the next financial year. Financial year starts from 1st April.

On click of Upload, the system has to display either an error message or a message of successful upload. The validations will include the following:

·   	The sub-head names in FPI sheet must be unique

·   	The Goal & Progress Indicator names in GPI & Project Name in PPI sheets must be unique

·   	The main head column in FPI sheet can specify one of the following values: Revenue, Variable Cost, Operating Expenses or Other Expenses if sub-head is not blank.

·   	Annual Goal and the Q1 to Q4 goals in FPI and GPI sheets must contain only numeric values

If any errors are found in the file, the data from the file will not be uploaded although the file itself will be stored in the system for reference.

Only FPI, GPI and PPI sheets from Annual Plan need to be read and uploaded. The uploaded Excel file should be stored in its entirety as an Excel file for reference. In FPI sheet, only those lines where the parameter type column is not blank will be read into the system. The parameter type column will specify one of the following values: Revenue, Variable Cost, Operating Expenses or Other Expenses.

Annual Plan can be re-uploaded any number of times as the data is used only for comparison for reporting purposes. And the last uploaded file for the year will be considered as the Annual Plan for the year.

On click of View History button, a popup will be opened which will have a grid with the following columns: Team, Plan Year, File Name, Uploaded Date, Status, Action. The Status will display either Successful or Failed depending on the upload status. Action column will display buttons for Download File, Error Log. On click of Download File, the uploaded Excel file will be downloaded. The Error Log button will be visible only if Status is Failed and on click of this button, the errors found in the uploaded file will be displayed.

***Tab: Upload Quarterly Plan***

Quarterly Plan file will have 4 sheets viz., FPI, GPI-M, GPI-W and PPI. GPI-M will detail the GPIs that will be tracked with monthly goals whereas GPI-W will contain those that have to be tracked with weekly goals.

This tab will capture the Team (dropdown of teams whose manager is the logged in user), Plan Year & Quarter (dropdown of financial years in the form of FY 25-26 – Q1), a button to browse for a file to upload and a button to Upload. There will also be buttons to Download Template, Create Issue, Add Action and View History of uploads.

The Download Template will be enabled only after Team has been selected. On click of this button, the blank template for the Quarterly Plan will be downloaded with pre-filled FPI, GPI and PPI parameters from the latest Annual Plan. Depending on the type of tracking identified in the Annual Plan (Weekly or Monthly), the GPIs in the Annual Plan will be split into GPI-M & GPI-W sheets.

The Plan Year & Quarter dropdown will be populated with current quarter and the next quarter in the form of FY 25-26 – Q1 format. If the current quarter is Q1 to Q3, it will show FY 25-26 – Q1 and FY 25-26 – Q2. If the current quarter is Q4, it will show FY 25-26 Q4 and FY 26-27 – Q1.

Once the Team, Plan Year & Quarter & File Selection is done, the Upload button will be enabled.

On click of Upload, the system has to display either an error message or a message of successful upload. The validations will include the following:

·   	The sub-head names in FPI sheet must be unique

·   	The Goal & Progress Indicator names in GPI & Project Name in PPI sheets must be unique

·   	The main head column in FPI sheet can specify one of the following values: Revenue, Variable Cost, Operating Expenses or Other Expenses if sub-head is not blank.

·   	Responsibility column must contain a valid member of the current team in the form of email ID

·   	In FPI, for each of the lines where the Responsibility has been identified, the main head and sub-head must also be identified and it has to be one of Revenue, Variable Cost, Operating Expenses or Other Expenses.

·   	The Quarter Goal & month wise columns in FPI & GPI-M sheets must contain only numeric values.

·   	The Quarter Goal & week wise columns in GPI-W sheet must contain only numeric values.

·   	In PPI, each week starting from the start date must have some task contiguously; however, the last task could end a few weeks before the end date.

If any errors are found in the file, the data from the file will not be uploaded although the file itself will be stored in the system for reference.

The uploaded Excel file should be stored in its entirety as an Excel file for reference.

Quarterly Plan can be re-uploaded only till any action has been initiated thru the Implement, review or improve option by any of the users for the team for the quarter. If any such action has already been done, then, system will prompt saying “We found some actions have been initiated against the old plan for the quarter. All such actions related to the plan for this quarter will be deleted. Are you sure you wish to upload the new plan (Yes / No)?”. If the user confirms, then, the new quarterly plan can be uploaded after all actions (done thru Implement, Review or Improve) related to the old plan is deleted.

On click of View History button, a popup will be opened which will have a grid with the following columns: Team, Plan Year & Quarter, File Name, Uploaded Date, Status, Action. The Status will display either Successful or Failed depending on the upload status. Action column will display buttons for Download File, Error Log. On click of Download File, the uploaded Excel file will be downloaded. The Error Log button will be visible only if Status is Failed and on click of this button, the errors found in the uploaded file will be displayed.

# **Implement**

# **This screen will have 3 tabs viz., My Numbers, My Projects and My To Do**

# ***Tab: My Numbers***

# **My Numbers will show all the FPI & GPI line items that were uploaded with the Responsibility of the logged in user. It could also be the line items which have reassigned to the logged in user by another user.**

Inside the My Numbers tab, there will be a radio button with two options: Weekly Numbers and Monthly Numbers.

On click of the Weekly Numbers button, a grid with the following columns will be displayed: Team, GPI (including unit of measure), Last Week Budget, Last Week Plan, Last Week Actual, Next Week Budget, Next Week Plan, Comments, Assigned To, and Actions.

On top of the grid, display the current week in the form of Week 19 – 20-Jul-25 to 26-Jul-25.

Last Week Actual and Next Week Plan will be editable only if “Assigned To” is the logged-in user or else it will be display only. If editable, the default value will be 0.00.

The Comments field will always be editable.

Assigned To will display the last assigned Team Member.

 

 

On click of the Monthly Numbers button, a grid with the following columns will be displayed: Month, Team, GPI, Last Month Budget, Last Month Plan, Last Month Actual, Next Month Budget, Next Month Plan, Comments, Assigned To, and Actions.

On top of the grid, the previous month (calculated with respect of review meeting date) will be displayed and the data will be related to that month.

Last Month Actual and Next Month Plan will be editable only if “Assigned To” is the logged-in user or else it will be display only. If editable, the default value will be 0.00.

The Comments field will always be editable.

Assigned To will display the last assigned Team Member.

 

For both Weekly and Monthly grids, the following buttons will be available:

Create an Issue: Opens the New Issue popup.

Add Action: Opens the New Action popup.

 

For both Weekly and Monthly grids, the following action buttons will be available for each row:

Reassign: Enabled only if Assigned To is the logged-in user. On click, opens the Reassign popup.

View Comments: Opens the View Comments popup.

 

The FPIs and GPIs that have been assigned to the logged in user in each Team’s Quarterly Plan-FPI & GPI sheets will be displayed here.

The FPIs & GPIs will be visible even if the parameter has been reassigned to another member

Last week data will be picked from the latest Quarterly Plan of the Team pertaining to the last week and similarly, Next week data will be picked up from the latest Quarterly Plan of the Team pertaining to the next week

Budget columns data will come from the latest uploaded Quarterly Plan of the Team. Whereas the last week plan column will be the data entered in the next week plan in the previous week.

The Last Week Actual column, the Next Week Plan column and the Comments column should be enabled by default, and it will be editable before the review related to this plan is done. Once the review is done, the screen will be display-only.

This screen does an auto save

 

***Tab: My Projects***

My Projects will show projects assigned to the logged-in user (either from the Quarterly Plan or reassigned). It will also be visible to users who have been assigned any tasks under a project.

 

On top of the grid, display the current quarter based on today’s date. (e.g., if today is 24-Aug-25, display Q3 of FY 25–26).

The grid will display the following columns: Expansion button \+, Team, PPI (Project) Name, Completion Criteria, Original Due Date, % Completion, Status, Revised Due Date, Assigned To, and Actions.

The expansion \+ button will open a Project Details slider.

Status will be calculated as \# of tasks completed / \# of total tasks.

Assigned To will display Self or Team Member.

 

For my project grid, the following buttons will be available:

Create an Issue: Opens the New Issue popup.

Add Action: Opens the New Action popup.

 

For each project name, the following action buttons will be available for each row:

Edit: Opens Edit Project popup.

Reassign: Visible only to the original Project Owner (Responsibility). On click, opens Reassign popup.

Mark Complete: Visible only to the Project Owner and if all tasks are marked Complete. On click, status changes to Completed, and the Complete icon changes to Undo. If Undo is clicked, status reverts to the previously updated status, and the icon switches back.

View History: Opens the Project History popup.

 

This screen is meant to view the status of each of the project that is assigned to the logged in user either in the latest Quarterly Plan for the Team or thru Reassign. This screen will also be visible to all the users to whom any Task has been assigned under a project.

 

**Project Details Slider**

When expanded, the project row will show a grid with columns: Task, Original Due Date, Status, Revised Due Date, Assigned To, and Actions.

Following action buttons will be available for each row:

Reassign: Visible only to the Project Owner. Opens Reassign popup.

View History: Opens the Task History popup.

 

***Tab: My To Do***

Status should show the current updated status OR blank Status if not updated.

My To Do will display all actions assigned to the logged-in user.

The grid will have the following columns: Team, Source, Action, Priority, Assigned To, Original Due Date, Status (Icon which define In Progress, Completed \+ Text), Revised Due Date, and Actions.

 

For my My To Do grid, the following buttons will be available:

Create an Issue: Opens the New Issue popup.

Add Action: Opens the New Action popup.

 

For each Action Name, the following action buttons will be available for each row:

Edit: Enabled only if there are no sub-actions and Assigned To \= Self. Opens Edit Action popup.

Reassign: Enabled only if there are no sub-actions. Opens Reassign popup.

Sub-Action: Enabled if sub-actions exist or if Assigned To is Self. Opens Sub-Action popup.

Mark Complete: Enabled if Assigned To is Self and status is Not Complete, OR Assigned To Not Self and status is Done, OR All sub-actions are marked Complete (status is Done). On click, status changes to Completed and icon changes to Undo. Undo reverts status to the last updated status and resets the icon.

Mark Reject: Enabled if status is Done or Rejected and there are no sub-actions. On click, opens Rejection Reason popup. If a reason already exists, it is editable. Status changes to Rejected, and the action is reopened.

View History: Opens Action History popup.

 

If an action or sub-action is assigned to anyone other than Self, the status will be shown as Done when the assignee marks the action as Complete. When the owner of the Action marks Complete, the Status will be shown as Complete.

If all sub-actions are marked as Complete, the parent action status will change to Done.

The rejection reason should be displayed to the assignee in View Comments

 

**Edit Project  Popup**

Edit Project Popup displays project details: Team, Source, Project Name, Completion Criteria, Responsibility, Due Dates, Status dropdown, Revised Due Date, Challenge, Comments.

Status dropdown has values: On Track, At Risk, Danger. If Danger is selected, Revised Due Date & Challenge become editable. If At Risk is selected, Challenge becomes editable.

Following Buttons will be available in Edit Project Popup:

Save: closes popup and refreshes main screen.

Cancel: asks for confirmation before closing with “You will lose the data entered. Do you wish to continue – Yes / No” closes popup if Yes clicked.

View History: Opens Project History popup.

 

**Edit Action  Popup**

Edit Action Popup displays following field details: Team, Source, Action, Priority, Original due dates, Last updated status, Last Revised Due Date, Status dropdown, Revised due date Challenge, Comments.

Status dropdown has values: On Track, At Risk, Danger. If Danger is selected, Revised Due Date & Challenge become editable. If At Risk is selected, Challenge becomes editable.

Following Buttons will be available in Edit Action Popup:

Save: closes popup and refreshes main screen.

Cancel: asks for confirmation before closing with “You will lose the data entered. Do you wish to continue – Yes / No” closes popup if Yes clicked.

View History: Opens Project History popup.

 

**Reassign Popup**

Reassign Popup will display following fields Reassign Team and Reassign Member: Both dropdowns default to “Select.”

Following buttons will be available:

Save: On click if Member is blank, show error: *“Please select Member”*. On success, close popup and refresh main screen.

Cancel: asks for confirmation before closing with “You will lose the data entered. Do you wish to continue – Yes / No” closes popup if Yes clicked.

 

**Sub-Action Popup**

Sub-Action Popup displays following fields Team, Source, Action, Priority, Original due date, Status, Revised due date.

Sub-Action grid columns will display following columns Action, Priority, Assigned To, Original Due Date, Status, Revised Due Date, Actions.

Following buttons will be available:

Add: Opens New Action Slider.

Back: Closes this popup and refreshes the main screen.

 

Following Action buttons will be available for each row:  
  Edit: Enabled only if there are no sub-actions and Assigned To is Self. Opens Edit Action popup.

Reassign: Enabled only if there are no sub-actions. Opens Reassign popup.

Sub-Action: Enabled if sub-actions exist or if Assigned To is Self. Opens Sub-Action popup.

Mark Complete: Enabled if Assigned To is Self and status is Not Complete, OR if Assigned To is Not Self and status is Done, OR if all sub-actions are Complete. On click, changes status to Completed and icon to Undo. Undo reverts status to previous and resets icon.

Mark Reject: Enabled if status is Done or Rejected and there are no sub-actions. On click, opens Rejection Reason popup. If a reason exists, it is editable. Status changes to Rejected.

View History: Opens Action History popup.

 

**View Project History Popup**

View Project History Popup will display full change history of a project. Following fields will be displayed Project Name, Completion %, Original Due Date, Responsibility.

Following Grid details will be displayed with columns Date of Change, Status, Revised Due Date, Challenges, and Comments. This will display only in descending order of Date of Change.

Following button will be available:

Close: Closes the popup.

 

**View History Popup**

View History Popup will display history of actions, including rejections. Following fields will be displayed Team, Source, Action, Priority, and Original Due Date.

Following Grid details will be displayed with columns Date of Change, Status, Revised Due Date, Challenges, and Comments. This will display only in descending order of Date of Change.

The list should include Rejections done by Action Owner

Following button will be available:

Close: Closes the popup.

 

**New Issue Popup**

*Common across: Financial Performance Indicator (FPI) Monthly / General Performance Indicators (GPI) Weekly & Monthly / My Tasks (My To Do) Things I have to do / All things assigned to me.*

New Issue popup allows the user to create a new issue. The following fields are displayed

Issue Title: This is mandatory for system to proceed.

Description: This is optional field.

Priority: This is a dropdown with values High, Medium, Low; default will be “Select”.

Required to be resolved by: This is a Date picker with format dd-mm-yyyy.

Team for which the issue has to be added: This will be a single dropdown with values \= Teams where the user is a Member and Teams where the user is in charge; default will be “Select”.

 

Following button will be available:

Save: If Team is blank, show error: “Please select a Team”. On success, close popup and refresh main screen.

Cancel: Shows confirmation message: “You will lose the data entered. Do you wish to continue – Yes / No”. Closes popup if Yes is clicked.

 

**New Action Popup**

*Common across: Financial Performance Indicator (FPI) Monthly / General Performance Indicators (GPI) Weekly & Monthly / My Tasks (My To Do) Things I have to do / All things assigned to me.*

New Action popup allows the user to create a new action. The following fields are displayed

Action: This is mandatory for system to proceed.

Priority: This is a dropdown with values High, Medium, Low; default will be “Select”.

Assigned To Team: This will be a mandatory single dropdown with values \= List of teams where the user is in charge and List of Team where the user is a member; default will be “Select”.

Assigned to member: This will be a mandatory single dropdown with values \= List of team members in the Team and Self for teams where the user is in charge and only Self where the user is a member; default will be “Select”.

Due Date: This is a Date picker with format dd-mm-yyyy.

Comments: Optional text field for user to add comments.

 

Following button will be available:

Save: Closes popup and refreshes the main screen.

Cancel: Shows confirmation message: “You will lose the data entered. Do you wish to continue – Yes / No”. Closes popup if Yes is clicked.

 

 

 

# **Review**

**Review Home Page**

On the top of the page, there will be a filter for Team, Review Type and the Month/Year. After these three fields, there will be a Search button. Below the filter fields, there will be a grid with the following columns: the team, the review type (daily, weekly, or monthly), the review date and time, and the available actions (Action Buttons). And below the grid, there will be a button for New Review.

Once the filter values for Team, Review Type and Month/Year are selected and Search button is clicked, the grid will be populated. Team will be a dropdown containing the names of the teams where the logged in user is in charge. Review Type will be Daily, Weekly or Monthly. Month/Year will contain a list of months & years for which data is available.

Action buttons in the grid will be: Edit/view Review Meeting and View Participants. On click of Edit/View Review Meeting button, the Review Meeting screen will be opened with pre-filled data. If there is any review subsequent to this review for the selected team, the review meeting will be opened for viewing only; else, it will be opened for edit.

**New Review Screen**

On the New Review Screen, the user can specify the team, the review type, the review date and time, the manager’s name, and select the team members (participants) to be included in the review. At the bottom of this screen, two buttons are available. The Back button returns the user to the Review Home Page, and the Create Review button confirms the details and opens the Edit/View Review Meeting screen with the meeting details filled in.

**Edit/View Review Meeting Screen**

The screen will display the review meeting details of Team, Meeting Date, Type of Review (Daily, Weekly or Monthly), Manager Name, Participants.

This screen comprises of 5 buttons (Review Notes, Decisions, Create Issue, Add Action, Back) on the side and 7 tabs (Commitments, FPI, GPI, PPI, Issues, Action Summary) on the top.

In case, Review Type is Daily, FPI, GPI and PPI tabs will not be shown. In case Review Type is Weekly or Monthly, all tabs will be shown.

This screen does an auto save.

On click of Review Notes, Review Notes popup should be opened.

On click of Decisions, Decisions popup will be opened.

On click of Create Issue, New Issue popup will be opened.

On click of Add Action, New Action popup will be opened.

On click of Back button, open the Review Grid.

***Tab: Commitments***

The Commitments tab displays a grid with the following columns: Team, Source, Action, Priority, Assigned To, Original Due Date, Status, Revised Due Date, and Actions.

The grid displays all pending actions (not yet marked as complete) from any review meetings conducted by the team in the past.

For each row in the grid, the following action buttons are available:

Edit button: This button will be enabled only if there are no sub-actions for this action and Assigned To is Self. On click, this opens the *Edit Action* popup.

Reassign button: This button will be enabled only if there are no sub-actions for this action. On click, this opens the *Reassign* popup.

Sub-Action button: This button will be enabled only if there are sub-actions for this action OR if Assigned To is Self. On click, this opens the *Sub-Action* popup.

Mark Complete button: This button will be enabled if the Assigned To is Self and status is not Complete OR if Assigned To is not Self and status is Done OR If there are sub-actions and all of them are Complete (status will be showing as Done). Changes the status to *Completed* and replaces itself with an *Undo button*.

Mark Reject button: This button will be enabled if the status is Done or Rejected and there are no sub-actions. On click, this opens a *Rejection Reason* popup and changes the status to *Rejected*. If there are any reasons already present, then display it for edit if the status is Rejected

View History button: Opens the *View History* popup.

***Tab: FPI (Financial Performance Indicator)***

On top of the grid, the previous month (calculated with respect of review meeting date) will be displayed and the data will be related to that month.

The FPI tab displays financial performance indicators in a grid with the following columns: Parameter, Last Month Budget, Last Month Plan, Last Month Actual, Next Month Budget, Next Month Plan, Comments, and Actions. On top of the grid, there will be a button called Detailed View.

FPI should be shown in the P\&L format (Revenue, Variable Cost, Gross Margin, Operating Expenses, EBIDTA, Other Expenses, Profit) with expandable elements for Revenue, Variable Cost, Operating Expenses & Other Expenses. When the expansion is clicked, the breakup elements should be shown as a slider or a popup.

Detailed View button: Opens the detailed view of FPI indicators which is a grid with the following columns: Parameter, This Month Budget, This month Plan, This Month Actual, QTD Budget, QTD Actual, YTD Budget, YTD Actual, Next Month Budget, Next Month Plan, Quarter Budget, Year Budget, Comments and Actions. In the Actions column, there will be action buttons for Create Issue (to open Create Issue popup) and Add Action (to open Action Items popup). The Detailed View will be displayed in P\&L format.

For each row in the grid, the following action buttons are available:

Details button: Opens the Details popup, which displays: Parameter, This Month Budget, This month Plan, This Month Actual, QTD Budget, QTD Actual, YTD Budget, YTD Actual, Next Month Budget, Next Month Plan, Quarter Budget, Year Budget, and Comments

Create Issue button: Opens the Create Issue popup.

Add Action button: Opens the Action Items popup.

***Tab: GPI***

There will be two radio buttons on the top saying: Weekly GPI and Monthly GPI. On click of the radio button, the appropriate data will be shown in the grid below.

On click of Weekly GPI radio button

The Weekly GPI grid includes the following columns: Team, GPI, Last Week Budget, Last Week Plan, Last Week Actual, Next Week Budget, Next Week Plan, Comments, and Actions. Color the rows differently depending on whether the Indicator Type is Goal or Progress. Above the grid, there will be a button called “Detailed View”.

Detailed View button: Opens the detailed view of GPI indicators, which includes: Action buttons, GPI, Parameter, Quarter Goal, W1, W2, W3, W4, W5, W6, W7, W8, W9, W10, W11, W12, and W13 (W stands for week)

For each row, the Details button, Create Issue and Add Action button are available.

Details button opens up Details popup which displays GPI, Parameters, Quarter Goal, W1, W2, W3, W4, W5, W6, W7, W8, W9, W10, W11, W12, and W13 (W stands for week)

Create Issue button opens the New Issue popup.

Add Action button opens Action Items popup.

Note: Each parameter will show Budget, Plan, and Actual numbers against each week – 3 rows for each week.

On click of Monthly GPI radio button

The Monthly GPI grid includes the following columns: Team, GPI, Last Month Budget, Last Month Plan, Last Month Actual, Next Month Budget, Next Month Plan, Comments, and Actions. Color the rows differently depending on whether the Indicator Type is Goal or Progress. Above the grid, there will be a button called “Detailed View”.

For each row, the Details button and the Add Action button are available.

The Detailed View button opens the detailed view of GPI indicators, which includes Action buttons, GPI, Parameter, Quarter Goal, M1, M2, and M3 (M stands for Month).

For each row, the Details button, Create Issue and Add Action button are available.

The Details button opens a popup displaying Action buttons, GPI, Parameter, Quarter Goal, M1, M2, and M3 (M stands for Month).

The Create Issue button opens the New Issue popup.

The Add Action button opens the Action Items popup.

Note: Each parameter will show Budget, Plan, and Actual numbers against each month – 3 rows for each month.

***Tab: PPI (Project Performance Indicators)***

The PPI tab displays project details in a grid. Columns include Project Name, Completion Criteria, Responsibility, Start Date, Due Date, Completion Percentage, Status, and Actions. Above the grid, there will be a button called “Detailed View”.

The Detailed View button opens the detailed view of PPI indicators, which includes Action, Project Name, Completion Criteria, Responsibility, Start Date, Due Date, W1, W2, W3, W4, W5, W6, W7, W8, W9, W10, W11, W12, and W13 (W stands for week). Clicking on any cell should function as button which should then open Action Item popup (with tasks shown as actions in the popup). The weekly cells should turn green if all tasks have been completed. The cell should turn light red if any task is not complete if the week is already past. For future weeks, if the status of the tasks are marked, the font color can turn red, yellow or green for the status of danger, at risk & on track respectively. On click of a cell, one should be able to see the status of all the tasks listed in the cell.

For each row, the action buttons are:

Details button opens Details Popup with Project Name, Completion Criteria, Responsibility, Start Date, Due Date, W1, W2, W3, W4, W5, W6, W7, W8, W9, W10, W11, W12, and W13 (W stands for week). Clicking on any cell should function as button which should then open Action Item popup (with tasks shown as actions in the popup). The weekly cells should turn green if all tasks have been completed. The cell should turn light red if any task is not complete if the week is already past. For future weeks, if the status of the tasks are marked, the font color can turn red, yellow or green for the status of danger, at risk & on track respectively. On click of a cell, one should be able to see the status of all the tasks listed in the cell.

Create Issue button opens the New Issue popup.

Add action button opens Action Item Popup

Mark Complete button can change status to completed and change completed icon to undo, and if undo icon is clicked system will change status to the last updated status. Enable only if all Tasks under the Project are in Complete status

Mark On Hold button can change status to On-Hold and change Mark on Hold icon to Resume. If Resume Icon is clicked change status to last updated status or blank if not updated and resume icon is replaced with On Hold icon. Enable only if Status is not Complete

Mark Drop button can change status to Dropped and change the mark drop icon to Mark Active. If Mark Active icon is clicked, change status to last updated status or blank if not updated Mark Active icon is replaced with Mark Drop Icon. Enable only if Status is not Complete

***Tab: Issues (Issue Log Management)***

The Issues tab manages the issue log with a grid showing ID, description, status, reported by, required by, actions completed (in the format of X of Y), and actions. For each row, the action buttons include:

Add Action opens Action Item Popup

Mark Resolved button changes the status to Resolved and replaces the Resolved icon with an Undo/Unresolved icon. If the Undo/Unresolved icon is clicked, the status reverts to the last updated status (or remains blank if not updated), and the Undo/Unresolved icon is replaced with the Mark Resolved icon.

Mark On Hold button changes the status to On Hold and replaces the On Hold icon with a Resume icon. If the Resume icon is clicked, the status reverts to the last updated status (or remains blank if not updated), and the Resume icon is replaced with the On Hold icon.

Mark Drop button changes the status to Dropped and replaces the Dropped icon with a Mark Active icon. If the Mark Active icon is clicked, the status reverts to the last updated status (or remains blank if not updated), and the Mark Active icon is replaced with the Dropped icon.

Escalate button changes the status to Escalated and asks for the Team to which the issue is to be escalated. The list of teams will be those where the logged in user is a member of.

***Tab: Action Summary***

All actions added during this review meeting will be shown in this tab.

The Action Summary tab shows all actions in a grid with columns for action, source, assignee, due date, status, and comments.

For each row:

Edit button opens Edit Action Screen

Delete button removes the action and refresh the screen.

 

**Review Notes Popup**

Review Notes Popup displays a grid with Serial Number, Review Notes, and Actions. Serial Number is auto generated. Review Notes are display only.

 Following Buttons will be available:

Add: On click, the Review Notes slider opens. Inside the slider, the Review Notes field will be a text field.

Save: On click saves the note and refreshes the review screen.

Cancel: On click asks for confirmation before closing with “You will lose the data entered. Do you wish to continue – Yes / No” and closes the slider if yes is clicked.

 Row-level action buttons are available in the grid:

Edit: opens the Review Notes slider.

Delete: deletes the row and refreshes the Serial Numbers.

 

**Decisions Popup**

Decisions Popup displays a grid with Serial Number, Decisions, and Actions. Serial Number is auto generated. Decisions are display only.

Following Buttons will be available:  
 Add: On click, the Decision slider opens. Inside the slider, the Decisions field will be a text field.

Save: On click saves the decision and refreshes the review screen.

Cancel: On click asks for confirmation before closing with “You will lose the data entered. Do you wish to continue – Yes / No” and closes the slider if Yes is clicked.

 Row-level action buttons are available in the grid:

Edit: opens the Decision slider.

Delete: deletes the row and refreshes the Serial Numbers.

 

**Action Item Popup**

Action Items Popup displays a grid with Action, Priority, Due Date, Assigned To, Comments, and Actions. All fields in the grid are display only.

The Grid Details should be populated based on the source where it’s getting clicked.

Following Buttons will be available:

Add: On click, the Action Items slider opens. Inside the slider, the following fields will be displayed:

Action: text field, mandatory.

Priority: dropdown with values High, Medium, Low. Default value is “Select.”

Assigned To Team: dropdown with teams where the logged-in user is in charge or a member. Default value is “Select.” Mandatory.

Assigned To Member: dropdown with members of the selected team. If user is in charge, Self will also be available. If user is only a member, then only Self will appear. Mandatory. If left blank, error message “Please select assignee” will appear.

Due Date: date picker with format dd-mm-yyyy.

Comments: text field.

 

Following Buttons will be available in Action Items Popup:

Save: closes popup and refreshes main screen.

Cancel: asks for confirmation before closing with “You will lose the data entered. Do you wish to continue – Yes / No” and closes popup if Yes clicked.

Row-level action buttons are available in the grid:

Edit: opens the Action Item slider.

Delete: deletes the row and refreshes the grid.

 

 

# **Improve**

 

***Tab: Upload Improvement Projects***

This tab will capture the Team (dropdown of teams whose manager is the logged-in user), Planning Year (dropdown of financial years in the form of FY 25-26; financial year begins on 1st April every year, for example FY 25-26 begins on 1st April 2025), Quarter (dropdown of four quarters Q1, Q2, Q3, Q4, with Q1 beginning on 1st April. The default will be the upcoming quarter, e.g. if today falls in Q1 then Q2 will be preselected), and a control to upload the Improvement Projects Plan file (drag-and-drop with browse option).

The Download Template button will always be enabled. On click of this button, the predefined template for the Improvement Projects Plan will be downloaded.

Once the Team, Planning Year, Quarter and File Selection are done, the Upload & Validate button will be enabled. On click of Upload & Validate, the system will perform validation and then display either an error message or a message of successful upload. The validations will include the following:

·   	The uploaded file must be in .xlsx format.

·   	Team, Planning Year and Quarter must be selected before upload.

If any errors are found in the file, the data from the file will not be uploaded although the file itself will be stored in the system for reference. The upload status in this case will be marked as Failed, and the error log will be available for download. On successful upload, the status will be Successful and the data from the file will be uploaded into the system.

 

 

***Tab: Project Plan History***

This tab will capture the Team filter (dropdown of teams with an option for All; default selection will be All).

On click of View History, a popup will be opened which will have a grid with the following columns: Team, Plan Year, Quarter, File Name, Uploaded Date, Status, Action. The Status will display either Successful or Failed depending on the upload status. The Action column will display buttons for Download and Error Log. On click of Download, the uploaded plan file will be downloaded to the user’s system. On click of Error Log, the corresponding error log file will be downloaded; this button will be visible only if the upload has Failed.

All columns except Actions should be sortable and filter-ready.

 

 

 

 

 

 

 

**Other Features Required**

Rewards for commitments

 

 

