from app import app, db, User
from werkzeug.security import generate_password_hash
from utils.credentials import get_admin_credentials

def init_admin_user():
    """Initialize or update the admin user with credentials from the file."""
    with app.app_context():
        # Get current admin credentials
        username, password = get_admin_credentials()
        
        # Check if admin user exists
        admin = User.query.filter_by(is_admin=True).first()
        
        if admin:
            # Update existing admin
            admin.username = username
            admin.password_hash = generate_password_hash(password)
            admin.email = f"{username}@justlearnit.com"
        else:
            # Create new admin user
            admin = User(
                username=username,
                email=f"{username}@justlearnit.com",
                password_hash=generate_password_hash(password),
                is_admin=True
            )
            db.session.add(admin)
        
        db.session.commit()
        print(f"Admin user initialized/updated:")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Email: {username}@justlearnit.com")

if __name__ == "__main__":
    init_admin_user() 