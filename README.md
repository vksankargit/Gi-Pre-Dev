# PRE System - Periodic Review Environment

A Django-based review tool for conducting periodic review meetings and tracking team performance indicators.

## Features

### User Roles
- **Admin**: Manage organizations and coordinators
- **Coordinator**: Manage users, teams, and impersonate general users
- **General**: Upload plans, track implementation, conduct reviews, and manage improvements

### Core Modules

#### 1. Plan Module
- Upload Annual Plans and Quarterly Plans
- Excel file validation and processing
- Plan history tracking
- Template downloads

#### 2. Implement Module
- **My Numbers**: Track FPI (Financial) and GPI (Goal) performance indicators
- **My Projects**: Monitor PPI (Project) progress and tasks
- **My To Do**: Manage actions and sub-actions

#### 3. Review Module
- Create and manage review meetings (Daily, Weekly, Monthly)
- Track commitments, FPI, GPI, PPI
- Issue management and action items
- Review notes and decisions

#### 4. Improve Module
- Upload improvement project plans
- Track improvement initiatives

### Key Features
- Role-based access control
- Comprehensive audit trail
- Mobile-friendly responsive design
- Excel file import/export functionality
- Advanced grid sorting and filtering
- Auto-save functionality
- Multi-level action management
- Impersonation for coordinators

## Technology Stack

- **Backend**: Django 4.2+
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **File Processing**: openpyxl for Excel handling
- **Forms**: django-crispy-forms with Bootstrap 5

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning)

### Step 1: Clone or Download the Project
```bash
# Option 1: Clone with Git
git clone <repository-url>
cd GI-Pre-Dev

# Option 2: Download and extract the ZIP file
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
```bash
# Copy the example environment file
copy .env.example .env

# Edit .env file with your settings
# For development, the default SQLite settings work fine
```

### Step 5: Database Setup
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (admin account)
python manage.py createsuperuser
```

### Step 6: Load Initial Data (Optional)
```bash
# Load financial years and other initial data
python manage.py loaddata initial_data.json
```

### Step 7: Run the Development Server
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` in your browser.

## Usage

### Initial Setup

1. **Login as Admin**: Use the superuser account created during setup
2. **Create Organizations**: Go to "Manage Organizations" and create your organization(s)
3. **Add Coordinators**: Add coordinator users to organizations
4. **Create Users**: Coordinators can create general users
5. **Setup Teams**: Create teams with managers and members

### Daily Workflow

#### For Team Managers:
1. **Upload Plans**: Use the Plan module to upload Annual and Quarterly plans
2. **Monitor Implementation**: Check team progress in the Implement module
3. **Conduct Reviews**: Schedule and run review meetings
4. **Track Improvements**: Upload and monitor improvement projects

#### For Team Members:
1. **Update Numbers**: Enter actual values for assigned FPI/GPI parameters
2. **Update Projects**: Track project progress and task completion
3. **Manage Actions**: Complete assigned actions and create sub-actions
4. **Participate in Reviews**: Attend review meetings and follow up on commitments

### Excel File Formats

#### Annual Plan Format
The system expects Excel files with three sheets:
- **FPI Sheet**: Financial Performance Indicators
- **GPI Sheet**: Goal Performance Indicators  
- **PPI Sheet**: Project Performance Indicators

#### Quarterly Plan Format
Four sheets are required:
- **FPI Sheet**: Monthly breakdown of financial indicators
- **GPI-M Sheet**: Monthly goal indicators
- **GPI-W Sheet**: Weekly goal indicators
- **PPI Sheet**: Weekly project tasks

### Key Features Usage

#### Grid Functionality
- **Sorting**: Click column headers to sort (ascending/descending/none)
- **Filtering**: Click filter icons to filter column values
- **Search**: Use search boxes to find specific records

#### Auto-save
Forms with `data-auto-save` attribute automatically save changes after 2 seconds of inactivity.

#### Impersonation
Coordinators can "Login As" general users to help with data entry or troubleshooting.

## Configuration

### Database Configuration
For production, update the `.env` file:
```
DATABASE_URL=postgresql://username:password@localhost:5432/pre_system
```

### Email Configuration
Configure email settings for forgot password functionality:
```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-smtp-server.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
```

### File Upload Settings
Adjust file upload limits in `settings.py`:
```python
FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400  # 25MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 26214400  # 25MB
```

## Development

### Project Structure
```
GI-Pre-Dev/
├── pre_system/          # Django project settings
├── accounts/            # User authentication and management
├── organizations/       # Organizations, teams, and coordinators
├── plans/              # Annual and quarterly plan management
├── implement/          # Implementation tracking (numbers, projects, actions)
├── review/             # Review meetings and tracking
├── improve/            # Improvement project management
├── templates/          # HTML templates
├── static/             # CSS, JavaScript, images
├── media/              # User uploaded files
└── requirements.txt    # Python dependencies
```

### Adding New Features

1. **Models**: Add new models to the appropriate app's `models.py`
2. **Views**: Create views in `views.py`
3. **URLs**: Update `urls.py` with new URL patterns
4. **Templates**: Create HTML templates in the app's template directory
5. **Migrations**: Run `python manage.py makemigrations` and `python manage.py migrate`

### Running Tests
```bash
python manage.py test
```

### Collecting Static Files (Production)
```bash
python manage.py collectstatic
```

## Security Considerations

- Change the `SECRET_KEY` in production
- Use HTTPS in production
- Configure proper database permissions
- Regularly backup data
- Keep dependencies updated
- Review audit trails regularly

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure all dependencies are installed with `pip install -r requirements.txt`
2. **Database Error**: Run migrations with `python manage.py migrate`
3. **Static Files Not Loading**: Run `python manage.py collectstatic`
4. **Permission Denied**: Check file permissions and user roles

### Getting Help

1. Check the Django error logs
2. Verify database connectivity
3. Ensure all environment variables are set correctly
4. Check the audit trail for user actions

## License

This project is proprietary software. All rights reserved.

## Version History

- **v1.0**: Initial release with core functionality
  - User management and authentication
  - Plan upload and management
  - Implementation tracking
  - Review meeting management
  - Improvement project tracking
  - Responsive design
  - Audit trail functionality