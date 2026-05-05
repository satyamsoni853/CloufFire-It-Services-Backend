"""
Seed realistic job seeker dashboard data for local development.
Run from backend: py seed_dashboard_data.py
"""
from datetime import datetime, timedelta, timezone

from auth import get_password_hash
from database import (
    Application,
    AuditLog,
    Base,
    ChatMessage,
    Interview,
    Job,
    JobAlert,
    Notification,
    SavedJob,
    SessionLocal,
    SiteSetting,
    User,
    engine,
)

Base.metadata.create_all(bind=engine)
db = SessionLocal()


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_or_create_user(email, defaults):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, **defaults)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


employer = get_or_create_user(
    "employer@cloudfire.com",
    {
        "full_name": "Rahul Sharma",
        "mobile": "9999999002",
        "role": "employer",
        "work_status": "employed",
        "hashed_password": get_password_hash("TestPass@123"),
        "is_active": True,
        "bio": "Hiring manager at TechCorp India.",
        "skills": "Recruitment, HR, Talent Management",
        "education": "B.Tech Computer Science",
        "experience": "5 years in tech recruitment",
    },
)

admin = get_or_create_user(
    "admin@cloudfire.com",
    {
        "full_name": "Admin User",
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
)

pending_employer = get_or_create_user(
    "pending-employer@cloudfire.com",
    {
        "full_name": "Neha Hiring",
        "mobile": "9999999010",
        "role": "employer",
        "work_status": "employed",
        "hashed_password": get_password_hash("TestPass@123"),
        "is_active": True,
        "is_verified": False,
        "bio": "Recruiter waiting for employer verification.",
        "skills": "Recruitment, Screening",
        "education": "MBA HR",
        "experience": "3 years in hiring",
    },
)

seeker = get_or_create_user(
    "jobseeker@cloudfire.com",
    {
        "full_name": "Priya Patel",
        "mobile": "9999999003",
        "role": "jobseeker",
        "work_status": "fresher",
        "hashed_password": get_password_hash("TestPass@123"),
        "is_active": True,
        "bio": "Full-stack developer with React and Python experience.",
        "skills": "React, Node.js, Python, FastAPI, SQL, AWS",
        "education": "B.Tech Computer Science",
        "experience": "1 year internship",
        "location": "Bengaluru",
        "availability": "Immediate",
    },
)

job_rows = [
    {
        "title": "Frontend React Developer",
        "company": "TechCorp India",
        "description": "Build responsive hiring dashboards and customer portals.",
        "location": "Bengaluru",
        "type": "Full-time",
        "experience_required": "Fresher to 2 years",
        "skills_required": "React, JavaScript, Tailwind, API Integration",
        "preferred_skills": "TypeScript, Recharts",
        "openings": 3,
        "salary": "6-9 LPA",
        "work_mode": "Hybrid",
        "department": "Engineering",
        "industry_type": "SaaS",
    },
    {
        "title": "Python FastAPI Engineer",
        "company": "CloudHire Labs",
        "description": "Create APIs for recruitment workflows and analytics.",
        "location": "Remote",
        "type": "Full-time",
        "experience_required": "1-3 years",
        "skills_required": "Python, FastAPI, SQL, Docker",
        "preferred_skills": "AWS, PostgreSQL",
        "openings": 2,
        "salary": "8-12 LPA",
        "work_mode": "Remote",
        "department": "Backend",
        "industry_type": "HR Tech",
    },
    {
        "title": "Full Stack Developer",
        "company": "SkillBridge Systems",
        "description": "Work on candidate portals, job matching, and assessment tools.",
        "location": "Hyderabad",
        "type": "Contract",
        "experience_required": "Fresher to 1 year",
        "skills_required": "React, Node.js, Python, MongoDB",
        "preferred_skills": "AWS, CI/CD",
        "openings": 4,
        "salary": "5-8 LPA",
        "work_mode": "Onsite",
        "department": "Product Engineering",
        "industry_type": "Education",
    },
    {
        "title": "Cloud Support Associate",
        "company": "NimbusWorks",
        "description": "Support AWS-hosted products and automate operational checks.",
        "location": "Pune",
        "type": "Full-time",
        "experience_required": "Fresher",
        "skills_required": "AWS, SQL, Linux",
        "preferred_skills": "Python, Docker",
        "openings": 5,
        "salary": "4-6 LPA",
        "work_mode": "Hybrid",
        "department": "Cloud Operations",
        "industry_type": "Cloud Services",
    },
    {
        "title": "Pending Data Analyst",
        "company": "ReviewQueue Analytics",
        "description": "Pending admin approval for analytics hiring.",
        "location": "Chennai",
        "type": "Full-time",
        "experience_required": "1-2 years",
        "skills_required": "SQL, Python, Power BI",
        "preferred_skills": "Statistics, Excel",
        "openings": 1,
        "salary": "5-7 LPA",
        "work_mode": "Hybrid",
        "department": "Analytics",
        "industry_type": "Consulting",
        "is_approved": False,
    },
]

jobs = []
for offset, data in enumerate(job_rows):
    job = db.query(Job).filter(Job.title == data["title"], Job.company == data["company"]).first()
    if not job:
        job = Job(**data, posted_by_id=employer.id, created_at=utcnow() - timedelta(days=offset * 3))
        db.add(job)
        db.commit()
        db.refresh(job)
    jobs.append(job)

application_statuses = ["Applied", "Under Review", "Shortlisted"]
for index, job in enumerate(jobs[:3]):
    application = db.query(Application).filter(Application.user_id == seeker.id, Application.job_id == job.id).first()
    if not application:
        db.add(Application(
            user_id=seeker.id,
            job_id=job.id,
            cover_letter=f"I am interested in the {job.title} role.",
            status=application_statuses[index],
            applied_at=utcnow() - timedelta(days=9 - index * 3),
        ))

for index, job in enumerate(jobs[1:]):
    saved = db.query(SavedJob).filter(SavedJob.user_id == seeker.id, SavedJob.job_id == job.id).first()
    if not saved:
        db.add(SavedJob(
            user_id=seeker.id,
            job_id=job.id,
            saved_at=utcnow() - timedelta(days=6 - index),
        ))

alert = db.query(JobAlert).filter(JobAlert.user_id == seeker.id, JobAlert.keyword == "React").first()
if not alert:
    db.add(JobAlert(user_id=seeker.id, keyword="React", location="Bengaluru", category="Engineering", frequency="Daily"))

interview = db.query(Interview).filter(Interview.seeker_id == seeker.id, Interview.job_id == jobs[0].id).first()
if not interview:
    db.add(Interview(
        job_id=jobs[0].id,
        seeker_id=seeker.id,
        employer_id=employer.id,
        title="Frontend React Developer Interview",
        description="Technical discussion with the frontend team.",
        scheduled_at=utcnow() + timedelta(days=2, hours=3),
        duration_minutes=45,
        status="Scheduled",
    ))

notification = db.query(Notification).filter(Notification.user_id == seeker.id, Notification.title == "Interview Scheduled").first()
if not notification:
    db.add(Notification(
        user_id=seeker.id,
        title="Interview Scheduled",
        message="Your frontend interview has been scheduled.",
        type="interview",
        is_read=False,
    ))

message = db.query(ChatMessage).filter(ChatMessage.sender_id == employer.id, ChatMessage.receiver_id == seeker.id).first()
if not message:
    db.add(ChatMessage(
        sender_id=employer.id,
        receiver_id=seeker.id,
        message="Hi Priya, your profile looks relevant for our React role.",
        is_read=False,
    ))

settings = {
    "headline": "Cloudfire: Direct Access to Elite Talent",
    "support_email": "support@cloudfire.com",
    "maintenance": "OFF",
}
for key, value in settings.items():
    setting = db.query(SiteSetting).filter(SiteSetting.key == key).first()
    if not setting:
        db.add(SiteSetting(key=key, value=value))

audit_log = db.query(AuditLog).filter(AuditLog.action == "SEED_DASHBOARD_DATA").first()
if not audit_log:
    db.add(AuditLog(
        admin_id=admin.id,
        action="SEED_DASHBOARD_DATA",
        target_type="system",
        details="Inserted local dashboard demo data for job seeker, employer, and admin dashboards.",
    ))

db.commit()
db.close()

print("Dashboard seed data is ready.")
print("Login as jobseeker@cloudfire.com with password TestPass@123")
