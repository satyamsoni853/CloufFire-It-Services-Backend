import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def update_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        print("Adding 'profile_image_url' column...")
        try:
            cur.execute("ALTER TABLE users ADD COLUMN profile_image_url TEXT;")
            print("Added column: profile_image_url")
        except psycopg2.errors.DuplicateColumn:
            conn.rollback()
            print("Column profile_image_url already exists.")
        except Exception as e:
            conn.rollback()
            print(f"Error adding column: {e}")
        
        conn.commit()
        cur.close()
        conn.close()
        print("Database update complete.")
        
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    update_db()
