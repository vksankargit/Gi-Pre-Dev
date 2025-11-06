@echo off
REM GI Pre-Dev System - Database Setup Script (Windows)
REM This script sets up a fresh database for the application

echo ===============================================
echo GI Pre-Dev System - Database Setup
echo ===============================================
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo WARNING: Virtual environment not activated!
    echo Please activate the virtual environment first:
    echo    venv\Scripts\activate
    echo.
    pause
    exit /b 1
)

echo Step 1: Backing up existing database (if exists)...
if exist db.sqlite3 (
    echo Database found. Creating backup...
    copy db.sqlite3 db.sqlite3.backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
    echo Backup created successfully.
) else (
    echo No existing database found. Proceeding with fresh setup...
)
echo.

echo Step 2: Running database migrations...
python manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Migration failed!
    pause
    exit /b 1
)
echo Migrations completed successfully.
echo.

echo Step 3: Creating superuser account...
echo.
echo Please enter details for the administrator account:
python manage.py createsuperuser
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo NOTE: Superuser creation was skipped or failed.
    echo You can create it later using: python manage.py createsuperuser
)
echo.

echo Step 4: Collecting static files...
python manage.py collectstatic --noinput
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Static files collection had issues.
    echo This is not critical for development, but may affect production.
)
echo.

echo ===============================================
echo Database Setup Complete!
echo ===============================================
echo.
echo Next steps:
echo 1. Start the development server: python manage.py runserver
echo 2. Open browser: http://localhost:8000
echo 3. Login with the superuser account you created
echo.
pause
