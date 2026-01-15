#!/usr/bin/env python3
"""
Migration script for Agency Flow Overhaul

This script updates the database schema to support the new agency flow:
- Adds agency_id column to agencies table
- Updates foreign key references to use agency_id instead of tax_id
- Removes pending_agencies table
- Migrates existing data appropriately

Run this script after updating the models but before running the application.
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database():
    """Migrate the database schema for the new agency flow"""

    # Database path
    db_path = Path('instance/nexaway.db')

    if not db_path.exists():
        print("❌ Database not found. Run create_db.py first.")
        return False

    print("🔄 Starting database migration...")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Step 1: Add agency_id column to agencies table
        print("📝 Adding agency_id column to agencies table...")
        cursor.execute("ALTER TABLE agencies ADD COLUMN agency_id VARCHAR(20)")

        # Step 2: Generate agency_id for existing approved agencies
        print("🔢 Generating agency_id for approved agencies...")
        cursor.execute("SELECT id FROM agencies WHERE status = 'approved' ORDER BY id")
        approved_agencies = cursor.fetchall()

        for (agency_id,) in approved_agencies:
            agency_code = f"A-{agency_id:03d}"
            cursor.execute(
                "UPDATE agencies SET agency_id = ? WHERE id = ?",
                (agency_code, agency_id)
            )
            print(f"   ✅ Agency {agency_id} -> {agency_code}")

        # Step 3: Create new users table structure with agency_id foreign key
        print("🔄 Updating users table structure...")

        # Create temporary table with new structure
        cursor.execute("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY,
                email VARCHAR(120) NOT NULL UNIQUE,
                password_hash VARCHAR(128) NOT NULL,
                role VARCHAR(20) NOT NULL,
                agency_id VARCHAR(20),
                FOREIGN KEY (agency_id) REFERENCES agencies (agency_id)
            )
        """)

        # Migrate existing user data
        cursor.execute("""
            INSERT INTO users_new (id, email, password_hash, role, agency_id)
            SELECT u.id, u.email, u.password_hash, u.role, a.agency_id
            FROM users u
            LEFT JOIN agencies a ON u.agency_id = a.tax_id
        """)

        # Replace old table
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        # Step 4: Update offers table structure
        print("🔄 Updating offers table structure...")

        cursor.execute("""
            CREATE TABLE offers_new (
                id INTEGER PRIMARY KEY,
                offer_id VARCHAR(20) NOT NULL UNIQUE,
                agency_id VARCHAR(20) NOT NULL,
                type VARCHAR(20) NOT NULL,
                title VARCHAR(200) NOT NULL,
                price FLOAT NOT NULL,
                currency VARCHAR(3) NOT NULL,
                from_city VARCHAR(10),
                to_city VARCHAR(10),
                date_from DATE,
                date_to DATE,
                seats_available INTEGER,
                description TEXT,
                segment VARCHAR(20),
                pilgrimage_type VARCHAR(20),
                domestic BOOLEAN DEFAULT 0,
                capacity INTEGER,
                tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agency_id) REFERENCES agencies (agency_id)
            )
        """)

        # Migrate existing offer data
        cursor.execute("""
            INSERT INTO offers_new (
                id, offer_id, agency_id, type, title, price, currency,
                from_city, to_city, date_from, date_to, seats_available,
                description, segment, pilgrimage_type, domestic, capacity, tags, created_at
            )
            SELECT o.id, o.offer_id, a.agency_id, o.type, o.title, o.price, o.currency,
                   o.from_city, o.to_city, o.date_from, o.date_to, o.seats_available,
                   o.description, o.segment, o.pilgrimage_type, o.domestic, o.capacity, o.tags, o.created_at
            FROM offers o
            LEFT JOIN agencies a ON o.agency_id = a.tax_id
        """)

        # Replace old table
        cursor.execute("DROP TABLE offers")
        cursor.execute("ALTER TABLE offers_new RENAME TO offers")

        # Step 5: Update reviews table structure
        print("🔄 Updating reviews table structure...")

        cursor.execute("""
            CREATE TABLE reviews_new (
                id INTEGER PRIMARY KEY,
                review_id VARCHAR(20) NOT NULL UNIQUE,
                agency_id VARCHAR(20) NOT NULL,
                customer_name VARCHAR(100) NOT NULL,
                customer_email VARCHAR(120) NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agency_id) REFERENCES agencies (agency_id)
            )
        """)

        # Migrate existing review data (skip orphaned reviews)
        cursor.execute("""
            INSERT INTO reviews_new (
                id, review_id, agency_id, customer_name, customer_email,
                rating, comment, status, created_at
            )
            SELECT r.id, r.review_id, a.agency_id, r.customer_name, r.customer_email,
                   r.rating, r.comment, r.status, r.created_at
            FROM reviews r
            INNER JOIN agencies a ON r.agency_id = a.tax_id
            WHERE a.agency_id IS NOT NULL
        """)

        # Report orphaned reviews
        cursor.execute("""
            SELECT COUNT(*) FROM reviews r
            LEFT JOIN agencies a ON r.agency_id = a.tax_id
            WHERE a.agency_id IS NULL
        """)
        orphaned_count = cursor.fetchone()[0]
        if orphaned_count > 0:
            print(f"⚠️  Skipped {orphaned_count} orphaned reviews (referenced non-existent agencies)")

        # Replace old table
        cursor.execute("DROP TABLE reviews")
        cursor.execute("ALTER TABLE reviews_new RENAME TO reviews")

        # Step 6: Drop pending_agencies table
        print("🗑️  Removing pending_agencies table...")
        cursor.execute("DROP TABLE IF EXISTS pending_agencies")

        # Step 7: Create indexes for performance
        print("📊 Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_agency_id ON users (agency_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_offers_agency_id ON offers (agency_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_reviews_agency_id ON reviews (agency_id)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_agencies_agency_id ON agencies (agency_id)")

        # Commit all changes
        conn.commit()

        print("✅ Migration completed successfully!")
        print("\n📋 Summary of changes:")
        print("   • Added agency_id column to agencies table")
        print("   • Generated A-xxx IDs for approved agencies")
        print("   • Updated users, offers, reviews to reference agency_id")
        print("   • Removed pending_agencies table")
        print("   • Created performance indexes")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

def verify_migration():
    """Verify that the migration was successful"""
    print("\n🔍 Verifying migration...")

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
            print("❌ agency_id column missing from agencies table")
            return False

        # Check foreign key references
        cursor.execute("PRAGMA foreign_key_list(users)")
        fks = cursor.fetchall()
        if not any(fk[3] == 'agency_id' for fk in fks):
            print("❌ users table foreign key not updated")
            return False

        # Check that pending_agencies table is gone
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pending_agencies'")
        if cursor.fetchone():
            print("❌ pending_agencies table still exists")
            return False

        # Check approved agencies have agency_id
        cursor.execute("SELECT COUNT(*) FROM agencies WHERE status='approved' AND agency_id IS NULL")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"❌ {count} approved agencies missing agency_id")
            return False

        print("✅ Migration verification passed!")
        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Agency Flow Migration Script")
    print("=" * 40)

    # Run migration
    if migrate_database():
        # Verify migration
        if verify_migration():
            print("\n🎉 Migration completed successfully!")
            print("You can now run the application with the new agency flow.")
            sys.exit(0)
        else:
            print("\n❌ Migration verification failed!")
            sys.exit(1)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
