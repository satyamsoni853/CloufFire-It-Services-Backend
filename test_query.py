import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)

print(f"Connecting...")
try:
    conn = psycopg2.connect(url)
    print("Connected!")
    cur = conn.cursor()
    print("Querying users count...")
    cur.execute("SELECT count(*) FROM users;")
    print(f"Users count: {cur.fetchone()[0]}")
    cur.close()
    conn.close()
    print("Done.")
except Exception as e:
    print(f"Error: {e}")
