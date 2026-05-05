import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check():
    url = os.getenv("DATABASE_URL")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
    cols = [r[0] for r in cur.fetchall()]
    print(f"Columns in 'users': {cols}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check()
