#!/usr/bin/env python3
"""
Backup existing data, recreate tables with correct schema, and restore data
"""
import sqlite3
from app import create_app
from app.models import db

def backup_data():
    """Backup all data from existing tables"""
    conn = sqlite3.connect('instance/nexaway.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    backup = {}

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        backup[table] = [dict(row) for row in rows]

    conn.close()
    return backup

def recreate_tables():
    """Drop and recreate all tables with correct schema"""
    app = create_app()
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create all tables with correct schema
        db.create_all()
        print("Tables recreated with correct schema")

def restore_data(backup):
    """Restore data to new tables"""
    app = create_app()
    with app.app_context():
        conn = sqlite3.connect('instance/nexaway.db')
        cursor = conn.cursor()

        # Restore data for each table
        for table, rows in backup.items():
            if rows:
                # Get column names from first row
                columns = list(rows[0].keys())
                placeholders = ','.join(['?' for _ in columns])
                column_names = ','.join(columns)

                # Insert data
                for row in rows:
                    values = [row[col] for col in columns]
                    try:
                        cursor.execute(f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})", values)
                    except Exception as e:
                        print(f"Error inserting into {table}: {e}")
                        # Skip problematic rows

        conn.commit()
        conn.close()
        print("Data restored")

if __name__ == '__main__':
    print("Backing up data...")
    backup = backup_data()

    print("Recreating tables...")
    recreate_tables()

    print("Restoring data...")
    restore_data(backup)

    print("Migration completed!")
