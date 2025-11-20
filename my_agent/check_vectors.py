import sqlite3
import os
import struct

# Path to your database
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../OpenMemory/backend/data/openmemory.sqlite"))

print(f"🧐 Inspecting Vectors at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check the 'memories' table for vector data
    cursor.execute("SELECT id, content, mean_vec, created_at FROM memories ORDER BY created_at DESC LIMIT 1")
    row = cursor.fetchone()

    if not row:
        print("📭 Database empty.")
    else:
        mem_id = row['id']
        vec_blob = row['mean_vec']
        content = row['content']
        created_at = row['created_at']
        print(f"\n📄 Memory ID: {mem_id}")
        print(f"📅 Created At: {created_at}")
        print(f"📝 Content: {str(content)[:50]}...")
        
        if vec_blob is None:
            print("❌ MEMORY TABLE VECTOR: NULL")
        else:
            print(f"✅ MEMORY TABLE VECTOR: FOUND ({len(vec_blob)} bytes)")

        # Check vectors table
        print("\n🔎 Checking 'vectors' table content...")
        # Based on schema seen in logs: id, sector, user_id, v, dim
        cursor.execute("SELECT sector, v FROM vectors WHERE id = ?", (mem_id,))
        vectors = cursor.fetchall()
        
        if not vectors:
            print("❌ VECTORS TABLE: NO ENTRIES FOUND for this memory")
        else:
            for v_row in vectors:
                sector = v_row['sector']
                v_blob = v_row['v']
                print(f"   - Sector '{sector}': {len(v_blob)} bytes")
                if len(v_blob) > 0:
                    print("     ✅ Vector data present")
                
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")