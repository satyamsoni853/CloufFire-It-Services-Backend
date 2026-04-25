import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL not found. Skipping migration.")
    exit(0)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

def update_jobs_table():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check if jobs table exists
        cur.execute("select exists(select * from information_schema.tables where table_name=%s)", ('jobs',))
        if not cur.fetchone()[0]:
            print("Jobs table does not exist. It will be created by SQLAlchemy on next run.")
            cur.close()
            conn.close()
            return

        # List of columns to check/add for jobs table
        columns_to_add = [
            ("experience_required", "TEXT"),
            ("skills_required", "TEXT"),
            ("openings", "INTEGER"),
            ("salary", "TEXT"),
            ("perks", "TEXT"),
            ("education_qualification", "TEXT"),
            ("preferred_skills", "TEXT"),
            ("certifications", "TEXT"),
            ("deadline", "TEXT"),
            ("application_method", "TEXT"),
            ("application_email", "TEXT"),
            ("application_link", "TEXT"),
            ("hr_name", "TEXT"),
            ("hr_phone", "TEXT"),
            ("company_description", "TEXT"),
            ("company_website", "TEXT"),
            ("company_logo_url", "TEXT"),
            ("work_mode", "TEXT"),
            ("shift_timing", "TEXT"),
            ("notice_period", "TEXT"),
            ("gender_preference", "TEXT"),
            ("industry_type", "TEXT"),
            ("department", "TEXT"),
            ("posted_by_id", "INTEGER"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]
        
        for col_name, col_type in columns_to_add:
            print(f"Checking column '{col_name}'...")
            try:
                cur.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type};")
                print(f"  Added column: {col_name}")
                conn.commit()
            except psycopg2.errors.DuplicateColumn:
                conn.rollback()
                print(f"  Column {col_name} already exists.")
            except Exception as e:
                conn.rollback()
                print(f"  Error adding column {col_name}: {e}")
        
        cur.close()
        conn.close()
        print("Jobs table update complete.")
        
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    update_jobs_table()
