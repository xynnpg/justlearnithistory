import os
import sqlite3
from app import db, app

def migrate_database():
    """Recreate the database with the correct schema."""
    print("Starting database migration...")
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'justlearnit.db')
    
    # Backup existing data if the database exists
    if os.path.exists(db_path):
        print("Backing up existing data...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing data
        lessons = []
        tests = []
        users = []
        
        try:
            cursor.execute("SELECT id, title, content, \"order\" FROM lesson")
            lessons = cursor.fetchall()
        except:
            print("No existing lessons found or error reading lessons.")
        
        try:
            cursor.execute("SELECT id, title, questions_json FROM test")
            tests = cursor.fetchall()
        except:
            print("No existing tests found or error reading tests.")
            
        try:
            cursor.execute("SELECT id, username, email, password_hash, is_admin FROM user")
            users = cursor.fetchall()
        except:
            print("No existing users found or error reading users.")
        
        conn.close()
        
        # Delete the old database
        print("Removing old database...")
        os.remove(db_path)
    
    # Create new database with correct schema
    print("Creating new database with correct schema...")
    with app.app_context():
        db.create_all()
        
        # Restore data if we had any
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Restore lessons
            for lesson in lessons:
                cursor.execute(
                    "INSERT INTO lesson (id, title, content, \"order\", created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                    lesson
                )
            
            # Restore tests
            for test in tests:
                cursor.execute(
                    "INSERT INTO test (id, title, questions_json) VALUES (?, ?, ?)",
                    test
                )
            
            # Restore users
            for user in users:
                cursor.execute(
                    "INSERT INTO user (id, username, email, password_hash, is_admin) VALUES (?, ?, ?, ?, ?)",
                    user
                )
            
            conn.commit()
            conn.close()
            print("Data restored successfully.")
    
    print("Database migration completed successfully.")

if __name__ == "__main__":
    migrate_database() 