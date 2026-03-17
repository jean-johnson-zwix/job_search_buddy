from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json",
    scopes=SCOPES
)
creds = flow.run_local_server(port=0)
print("GOOGLE_REFRESH_TOKEN =", creds.refresh_token)
print("GOOGLE_CLIENT_ID     =", creds.client_id)
print("GOOGLE_CLIENT_SECRET =", creds.client_secret)