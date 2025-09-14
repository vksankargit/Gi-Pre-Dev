#!/usr/bin/env python
"""
Setup script for PRE System
This script helps with initial setup and database population
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
    django.setup()

def run_migrations():
    """Create and run database migrations"""
    print("Creating database migrations...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    
    print("Applying database migrations...")
    execute_from_command_line(['manage.py', 'migrate'])

def load_initial_data():
    """Load initial data fixtures"""
    print("Loading initial data...")
    try:
        execute_from_command_line(['manage.py', 'loaddata', 'initial_data.json'])
        print("Initial data loaded successfully.")
    except Exception as e:
        print(f"Warning: Could not load initial data: {e}")

def create_superuser():
    """Prompt to create superuser"""
    print("\nCreating superuser account...")
    print("Please provide details for the admin user:")
    execute_from_command_line(['manage.py', 'createsuperuser'])

def main():
    """Main setup function"""
    print("=" * 50)
    print("PRE System Setup")
    print("=" * 50)
    
    setup_django()
    run_migrations()
    load_initial_data()
    
    # Ask if user wants to create superuser
    create_admin = input("\nDo you want to create an admin user now? (y/n): ").lower().strip()
    if create_admin in ['y', 'yes']:
        create_superuser()
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure your settings")
    print("2. Run 'python manage.py runserver' to start the development server")
    print("3. Visit http://127.0.0.1:8000/ in your browser")
    print("4. Login with your admin credentials")
    print("5. Create organizations, users, and teams")
    print("\nFor detailed instructions, see README.md")

if __name__ == '__main__':
    main()