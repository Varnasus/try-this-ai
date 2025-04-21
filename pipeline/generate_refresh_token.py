import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json", SCOPES
    )
    creds = flow.run_local_server(port=8080, prompt='consent')

    print("\n✅ Refresh token generated successfully:\n")
    print(f"refresh_token: {creds.refresh_token}")

    with open("yt_tokens.json", "w") as f:
        json.dump({
            "refresh_token": creds.refresh_token,
            "token": creds.token,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "token_uri": creds.token_uri
        }, f, indent=2)

if __name__ == "__main__":
    main()
