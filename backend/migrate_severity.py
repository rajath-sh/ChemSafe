import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'chemsafe.db')

print(f"Migrating {db_path}...")
conn = sqlite3.connect(db_path)

conn.execute("UPDATE alerts SET severity='INFO' WHERE severity IN ('LOW', 'MEDIUM', 'low', 'medium')")
conn.execute("UPDATE alerts SET severity='WARNING' WHERE severity IN ('HIGH', 'high')")
conn.execute("UPDATE incidents SET severity='INFO' WHERE severity IN ('LOW', 'MEDIUM', 'low', 'medium')")
conn.execute("UPDATE incidents SET severity='WARNING' WHERE severity IN ('HIGH', 'high')")
conn.execute("UPDATE notifications SET priority='INFO' WHERE priority IN ('LOW', 'MEDIUM', 'low', 'medium')")
conn.execute("UPDATE notifications SET priority='WARNING' WHERE priority IN ('HIGH', 'high')")
conn.commit()
conn.close()
print("Migration fixed.")
