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
            print(f"Added column: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {col_name} already exists.")
            else:
                print(f"Error adding {col_name}: {e}")

    # Set default values for existing rows
    cursor.execute("UPDATE users SET role = 'jobseeker' WHERE role IS NULL")
    cursor.execute("UPDATE users SET is_active = 1 WHERE is_active IS NULL")

    conn.commit()
    conn.close()
    print("SQLite migration complete.")

if __name__ == "__main__":
    migrate()
