import hashlib
import json
import os
import secrets
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "site" / "data" / "auth.json"
ITERATIONS = 300000


def main():
    user = os.environ.get("ADMIN_USERNAME", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if not user or not password:
        OUT.write_text(json.dumps({"enabled": False}, indent=2))
        print("auth: ADMIN_USERNAME/ADMIN_PASSWORD not set -> editor open (set secrets to lock)")
        return
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    OUT.write_text(
        json.dumps(
            {
                "enabled": True,
                "username": user,
                "salt": salt.hex(),
                "iterations": ITERATIONS,
                "hash": digest.hex(),
            },
            indent=2,
        )
    )
    print("auth: lock generated (no plaintext written; password stays in the secret)")


if __name__ == "__main__":
    main()
