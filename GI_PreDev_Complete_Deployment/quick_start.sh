#!/bin/bash
# GI Pre-Dev System - Quick Start Script (Linux/Mac)
# This script provides a quick way to start the application

echo "==============================================="
echo "GI Pre-Dev System - Quick Start"
echo "==============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo ""
    echo "Please run the setup first:"
    echo "1. Create virtual environment: python -m venv venv"
    echo "2. Activate it: source venv/bin/activate"
    echo "3. Install dependencies: pip install -r requirements.txt"
    echo "4. Run database setup: bash setup_database.sh"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment!"
    exit 1
fi
echo "Virtual environment activated."
echo ""

# Check if database exists
if [ ! -f db.sqlite3 ]; then
    echo "WARNING: Database not found!"
    echo ""
    read -p "Would you like to set up the database now? (y/n) " setup_db
    if [ "$setup_db" = "y" ] || [ "$setup_db" = "Y" ]; then
        bash setup_database.sh
    else
        echo ""
        echo "Please run setup_database.sh before starting the server."
        exit 1
    fi
fi

# Start the development server
echo "Starting development server..."
echo ""
echo "Server will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""
python manage.py runserver

# If server stops
echo ""
echo "Server stopped."
