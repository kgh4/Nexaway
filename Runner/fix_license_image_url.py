import sqlite3

# Connect to the database
conn = sqlite3.connect('instance/nexaway.db')
cursor = conn.cursor()

# Check current schema
cursor.execute("PRAGMA table_info(pending_agencies);")
columns = cursor.fetchall()
for col in columns:
    print(f"Column: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}")

# Since SQLite doesn't support ALTER COLUMN directly for NOT NULL,
# we need to recreate the table with the correct schema
# But to keep it simple, let's just update the model to make it nullable=False if needed,
# or provide a default value.

# For now, let's make the column nullable by recreating the table
# First, backup data
cursor.execute("SELECT * FROM pending_agencies;")
data = cursor.fetchall()

# Get column names
cursor.execute("PRAGMA table_info(pending_agencies);")
columns_info = cursor.fetchall()
column_names = [col[1] for col in columns_info]

# Drop and recreate table with correct schema
cursor.execute("DROP TABLE IF EXISTS pending_agencies_new;")
cursor.execute("""
CREATE TABLE pending_agencies_new (
    id INTEGER PRIMARY KEY,
    pending_id TEXT UNIQUE NOT NULL,
    agency_tax_id TEXT NOT NULL,
    company_name TEXT NOT NULL,
    official_name TEXT,
    email TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    governorate TEXT,
    website TEXT,
    sectors TEXT,
    tourism_license TEXT,
    registry_number TEXT,
    license_image_url TEXT,  -- Now nullable
    password_hash TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
""")

# Insert data back
placeholders = ', '.join(['?'] * len(column_names))
for row in data:
    cursor.execute(f"INSERT INTO pending_agencies_new ({', '.join(column_names)}) VALUES ({placeholders});", row)

# Drop old table and rename new one
cursor.execute("DROP TABLE pending_agencies;")
cursor.execute("ALTER TABLE pending_agencies_new RENAME TO pending_agencies;")

conn.commit()
print("✅ Fixed license_image_url to be nullable.")

conn.close()
