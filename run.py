#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from utils.init_admin import init_admin_user

def main():
    """Initialize the application and admin user."""
    # Create the database tables
    with app.app_context():
        db.create_all()
    
    # Initialize the admin user with credentials from the file
    init_admin_user()
    
    # Run the application
    app.run(debug=True)

if __name__ == "__main__":  
    main() 