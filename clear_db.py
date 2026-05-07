import sqlite3
import time

try:
    conn = sqlite3.connect('data/app.db', timeout=10)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    
    # disable foreign keys
    c.execute("PRAGMA foreign_keys = OFF;")
    
    for table_name in tables:
        if table_name[0] != 'sqlite_sequence':
            try:
                c.execute(f"DROP TABLE IF EXISTS {table_name[0]};")
            except Exception as e:
                pass
    
    conn.commit()
    conn.close()
    print("Database cleared successfully.")
except Exception as e:
    print("Error:", e)
