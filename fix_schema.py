from sqlalchemy import text
from database import engine

def fix_schema():
    print("Fixing database schema...")
    with engine.connect() as conn:
        # Add columns to users table
        columns_to_add_users = [
            ("is_verified", "BOOLEAN DEFAULT FALSE"),
            ("availability", "VARCHAR DEFAULT 'Immediate'"),
            ("is_featured", "BOOLEAN DEFAULT FALSE"),
            ("boost_expiry", "TIMESTAMP NULL")
        ]
        
        for col_name, col_type in columns_to_add_users:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"Added column {col_name} to users table.")
            except Exception as e:
                print(f"Column {col_name} might already exist or error: {e}")
                conn.rollback()

        # Add columns to jobs table
        try:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN is_approved BOOLEAN DEFAULT TRUE"))
            conn.commit()
            print("Added column is_approved to jobs table.")
        except Exception as e:
            print(f"Column is_approved might already exist or error: {e}")
            conn.rollback()

        # Create new tables if they don't exist
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    admin_id INTEGER,
                    action VARCHAR,
                    target_id INTEGER,
                    target_type VARCHAR,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details VARCHAR
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS site_settings (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR UNIQUE,
                    value VARCHAR,
                    type VARCHAR DEFAULT 'text'
                )
            """))
            conn.commit()
            print("AuditLog and SiteSetting tables verified/created.")
        except Exception as e:
            print(f"Error creating tables: {e}")
            conn.rollback()

    print("Schema fix completed.")

if __name__ == "__main__":
    fix_schema()
