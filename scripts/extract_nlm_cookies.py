#!/usr/bin/env python3
"""
Extract Google/NotebookLM cookies from Chrome and create
a Playwright-compatible storage_state.json for notebooklm-py CLI.
"""

import sqlite3
import os
import json
import shutil
import subprocess
import tempfile

CHROME_COOKIES = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome/Default/Cookies"
)
STORAGE_FILE = os.path.expanduser("~/.notebooklm/storage_state.json")

os.makedirs(os.path.dirname(STORAGE_FILE), exist_ok=True)

# Chrome locks the Cookies DB, so copy it first
tmp = tempfile.mktemp(suffix=".db")
shutil.copy2(CHROME_COOKIES, tmp)

# On macOS, Chrome encrypts cookie values using the Keychain.
# We need to decrypt them using the "Chrome Safe Storage" key.
def get_chrome_key():
    """Get Chrome's encryption key from macOS Keychain."""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", "Chrome Safe Storage", "-w"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Warning: Could not get Chrome key: {result.stderr}")
        return None
    return result.stdout.strip()

def decrypt_cookie_value(encrypted_value, key):
    """Decrypt Chrome cookie value on macOS."""
    if not encrypted_value or len(encrypted_value) <= 3:
        return ""

    # v10 encryption (macOS)
    if encrypted_value[:3] == b'v10':
        try:
            import hashlib
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import padding
            from cryptography.hazmat.backends import default_backend

            # Derive key
            derived_key = hashlib.pbkdf2_hmac(
                'sha1', key.encode('utf-8'), b'saltysalt', 1003, dklen=16
            )

            # Decrypt
            iv = b' ' * 16
            cipher = Cipher(
                algorithms.AES(derived_key), modes.CBC(iv), backend=default_backend()
            )
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted_value[3:]) + decryptor.finalize()

            # Remove PKCS7 padding
            pad_len = decrypted[-1]
            if isinstance(pad_len, int) and 1 <= pad_len <= 16:
                decrypted = decrypted[:-pad_len]

            return decrypted.decode('utf-8', errors='replace')
        except ImportError:
            print("Need cryptography package. Installing...")
            subprocess.run(
                ["pip3", "install", "--user", "--break-system-packages", "cryptography"],
                capture_output=True
            )
            # Retry after install
            import hashlib
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend

            derived_key = hashlib.pbkdf2_hmac(
                'sha1', key.encode('utf-8'), b'saltysalt', 1003, dklen=16
            )
            iv = b' ' * 16
            cipher = Cipher(
                algorithms.AES(derived_key), modes.CBC(iv), backend=default_backend()
            )
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(encrypted_value[3:]) + decryptor.finalize()
            pad_len = decrypted[-1]
            if isinstance(pad_len, int) and 1 <= pad_len <= 16:
                decrypted = decrypted[:-pad_len]
            return decrypted.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"Decryption error: {e}")
            return ""

    return encrypted_value.decode('utf-8', errors='replace') if isinstance(encrypted_value, bytes) else str(encrypted_value)

# Get Chrome encryption key
chrome_key = get_chrome_key()
if not chrome_key:
    print("ERROR: Cannot access Chrome Keychain. You may need to allow access.")
    exit(1)

print(f"Got Chrome encryption key")

# Query cookies for Google domains
conn = sqlite3.connect(tmp)
cursor = conn.cursor()

# Get all Google-related cookies needed for NotebookLM
domains = [
    '.google.com',
    '.notebooklm.google.com',
    'notebooklm.google.com',
    '.accounts.google.com',
    'accounts.google.com',
    '.googleapis.com',
    '.youtube.com',
]

domain_filter = " OR ".join([f"host_key LIKE '%{d}%'" for d in domains])

cursor.execute(f"""
    SELECT host_key, name, encrypted_value, path, expires_utc, is_secure, is_httponly, samesite
    FROM cookies
    WHERE {domain_filter}
    ORDER BY host_key
""")

rows = cursor.fetchall()
print(f"Found {len(rows)} Google cookies")

# Convert to Playwright storage_state format
cookies = []
for host, name, enc_value, path, expires, secure, httponly, samesite in rows:
    value = decrypt_cookie_value(enc_value, chrome_key)
    if not value:
        continue

    # Convert Chrome timestamp to Unix (Chrome uses microseconds since 1601-01-01)
    expires_unix = -1
    if expires and expires > 0:
        expires_unix = (expires / 1000000) - 11644473600

    sameSite_map = {0: "None", 1: "Lax", 2: "Strict"}

    cookie = {
        "name": name,
        "value": value,
        "domain": host,
        "path": path or "/",
        "expires": expires_unix,
        "httpOnly": bool(httponly),
        "secure": bool(secure),
        "sameSite": sameSite_map.get(samesite, "None"),
    }
    cookies.append(cookie)

conn.close()
os.unlink(tmp)

# Write storage state
storage_state = {
    "cookies": cookies,
    "origins": [
        {
            "origin": "https://notebooklm.google.com",
            "localStorage": []
        }
    ]
}

with open(STORAGE_FILE, 'w') as f:
    json.dump(storage_state, f, indent=2)

print(f"\n✓ Saved {len(cookies)} cookies to {STORAGE_FILE}")
print(f"✓ File size: {os.path.getsize(STORAGE_FILE)} bytes")
print("\nYou can now use: notebooklm list")
