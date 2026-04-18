"""
Seed script to insert test users (admin, employer, jobseeker) into the database.
Run: python seed_users.py
"""
from database import SessionLocal, User, Base, engine
from auth import get_password_hash

Base.metadata.create_all(bind=engine)

db = SessionLocal()

test_users = [
    {
        "full_name": "Admin User",
        "email": "admin@cloudfire.com",
        "mobile": "9999999001",
        "role": "admin",
        "work_status": "employed",
        "hashed_password": get_password_hash("TestPass@123"),
        "is_active": True,
        "bio": "Platform administrator at Cloudfire IT Services.",
        "skills": "Management, Analytics, Operations",
        "education": "MBA in Information Technology",
        "experience": "10+ years in IT management",
    },
    {
        "full_name": "Rahul Sharma",
        "email": "employer@cloudfire.com",
        "mobile": "9999999002",
        "role": "employer",
        "work_status": "employed",
        "hashed_password": get_password_hash("TestPass@123"),
        "is_active": True,
        "bio": "Hiring manager at TechCorp India. Looking for skilled developers.",
        "skills": "Recruitment, HR, Talent Management",
        "education": "B.Tech Computer Science",
        "experience": "5 years in tech recruitment",
    },
    {
        "full_name": "Priya Patel",
        "email": "jobseeker@cloudfire.com",
        "mobile": "9999999003",
        "role": "jobseeker",
        "work_status": "fresher",
        "hashed_password": get_password_hash("TestPass@123"),
        "is_active": True,
        "bio": "Passionate full-stack developer with experience in React and Node.js.",
        "skills": "React, Node.js, Python, MongoDB, AWS",
        "education": "B.Tech Computer Science - IIT Delhi",
        "experience": "1 year internship at Infosys",
    },
    {
        "full_name": "Amit Kumar",
        "email": "amit@cloudfire.com",
        "mobile": "9999999004",
        "role": "jobseeker",
        "work_status": "experienced",
        "hashed_password": get_password_hash("TestPass@123"),
        "is_active": True,
        "bio": "Senior backend developer specializing in Python and cloud architecture.",
        "skills": "Python, Django, FastAPI, Docker, AWS, PostgreSQL",
        "education": "M.Tech Software Engineering",
        "experience": "4 years at Wipro, 2 years at TCS",
    },
    {
        "full_name": "Sneha Verma",
        "email": "sneha@cloudfire.com",
        "mobile": "9999999005",
        "role": "jobseeker",
        "work_status": "fresher",
        "hashed_password": get_password_hash("TestPass@123"),
        "is_active": True,
        "bio": "UI/UX designer with a passion for creating beautiful digital experiences.",
        "skills": "Figma, Adobe XD, HTML, CSS, JavaScript, Tailwind",
        "education": "BDes - NID Ahmedabad",
        "experience": "6 months freelance",
    },
    {
        "full_name": "Vikram Singh",
        "email": "vikram@cloudfire.com",
        "mobile": "9999999006",
        "role": "employer",
        "work_status": "employed",
        "hashed_password": get_password_hash("TestPass@123"),
        "is_active": True,
        "bio": "CTO at StartupHub. Building the future of EdTech.",
        "skills": "Leadership, Architecture, Cloud, DevOps",
        "education": "MS Computer Science - Stanford",
        "experience": "12 years in tech leadership",
    },
]

inserted = 0
skipped = 0

for user_data in test_users:
    existing = db.query(User).filter(User.email == user_data["email"]).first()
    if existing:
        print(f"  SKIP: {user_data['email']} (already exists)")
        skipped += 1
    else:
        new_user = User(**user_data)
        db.add(new_user)
        print(f"  ADD:  {user_data['email']} ({user_data['role']})")
        inserted += 1

db.commit()
db.close()

print(f"\nDone! Inserted: {inserted}, Skipped: {skipped}")
print("\nTest Credentials (all passwords: TestPass@123):")
print("  Admin:      admin@cloudfire.com")
print("  Employer:   employer@cloudfire.com")
print("  Job Seeker: jobseeker@cloudfire.com")
