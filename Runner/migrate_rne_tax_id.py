#!/usr/bin/env python3
"""
Migration script for TN RNE Tax ID Format Update

This script updates the database schema to support the new TN RNE format:
- Changes tax_id column from VARCHAR(8) to VARCHAR(9)
- Supports 12345678A format (8 digits + 1 uppercase letter, no dash)
- Normalizes existing tax_ids by removing dashes and uppercasing

Run this script after updating the models but before running the application.
"""

import sqlite3
import sys
from pathlib import Path

def migrate_database():
    """Migrate the database schema for the new TN RNE format"""

    # Database path
    db_path = Path('instance/nexaway.db')

    if not db_path.exists():
        print("❌ Database not found. Run create_db.py first.")
        return False

    print("🔄 Starting TN RNE tax_id migration...")

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Step 1: Create new agencies table with updated tax_id column
        print("📝 Updating agencies table tax_id column to VARCHAR(9)...")

        cursor.execute("""
            CREATE TABLE agencies_new (
                id INTEGER PRIMARY KEY,
                agency_id VARCHAR(20) UNIQUE,
                tax_id VARCHAR(9) UNIQUE NOT NULL,
                company_name VARCHAR(200) NOT NULL,
                official_name VARCHAR(200),
                category VARCHAR(1),
                email VARCHAR(150),
                phone VARCHAR(50),
                address VARCHAR(255),
                governorate VARCHAR(80),
                website VARCHAR(200),
                sectors VARCHAR(100),
                tourism_license VARCHAR(50),
                registry_number VARCHAR(50),
                verification_status VARCHAR(20) DEFAULT 'pending',
                status VARCHAR(20) DEFAULT 'pending',
                source VARCHAR(20) DEFAULT 'csv',
                password_hash VARCHAR(128),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Step 2: Migrate existing agency data
        print("🔄 Migrating existing agency data...")
        cursor.execute("""
            INSERT INTO agencies_new (
                id, agency_id, tax_id, company_name, official_name, category,
                email, phone, address, governorate, website, sectors,
                tourism_license, registry_number, verification_status, status,
                source, password_hash, created_at, updated_at
            )
            SELECT
                id, agency_id, UPPER(REPLACE(tax_id, '-', '')), company_name, official_name, category,
                email, phone, address, governorate, website, sectors,
                tourism_license, registry_number, verification_status, status,
                source, password_hash, created_at, updated_at
            FROM agencies
        """)

        # Step 3: Replace old table with new one
        cursor.execute("DROP TABLE agencies")
        cursor.execute("ALTER TABLE agencies_new RENAME TO agencies")

        # Step 4: Recreate indexes
        print("📊 Recreating indexes...")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_agencies_tax_id ON agencies (tax_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_agencies_governorate ON agencies (governorate)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_agencies_verification_status ON agencies (verification_status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_agencies_status ON agencies (status)")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_agencies_agency_id ON agencies (agency_id)")

        # Commit all changes
        conn.commit()

        print("✅ TN RNE migration completed successfully!")
        print("\n📋 Summary of changes:")
        print("   • Updated tax_id column to VARCHAR(9)")
        print("   • Normalized existing tax_ids (removed dashes, uppercased)")
        print("   • Recreated indexes for performance")

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

        # Check tax_id column length
        cursor.execute("PRAGMA table_info(agencies)")
        columns = cursor.fetchall()
        tax_id_col = next((col for col in columns if col[1] == 'tax_id'), None)
        if not tax_id_col or 'VARCHAR(9)' not in tax_id_col[2].upper():
            print("❌ tax_id column not updated to VARCHAR(9)")
            return False

        # Check that all tax_ids are uppercase
        cursor.execute("SELECT COUNT(*) FROM agencies WHERE tax_id != UPPER(tax_id)")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"❌ {count} tax_ids are not uppercase")
            return False

        print("✅ Migration verification passed!")
        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 TN RNE Tax ID Migration Script")
    print("=" * 40)

    # Run migration
    if migrate_database():
        # Verify migration
        if verify_migration():
            print("\n🎉 Migration completed successfully!")
            print("You can now use the new ABCDEFG-1 TN RNE format.")
            sys.exit(0)
        else:
            print("\n❌ Migration verification failed!")
            sys.exit(1)
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
