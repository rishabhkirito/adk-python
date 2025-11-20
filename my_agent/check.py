import sqlite3
import os

# Verify this path is still correct based on your last run
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../OpenMemory/backend/data/openmemory.sqlite"))

print(f"🧐 Inspecting database at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # This allows us to access columns by name
    cursor = conn.cursor()

    # 1. Get the column names for the 'memories' table
    cursor.execute("PRAGMA table_info(memories);")
    columns_info = cursor.fetchall()
    column_names = [col['name'] for col in columns_info]
    
    print(f"📋 Columns found: {column_names}\n")

    # 2. Select everything from the last 3 memories
    # We use * so we don't guess column names wrong again
    cursor.execute(f"SELECT * FROM memories ORDER BY created_at DESC LIMIT 3")
    rows = cursor.fetchall()

    if not rows:
        print("📭 The database is empty!")
    else:
        for i, row in enumerate(rows):
            print(f"--- Memory #{i+1} ---")
            
            # Try to find the text content (usually named 'content', 'text', or 'body')
            content = ""
            if 'content' in column_names:
                content = row['content']
            elif 'text' in column_names:
                content = row['text']
            
            print(f"LENGTH: {len(content)} characters")
            print(f"CONTENT START: {str(content)[:200]}...") 
            print("------------------\n")

    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")