import os
import sys
import time
from google.adk.tools import ToolContext

# Add the src directory to the path so we can import the agent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from my_agent.agent import knowledge_agent
from my_agent.knowledge_tools import add_text_to_knowledge_base, search_knowledge_base, fetch_or_find_document

def test_memory_flow():
    print("--- Starting Verification ---")
    
    # 1. Create a dummy file
    unique_id = int(time.time())
    filename = f"test_memory_{unique_id}.txt"
    content = f"This is a test memory for verifying embeddings. ID: {unique_id}"
    
    with open(filename, "w") as f:
        f.write(content)
    print(f"Created {filename}")

    # 2. Add to Knowledge Base
    print("\n--- Adding to Memory ---")
    # Passing None for tool_context as we don't use it in the implementation
    result = add_text_to_knowledge_base(content, filename, "Personal", ["test", "debug", f"id_{unique_id}"], None)
    print(f"Add Result: {result}")
    
    if result.get("status") != "success":
        print("❌ Failed to add memory. Exiting.")
        exit(1)

    # 3. Search (to see if it was indexed - might take a moment for embeddings but text search should work)
    print("\n--- Searching Memory ---")
    time.sleep(2) # Give it a moment
    search_result = search_knowledge_base(f"ID: {unique_id}", None)
    print(f"Search Result: {search_result}")

    # 4. Fetch Document
    print("\n--- Fetching Document ---")
    fetch_result = fetch_or_find_document(filename)
    print(f"Fetch Result: {fetch_result}")
    
    # Cleanup
    try:
        os.remove(filename)
    except:
        pass
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    test_memory_flow()
