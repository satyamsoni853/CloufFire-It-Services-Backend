import sqlite3

def check_db():
    conn = sqlite3.connect('sql_app.db')
    cursor = conn.cursor()
    
    print("--- Jobs matching 'fr' ---")
    cursor.execute("SELECT title, company FROM jobs WHERE title LIKE '%fr%' OR company LIKE '%fr%'")
    jobs = cursor.fetchall()
    for job in jobs:
        print(job)
        
    print("\n--- Users matching 'fr' ---")
    cursor.execute("SELECT full_name, skills FROM users WHERE full_name LIKE '%fr%' OR skills LIKE '%fr%'")
    users = cursor.fetchall()
    for user in users:
        print(user)
    
    conn.close()

if __name__ == "__main__":
    check_db()
