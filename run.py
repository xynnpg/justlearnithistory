
import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from utils.init_admin import init_admin_user

def main():
    with app.app_context():
        db.create_all()
    

    init_admin_user()
    


if __name__ == "__main__":  
    main() 