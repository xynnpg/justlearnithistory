import os
import random
import string
import time
from datetime import datetime, timedelta
from pathlib import Path

# Define the credentials file path
CREDENTIALS_DIR = Path("credentials")
CREDENTIALS_FILE = CREDENTIALS_DIR / "admin_credentials.txt"

def generate_random_string(length=12):
    """Generate a random string of specified length."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def generate_credentials():
    """Generate new random username and password."""
    username = f"admin_{generate_random_string(8)}"
    password = generate_random_string(12)
    return username, password

def load_credentials():
    """Load credentials from file or generate new ones if needed."""
    # Create credentials directory if it doesn't exist
    CREDENTIALS_DIR.mkdir(exist_ok=True)
    
    # Check if credentials file exists and is not expired
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 3:
                username = lines[0].strip()
                password = lines[1].strip()
                last_updated = datetime.fromisoformat(lines[2].strip())
                
                # Check if credentials are still valid (less than 7 days old)
                if datetime.now() - last_updated < timedelta(days=7):
                    return username, password
    
    # Generate new credentials
    username, password = generate_credentials()
    
    # Save new credentials
    with open(CREDENTIALS_FILE, 'w') as f:
        f.write(f"{username}\n")
        f.write(f"{password}\n")
        f.write(f"{datetime.now().isoformat()}\n")
    
    return username, password

def get_admin_credentials():
    """Get the current admin credentials."""
    return load_credentials() 