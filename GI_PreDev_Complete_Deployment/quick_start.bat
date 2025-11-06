@echo off
REM GI Pre-Dev System - Quick Start Script (Windows)
REM This script provides a quick way to start the application

echo ===============================================
echo GI Pre-Dev System - Quick Start
echo ===============================================
echo.

REM Check if virtual environment exists
if not exist venv (
    echo ERROR: Virtual environment not found!
    echo.
    echo Please run the setup first:
    echo 1. Create virtual environment: python -m venv venv
    echo 2. Activate it: venv\Scripts\activate
    echo 3. Install dependencies: pip install -r requirements.txt
    echo 4. Run database setup: setup_database.bat
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)
echo Virtual environment activated.
echo.

REM Check if database exists
if not exist db.sqlite3 (
    echo WARNING: Database not found!
    echo.
    echo Would you like to set up the database now? (Y/N)
    set /p setup_db=
    if /i "%setup_db%"=="Y" (
        call setup_database.bat
    ) else (
        echo.
        echo Please run setup_database.bat before starting the server.
        pause
        exit /b 1
    )
)

REM Start the development server
echo Starting development server...
echo.
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver

REM If server stops, pause
echo.
echo Server stopped.
pause
