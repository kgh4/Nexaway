import sqlite3

# Connect to the database
conn = sqlite3.connect('instance/nexaway.db')
cursor = conn.cursor()

# Add the password_hash column
try:
    cursor.execute("ALTER TABLE pending_agencies ADD COLUMN password_hash TEXT;")
    conn.commit()
    print("✅ Column 'password_hash' added to 'pending_agencies' table.")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")
finally:
    conn.close()
