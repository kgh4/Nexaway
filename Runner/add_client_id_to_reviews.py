#!/usr/bin/env python3
"""
Migration script to add client_id column to reviews table
"""

import sqlite3
from pathlib import Path

def migrate_reviews_client_id():
    """Add client_id column to reviews table and backfill data"""
    db_path = Path('instance/nexaway.db')
    if not db_path.exists():
        print("❌ Database not found")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if column already exists
        cursor.execute("PRAGMA table_info(reviews)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'client_id' in columns:
            print("✅ client_id column already exists")
            return True

        # Add client_id column
        print("➕ Adding client_id column to reviews table...")
        cursor.execute("ALTER TABLE reviews ADD COLUMN client_id INTEGER REFERENCES users(id)")

        # Backfill data: Set client_id where customer_email matches users.email
        print("🔄 Backfilling client_id data...")
        cursor.execute("""
            UPDATE reviews
            SET client_id = (
                SELECT u.id
                FROM users u
                WHERE u.email = reviews.customer_email
                AND u.role = 'client'
            )
            WHERE client_id IS NULL
        """)

        conn.commit()
        print("✅ Migration completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    migrate_reviews_client_id()
