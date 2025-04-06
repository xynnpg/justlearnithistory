import os
import sqlite3
from app import db, app

def migrate_database():
    """Recreate the database with the correct schema."""
    print("Starting database migration...")
    
    # Get the database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'justlearnit.db')
    
    # Backup existing data if the database exists
    existing_data = {'lessons': [], 'tests': [], 'users': []}
    
    if os.path.exists(db_path):
        print("Backing up existing data...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get existing data
        try:
            cursor.execute("SELECT id, title, content, \"order\" FROM lesson")
            existing_data['lessons'] = cursor.fetchall()
            print(f"Backed up {len(existing_data['lessons'])} lessons")
        except Exception as e:
            print(f"No existing lessons found or error reading lessons: {e}")
        
        try:
            cursor.execute("SELECT id, title, questions_json FROM test")
            existing_data['tests'] = cursor.fetchall()
            print(f"Backed up {len(existing_data['tests'])} tests")
        except Exception as e:
            print(f"No existing tests found or error reading tests: {e}")
            
        try:
            cursor.execute("SELECT id, username, email, password_hash, is_admin FROM user")
            existing_data['users'] = cursor.fetchall()
            print(f"Backed up {len(existing_data['users'])} users")
        except Exception as e:
            print(f"No existing users found or error reading users: {e}")
        
        conn.close()
        
        # Delete the old database
        print("Removing old database...")
        os.remove(db_path)
    
    # Create new database with correct schema
    print("Creating new database with correct schema...")
    with app.app_context():
        db.create_all()
        
        # Restore data if we had any
        if any(existing_data.values()):
            print("Restoring data to new database...")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Restore lessons
            for lesson in existing_data['lessons']:
                try:
                    cursor.execute(
                        "INSERT INTO lesson (id, title, content, \"order\", created_at) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)",
                        lesson
                    )
                except Exception as e:
                    print(f"Error restoring lesson {lesson[0]}: {e}")
            
            # Restore tests with default order
            for i, test in enumerate(existing_data['tests'], 1):
                try:
                    cursor.execute(
                        "INSERT INTO test (id, title, questions_json, \"order\") VALUES (?, ?, ?, ?)",
                        (test[0], test[1], test[2], i)
                    )
                except Exception as e:
                    print(f"Error restoring test {test[0]}: {e}")
            
            # Restore users
            for user in existing_data['users']:
                try:
                    cursor.execute(
                        "INSERT INTO user (id, username, email, password_hash, is_admin) VALUES (?, ?, ?, ?, ?)",
                        user
                    )
                except Exception as e:
                    print(f"Error restoring user {user[0]}: {e}")
            
            conn.commit()
            conn.close()
            print("Data restored successfully.")
    
    print("Database migration completed successfully.")

if __name__ == '__main__':
    migrate_database() 