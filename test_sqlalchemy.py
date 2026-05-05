from database import SessionLocal, User
from auth import get_password_hash

def test_db():
    db = SessionLocal()
    try:
        # Check if we can query the User model with new fields
        user = db.query(User).first()
        if user:
            print(f"Successfully queried user: {user.email}")
            print(f"is_verified: {user.is_verified}")
            print(f"availability: {user.availability}")
        else:
            print("No users found, but query succeeded.")
    except Exception as e:
        print(f"Query failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_db()
