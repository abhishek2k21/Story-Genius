import sys
import os
sys.path.append(os.getcwd())

from app.core.database import get_db_session, DBUser
from app.auth.service import auth_service

def check_users():
    db = get_db_session()
    users = db.query(DBUser).all()
    print(f"Found {len(users)} users in DB:")
    for u in users:
        print(f"- {u.username} ({u.email}) [Status: {u.status}]")
        # Verify password for testuser
        if u.username == 'testuser':
            from app.auth.password import verify_password
            is_valid = verify_password("Demo1234!", u.password_hash)
            print(f"  Password 'Demo1234!' valid: {is_valid}")

    db.close()

if __name__ == "__main__":
    check_users()
