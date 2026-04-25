import sqlite3
import os

DB_PATH = "sql_app.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Nothing to migrate.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Columns to add to users table
    columns = [
        ("role", "TEXT DEFAULT 'jobseeker'"),
        ("is_active", "BOOLEAN DEFAULT 0"),
        ("otp", "TEXT"),
        ("otp_expiry", "DATETIME"),
        ("education", "TEXT"),
        ("experience", "TEXT"),
        ("skills", "TEXT"),
        ("resume_url", "TEXT"),
        ("profile_image_url", "TEXT"),
        ("bio", "TEXT"),
        ("work_status", "TEXT"),
        ("mobile", "TEXT")
    ]

    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"Added column to users: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column users.{col_name} already exists.")
            else:
                print(f"Error adding {col_name} to users: {e}")

    # Set default values for existing rows
    try:
        cursor.execute("UPDATE users SET role = 'jobseeker' WHERE role IS NULL")
        cursor.execute("UPDATE users SET is_active = 1 WHERE is_active IS NULL")
    except Exception as e:
        print(f"Error updating defaults for users: {e}")

    # Columns to add to jobs table
    job_columns = [
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
        ("created_at", "DATETIME")
    ]

    for col_name, col_type in job_columns:
        try:
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
            print(f"Added column to jobs: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column jobs.{col_name} already exists.")
            else:
                print(f"Error adding {col_name} to jobs: {e}")

    conn.commit()
    conn.close()
    print("SQLite migration complete.")

if __name__ == "__main__":
    migrate()
