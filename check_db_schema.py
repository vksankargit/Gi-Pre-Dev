#!/usr/bin/env python
import sqlite3

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("All tables in database:")
print("=" * 50)
user_tables = []
for table in tables:
    if 'user' in table[0].lower():
        user_tables.append(table[0])
    print(f"- {table[0]}")

print(f"\nUser-related tables found: {user_tables}")
print("\n" + "=" * 50)

# Check if review_meetings_participants table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='review_meetings_participants'")
participants_table = cursor.fetchone()
print(f"Table review_meetings_participants exists: {bool(participants_table)}")

# Get schema for review_meetings table
cursor.execute("PRAGMA table_info(review_meetings)")
columns = cursor.fetchall()

print("\nCurrent review_meetings table schema:")
print("=" * 50)
for column in columns:
    print(f"Column: {column[1]}, Type: {column[2]}, Not Null: {column[3]}, Default: {column[4]}")

conn.close()