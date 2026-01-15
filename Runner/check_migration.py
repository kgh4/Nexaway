#!/usr/bin/env python3
"""
Simple migration verification script
"""

import sqlite3
from pathlib import Path

def check_migration():
    """Check if migration is complete"""
    db_path = Path('instance/nexaway.db')
    if not db_path.exists():
        print("❌ Database not found")
        return False

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check agencies table
        cursor.execute("PRAGMA table_info(agencies)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'agency_id' not in columns:
            print("❌ agency_id column missing")
            return False

        # Check approved agencies have agency_id
        cursor.execute("SELECT COUNT(*) FROM agencies WHERE status='approved' AND agency_id IS NULL")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"❌ {count} approved agencies missing agency_id")
            return False

        print("✅ Migration verified!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    check_migration()
