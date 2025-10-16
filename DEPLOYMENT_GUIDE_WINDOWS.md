# Windows Server IIS Deployment Guide
## GI Performance Review System

---

## Prerequisites

### 1. Software Requirements
- **Windows Server 2016/2019/2022** or Windows 10/11 Pro
- **IIS (Internet Information Services)** 10.0 or higher
- **Python 3.11 or 3.13** (installed at `C:\Python313\` or adjust path in web.config)
- **PostgreSQL 14+** (recommended) or SQL Server
- **Visual C++ Redistributable** (for Python packages)
- **URL Rewrite Module** for IIS
- **HttpPlatformHandler** for IIS

### 2. Download and Install Components

#### Install Python
```powershell
# Download Python 3.13 from https://www.python.org/downloads/
# During installation:
# - Check "Add Python to PATH"
# - Choose "Customize installation"
# - Install to C:\Python313\
# - Check "Install for all users"
```

#### Install IIS
```powershell
# Open PowerShell as Administrator
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServer
Enable-WindowsOptionalFeature -Online -FeatureName IIS-CommonHttpFeatures
Enable-WindowsOptionalFeature -Online -FeatureName IIS-HttpErrors
Enable-WindowsOptionalFeature -Online -FeatureName IIS-ApplicationDevelopment
Enable-WindowsOptionalFeature -Online -FeatureName IIS-Security
Enable-WindowsOptionalFeature -Online -FeatureName IIS-RequestFiltering
```

#### Install IIS Components
1. **HttpPlatformHandler**
   - Download from: https://www.iis.net/downloads/microsoft/httpplatformhandler
   - Install: `HttpPlatformHandler_amd64.msi`

2. **URL Rewrite Module**
   - Download from: https://www.iis.net/downloads/microsoft/url-rewrite
   - Install: `rewrite_amd64_en-US.msi`

#### Install PostgreSQL (Recommended)
```powershell
# Download from https://www.postgresql.org/download/windows/
# During installation:
# - Set password for postgres user
# - Port: 5432
# - Create database: pre_system_db
```

---

## Deployment Steps

### Step 1: Prepare Application Directory

```powershell
# Create application directory
mkdir C:\inetpub\wwwroot\pre_system
cd C:\inetpub\wwwroot\pre_system

# Copy application files
# - Copy all files from C:\GI-Pre-Dev to C:\inetpub\wwwroot\pre_system
```

### Step 2: Set Up Python Virtual Environment

```powershell
# Navigate to application directory
cd C:\inetpub\wwwroot\pre_system

# Create virtual environment
C:\Python313\python.exe -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install production requirements
pip install --upgrade pip
pip install -r requirements-prod.txt
```

### Step 3: Configure Environment Variables

Create `.env` file in `C:\inetpub\wwwroot\pre_system\`:

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-very-long-random-secret-key-change-this-in-production
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,server-ip-address

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/pre_system_db

# For SQL Server (alternative)
# DATABASE_URL=mssql://username:password@localhost/pre_system_db?driver=ODBC+Driver+17+for+SQL+Server

# Email Configuration (Production SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# Static and Media Files
STATIC_URL=/static/
STATIC_ROOT=C:\inetpub\wwwroot\pre_system\staticfiles
MEDIA_URL=/media/
MEDIA_ROOT=C:\inetpub\wwwroot\pre_system\media

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=SAMEORIGIN

# Optional: Redis for caching
# REDIS_URL=redis://localhost:6379/0
```

### Step 4: Database Setup

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Test the application locally
python manage.py runserver
# Visit http://localhost:8000 to verify
```

### Step 5: Configure IIS Application Pool

```powershell
# Open IIS Manager (inetmgr)
# Or use PowerShell:

Import-Module WebAdministration

# Create Application Pool
New-WebAppPool -Name "PreSystemAppPool"

# Configure App Pool
Set-ItemProperty IIS:\AppPools\PreSystemAppPool -Name "managedRuntimeVersion" -Value ""
Set-ItemProperty IIS:\AppPools\PreSystemAppPool -Name "enable32BitAppOnWin64" -Value $false
Set-ItemProperty IIS:\AppPools\PreSystemAppPool -Name "managedPipelineMode" -Value "Integrated"

# Set identity to ApplicationPoolIdentity
Set-ItemProperty IIS:\AppPools\PreSystemAppPool -Name "processModel.identityType" -Value 2

# Set recycling options
Set-ItemProperty IIS:\AppPools\PreSystemAppPool -Name "recycling.periodicRestart.time" -Value "00:00:00"
Set-ItemProperty IIS:\AppPools\PreSystemAppPool -Name "recycling.periodicRestart.memory" -Value 0

# Set idle timeout (20 minutes)
Set-ItemProperty IIS:\AppPools\PreSystemAppPool -Name "processModel.idleTimeout" -Value "00:20:00"
```

### Step 6: Create IIS Website

```powershell
# Remove default website (optional)
Remove-Website -Name "Default Web Site"

# Create new website
New-Website -Name "PreSystem" `
            -Port 80 `
            -PhysicalPath "C:\inetpub\wwwroot\pre_system" `
            -ApplicationPool "PreSystemAppPool"

# Or using IIS Manager:
# 1. Right-click Sites > Add Website
# 2. Site name: PreSystem
# 3. Application pool: PreSystemAppPool
# 4. Physical path: C:\inetpub\wwwroot\pre_system
# 5. Binding: HTTP, Port 80, Host name: your-domain.com
```

### Step 7: Set Folder Permissions

```powershell
# Grant IIS_IUSRS read/write access to application folder
$path = "C:\inetpub\wwwroot\pre_system"
$acl = Get-Acl $path
$permission = "IIS_IUSRS", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
$acl.SetAccessRule($accessRule)
Set-Acl $path $acl

# Grant permissions to specific folders
$folders = @("media", "staticfiles", "logs")
foreach ($folder in $folders) {
    $folderPath = Join-Path $path $folder
    if (-not (Test-Path $folderPath)) {
        New-Item -ItemType Directory -Path $folderPath
    }
    $acl = Get-Acl $folderPath
    $acl.SetAccessRule($accessRule)
    Set-Acl $folderPath $acl
}

# Grant permissions to database file (if using SQLite)
if (Test-Path "$path\db.sqlite3") {
    $acl = Get-Acl "$path\db.sqlite3"
    $acl.SetAccessRule($accessRule)
    Set-Acl "$path\db.sqlite3" $acl
}
```

### Step 8: Configure Logging

```powershell
# Create logs directory
mkdir C:\inetpub\wwwroot\pre_system\logs

# Grant write permissions to logs folder
$logsPath = "C:\inetpub\wwwroot\pre_system\logs"
$acl = Get-Acl $logsPath
$permission = "IIS_IUSRS", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
$acl.SetAccessRule($accessRule)
Set-Acl $logsPath $acl
```

### Step 9: Update web.config

Copy the provided `web.config` to `C:\inetpub\wwwroot\pre_system\web.config`

**Important**: Update these values in web.config:
- `processPath`: Path to Python executable (e.g., `C:\Python313\python.exe`)
- `arguments`: Use full path to venv Python: `C:\inetpub\wwwroot\pre_system\venv\Scripts\python.exe`
- Environment variables: SECRET_KEY, DEBUG, DATABASE_URL

**Updated web.config arguments line:**
```xml
arguments="C:\inetpub\wwwroot\pre_system\venv\Scripts\python.exe -m gunicorn pre_system.wsgi:application --bind 0.0.0.0:%HTTP_PLATFORM_PORT% --workers 4 --timeout 120"
```

### Step 10: Configure SSL/HTTPS (Production)

#### Option A: Using Let's Encrypt (Free SSL)

```powershell
# Install win-acme (Let's Encrypt client for Windows)
# Download from: https://www.win-acme.com/

# Run win-acme
.\wacs.exe

# Follow prompts to:
# 1. Choose your IIS website
# 2. Validate domain ownership
# 3. Install certificate
# 4. Set up auto-renewal
```

#### Option B: Using Commercial SSL Certificate

1. Purchase SSL certificate from CA
2. In IIS Manager:
   - Select server > Server Certificates
   - Import certificate (.pfx file)
   - Select website > Bindings > Add
   - Type: HTTPS, Port: 443
   - Select SSL certificate

3. Update web.config to redirect HTTP to HTTPS (uncomment redirect rule)

### Step 11: Test Deployment

```powershell
# Restart IIS
iisreset

# Test locally
# Open browser: http://localhost

# Check logs
Get-Content C:\inetpub\wwwroot\pre_system\logs\python.log -Tail 50

# Test from external network
# http://your-domain.com
# https://your-domain.com
```

### Step 12: Configure Windows Firewall

```powershell
# Allow HTTP (Port 80)
New-NetFirewallRule -DisplayName "Allow HTTP" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow

# Allow HTTPS (Port 443)
New-NetFirewallRule -DisplayName "Allow HTTPS" -Direction Inbound -LocalPort 443 -Protocol TCP -Action Allow

# Allow PostgreSQL (if needed for remote access)
New-NetFirewallRule -DisplayName "PostgreSQL" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow
```

---

## Post-Deployment Configuration

### 1. Database Backup

```powershell
# PostgreSQL backup script
$date = Get-Date -Format "yyyy-MM-dd_HHmm"
$backupFile = "C:\Backups\pre_system_$date.sql"
& "C:\Program Files\PostgreSQL\14\bin\pg_dump.exe" -U postgres -d pre_system_db -F c -f $backupFile

# Schedule daily backups using Task Scheduler
```

### 2. Application Monitoring

```powershell
# Install Application Insights or set up monitoring
# Monitor:
# - Application logs: C:\inetpub\wwwroot\pre_system\logs\
# - IIS logs: C:\inetpub\logs\LogFiles\
# - Event Viewer: Application and System logs
```

### 3. Performance Tuning

**Update settings.py for production:**

```python
# Add to pre_system/settings.py

# Caching with Redis (optional)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session using Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Database Connection Pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'pre_system_db',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': r'C:\inetpub\wwwroot\pre_system\logs\django.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
```

### 4. Scheduled Tasks

```powershell
# Create scheduled task for cleanup operations
# Task Scheduler > Create Task
# Trigger: Daily at 2:00 AM
# Action: C:\inetpub\wwwroot\pre_system\venv\Scripts\python.exe
# Arguments: C:\inetpub\wwwroot\pre_system\manage.py clearsessions
```

---

## Troubleshooting

### Issue 1: HTTP Error 500.0 - Internal Server Error

**Solution:**
```powershell
# Check logs
Get-Content C:\inetpub\wwwroot\pre_system\logs\python.log -Tail 100

# Verify Python path in web.config
# Ensure virtual environment is activated
# Check environment variables
```

### Issue 2: Static Files Not Loading

**Solution:**
```powershell
# Re-collect static files
cd C:\inetpub\wwwroot\pre_system
.\venv\Scripts\Activate.ps1
python manage.py collectstatic --noinput

# Verify IIS URL Rewrite rules
# Check folder permissions for staticfiles folder
```

### Issue 3: Database Connection Errors

**Solution:**
```powershell
# Test database connection
cd C:\inetpub\wwwroot\pre_system
.\venv\Scripts\Activate.ps1
python manage.py dbshell

# Verify DATABASE_URL in .env file
# Check PostgreSQL service is running
Get-Service -Name postgresql*
```

### Issue 4: Permission Denied Errors

**Solution:**
```powershell
# Grant full control to IIS_IUSRS
icacls "C:\inetpub\wwwroot\pre_system" /grant "IIS_IUSRS:(OI)(CI)F" /T

# Restart IIS
iisreset
```

### Issue 5: Application Won't Start

**Solution:**
```powershell
# Check Application Pool status
Get-WebAppPoolState -Name PreSystemAppPool

# Start if stopped
Start-WebAppPool -Name PreSystemAppPool

# Check Event Viewer for errors
Get-EventLog -LogName Application -Newest 20 | Where-Object {$_.Source -like "*IIS*"}
```

---

## Maintenance

### Daily Tasks
- Monitor application logs
- Check disk space
- Review error logs

### Weekly Tasks
- Database backup verification
- Performance monitoring
- Security updates check

### Monthly Tasks
- Update Python packages
- Review and rotate logs
- Security audit
- Performance optimization

---

## Security Checklist

- [ ] DEBUG=False in production
- [ ] SECRET_KEY is strong and unique
- [ ] ALLOWED_HOSTS configured correctly
- [ ] Database password is strong
- [ ] SSL/HTTPS enabled
- [ ] Security headers configured in web.config
- [ ] File upload size limits set
- [ ] CSRF protection enabled
- [ ] XSS protection enabled
- [ ] SQL injection prevention (Django ORM)
- [ ] Regular backups configured
- [ ] Monitoring and alerting set up
- [ ] Firewall rules configured
- [ ] Latest security patches applied
- [ ] Access logs enabled and monitored

---

## Useful Commands

```powershell
# Restart IIS
iisreset

# Restart specific App Pool
Restart-WebAppPool -Name PreSystemAppPool

# View IIS logs
Get-Content "C:\inetpub\logs\LogFiles\W3SVC1\u_ex$(Get-Date -Format yyMMdd).log" -Tail 50

# View Application logs
Get-Content C:\inetpub\wwwroot\pre_system\logs\python.log -Tail 50

# Django management commands
cd C:\inetpub\wwwroot\pre_system
.\venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python manage.py clearsessions

# Check Python packages
pip list

# Update packages
pip install --upgrade -r requirements-prod.txt
```

---

## Additional Resources

- Django Deployment Checklist: https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/
- IIS Documentation: https://docs.microsoft.com/en-us/iis/
- HttpPlatformHandler: https://github.com/aspnet/HttpPlatformHandler
- PostgreSQL on Windows: https://www.postgresql.org/download/windows/
- Let's Encrypt: https://letsencrypt.org/

---

## Support

For issues or questions:
- Check logs: `C:\inetpub\wwwroot\pre_system\logs\`
- Review Django documentation
- Check IIS Event Viewer
- Contact system administrator

