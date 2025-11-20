import pathlib
from google.adk.tools import ToolContext

# These are the original file tools you built

def list_files(directory: str = ".") -> dict:
    """
    Lists all files and subdirectories in a specified directory recursively.

    Args:
        directory (str, optional): The directory to list. Defaults to the 
                                   current directory (".").

    Returns:
        dict: A dictionary containing 'status' and 'files' or 'error_message'.
    """
    print(f"[Tool Call] list_files(directory='{directory}')")
    try:
        p = pathlib.Path(directory)
        if not p.is_dir():
            return {"status": "error", "error_message": f"Path '{directory}' is not a valid directory."}
        
        files = [str(file.relative_to(p)) for file in p.rglob('*') if file.is_file()]
        return {"status": "success", "files": files}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

def read_file(filepath: str) -> dict:
    """
    Reads the content of a specified text file. (Use 'read_pdf' for PDFs).

    Args:
        filepath (str): The relative or absolute path to the file.

    Returns:
        dict: A dictionary containing 'status' and 'content' or 'error_message'.
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

def write_file(filepath: str, content: str, tool_context: ToolContext) -> dict:
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
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        tool_context.state['last_written_file'] = str(p)
        return {"status": "success", "filepath": str(p)}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}