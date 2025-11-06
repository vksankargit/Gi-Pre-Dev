# GI Pre-Dev System - Complete Installation Guide

## Fresh Installation from Scratch

**Package**: GI Pre-Dev System - Complete Deployment Package
**Date**: October 30, 2025
**Version**: 1.0
**Status**: Production Ready

---

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Pre-Installation Checklist](#pre-installation-checklist)
3. [Installation Steps](#installation-steps)
4. [Database Setup](#database-setup)
5. [Initial Configuration](#initial-configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), or macOS 10.15+
- **Python**: 3.8 or higher (3.11+ recommended)
- **RAM**: 4 GB minimum (8 GB recommended)
- **Disk Space**: 2 GB minimum
- **Browser**: Chrome, Firefox, Edge, or Safari (latest versions)

### Software Dependencies
- Python 3.8+
- pip (Python package installer)
- Git (optional, for version control)
- Virtual environment tool (venv or virtualenv)

---

## Pre-Installation Checklist

Before starting the installation, ensure you have:

- [ ] Python 3.8+ installed and accessible via command line
- [ ] pip package manager installed
- [ ] Sufficient disk space (at least 2 GB free)
- [ ] Administrator/sudo access (for some installations)
- [ ] Internet connection (for downloading dependencies)
- [ ] Text editor or IDE (VS Code, PyCharm, etc.)

### Verify Python Installation

```bash
# Check Python version
python --version
# or
py --version

# Check pip version
pip --version
# or
py -m pip --version
```

Expected output: Python 3.8.0 or higher

---

## Installation Steps

### Step 1: Extract Deployment Package

Extract the `GI_PreDev_Complete_Deployment` package to your desired location:

```
Recommended locations:
- Windows: C:\GI-Pre-Dev
- Linux/Mac: ~/GI-Pre-Dev or /opt/GI-Pre-Dev
```

Your directory structure should look like this:

```
GI_PreDev_Complete_Deployment/
├── accounts/
├── api/
├── implement/
├── improve/
├── improvements/
├── plans/
├── pre_system/
├── reviews/
├── static/
├── templates/
├── media/
├── manage.py
├── db.sqlite3
├── requirements.txt
└── INSTALLATION_GUIDE.md (this file)
```

### Step 2: Create Virtual Environment

```bash
# Navigate to the deployment directory
cd GI_PreDev_Complete_Deployment

# Create virtual environment
python -m venv venv
# or
py -m venv venv

# Activate virtual environment

## On Windows:
venv\Scripts\activate

## On Linux/Mac:
source venv/bin/activate
```

You should see `(venv)` at the beginning of your command prompt.

### Step 3: Install Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install required packages
pip install -r requirements.txt
```

This will install:
- Django 5.2.6 (Web framework)
- openpyxl 3.1.5 (Excel file processing)
- pandas 2.3.2 (Data manipulation)
- pillow 11.3.0 (Image processing)
- django-crispy-forms (Form rendering)
- And other dependencies...

**Installation time**: ~5-10 minutes depending on your internet speed.

### Step 4: Verify Installation

```bash
# Check Django installation
python manage.py --version

# Expected output: 5.2.6 or similar
```

---

## Database Setup

The package includes a pre-configured SQLite database (`db.sqlite3`).

### Option A: Use Included Database (Recommended for Testing)

The included database has:
- Pre-configured tables and schemas
- Sample data for testing
- All migrations applied

**No additional setup required!**

### Option B: Create Fresh Database

If you prefer a clean database:

```bash
# Backup the included database (optional)
copy db.sqlite3 db.sqlite3.backup
# or on Linux/Mac:
cp db.sqlite3 db.sqlite3.backup

# Delete existing database
del db.sqlite3
# or on Linux/Mac:
rm db.sqlite3

# Create new database and run migrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser
```

Follow the prompts to create an admin account:
- Username: (your choice)
- Email: (optional)
- Password: (minimum 8 characters)

---

## Initial Configuration

### Step 1: Configure Settings (Optional)

The system is pre-configured with default settings. For production deployment, you may want to update:

**File**: `pre_system/settings.py`

```python
# Security settings
SECRET_KEY = 'your-secret-key-here'  # Change this in production!
DEBUG = False  # Set to False for production

# Allowed hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'your-domain.com']

# Database (already configured for SQLite)
# For PostgreSQL/MySQL, update the DATABASES setting
```

### Step 2: Collect Static Files (For Production)

```bash
# Collect all static files to a single directory
python manage.py collectstatic

# Answer 'yes' when prompted
```

This creates a `staticfiles` directory with all CSS, JS, and images.

---

## Starting the Server

### Development Server

```bash
# Start the development server
python manage.py runserver

# Or specify port:
python manage.py runserver 8000

# Or bind to all interfaces:
python manage.py runserver 0.0.0.0:8000
```

Expected output:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
October 30, 2025 - 23:30:00
Django version 5.2.6, using settings 'pre_system.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

**Access the application**:
- Local: http://localhost:8000
- Network: http://your-ip-address:8000

### Production Server (Using Gunicorn)

```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
gunicorn pre_system.wsgi:application --bind 0.0.0.0:8000

# With workers:
gunicorn pre_system.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## Testing

### Step 1: Access the Application

Open your browser and navigate to:
```
http://localhost:8000
```

### Step 2: Login

If using the included database, use the pre-configured credentials:
- **Username**: (check with system administrator)
- **Password**: (check with system administrator)

If you created a fresh database, use the superuser credentials you created.

### Step 3: Test Key Features

#### A. Dashboard Access
1. Navigate to "Implement" section
2. Verify dashboard loads correctly
3. Check "Weekly Numbers" tab
4. Check "Monthly Numbers" tab

#### B. Week/Month Selector
1. Click on "Weekly Numbers" tab
2. Verify week dropdown shows:
   - ISO week numbers (e.g., Week 40, Week 41)
   - Date ranges in brackets
   - Current week marked as "(Current)"
3. Select a different week from dropdown
4. Verify page reloads with selected week's data

5. Click on "Monthly Numbers" tab
6. Verify month dropdown shows:
   - Month names with date ranges
   - Current month marked as "(Current)"
7. Select a different month
8. Verify page reloads with selected month's data

#### C. Other Features
1. Test "Annual Plan" upload
2. Test "Quarterly Plan" upload
3. Test "Review" section
4. Test "Improvement" section

---

## Application Structure

### Django Apps

1. **accounts** - User authentication and management
2. **api** - REST API endpoints
3. **implement** - Implementation dashboard and tracking
4. **improve** - Improvement project management
5. **improvements** - Additional improvement features
6. **plans** - Annual and quarterly planning
7. **reviews** - Review meetings and tracking
8. **pre_system** - Main configuration and settings

### Key Files

- `manage.py` - Django management script
- `db.sqlite3` - SQLite database
- `requirements.txt` - Python dependencies
- `pre_system/settings.py` - Django settings
- `pre_system/urls.py` - URL routing

### Directories

- `static/` - CSS, JavaScript, images
- `templates/` - HTML templates
- `media/` - User-uploaded files

---

## Troubleshooting

### Issue 1: Python not found

**Error**: `'python' is not recognized as an internal or external command`

**Solution**:
- Verify Python is installed: `py --version`
- Use `py` instead of `python` on Windows
- Add Python to PATH environment variable

### Issue 2: Port already in use

**Error**: `Error: That port is already in use`

**Solution**:
```bash
# Use a different port
python manage.py runserver 8001

# Or find and kill the process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <process_id> /F

# Linux/Mac:
lsof -ti:8000 | xargs kill -9
```

### Issue 3: Module not found

**Error**: `ModuleNotFoundError: No module named 'django'`

**Solution**:
```bash
# Ensure virtual environment is activated
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

### Issue 4: Database locked

**Error**: `database is locked`

**Solution**:
- Close any other processes accessing the database
- Restart the development server
- Check file permissions on db.sqlite3

### Issue 5: Static files not loading

**Error**: CSS/JS not loading, page looks unstyled

**Solution**:
```bash
# Collect static files
python manage.py collectstatic

# Ensure DEBUG=True in settings.py for development
```

### Issue 6: Migrations not applied

**Error**: `Table doesn't exist` or `no such table`

**Solution**:
```bash
# Apply all migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

---

## Admin Interface

Django provides a built-in admin interface for managing data.

**Access**: http://localhost:8000/admin

**Features**:
- User management
- View and edit all database tables
- Add/delete records
- Import/export data

---

## Backup and Maintenance

### Database Backup

```bash
# SQLite backup
sqlite3 db.sqlite3 ".backup 'backup_YYYYMMDD.sqlite3'"

# Or simple file copy
copy db.sqlite3 backup_YYYYMMDD.sqlite3
```

### Media Files Backup

```bash
# Windows
xcopy /E /I media media_backup_YYYYMMDD

# Linux/Mac
cp -r media media_backup_YYYYMMDD
```

### Regular Maintenance

1. **Weekly**: Backup database
2. **Monthly**: Update dependencies: `pip install --upgrade -r requirements.txt`
3. **Quarterly**: Review and clean old media files
4. **Annually**: Review and archive old data

---

## Production Deployment

For production deployment, consider:

### Security
- Set `DEBUG = False` in settings.py
- Change `SECRET_KEY` to a unique value
- Configure `ALLOWED_HOSTS`
- Use HTTPS (SSL/TLS certificate)
- Enable CSRF protection
- Configure secure cookies

### Database
- Use PostgreSQL or MySQL instead of SQLite
- Set up regular automated backups
- Configure connection pooling

### Web Server
- Use Nginx or Apache as reverse proxy
- Configure gunicorn with multiple workers
- Set up process manager (systemd or supervisor)
- Configure logging and monitoring

### Static Files
- Serve static files via CDN or web server
- Use WhiteNoise for Django static files

### Monitoring
- Set up error tracking (Sentry, etc.)
- Configure logging
- Monitor server resources

---

## Feature Highlights

### 1. Week/Month Dropdown Selector
- View historical weekly/monthly data
- ISO week numbers with date ranges
- Quarter boundary support
- Data locking for completed reviews

### 2. Planning System
- Annual plan management
- Quarterly plan tracking
- Automated goal calculations
- Quarter transition handling

### 3. Implementation Tracking
- Task management
- Action items and sub-actions
- Due date tracking
- Status monitoring

### 4. Review System
- Weekly review meetings
- Monthly review meetings
- Issue tracking
- Action item follow-up

### 5. Improvement Projects
- PPI (Process Performance Indicators) tracking
- Project goal management
- Quarter-wise monitoring

---

## Support and Documentation

### Additional Resources
- Django Documentation: https://docs.djangoproject.com/
- Python Documentation: https://docs.python.org/
- Bootstrap Documentation: https://getbootstrap.com/docs/

### System Documentation
- Review `CHANGES_SUMMARY.md` for recent changes
- Check `DEPLOYMENT_INSTRUCTIONS.md` for deployment details
- Refer to inline code comments for technical details

---

## Quick Reference Commands

```bash
# Start development server
python manage.py runserver

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic

# Open Django shell
python manage.py shell

# Check for issues
python manage.py check

# Show migrations status
python manage.py showmigrations

# Create new migrations
python manage.py makemigrations

# Flush database (caution!)
python manage.py flush
```

---

## Financial Year Configuration

The system uses this financial year structure:

- **Q1**: April, May, June
- **Q2**: July, August, September
- **Q3**: October, November, December
- **Q4**: January, February, March

**Important**: Each quarter starts on the Monday on or before the 1st of the starting month.

**Example**: Q3 2025 starts on September 29, 2025 (Monday before October 1)

---

## Changelog

### Version 1.0 (October 30, 2025)
- Initial complete deployment package
- Week/month dropdown selector feature
- Quarter boundary support
- Historical data tracking
- Data locking mechanism
- Complete documentation

---

## Success Checklist

Installation is complete when:

- [ ] Virtual environment created and activated
- [ ] All dependencies installed successfully
- [ ] Database setup completed
- [ ] Development server starts without errors
- [ ] Application accessible in browser
- [ ] Login successful
- [ ] Dashboard loads correctly
- [ ] Week/month dropdowns visible and functional
- [ ] Static files loading (CSS/JS)
- [ ] No errors in browser console
- [ ] No errors in server logs

---

## Contact and Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Django documentation
3. Check server logs for detailed error messages
4. Verify all installation steps were completed

---

**Installation Package Created**: October 30, 2025
**Created By**: Claude Code
**Status**: Ready for Deployment
**Version**: 1.0

---

**Welcome to GI Pre-Dev System!**

Thank you for installing the GI Pre-Dev System. This comprehensive solution helps you manage annual plans, quarterly plans, implementation tracking, reviews, and improvement projects.

Start the server and access http://localhost:8000 to begin!
