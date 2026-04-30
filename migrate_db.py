import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback or check
if not DATABASE_URL:
    print("DATABASE_URL not found. Skipping migration.")
    exit(0)

# SQLAlchemy/psycopg2 1.4+ requires 'postgresql://' instead of 'postgres://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def update_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # List of columns to check/add
        columns_to_add = [
            ("role", "TEXT DEFAULT 'jobseeker'"),
            ("is_active", "BOOLEAN DEFAULT FALSE"),
            ("otp", "TEXT"),
            ("otp_expiry", "TIMESTAMP"),
            ("education", "TEXT"),
            ("experience", "TEXT"),
            ("skills", "TEXT"),
            ("resume_url", "TEXT"),
            ("profile_image_url", "TEXT"),
            ("bio", "TEXT"),
            ("work_status", "TEXT"),
            ("mobile", "TEXT"),
            ("location", "TEXT"),
            ("salary", "TEXT"),
            ("projects", "TEXT"),
            ("summary", "TEXT"),
            ("gender", "TEXT"),
            ("dob", "TEXT"),
            ("languages", "TEXT")
        ]
        
        for col_name, col_type in columns_to_add:
            print(f"Checking column '{col_name}'...")
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};")
                print(f"  Added column: {col_name}")
                conn.commit()
            except psycopg2.errors.DuplicateColumn:
                conn.rollback()
                print(f"  Column {col_name} already exists.")
            except Exception as e:
                conn.rollback()
                print(f"  Error adding column {col_name}: {e}")
        
        # Ensure all existing users have a role if it was just added
        print("Updating existing users to have a default role...")
        cur.execute("UPDATE users SET role = 'jobseeker' WHERE role IS NULL;")
        cur.execute("UPDATE users SET is_active = TRUE WHERE is_active IS NULL;")
        conn.commit()
        
        cur.close()
        conn.close()
        print("Database update complete.")
        
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    update_db()
