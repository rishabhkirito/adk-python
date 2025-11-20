import os
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_creds():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    
    # --- FIX: Get the directory where THIS script lives ---
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define full paths to the keys
    token_path = os.path.join(base_dir, 'token.json')
    creds_path = os.path.join(base_dir, 'credentials.json')
    # ----------------------------------------------------

    # The file token.json stores the user's access and refresh tokens
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                # Helpful error message showing exactly where it looked
                raise FileNotFoundError(f"Could not find 'credentials.json' at: {creds_path}")
                
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
            
    return creds

if __name__ == '__main__':
    # This block allows you to test the auth manually
    print("🔐 Launching Google Login...")
    try:
        get_gmail_creds()
        print("✅ Login successful! 'token.json' created/verified.")
    except Exception as e:
        print(f"❌ Error: {e}")