import requests
import json

OPENMEMORY_API_URL = "http://localhost:8080"

def debug_search():
    query = "skills in Rishabh's resume"
    
    print(f"🔍 Sending Query: '{query}'...")
    
    # This mimics exactly what your Agent sends
    payload = {
        "query": query,
        "topK": 3,
        "filter": {
            "sectors": ["episodic", "semantic", "reflective", "procedural"] 
        }
    }
    
    try:
        response = requests.post(
            f"{OPENMEMORY_API_URL}/memory/query",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ SERVER RESPONSE:")
            print(json.dumps(data, indent=2))
            
            results = data.get("results", [])
            print(f"\n📊 Total Results Found: {len(results)}")
            
            if len(results) == 0:
                print("⚠️  Server found 0 matches. (Threshold might be too high)")
            else:
                print("🎉 Server returned data! The Agent is just ignoring it.")
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Connection Failed: {str(e)}")

if __name__ == "__main__":
    debug_search()