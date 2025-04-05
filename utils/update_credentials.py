import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from app import app
from utils.credentials import load_credentials
from utils.init_admin import init_admin_user

def update_credentials():
    """Update admin credentials if they are older than 7 days."""
    # Get current credentials
    username, password = load_credentials()
    
    # Initialize/update the admin user with the new credentials
    init_admin_user()
    
    print(f"Credentials updated at {datetime.now().isoformat()}")

if __name__ == "__main__":
    update_credentials() 