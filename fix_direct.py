import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def fix():
    url = os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL not found")
        return
    
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        
    print(f"Connecting to DB...")
    try:
        conn = psycopg2.connect(url)
        conn.autocommit = True
        cur = conn.cursor()
        
        cols = [
            ("is_verified", "BOOLEAN DEFAULT FALSE"),
            ("availability", "VARCHAR DEFAULT 'Immediate'"),
            ("is_featured", "BOOLEAN DEFAULT FALSE"),
            ("boost_expiry", "TIMESTAMP NULL")
        ]
        
        for name, dtype in cols:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {name} {dtype}")
                print(f"Added {name} to users")
            except Exception as e:
                print(f"Skipping {name}: {e}")
                
        try:
            cur.execute("ALTER TABLE jobs ADD COLUMN is_approved BOOLEAN DEFAULT TRUE")
            print("Added is_approved to jobs")
        except Exception as e:
            print(f"Skipping is_approved: {e}")
            
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                admin_id INTEGER,
                action VARCHAR,
                target_id INTEGER,
                target_type VARCHAR,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details VARCHAR
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS site_settings (
                id SERIAL PRIMARY KEY,
                key VARCHAR UNIQUE,
                value VARCHAR,
                type VARCHAR DEFAULT 'text'
            )
        """)
        print("Tables verified")
        
        cur.close()
        conn.close()
        print("Done")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix()
