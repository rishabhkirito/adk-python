import fitz # PyMuPDF
import pytesseract
from PIL import Image
import io
import requests
import json
import os
from google.adk.tools import ToolContext

# Point to your running OpenMemory server
# Your logs showed it running on port 8080
OPENMEMORY_API_URL = "http://localhost:8080"

# Keep the original PDF/OCR tools (they run locally)
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

# --- 1. Local File Reading Tools (unchanged) ---

def read_pdf(filepath: str) -> dict:
    """
    Extracts text from a PDF. 
    HYBRID MODE: Tries standard text extraction first. 
    If that fails (scanned PDF), it converts pages to images and uses OCR.
    """
    print(f"[Tool Call] read_pdf(filepath='{filepath}')")
    try:
        doc = fitz.open(filepath)
        full_text = ""
        
        for page_num, page in enumerate(doc):
            # 1. Try standard text extraction
            text = page.get_text()
            
            # 2. If text is too short/empty, assume it's an image/scan
            if len(text.strip()) < 50: 
                print(f"   - Page {page_num+1} looks like an image. Running OCR...")
                
                # --- FIX: POINT TO TESSERACT EXE ---
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                # -----------------------------------
                
                # Render page to an image (pixmap)
                pix = page.get_pixmap()
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Run Tesseract OCR
                text = pytesseract.image_to_string(img)
                
            full_text += f"\n--- Page {page_num+1} ---\n{text}"
            
        doc.close()
        return {"status": "success", "content": full_text}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

def read_image_ocr(filepath: str) -> dict:
    """
    Extracts text from an image file using OCR.
    """
    print(f"[Tool Call] read_image_ocr(filepath='{filepath}')")
    if not os.path.exists(filepath):
        return {"status": "error", "error_message": f"File not found: {filepath}"}

    try:
        # Ensure this path matches your system
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img)
        
        if not text.strip():
             return {"status": "warning", "content": "", "message": "OCR completed but found no text."}

        return {"status": "success", "content": text}
    except Exception as e:
        return {"status": "error", "error_message": f"Failed to perform OCR: {str(e)}"}

# --- 2. New OpenMemory Tools (API Connected) ---

def add_text_to_knowledge_base(text: str, source: str, category: str, tags: list[str], tool_context: ToolContext) -> dict:
    """
    Adds text content to the OpenMemory knowledge base with categorization.
    
    Args:
        text (str): The text content to add.
        source (str): The source (e.g., 'resume.pdf').
        category (str): The category of the document (e.g., 'Work', 'Personal').
        tags (list[str]): A list of tags/keywords.
    """
    print(f"[Tool Call] add_text_to_knowledge_base(source='{source}', category='{category}', tags={tags})")
    try:
        # Based on standard OpenMemory API structure
        payload = {
            "content": text,
            "metadata": {
                "source": source,
                "type": "document",
                "category": category,
                "tags": tags
            }
        }
        
        response = requests.post(
            f"{OPENMEMORY_API_URL}/memory/add",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code != 200:
            return {"status": "error", "error_message": f"OpenMemory Error {response.status_code}: {response.text}"}

        return {"status": "success", "response": response.json()}
    
    except requests.exceptions.ConnectionError:
        return {"status": "error", "error_message": "System Offline: Could not connect to OpenMemory server."}
    except Exception as e:
        return {"status": "error", "error_message": f"Failed to connect to OpenMemory: {str(e)}"}

def search_knowledge_base(query: str, tool_context: ToolContext) -> dict:
    """
    Searches the OpenMemory knowledge base for relevant text.
    """
    print(f"[Tool Call] search_knowledge_base(query='{query}')")
    try:
        payload = {
            "query": query,
            "topK": 3,
            # ROBUSNESS UPGRADE: 
            # Explicitly tell OpenMemory to check the 'episodic' sector 
            # (where document uploads often live) and 'semantic' (facts).
            "filter": {
                "sectors": ["episodic", "semantic", "reflective"] 
            }
        }
        
        response = requests.post(
            f"{OPENMEMORY_API_URL}/memory/query",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code != 200:
            return {"status": "error", "error_message": f"OpenMemory Error {response.status_code}: {response.text}"}
            
        data = response.json()
        results = data.get("matches", [])
        
        if not results:
            # DEBUGGING HELP:
            # If we find nothing, tell the user exactly why (instead of silence)
            return {"status": "success", "results": "No matching memories found. Try asking about the specific document (e.g., 'resume')."}

        formatted_results = []
        for res in results:
            content = res.get('content', '')
            meta = res.get('metadata', {})
            source = meta.get('source', 'unknown')
            category = meta.get('category', 'General')
            
            # The score tells us how confident the AI is (0.0 to 1.0)
            score = res.get('similarity', 0.0) 
            
            formatted_results.append(f"[Score: {score:.2f}] [Category: {category}] Source: {source} | Content: {content[:500]}...")

        return {"status": "success", "results": formatted_results}
        
    except Exception as e:
        return {"status": "error", "error_message": f"Failed to connect to OpenMemory: {str(e)}"}

def fetch_or_find_document(document_name: str) -> dict:
    """
    Searches for a document locally by name.
    """
    print(f"[Tool Call] fetch_or_find_document(document_name='{document_name}')")
    try:
        # Search in the current directory and subdirectories
        start_dir = "."
        found_files = []
        for root, dirs, files in os.walk(start_dir):
            if document_name in files:
                found_files.append(os.path.join(root, document_name))
        
        if not found_files:
             # Try fuzzy match or partial match if exact match fails? 
             # For now, let's stick to exact match or "contains"
             for root, dirs, files in os.walk(start_dir):
                for file in files:
                    if document_name.lower() in file.lower():
                        found_files.append(os.path.join(root, file))

        if not found_files:
            return {"status": "error", "error_message": f"Document '{document_name}' not found locally."}
        
        # Return the first found file
        filepath = found_files[0]
        return {"status": "success", "filepath": filepath, "found_files": found_files}

    except Exception as e:
        return {"status": "error", "error_message": str(e)}