import os
import pathlib
from typing import Dict, Any, List
from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext, google_search
from google.adk.code_executors import BuiltInCodeExecutor
from knowledge_tools import read_pdf, read_image_ocr, add_text_to_knowledge_base, search_knowledge_base
# --- 1. Define Tools for the File Manager Agent ---
# These are simple Python functions that will be given to the file agent
# The docstrings are VERY important, as they tell the agent how to use the tool.

def list_files(directory: str = ".") -> Dict[str, Any]:
    """
    Lists all files and subdirectories in a specified directory recursively.

    Args:
        directory (str, optional): The directory to list. Defaults to the 
                                   current directory (".").

    Returns:
        dict: A dictionary containing a 'status' ('success' or 'error')
              and either a 'files' list or an 'error_message'.
    """
    print(f"[Tool Call] list_files(directory='{directory}')")
    try:
        p = pathlib.Path(directory)
        if not p.is_dir():
            return {"status": "error", "error_message": f"Path '{directory}' is not a valid directory."}
        
        # Use rglob() to recursively find all files
        files = [str(file.relative_to(p)) for file in p.rglob('*') if file.is_file()]
        return {"status": "success", "files": files}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

def read_file(filepath: str) -> Dict[str, Any]:
    """
    Reads the content of a specified text file.

    Args:
        filepath (str): The relative or absolute path to the file.

    Returns:
        dict: A dictionary containing 'status' and either 'content' or 'error_message'.
    """
    print(f"[Tool Call] read_file(filepath='{filepath}')")
    try:
        p = pathlib.Path(filepath)
        if not p.is_file():
            return {"status": "error", "error_message": f"File not found: {filepath}"}
        
        content = p.read_text()
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

def write_file(filepath: str, content: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Writes or overwrites content to a specified file. 
    Creates the directory if it doesn't exist.

    Args:
        filepath (str): The relative or absolute path to the file.
        content (str): The text content to write to the file.
        tool_context (ToolContext): Injected by ADK. Used to update state.

    Returns:
        dict: A dictionary containing 'status' and 'filepath' or 'error_message'.
    """
    print(f"[Tool Call] write_file(filepath='{filepath}', ...)")
    try:
        p = pathlib.Path(filepath)
        # Create parent directories if they don't exist
        p.parent.mkdir(parents=True, exist_ok=True)
        
        p.write_text(content)
        
        # Example of using ToolContext to update the session state
        tool_context.state['last_written_file'] = str(p)
        
        return {"status": "success", "filepath": str(p)}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

# --- 2. Define the Specialized Sub-Agents (The Team) ---

# The Search Agent
search_agent = Agent(
    name="search_agent",
    model="gemini-2.5-pro",
    description="A specialist agent that searches the web for documentation, code examples, and solutions to problems.",
    instruction="You are a search expert. Use the `Google Search` tool to find the most relevant information for the user's query.",
    tools=[google_search],  # Use the built-in Google Search tool
)

# The File Manager Agent
file_manager_agent = Agent(
    name="file_manager_pro",
    model="gemini-2.5-flash",
    description="A specialist agent that manages project files. It can read, write, and list files.",
    instruction="You are a file system manager. Use the `list_files`, `read_file`, and `write_file` tools to manage the project directory.",
    tools=[list_files, read_file, write_file], # Give it the tools we defined
)

# The Coding Agent
coding_agent = Agent(
    name="coding_agent",
    model="gemini-2.5-pro",
    description="A specialist agent that writes, refactors, and debugs Python code. It uses a code executor to test snippets.",
    instruction="You are a senior Python developer. Write clean, efficient code. Use the code executor to generate and test code snippets.",
    code_executor=BuiltInCodeExecutor(), # Give it the built-in code executor
)

knowledge_agent = Agent(
    name="knowledge_agent",
    model="gemini-2.5-pro", # (or 2.5-pro)
    description="A specialist agent that reads, understands, and indexes knowledge from files.",
    instruction="""
    You are a knowledge management expert.
    Your job is to ingest and retrieve information.
    - Use 'read_pdf' for .pdf files.
    - Use 'read_image_ocr' for .png, .jpg, or .bmp files.
    - Use 'add_text_to_knowledge_base' to save extracted text.
    - Use 'search_knowledge_base' to answer user questions.
    - For simple text files, use the 'read_file' tool.
    """,
    # Give it the file-reading and knowledge tools
    tools=[
        read_file,          # From your file_manager
        read_pdf,           # New
        read_image_ocr,     # New
        add_text_to_knowledge_base, # New
        search_knowledge_base     # New
    ], 
)

# --- 3. Define the Root Agent (The Orchestrator) ---
# This is the main agent that ADK will run.
root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash", # (or 2.5-flash)
    description="The main orchestrator for the AI-POS project.",
    
    instruction="""
    You are the project manager for a personal AI operating system.
    Your goal is to fulfill the user's request by delegating tasks 
    to your team of specialist agents.

    Your Team:
    - `search_agent`: For web research.
    - `file_manager_agent`: For simple file operations (list, write, delete).
    - `coding_agent`: For generating code.
    - `knowledge_agent`: For reading, ingesting, and searching the content of
                          PDFs, images, and text files.

    Your Plan:
    1.  Understand the user's goal.
    2.  If the user wants to *read* or *understand* a file, delegate to `knowledge_agent`.
    3.  If the user wants to *search* their knowledge, delegate to `knowledge_agent`.
    4.  If the user wants to *write* a new file, delegate to `file_manager_agent`.
    5.  For all other tasks, use your best judgment.
    """,
    
    # Add the new agent to the team
    sub_agents=[
        search_agent,
        file_manager_agent,
        coding_agent,
        knowledge_agent  # <-- NEW TEAM MEMBER
    ]
)