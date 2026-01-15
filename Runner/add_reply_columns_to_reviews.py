#!/usr/bin/env python3
"""
Add missing columns to reviews table for reply functionality
"""
import sqlite3
from app import create_app

def add_reply_columns():
    """Add reply_at, re_rating, re_comment, trust_bonus columns to reviews table"""
    app = create_app()
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if columns exist
        cursor.execute("PRAGMA table_info(reviews)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add missing columns
        if 'reply_at' not in columns:
            print("Adding reply_at column...")
            cursor.execute("ALTER TABLE reviews ADD COLUMN reply_at DATETIME")

        if 're_rating' not in columns:
            print("Adding re_rating column...")
            cursor.execute("ALTER TABLE reviews ADD COLUMN re_rating INTEGER")

        if 're_comment' not in columns:
            print("Adding re_comment column...")
            cursor.execute("ALTER TABLE reviews ADD COLUMN re_comment TEXT")

        if 'trust_bonus' not in columns:
            print("Adding trust_bonus column...")
            cursor.execute("ALTER TABLE reviews ADD COLUMN trust_bonus INTEGER DEFAULT 0")

        conn.commit()
        conn.close()
        print("✅ Migration completed successfully!")

if __name__ == '__main__':
    add_reply_columns()
