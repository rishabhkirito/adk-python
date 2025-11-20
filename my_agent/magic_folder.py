import time
import os
import shutil
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google.genai import Client
from dotenv import load_dotenv

# Import tools
from knowledge_tools import read_pdf, read_image_ocr, add_text_to_knowledge_base

load_dotenv()
client = Client(api_key=os.getenv("GOOGLE_API_KEY"))

# --- CONFIGURATION ---
USER_PROFILE = os.environ.get("USERPROFILE")
ONEDRIVE_DESKTOP = os.path.join(USER_PROFILE, "OneDrive", "Desktop")

WATCH_FOLDER = os.path.join(ONEDRIVE_DESKTOP, "AI_Drop_Zone")
VAULT_BASE_FOLDER = os.path.join(ONEDRIVE_DESKTOP, "My_Digital_Vault")

os.makedirs(WATCH_FOLDER, exist_ok=True)
os.makedirs(VAULT_BASE_FOLDER, exist_ok=True)

def process_file(filepath):
    """Standalone function to process a file so we can call it from anywhere."""
    filename = os.path.basename(filepath)
    
    if filename.startswith(".") or filename.lower() == "desktop.ini":
        return

    # Wait for file lock to release (OneDrive sync)
    time.sleep(2) 
    
    print(f"\n📖 Processing: {filename}")
    
    # 1. Extract Content
    res = {"status": "error", "error_message": "Unknown type"}
    ext = filename.lower().split('.')[-1]
    
    if ext == "pdf":
        res = read_pdf(filepath)
    elif ext in ["png", "jpg", "jpeg"]:
        res = read_image_ocr(filepath)
    elif ext in ["txt", "md", "py", "json"]:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                res = {"status": "success", "content": f.read()}
        except Exception as e:
            res = {"status": "error", "error_message": str(e)}
    else:
        print(f"⚠️ Unsupported file type: {ext}")
        return
    
    if res.get("status") == "error":
        print(f"❌ Read Failed: {res.get('error_message')}")
        return

    content = res['content']
    if not content or len(content.strip()) < 10:
        print("⚠️ File appears empty (or is an image without readable text).")
        return

    # 2. Analyze
    print(f"🧠 Analyzing content...")
    try:
        prompt = f"""
        Analyze this document. Output JSON with 'category' and 'tags'.
        Categories: [Work, Identity, Travel, Finance, Health, Education, Personal].
        Tags: 3-5 keywords.
        
        Content start:
        {content[:2000]}
        """
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        meta = json.loads(response.text)
        category = meta.get("category", "General")
        tags = meta.get("tags", [])
        
        print(f"🏷️  Classified: [{category}]")

        # 3. MOVE TO VAULT
        category_folder = os.path.join(VAULT_BASE_FOLDER, category)
        os.makedirs(category_folder, exist_ok=True)
        
        final_path = os.path.join(category_folder, filename)
        if os.path.exists(final_path):
            base, extension = os.path.splitext(filename)
            final_path = os.path.join(category_folder, f"{base}_{int(time.time())}{extension}")
        
        shutil.move(filepath, final_path)
        print(f"📂 Filed physically to: {final_path}")

        # 4. Save to Memory
        class MockContext: pass
        save_res = add_text_to_knowledge_base(content, final_path, category, tags, MockContext())
        
        if save_res.get("status") == "success":
            print(f"✅ Memory updated.")
        else:
            print(f"❌ Memory Error: {save_res.get('error_message')}")

    except Exception as e:
        print(f"❌ Processing Error: {e}")

class SmartIngestHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"👀 Event Detected (Create): {event.src_path}")
            process_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            # When you drag a file in, sometimes it's a 'Move' event
            print(f"👀 Event Detected (Move): {event.dest_path}")
            process_file(event.dest_path)

    def on_modified(self, event):
        # Optional: Sometimes OneDrive modifies a placeholder file
        # Leaving this out for now to avoid double-processing, 
        # but 'on_moved' handles most drag-and-drop cases.
        pass

if __name__ == "__main__":
    print(f"🚀 AI Magic Folder Active (OneDrive Edition)")
    print(f"📂 Monitoring: {WATCH_FOLDER}")
    print(f"🔒 Vault: {VAULT_BASE_FOLDER}")
    
    # --- NEW: Scan for existing files on startup ---
    print("🔎 Scanning for existing files...")
    existing_files = [f for f in os.listdir(WATCH_FOLDER) if os.path.isfile(os.path.join(WATCH_FOLDER, f))]
    for f in existing_files:
        print(f"Found existing file: {f}")
        process_file(os.path.join(WATCH_FOLDER, f))
    print("✅ Startup scan complete. Listening for new files...\n")
    # -----------------------------------------------

    observer = Observer()
    observer.schedule(SmartIngestHandler(), WATCH_FOLDER, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()