"""One-time Google Calendar login. Opens a browser, saves token.json (read-only access).

1. Put credentials.json (OAuth "Desktop app" client from Google Cloud Console) in the project root.
2. Run: python scripts/google_auth.py
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
creds = flow.run_local_server(port=0)
with open("token.json", "w") as f:
    f.write(creds.to_json())
print("Saved token.json. For cloud hosting, paste its contents into the GOOGLE_TOKEN_JSON env var.")
