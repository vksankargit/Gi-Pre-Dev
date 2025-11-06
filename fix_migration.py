import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pre_system.settings')
django.setup()

from django.db import connection

# Fix the foreign key issue
with connection.cursor() as cursor:
    cursor.execute("PRAGMA foreign_keys=OFF;")
    cursor.execute("DELETE FROM project_status WHERE project_id NOT IN (SELECT id FROM ppi_projects);")
    cursor.execute("PRAGMA foreign_keys=ON;")
    print("Fixed foreign key integrity issues")
