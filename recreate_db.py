import os
import sqlite3
from app import db, app

def recreate_database():
    """Recreate the database from scratch to ensure it has the correct schema."""
    print("Recreating database...")
    
    # Connect to the database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'justlearnit.db')
    
    # Delete the existing database file if it exists
    if os.path.exists(db_path):
        print(f"Deleting existing database at {db_path}")
        os.remove(db_path)
    
    # Create a new database with the correct schema
    print("Creating new database with correct schema...")
    with app.app_context():
        db.create_all()
    
    print("Database recreated successfully.")

if __name__ == "__main__":
    recreate_database() 