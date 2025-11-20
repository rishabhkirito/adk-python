import os
import pathlib
from typing import Dict, Any, List
from google.adk.agents import Agent
from google.adk.tools import FunctionTool, ToolContext, google_search
from google.adk.code_executors import BuiltInCodeExecutor
# Correct relative import
from .gmail_tools import search_gmail, read_email_content

# --- 1. Import All Our Tools ---

# Import the simple file tools
from .file_tools import list_files, read_file, write_file

# Import the new, advanced knowledge tools
from .knowledge_tools import (
    read_pdf, 
    read_image_ocr, 
    add_text_to_knowledge_base, 
    search_knowledge_base,
    fetch_or_find_document
)

# --- 2. Define the Specialized Sub-Agents (The Team) ---

# The Search Agent (for web research)
search_agent = Agent(
    name="search_agent",
    model="gemini-2.5-pro", # Use the model names that work for you
    description="A specialist agent that searches the web for documentation, code examples, and solutions to problems.",
    instruction="You are a search expert. Use the `Google Search` tool to find the most relevant information for the user's query.",
    tools=[google_search], 
)

# The File Manager Agent (for simple file tasks)
file_manager_pro = Agent(
    name="file_manager_pro",
    model="gemini-2.5-flash",
    description="A specialist agent that manages project files. It can list and write files.",
    instruction="You are a file system manager. Use the `list_files` and `write_file` tools.",
    tools=[list_files, write_file], # Note: We gave read_file to the KnowledgeAgent
)

# The Coding Agent (for writing code)
coding_agent = Agent(
    name="coding_agent",
    model="gemini-2.5-pro",
    description="A specialist agent that writes, refactors, and debugs Python code.",
    instruction="You are a senior Python developer. Write clean, efficient code.",
    code_executor=BuiltInCodeExecutor(), 
)

# --- NEW: The Knowledge Agent (for your AI-POS) ---
knowledge_agent = Agent(
    name="knowledge_agent",
    model="gemini-2.5-pro",
    description="A specialist agent that reads, understands, indexes, and retrieves knowledge from files.",
    instruction="""
    You are the 'Librarian' of the AI-POS system. Your goal is to organize and retrieve information with precision.

    **Your Responsibilities:**
    1.  **Ingest & Organize**: When reading a file, you MUST analyze its content and assign it a **Category** and **Tags** before adding it to the knowledge base.
        -   **Standard Categories**: Identity, Travel, Finance, Work, Education, Health, Personal.
        -   **Custom Categories**: Create a new one only if the document is truly unique.
        -   **Tags**: Extract 3-5 specific keywords (e.g., "invoice", "2024", "project-alpha").
    2.  **Retrieve**: When searching, always mention the **Category** of the documents you find in your final answer.
    3.  **Robustness**: If a file is empty or unreadable, report it clearly instead of crashing.

    **Workflow for Adding Files:**
    -   Read the file (PDF or Image).
    -   Analyze the text.
    -   Determine `category` and `tags`.
    -   Call `add_text_to_knowledge_base(text, source, category, tags)`.
    
    **Workflow for Searching:**
    -   Call `search_knowledge_base(query)`.
    -   Present results: "Found in [Category]: [Summary of content]..."
    """,
    tools=[
        read_file,          # From file_tools
        read_pdf,           # From knowledge_tools
        read_image_ocr,     # From knowledge_tools
        add_text_to_knowledge_base, # From knowledge_tools
        search_knowledge_base,     # From knowledge_tools
        fetch_or_find_document   # From knowledge_tools
    ], 
)

life_os_agent = Agent(
    name="life_os_agent",
    model="gemini-2.5-flash",
    description="A specialist agent that manages the user's digital life, specifically emails.",
    instruction="""
    You are the user's personal secretary. 
    - Use `search_gmail` to find relevant emails (bills, tickets, updates).
    - Use `read_email_content` to get the details.
    - If you find important information (like a flight ticket), pass it to the `knowledge_agent` to save it.
    """,
    tools=[search_gmail, read_email_content]
)

# --- 3. Define the Root Agent (The AI-POS Coordinator) ---
root_agent = Agent(
    name="root_agent",
    model="gemini-2.5-flash", # A fast model is good for orchestration
    description="The main orchestrator for the AI-POS project.",
    
    instruction="""
    You are the CoordinatorAgent for AI-POS, a personal AI operating system.
    Your goal is to fulfill the user's request by delegating tasks 
    to your team of specialist agents.

    Your Team:
    - `search_agent`: For web research.
    - `file_manager_pro`: For simple file operations (listing, writing new files).
    - `coding_agent`: For generating code.
    - `knowledge_agent`: **This is your Primary Memory.** Use it for reading files, 
                         understanding content, searching the knowledge base, 
                         and answering questions about the user's life, skills, and documents.

    CRITICAL RULES:
    1. Your primary goal is to answer questions about the user's life, work, and documents.
    2. If the user asks a personal question (e.g., "What are my skills?", "Where is my ticket?", "Who am I?"), 
       you MUST delegate to `knowledge_agent` immediately to search the database.
    3. NEVER say "I don't know" or "I don't have access" without checking the `knowledge_agent` first.
    4. Assume you HAVE access to the user's data through your tools.

    Your Delegation Plan:
    1.  **Personal Info & Memory:** If the user asks about themselves, their files, skills, or past info, delegate to `knowledge_agent`.
    2.  **Ingestion:** If the user provides a file to "read" or "learn", delegate to `knowledge_agent`.
    3.  **File System:** If the user wants to *write* a new file or *list* directories, delegate to `file_manager_pro`.
    4.  **Coding:** If the user needs code, delegate to `coding_agent`.
    5.  **Web Research:** For external web research, delegate to `search_agent`.
    """,
    
    # Tell the root agent about its new, powerful team
    sub_agents=[
        search_agent,
        file_manager_pro,
        coding_agent,
        knowledge_agent,
        life_os_agent  # <-- The new team member!
    ]
)