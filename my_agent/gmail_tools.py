import base64
import os
from googleapiclient.discovery import build
from .gmail_auth import get_gmail_creds
from bs4 import BeautifulSoup

def search_gmail(query: str, max_results: int = 5) -> dict:
    """
    Searches Gmail for emails matching the query.
    Example queries: "subject:receipt", "from:airline", "is:unread"
    """
    print(f"[Tool Call] search_gmail(query='{query}')")
    try:
        creds = get_gmail_creds()
        service = build('gmail', 'v1', credentials=creds)

        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])

        email_list = []
        if not messages:
            return {"status": "success", "emails": "No emails found matching that query."}

        for msg in messages:
            # Get details for each email
            msg_detail = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            payload = msg_detail['payload']
            headers = payload['headers']

            # Extract Subject and From
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            snippet = msg_detail.get('snippet', '')

            email_list.append({
                "id": msg['id'],
                "subject": subject,
                "from": sender,
                "snippet": snippet
            })

        return {"status": "success", "emails": email_list}

    except Exception as e:
        return {"status": "error", "error_message": str(e)}

def read_email_content(email_id: str) -> dict:
    """
    Reads the full body content of a specific email.
    """
    print(f"[Tool Call] read_email_content(id='{email_id}')")
    try:
        creds = get_gmail_creds()
        service = build('gmail', 'v1', credentials=creds)

        msg = service.users().messages().get(userId='me', id=email_id, format='full').execute()
        payload = msg['payload']
        
        body_text = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body_text += base64.urlsafe_b64decode(data).decode('utf-8')
        elif 'body' in payload:
            data = payload['body']['data']
            body_text += base64.urlsafe_b64decode(data).decode('utf-8')

        # Clean up formatting
        return {"status": "success", "full_text": body_text[:5000]} # Limit size

    except Exception as e:
        return {"status": "error", "error_message": str(e)}