import json
import sys

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Run: pip install google-auth-oauthlib", file=sys.stderr)
    raise SystemExit(1)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/youtube_auth.py client_secret.json")
        raise SystemExit(1)
    flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    print("\nAdd these as GitHub repository secrets:\n")
    print(json.dumps(
        {
            "YOUTUBE_CLIENT_ID": creds.client_id,
            "YOUTUBE_CLIENT_SECRET": creds.client_secret,
            "YOUTUBE_REFRESH_TOKEN": creds.refresh_token,
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
