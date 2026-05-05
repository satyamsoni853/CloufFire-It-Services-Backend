import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)

print(f"Connecting to {url.split('@')[1]}...")
try:
    conn = psycopg2.connect(url)
    print("Connected successfully!")
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print(cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
