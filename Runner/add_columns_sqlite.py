import sqlite3

# Connect to the database
conn = sqlite3.connect('instance/nexaway.db')
cursor = conn.cursor()

# Get existing columns
cursor.execute("PRAGMA table_info(reviews)")
existing_columns = [row[1] for row in cursor.fetchall()]

print("Existing columns:", existing_columns)

# Columns to add
columns_to_add = [
    ('reply_at', 'DATETIME'),
    ('re_rating', 'INTEGER'),
    ('re_comment', 'TEXT'),
    ('trust_bonus', 'INTEGER DEFAULT 0'),
    ('updated_at', 'DATETIME')
]

# Add missing columns
for col_name, col_type in columns_to_add:
    if col_name not in existing_columns:
        try:
            cursor.execute(f"ALTER TABLE reviews ADD COLUMN {col_name} {col_type}")
            print(f"Added column: {col_name}")
        except Exception as e:
            print(f"Error adding {col_name}: {e}")

conn.commit()
conn.close()

print("Migration completed!")
