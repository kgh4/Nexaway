import sqlite3

conn = sqlite3.connect('instance/nexaway.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(reviews)")
columns = cursor.fetchall()
print("Columns in reviews table:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")
conn.close()
