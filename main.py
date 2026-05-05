from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
import shutil
import uuid
import os
import random
from datetime import datetime, timedelta
from database import get_db, User, Job, ChatMessage, Interview, Notification, JobAlert, Application, SavedJob, AuditLog, SiteSetting

from mail_utils import send_otp_email, send_notification_email
from auth import get_password_hash, verify_password, create_access_token, create_refresh_token, create_pending_token, verify_pending_token, SECRET_KEY, ALGORITHM
from jose import jwt, JWTError

app = FastAPI(title="Cloudfire IT Services API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    from database import Base, engine
    Base.metadata.create_all(bind=engine)


# Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    print(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        print(f"Response status: {response.status_code} (Duration: {duration:.4f}s)")
        return response
    except Exception as e:
        duration = time.time() - start_time
        print(f"Unhandled error during request: {str(e)} (Duration: {duration:.4f}s)")
        import traceback
        traceback.print_exc()
        raise



from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"Validation error: {exc.errors()}")
    print(f"Request body: {await request.body()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(await request.body())},
    )

# Authentication Dependency
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        if token.startswith("Bearer "):
            token = token[7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Pydantic models
class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[str] = None
    bio: Optional[str] = None
    resume_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_profile_public: Optional[bool] = None
    search_status: Optional[str] = None

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    mobile: str
    work_status: str
    role: str = "jobseeker"

class VerifyOTP(BaseModel):
    token: str
    otp: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    role: str

class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    full_name: str
    email: str
    mobile: Optional[str] = None
    role: str
    work_status: Optional[str] = None
    education: Optional[str] = None
    experience: Optional[str] = None
    skills: Optional[str] = None
    bio: Optional[str] = None
    resume_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    is_profile_public: bool = True
    search_status: str = "Actively Looking"

class JobCreate(BaseModel):
    title: str
    company: str
    description: Optional[str] = None
    location: str
    type: str
    experience_required: Optional[str] = None
    skills_required: Optional[str] = None
    openings: Optional[int] = None
    salary: str
    perks: Optional[str] = None
    education_qualification: Optional[str] = None
    preferred_skills: Optional[str] = None
    certifications: Optional[str] = None
    deadline: Optional[str] = None
    application_method: Optional[str] = None
    application_email: Optional[str] = None
    application_link: Optional[str] = None
    hr_name: Optional[str] = None
    hr_phone: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    company_logo_url: Optional[str] = None
    work_mode: Optional[str] = None
    shift_timing: Optional[str] = None
    notice_period: Optional[str] = None
    gender_preference: Optional[str] = None
    industry_type: Optional[str] = None
    department: Optional[str] = None

class ContactSeeker(BaseModel):
    seeker_email: str
    message: str

class ApplyJob(BaseModel):
    job_id: int
    cover_letter: Optional[str] = None

class SavedJobCreate(BaseModel):
    job_id: int

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

class SendMessage(BaseModel):
    receiver_id: int
    message: str

class ScheduleInterview(BaseModel):
    job_id: int
    seeker_id: int
    title: str
    description: Optional[str] = None
    scheduled_at: str # ISO format
    duration_minutes: int = 30
    meeting_link: Optional[str] = None

class CreateJobAlert(BaseModel):
    keyword: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    min_salary: Optional[str] = None
    frequency: str = "Daily"

class SubmitAssessment(BaseModel):
    skill: str
    score: int
    total_questions: int

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    type: Optional[str] = None
    experience_required: Optional[str] = None
    skills_required: Optional[str] = None
    openings: Optional[int] = None
    salary: Optional[str] = None
    perks: Optional[str] = None
    education_qualification: Optional[str] = None
    preferred_skills: Optional[str] = None
    certifications: Optional[str] = None
    deadline: Optional[str] = None
    application_method: Optional[str] = None
    application_email: Optional[str] = None
    application_link: Optional[str] = None
    hr_name: Optional[str] = None
    hr_phone: Optional[str] = None
    company_description: Optional[str] = None
    company_website: Optional[str] = None
    company_logo_url: Optional[str] = None
    work_mode: Optional[str] = None
    shift_timing: Optional[str] = None
    notice_period: Optional[str] = None
    gender_preference: Optional[str] = None
    industry_type: Optional[str] = None
    department: Optional[str] = None

class UpdateSiteSetting(BaseModel):
    key: str
    value: str

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


# Routes
@app.get("/")
async def root():
    return {"status": "ok", "message": "Cloudfire IT Services API is running"}

@app.get("/health")
async def health_check():
    return {"status": "alive", "timestamp": datetime.utcnow()}

@app.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "full_name": current_user.full_name,
        "email": current_user.email,
        "mobile": current_user.mobile,
        "role": current_user.role,
        "work_status": current_user.work_status,
        "education": current_user.education,
        "experience": current_user.experience,
        "skills": current_user.skills,
        "bio": current_user.bio,
        "resume_url": current_user.resume_url,
        "profile_image_url": current_user.profile_image_url,
        "is_profile_public": current_user.is_profile_public,
        "search_status": current_user.search_status
    }

@app.put("/profile")
async def update_profile(profile_data: ProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    await send_notification_email(
        current_user.email,
        "Profile Updated",
        f"Hello {current_user.full_name}, your profile has been successfully updated on Cloudfire IT Services."
    )
    return {"message": "Profile updated successfully"}

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = f"uploads/resumes/{file_name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    current_user.resume_url = f"{BASE_URL}/{file_path}"
    db.commit()
    return {"url": current_user.resume_url}

@app.post("/upload-image")
async def upload_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = f"uploads/images/{file_name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    current_user.profile_image_url = f"{BASE_URL}/{file_path}"
    db.commit()
    return {"url": current_user.profile_image_url}

# Mount uploads directory
if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

def _split_csv(value: Optional[str]):
    if not value:
        return []
    return [item.strip().lower() for item in value.split(",") if item.strip()]

def _job_to_dict(job: Job):
    data = job.__dict__.copy()
    data.pop("_sa_instance_state", None)
    return data

def _build_recommended_jobs(current_user: User, jobs: List[Job], limit: int = 4):
    user_skills = set(_split_csv(current_user.skills))
    recommendations = []

    for job in jobs:
        required_skills = set(_split_csv(job.skills_required))
        preferred_skills = set(_split_csv(job.preferred_skills))
        all_job_skills = required_skills | preferred_skills
        matched_skills = sorted(user_skills & all_job_skills)

        score = 0
        if matched_skills:
            score += len(matched_skills) * 20
        if current_user.work_status and job.experience_required:
            if current_user.work_status.lower() in job.experience_required.lower():
                score += 15
        if current_user.location and job.location:
            if current_user.location.lower() in job.location.lower() or job.location.lower() in current_user.location.lower():
                score += 10
        if job.created_at:
            score += max(0, 10 - (datetime.utcnow() - job.created_at).days)

        job_data = _job_to_dict(job)
        job_data["match_score"] = min(score, 100)
        job_data["matched_skills"] = matched_skills[:5]
        recommendations.append(job_data)

    recommendations.sort(key=lambda item: (item["match_score"], item.get("created_at") or datetime.min), reverse=True)
    return recommendations[:limit]

def _weekly_activity(applications: List[Application], saved_jobs: List[SavedJob], interviews: List[Interview]):
    today = datetime.utcnow().date()
    start = today - timedelta(days=27)
    rows = []

    for index in range(4):
        week_start = start + timedelta(days=index * 7)
        week_end = week_start + timedelta(days=6)
        rows.append({
            "name": f"Week {index + 1}" if index < 3 else "This Week",
            "applications": len([item for item in applications if item.applied_at and week_start <= item.applied_at.date() <= week_end]),
            "saved": len([item for item in saved_jobs if item.saved_at and week_start <= item.saved_at.date() <= week_end]),
            "interviews": len([item for item in interviews if item.scheduled_at and week_start <= item.scheduled_at.date() <= week_end]),
        })

    return rows

def _daily_job_activity(applications: List[Application], saved_jobs: List[SavedJob]):
    today = datetime.utcnow().date()
    rows = []

    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        rows.append({
            "name": day.strftime("%a"),
            "applications": len([item for item in applications if item.applied_at and item.applied_at.date() == day]),
            "saved": len([item for item in saved_jobs if item.saved_at and item.saved_at.date() == day]),
        })

    return rows

def _top_skills_from_users(users: List[User], limit: int = 8):
    counts = {}
    for user in users:
        for skill in _split_csv(user.skills):
            label = skill.title()
            counts[label] = counts.get(label, 0) + 1
    return [
        {"name": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]

def _top_skills_from_jobs(jobs: List[Job], limit: int = 8):
    counts = {}
    for job in jobs:
        for skill in _split_csv(job.skills_required) + _split_csv(job.preferred_skills):
            label = skill.title()
            counts[label] = counts.get(label, 0) + 1
    return [
        {"name": name, "count": count}
        for name, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
    ]

def _user_growth(users: List[User]):
    ordered = sorted(users, key=lambda user: user.id or 0)
    labels = ["Start", "20%", "40%", "60%", "80%", "Now"]
    if not ordered:
        return [{"name": label, "users": 0} for label in labels]
    return [
        {"name": label, "users": max(1, round(len(ordered) * (index + 1) / len(labels)))}
        for index, label in enumerate(labels)
    ]

def _monthly_platform_activity(applications: List[Application], jobs: List[Job], interviews: List[Interview]):
    rows = []
    today = datetime.utcnow().date()
    for offset in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=offset * 31)).replace(day=1)
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        rows.append({
            "name": month_start.strftime("%b"),
            "jobs": len([job for job in jobs if job.created_at and month_start <= job.created_at.date() < next_month]),
            "applications": len([app_item for app_item in applications if app_item.applied_at and month_start <= app_item.applied_at.date() < next_month]),
            "interviews": len([item for item in interviews if item.scheduled_at and month_start <= item.scheduled_at.date() < next_month]),
        })
    return rows

def _employer_daily_activity(jobs: List[Job], applications: List[Application]):
    today = datetime.utcnow().date()
    rows = []
    job_ids = {job.id for job in jobs}
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        rows.append({
            "name": day.strftime("%a"),
            "jobs": len([job for job in jobs if job.created_at and job.created_at.date() == day]),
            "applications": len([item for item in applications if item.job_id in job_ids and item.applied_at and item.applied_at.date() == day]),
        })
    return rows

@app.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = current_user.role
    
    if role == "admin":
        total_users = db.query(func.count(User.id)).scalar()
        total_jobseekers = db.query(func.count(User.id)).filter(User.role == "jobseeker").scalar()
        total_employers = db.query(func.count(User.id)).filter(User.role == "employer").scalar()
        total_admins = db.query(func.count(User.id)).filter(User.role == "admin").scalar()
        
        active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
        inactive_users = total_users - active_users
        
        profiles_with_resume = db.query(func.count(User.id)).filter(User.role == "jobseeker", User.resume_url != None).scalar()
        
        total_jobs = db.query(func.count(Job.id)).scalar()
        approved_jobs = db.query(func.count(Job.id)).filter(Job.is_approved == True).scalar()
        pending_jobs_count = total_jobs - approved_jobs
        
        total_applications = db.query(func.count(Application.id)).scalar()
        total_interviews = db.query(func.count(Interview.id)).scalar()
        
        pending_employers = db.query(func.count(User.id)).filter(User.role == "employer", User.is_verified == False).scalar()
        unread_notifications = db.query(func.count(Notification.id)).filter(Notification.is_read == False).scalar()
        
        # Still need some actual data for lists
        recent_jobs_raw = db.query(Job).order_by(Job.created_at.desc()).limit(5).all()
        recent_jobs = []
        for job in recent_jobs_raw:
            job_data = _job_to_dict(job)
            job_data["application_count"] = db.query(func.count(Application.id)).filter(Application.job_id == job.id).scalar()
            recent_jobs.append(job_data)
            
        # Charts data (these still use lists for now, but could be optimized further)
        all_users = db.query(User).all()
        all_jobs = db.query(Job).all()
        all_applications = db.query(Application).all()
        all_interviews = db.query(Interview).all()

        return {
            "role": "admin",
            "total_users": total_users,
            "total_jobseekers": total_jobseekers,
            "total_employers": total_employers,
            "total_admins": total_admins,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "profiles_with_resume": profiles_with_resume,
            "total_jobs": total_jobs,
            "approved_jobs": approved_jobs,
            "pending_jobs": pending_jobs_count,
            "total_applications": total_applications,
            "total_interviews": total_interviews,
            "pending_employers": pending_employers,
            "unread_notifications": unread_notifications,
            "role_distribution": [
                {"name": "Job Seekers", "value": total_jobseekers},
                {"name": "Employers", "value": total_employers},
                {"name": "Admins", "value": total_admins},
            ],
            "activity_distribution": [
                {"name": "Active", "value": active_users},
                {"name": "Inactive", "value": inactive_users},
            ],
            "platform_activity": _monthly_platform_activity(all_applications, all_jobs, all_interviews),
            "top_job_skills": _top_skills_from_jobs(all_jobs),
            "user_growth": _user_growth(all_users),
            "recent_users": [
                {
                    "id": u.id,
                    "full_name": u.full_name,
                    "email": u.email,
                    "role": u.role,
                    "is_active": u.is_active,
                    "is_verified": u.is_verified,
                }
                for u in sorted(all_users, key=lambda x: x.id, reverse=True)[:6]
            ],
            "recent_jobs": recent_jobs,
        }
    elif role == "employer":
        employer_jobs = db.query(Job).filter(Job.posted_by_id == current_user.id).order_by(Job.created_at.desc()).all()
        employer_job_ids = {job.id for job in employer_jobs}
        employer_applications = [
            application for application in all_applications
            if application.job_id in employer_job_ids
        ]
        upcoming_interviews = [
            interview for interview in all_interviews
            if interview.employer_id == current_user.id and interview.scheduled_at and interview.scheduled_at >= datetime.utcnow()
        ]
        recent_applications = []
        for application in employer_applications[:6]:
            job = db.query(Job).filter(Job.id == application.job_id).first()
            seeker = db.query(User).filter(User.id == application.user_id).first()
            if job and seeker:
                recent_applications.append({
                    "id": application.id,
                    "job_id": job.id,
                    "job_title": job.title,
                    "company": job.company,
                    "status": application.status,
                    "applied_at": application.applied_at,
                    "candidate": {
                        "id": seeker.id,
                        "full_name": seeker.full_name,
                        "email": seeker.email,
                        "skills": seeker.skills,
                        "resume_url": seeker.resume_url,
                        "profile_image_url": seeker.profile_image_url,
                    },
                })
        job_cards = []
        for job in employer_jobs[:5]:
            job_data = _job_to_dict(job)
            job_data["application_count"] = len([item for item in employer_applications if item.job_id == job.id])
            job_cards.append(job_data)

        return {
            "role": "employer",
            "available_talent": len(jobseekers),
            "talent_with_resume": len([u for u in jobseekers if u.resume_url]),
            "talent_with_skills": len([u for u in jobseekers if u.skills]),
            "total_employers": len(employers),
            "posted_jobs": len(employer_jobs),
            "approved_jobs": len([job for job in employer_jobs if job.is_approved]),
            "pending_jobs": len([job for job in employer_jobs if not job.is_approved]),
            "total_applications": len(employer_applications),
            "upcoming_interviews_count": len(upcoming_interviews),
            "unread_messages": db.query(ChatMessage).filter(ChatMessage.receiver_id == current_user.id, ChatMessage.is_read == False).count(),
            "candidate_status": [
                {"name": "Fresher", "value": len([u for u in jobseekers if (u.work_status or "").lower() == "fresher"])},
                {"name": "Experienced", "value": len([u for u in jobseekers if (u.work_status or "").lower() == "experienced"])},
                {"name": "Other", "value": len([u for u in jobseekers if (u.work_status or "").lower() not in ["fresher", "experienced"]])},
            ],
            "application_status": [
                {"name": status_name, "value": len([item for item in employer_applications if item.status == status_name])}
                for status_name in ["Applied", "Under Review", "Shortlisted", "Rejected", "Hired"]
            ],
            "daily_activity": _employer_daily_activity(employer_jobs, employer_applications),
            "top_candidate_skills": _top_skills_from_users(jobseekers),
            "recent_applications": recent_applications,
            "recent_jobs": job_cards,
        }
    else:
        profile_field_map = {
            "Full name": current_user.full_name,
            "Mobile": current_user.mobile,
            "Education": current_user.education,
            "Experience": current_user.experience,
            "Skills": current_user.skills,
            "Bio": current_user.bio,
            "Resume": current_user.resume_url,
            "Location": current_user.location,
            "Availability": current_user.availability,
        }
        filled = len([value for value in profile_field_map.values() if value])

        applications = db.query(Application).filter(Application.user_id == current_user.id).order_by(Application.applied_at.desc()).all()
        saved_jobs = db.query(SavedJob).filter(SavedJob.user_id == current_user.id).order_by(SavedJob.saved_at.desc()).all()
        interviews = db.query(Interview).filter(Interview.seeker_id == current_user.id).order_by(Interview.scheduled_at.asc()).all()
        job_alerts = db.query(JobAlert).filter(JobAlert.user_id == current_user.id).all()
        unread_messages = db.query(ChatMessage).filter(ChatMessage.receiver_id == current_user.id, ChatMessage.is_read == False).count()
        unread_notifications = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).count()
        approved_jobs = db.query(Job).filter(Job.is_approved == True).order_by(Job.created_at.desc()).all()
        applied_job_ids = {application.job_id for application in applications}
        saved_job_ids = {saved.job_id for saved in saved_jobs}
        open_jobs = [job for job in approved_jobs if job.id not in applied_job_ids]

        recent_applications = []
        for application in applications[:4]:
            job = db.query(Job).filter(Job.id == application.job_id).first()
            if job:
                recent_applications.append({
                    "id": application.id,
                    "job_id": job.id,
                    "job_title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "status": application.status,
                    "applied_at": application.applied_at,
                })

        saved_job_cards = []
        for saved in saved_jobs[:4]:
            job = db.query(Job).filter(Job.id == saved.job_id).first()
            if job:
                job_data = _job_to_dict(job)
                job_data["saved_at"] = saved.saved_at
                saved_job_cards.append(job_data)

        upcoming_interviews = []
        for interview in [item for item in interviews if item.scheduled_at and item.scheduled_at >= datetime.utcnow()][:3]:
            job = db.query(Job).filter(Job.id == interview.job_id).first()
            employer = db.query(User).filter(User.id == interview.employer_id).first()
            upcoming_interviews.append({
                "id": interview.id,
                "title": interview.title,
                "job_title": job.title if job else "N/A",
                "company": job.company if job else "N/A",
                "employer_name": employer.full_name if employer else "Recruiter",
                "scheduled_at": interview.scheduled_at,
                "duration_minutes": interview.duration_minutes,
                "status": interview.status,
            })

        return {
            "role": "jobseeker",
            "profile_completeness": round((filled / len(profile_field_map)) * 100),
            "profile_missing_fields": [label for label, value in profile_field_map.items() if not value],
            "has_resume": bool(current_user.resume_url),
            "has_skills": bool(current_user.skills),
            "total_employers": len(employers),
            "total_jobseekers": len(jobseekers),
            "total_open_jobs": len(approved_jobs),
            "total_applications": len(applications),
            "total_saved_jobs": len(saved_jobs),
            "total_interviews": len(interviews),
            "upcoming_interviews_count": len([item for item in interviews if item.scheduled_at and item.scheduled_at >= datetime.utcnow()]),
            "job_alerts_count": len(job_alerts),
            "unread_messages": unread_messages,
            "unread_notifications": unread_notifications,
            "weekly_activity": _weekly_activity(applications, saved_jobs, interviews),
            "daily_job_activity": _daily_job_activity(applications, saved_jobs),
            "application_status": [
                {"name": status_name, "value": len([item for item in applications if item.status == status_name])}
                for status_name in ["Applied", "Under Review", "Shortlisted", "Rejected", "Hired"]
            ],
            "recent_applications": recent_applications,
            "saved_jobs": saved_job_cards,
            "upcoming_interviews": upcoming_interviews,
            "recommended_jobs": _build_recommended_jobs(current_user, open_jobs, limit=4),
            "saved_job_ids": list(saved_job_ids),
        }

@app.get("/notifications")
async def get_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Fetch real notifications from DB
    db_notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).limit(20).all()
    
    result = []
    for n in db_notifications:
        result.append({
            "id": n.id,
            "title": n.title,
            "message": n.message,
            "time": n.created_at.strftime("%Y-%m-%d %H:%M"),
            "icon": "🔔" if n.type == "alert" else "💼" if n.type == "application" else "📅" if n.type == "interview" else "💬",
            "priority": "high" if not n.is_read else "low",
            "is_read": n.is_read,
            "type": n.type
        })
    
    # Add a welcome notification if no others exist
    if not result:
        result.append({
            "id": "welcome",
            "title": f"Welcome back, {current_user.full_name.split(' ')[0]}!",
            "time": "Just now",
            "icon": "👋",
            "priority": "low",
            "is_read": False,
            "type": "alert"
        })
        
    return result

@app.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if notification:
        notification.is_read = True
        db.commit()
    return {"message": "Notification marked as read"}

@app.get("/jobs")
async def get_jobs(db: Session = Depends(get_db)):
    try:
        jobs = db.query(Job).all()
        return jobs
    except Exception as e:
        print(f"Error fetching jobs: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/jobs")
async def post_job(job_data: JobCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["employer", "admin"]:
        raise HTTPException(status_code=403, detail="Only employers and admins can post jobs")
    new_job = Job(
        **job_data.model_dump(),
        posted_by_id=current_user.id
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    await send_notification_email(
        current_user.email,
        "Job Posted Successfully",
        f"Hello {current_user.full_name}, you have successfully posted a new job: {new_job.title} at {new_job.company}."
    )
    
    return new_job

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["employer", "admin"]:
        raise HTTPException(status_code=403, detail="Only employers and admins can delete jobs")
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Employers can only delete their own jobs, admins can delete any
    if current_user.role == "employer" and job.posted_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete jobs you posted")
    
    job_title = job.title
    db.delete(job)
    db.commit()
    
    await send_notification_email(
        current_user.email,
        "Job Removed",
        f"Hello {current_user.full_name}, the job '{job_title}' has been successfully removed."
    )
    
    return {"message": "Job deleted successfully"}

@app.put("/jobs/{job_id}")
async def update_job(job_id: int, job_data: JobUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["employer", "admin"]:
        raise HTTPException(status_code=403, detail="Only employers and admins can edit jobs")
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if current_user.role == "employer" and job.posted_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit jobs you posted")
        
    for field, value in job_data.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
        
    db.commit()
    db.refresh(job)
    return job

@app.get("/employer/jobs")
async def get_employer_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "employer":
        raise HTTPException(status_code=403, detail="Permission denied")
    
    jobs = db.query(Job).filter(Job.posted_by_id == current_user.id).all()
    from database import Application
    
    result = []
    for job in jobs:
        app_count = db.query(Application).filter(Application.job_id == job.id).count()
        job_dict = job.__dict__.copy()
        job_dict["application_count"] = app_count
        result.append(job_dict)
        
    return result

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_email = user.email
    user_name = user.full_name
    db.delete(user)
    db.commit()
    
    await send_notification_email(
        current_user.email, # Notify admin
        "User Account Removed",
        f"Admin, you have successfully removed the user account for {user_name} ({user_email})."
    )
    
    return {"message": "User deleted successfully"}

@app.delete("/account")
async def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted successfully"}

@app.put("/change-password")
async def change_password(data: ChangePassword, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    current_user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@app.post("/contact-seeker")
async def contact_seeker(data: ContactSeeker, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["employer", "admin"]:
        raise HTTPException(status_code=403, detail="Only employers can contact seekers")
    
    seeker = db.query(User).filter(User.email == data.seeker_email).first()
    if not seeker:
        raise HTTPException(status_code=404, detail="Job seeker not found")
    
    # Send email to seeker
    await send_notification_email(
        seeker.email,
        f"New message from {current_user.full_name} via Cloudfire",
        f"Hello {seeker.full_name},<br><br>{current_user.full_name} ({current_user.email}) from Cloudfire wants to connect with you.<br><br><strong>Message:</strong><br>{data.message}<br><br>You can reply directly to this employer at: <strong>{current_user.email}</strong>"
    )
    # Notify employer too
    await send_notification_email(
        current_user.email,
        "Contact Request Sent",
        f"Hello {current_user.full_name}, your message has been sent to {seeker.full_name} ({seeker.email}) successfully."
    )
    
    return {"message": f"Message sent to {seeker.full_name} successfully"}

@app.post("/apply-job")
async def apply_to_job(data: ApplyJob, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "jobseeker":
        raise HTTPException(status_code=403, detail="Only job seekers can apply to jobs")
    
    job = db.query(Job).filter(Job.id == data.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Find the employer who posted the job
    employer = db.query(User).filter(User.id == job.posted_by_id).first()
    employer_email = employer.email if employer else None
    
    # Build resume info
    resume_info = f"<br><strong>Resume:</strong> <a href='{current_user.resume_url}'>View Resume</a>" if current_user.resume_url else "<br><em>No resume uploaded</em>"
    cover = f"<br><br><strong>Cover Letter:</strong><br>{data.cover_letter}" if data.cover_letter else ""
    
    # Email the employer
    if employer_email:
        await send_notification_email(
            employer_email,
            f"New Application for {job.title}",
            f"Hello,<br><br><strong>{current_user.full_name}</strong> ({current_user.email}) has applied for the position of <strong>{job.title}</strong> at <strong>{job.company}</strong>.{resume_info}{cover}<br><br>Contact the applicant at: <strong>{current_user.email}</strong> | Phone: <strong>{current_user.mobile or 'N/A'}</strong>"
        )
    
    # Confirm to jobseeker
    await send_notification_email(
        current_user.email,
        f"Application Submitted: {job.title}",
        f"Hello {current_user.full_name}, you have successfully applied for the position of <strong>{job.title}</strong> at <strong>{job.company}</strong>. The employer will review your application and contact you if interested."
    )
    
    from database import Application
    new_app = Application(
        user_id=current_user.id,
        job_id=job.id,
        cover_letter=data.cover_letter,
        status="Applied"
    )
    db.add(new_app)
    
    # Notify employer
    notification = Notification(
        user_id=job.posted_by_id,
        title=f"New Application for {job.title}",
        message=f"{current_user.full_name} has applied for your job posting.",
        type="application"
    )
    db.add(notification)
    
    db.commit()
    
    return {"message": f"Successfully applied for {job.title} at {job.company}"}

class UpdateApplicationStatus(BaseModel):
    status: str

@app.post("/applications/{application_id}/status")
async def update_app_status(application_id: int, data: UpdateApplicationStatus, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    app_item = db.query(Application).filter(Application.id == application_id).first()
    if not app_item:
        raise HTTPException(status_code=404, detail="Application not found")
    
    job = db.query(Job).filter(Job.id == app_item.job_id).first()
    if not job or (job.posted_by_id != current_user.id and current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    app_item.status = data.status
    
    # Notify seeker
    notification = Notification(
        user_id=app_item.user_id,
        title=f"Application Update: {job.title}",
        message=f"Your application status for {job.title} has been updated to '{data.status}'.",
        type="application"
    )
    db.add(notification)
    
    db.commit()
    return {"message": f"Application status updated to {data.status}"}

@app.get("/applications")
async def get_applications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "jobseeker":
        raise HTTPException(status_code=403, detail="Permission denied")
    apps = db.query(Application).filter(Application.user_id == current_user.id).all()
    result = []
    for app_ in apps:
        job = db.query(Job).filter(Job.id == app_.job_id).first()
        if job:
            app_dict = app_.__dict__.copy()
            app_dict["job_title"] = job.title
            app_dict["company"] = job.company
            app_dict["location"] = job.location
            result.append(app_dict)
    return result

@app.post("/saved-jobs")
async def save_job(data: SavedJobCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "jobseeker":
        raise HTTPException(status_code=403, detail="Permission denied")
    existing = db.query(SavedJob).filter(SavedJob.user_id == current_user.id, SavedJob.job_id == data.job_id).first()
    if existing:
        return {"message": "Job already saved"}
    
    new_saved = SavedJob(user_id=current_user.id, job_id=data.job_id)
    db.add(new_saved)
    db.commit()
    return {"message": "Job saved successfully"}

@app.get("/saved-jobs")
async def get_saved_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "jobseeker":
        raise HTTPException(status_code=403, detail="Permission denied")
    saved = db.query(SavedJob).filter(SavedJob.user_id == current_user.id).all()
    result = []
    for s in saved:
        job = db.query(Job).filter(Job.id == s.job_id).first()
        if job:
            result.append(job)
    return result

@app.delete("/saved-jobs/{job_id}")
async def remove_saved_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "jobseeker":
        raise HTTPException(status_code=403, detail="Permission denied")
    saved = db.query(SavedJob).filter(SavedJob.user_id == current_user.id, SavedJob.job_id == job_id).first()
    if saved:
        db.delete(saved)
        db.commit()
    return {"message": "Saved job removed"}

@app.get("/employer/jobseekers")
async def get_all_jobseekers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if str(current_user.role).lower() not in ["employer", "admin"]:
        raise HTTPException(status_code=403, detail="Permission denied")
    return db.query(User).filter(User.role == "jobseeker").all()

@app.get("/admin/all-users")
async def get_all_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return db.query(User).all()

@app.post("/signup")
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    normalized_email = user_data.email.strip().lower()
    normalized_mobile = user_data.mobile.strip()
    normalized_full_name = user_data.full_name.strip()

    db_user = db.query(User).filter(User.email.ilike(normalized_email)).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="This email already exists. Please log in or use a different email.",
        )
    
    hashed_pwd = get_password_hash(user_data.password)
    
    new_user = User(
        email=normalized_email,
        full_name=normalized_full_name,
        mobile=normalized_mobile,
        role=user_data.role,
        work_status=user_data.work_status.strip(),
        hashed_password=hashed_pwd,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    try:
        await send_notification_email(
            new_user.email,
            "Welcome to Cloudfire IT Services",
            f"Hello {new_user.full_name}, your account has been successfully created. Welcome to our platform!"
        )
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")
        
    access_token = create_access_token(data={"sub": new_user.email, "role": new_user.role})
    refresh_token = create_refresh_token(new_user.email)
    return {
        "message": "Account created successfully!", 
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer", 
        "role": new_user.role
    }

@app.post("/verify-otp")
async def verify_otp(data: VerifyOTP, db: Session = Depends(get_db)):
    payload = verify_pending_token(data.token)
    if not payload:
        raise HTTPException(status_code=400, detail="Session expired")
    if payload.get("otp") != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    email = payload.get("email")
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(
        email=email,
        full_name=payload.get("full_name"),
        mobile=payload.get("mobile"),
        role=payload.get("role"),
        work_status=payload.get("work_status"),
        hashed_password=payload.get("hashed_password"),
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    await send_notification_email(
        new_user.email,
        "Welcome to Cloudfire IT Services",
        f"Hello {new_user.full_name}, your account has been successfully verified and created. Welcome to our platform!"
    )
    
    access_token = create_access_token(data={"sub": new_user.email, "role": new_user.role})
    refresh_token = create_refresh_token(new_user.email)
    return {
        "message": "Account created!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": new_user.role,
    }

@app.post("/forgot-password")
async def forgot_password(email: EmailStr, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User with this email does not exist")
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    user.otp = otp
    user.otp_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.commit()
    try:
        await send_otp_email(email, otp)
        return {"message": "Password reset OTP sent to your email."}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to send reset OTP email right now. Please try again in a moment.",
        )

@app.post("/reset-password")
async def reset_password(email: EmailStr, otp: str, new_password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or user.otp != otp or datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    user.hashed_password = get_password_hash(new_password)
    user.otp = None
    user.otp_expiry = None
    db.commit()
    return {"message": "Password reset successful!"}

@app.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        # Normalize email to match signup logic
        normalized_email = user_data.email.strip().lower()
        user = db.query(User).filter(User.email == normalized_email).first()
        
        if not user or not verify_password(user_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Please verify your email first")
        
        # Ensure role is a string (fallback to jobseeker if None)
        user_role = str(user.role) if user.role else "jobseeker"
        
        access_token = create_access_token(data={"sub": user.email, "role": user_role})
        refresh_token = create_refresh_token(user.email)
        return {
            "access_token": access_token, 
            "refresh_token": refresh_token,
            "token_type": "bearer", 
            "role": user_role
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

class RefreshRequest(BaseModel):
    refresh_token: str

@app.post("/refresh")
async def refresh_access_token(data: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
            
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.is_active:
            raise HTTPException(status_code=401, detail="User is inactive")
            
        new_access_token = create_access_token(data={"sub": user.email, "role": user.role})
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate refresh token")
@app.post("/admin/verify-employer/{user_id}")
async def verify_employer(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_verified = True
    log = AuditLog(admin_id=current_user.id, action="VERIFY_EMPLOYER", target_id=user_id, target_type="user", details=f"Verified employer {user.full_name}")
    db.add(log)
    
    # Notify user
    notification = Notification(
        user_id=user.id,
        title="Account Verified",
        message="Your employer account has been successfully verified by the admin.",
        type="alert"
    )
    db.add(notification)
    
    db.commit()
    return {"message": "Employer verified successfully"}

@app.post("/admin/approve-job/{job_id}")
async def approve_job(job_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_approved = True
    log = AuditLog(admin_id=current_user.id, action="APPROVE_JOB", target_id=job_id, target_type="job", details=f"Approved job {job.title}")
    db.add(log)
    
    # Notify employer
    notification = Notification(
        user_id=job.posted_by_id,
        title="Job Approved",
        message=f"Your job posting '{job.title}' has been approved and is now live.",
        type="alert"
    )
    db.add(notification)
    
    db.commit()
    return {"message": "Job approved successfully"}

@app.get("/admin/audit-logs")
async def get_audit_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()

@app.get("/admin/revenue")
async def get_revenue_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return [
        {"month": "Jan", "revenue": 1200},
        {"month": "Feb", "revenue": 2100},
        {"month": "Mar", "revenue": 1800},
        {"month": "Apr", "revenue": 3500},
        {"month": "May", "revenue": 4200},
    ]

@app.get("/admin/settings")
async def get_site_settings(db: Session = Depends(get_db)):
    return db.query(SiteSetting).all()

@app.post("/admin/settings")
async def update_site_setting(data: UpdateSiteSetting, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    setting = db.query(SiteSetting).filter(SiteSetting.key == data.key).first()
    if setting:
        setting.value = data.value
    else:
        setting = SiteSetting(key=data.key, value=data.value)
        db.add(setting)
    log = AuditLog(admin_id=current_user.id, action="UPDATE_SETTING", target_type="setting", details=f"Updated {data.key}")
    db.add(log)
    db.commit()
    return {"message": "Setting updated"}

@app.get("/search")
async def global_search(q: str, db: Session = Depends(get_db)):
    # Search jobs
    jobs = db.query(Job).filter(
        (Job.title.ilike(f"%{q}%")) | 
        (Job.company.ilike(f"%{q}%")) | 
        (Job.skills_required.ilike(f"%{q}%")) |
        (Job.description.ilike(f"%{q}%")) |
        (Job.location.ilike(f"%{q}%")) |
        (Job.experience_required.ilike(f"%{q}%")) |
        (Job.type.ilike(f"%{q}%"))
    ).limit(20).all()
    
    # Search talents (jobseekers)
    talents = db.query(User).filter(
        (User.role == "jobseeker"),
        (User.is_active == True),
        (
            (User.full_name.ilike(f"%{q}%")) | 
            (User.skills.ilike(f"%{q}%")) |
            (User.bio.ilike(f"%{q}%")) |
            (User.location.ilike(f"%{q}%")) |
            (User.work_status.ilike(f"%{q}%")) |
            (User.education.ilike(f"%{q}%"))
        )
    ).limit(20).all()
    
    return {
        "jobs": jobs,
        "talents": talents
    }

# --- CHAT ENDPOINTS ---
@app.get("/messages/{contact_id}")
async def get_messages(contact_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.receiver_id == contact_id)) |
        ((ChatMessage.sender_id == contact_id) & (ChatMessage.receiver_id == current_user.id))
    ).order_by(ChatMessage.timestamp.asc()).all()
    return messages

@app.post("/messages")
async def send_message(data: SendMessage, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_msg = ChatMessage(
        sender_id=current_user.id,
        receiver_id=data.receiver_id,
        message=data.message
    )
    db.add(new_msg)
    
    # Create notification for receiver
    notification = Notification(
        user_id=data.receiver_id,
        title=f"New message from {current_user.full_name}",
        message=data.message[:50] + "..." if len(data.message) > 50 else data.message,
        type="message"
    )
    db.add(notification)
    db.commit()
    return new_msg

@app.get("/chat-contacts")
async def get_chat_contacts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Simple logic: anyone the user has messaged or received from
    sent_to = db.query(ChatMessage.receiver_id).filter(ChatMessage.sender_id == current_user.id).distinct().all()
    received_from = db.query(ChatMessage.sender_id).filter(ChatMessage.receiver_id == current_user.id).distinct().all()
    
    contact_ids = set([r[0] for r in sent_to] + [r[0] for r in received_from])
    contacts = db.query(User).filter(User.id.in_(contact_ids)).all()
    return contacts

# --- INTERVIEW ENDPOINTS ---
@app.post("/interviews")
async def schedule_interview(data: ScheduleInterview, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["employer", "admin"]:
        raise HTTPException(status_code=403, detail="Only employers can schedule interviews")
    
    # Parse date
    try:
        scheduled_dt = datetime.fromisoformat(data.scheduled_at.replace('Z', '+00:00'))
    except:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")

    new_interview = Interview(
        job_id=data.job_id,
        seeker_id=data.seeker_id,
        employer_id=current_user.id,
        title=data.title,
        description=data.description,
        scheduled_at=scheduled_dt,
        duration_minutes=data.duration_minutes,
        meeting_link=data.meeting_link
    )
    db.add(new_interview)
    
    # Notify seeker
    notification = Notification(
        user_id=data.seeker_id,
        title="New Interview Scheduled",
        message=f"You have an interview for {data.title} on {scheduled_dt.strftime('%Y-%m-%d %H:%M')}",
        type="interview"
    )
    db.add(notification)
    db.commit()
    return new_interview

@app.get("/interviews")
async def get_interviews(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "jobseeker":
        interviews = db.query(Interview).filter(Interview.seeker_id == current_user.id).all()
    else:
        interviews = db.query(Interview).filter(Interview.employer_id == current_user.id).all()
    
    result = []
    for itv in interviews:
        itv_dict = itv.__dict__.copy()
        job = db.query(Job).filter(Job.id == itv.job_id).first()
        other_user = db.query(User).filter(User.id == (itv.employer_id if current_user.role == "jobseeker" else itv.seeker_id)).first()
        itv_dict["job_title"] = job.title if job else "N/A"
        itv_dict["other_user_name"] = other_user.full_name if other_user else "Unknown"
        result.append(itv_dict)
    return result

# --- JOB ALERT ENDPOINTS ---
@app.post("/job-alerts")
async def create_job_alert(data: CreateJobAlert, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alert = JobAlert(
        user_id=current_user.id,
        **data.model_dump()
    )
    db.add(alert)
    db.commit()
    return {"message": "Job alert created successfully"}

@app.get("/job-alerts")
async def get_job_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(JobAlert).filter(JobAlert.user_id == current_user.id).all()

# --- RESUME PARSING (AI SIMULATION) ---
@app.post("/parse-resume")
async def parse_resume(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.resume_url:
        raise HTTPException(status_code=400, detail="No resume found. Please upload one first.")
    
    # In a real app, we would use an AI library or API here.
    # For now, we simulate extraction based on the user's current data or generic professional patterns.
    # We'll "extract" some mock data to show the feature works.
    
    mock_extracted = {
        "skills": "React, Python, Node.js, Fast API, SQL, AWS, Docker, Kubernetes, Git, Agile",
        "education": "Bachelor of Technology in Computer Science (Graduated 2023)\nGPA: 3.8/4.0",
        "experience": "Software Engineer Intern at TechCorp (6 months)\nDeveloped responsive web applications using React and Tailwind CSS.",
        "bio": "Passionate software developer with a strong foundation in full-stack development and cloud technologies."
    }
    
    # Update user profile with "extracted" data
    current_user.skills = mock_extracted["skills"]
    current_user.education = mock_extracted["education"]
    current_user.experience = mock_extracted["experience"]
    current_user.bio = mock_extracted["bio"]
    
    db.commit()
    return {"message": "Resume parsed successfully", "extracted_data": mock_extracted}

# --- SKILL ASSESSMENT ENDPOINTS ---
@app.post("/submit-assessment")
async def submit_assessment(data: SubmitAssessment, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Logic to store assessment results (can be added to User model or a new table)
    # For now, we'll just add it to the user's bio/skills as a "Verified" badge
    result_str = f"Verified {data.skill}: {data.score}/{data.total_questions}"
    if current_user.skills:
        current_user.skills += f", {result_str}"
    else:
        current_user.skills = result_str
    
    db.commit()
    return {"message": "Assessment submitted successfully", "score": data.score}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    # In production, we don't want reload=True
    is_dev = os.environ.get("ENV", "production").lower() == "development"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=is_dev)
