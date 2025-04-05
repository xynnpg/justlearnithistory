import os
import sqlite3
import datetime

def fix_database():
    """Fix the database by adding the created_at column to the Lesson table."""
    print("Fixing database...")
    
    # Connect to the database
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'justlearnit.db')
    
    if not os.path.exists(db_path):
        print("Database file not found. Please run the application first to create it.")
        return
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the created_at column exists
        cursor.execute("PRAGMA table_info(lesson)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'created_at' not in column_names:
            print("Adding created_at column to Lesson table...")
            
            # Add the created_at column with a default value
            cursor.execute("ALTER TABLE lesson ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            
            print("Column added successfully.")
        else:
            print("The created_at column already exists in the Lesson table.")
    
    except Exception as e:
        print(f"Error fixing database: {e}")
        conn.rollback()
    finally:
        conn.commit()
        conn.close()
        print("Database fix completed.")

if __name__ == "__main__":
    fix_database() 