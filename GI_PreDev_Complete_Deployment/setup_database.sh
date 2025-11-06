#!/bin/bash
# GI Pre-Dev System - Database Setup Script (Linux/Mac)
# This script sets up a fresh database for the application

echo "==============================================="
echo "GI Pre-Dev System - Database Setup"
echo "==============================================="
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "WARNING: Virtual environment not activated!"
    echo "Please activate the virtual environment first:"
    echo "   source venv/bin/activate"
    echo ""
    exit 1
fi

echo "Step 1: Backing up existing database (if exists)..."
if [ -f db.sqlite3 ]; then
    echo "Database found. Creating backup..."
    cp db.sqlite3 "db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)"
    echo "Backup created successfully."
else
    echo "No existing database found. Proceeding with fresh setup..."
fi
echo ""

echo "Step 2: Running database migrations..."
python manage.py migrate
if [ $? -ne 0 ]; then
    echo "ERROR: Migration failed!"
    exit 1
fi
echo "Migrations completed successfully."
echo ""

echo "Step 3: Creating superuser account..."
echo ""
echo "Please enter details for the administrator account:"
python manage.py createsuperuser
if [ $? -ne 0 ]; then
    echo ""
    echo "NOTE: Superuser creation was skipped or failed."
    echo "You can create it later using: python manage.py createsuperuser"
fi
echo ""

echo "Step 4: Collecting static files..."
python manage.py collectstatic --noinput
if [ $? -ne 0 ]; then
    echo "WARNING: Static files collection had issues."
    echo "This is not critical for development, but may affect production."
fi
echo ""

echo "==============================================="
echo "Database Setup Complete!"
echo "==============================================="
echo ""
echo "Next steps:"
echo "1. Start the development server: python manage.py runserver"
echo "2. Open browser: http://localhost:8000"
echo "3. Login with the superuser account you created"
echo ""
