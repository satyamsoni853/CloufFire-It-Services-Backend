from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
import shutil
import uuid
import os
import random
from datetime import datetime, timedelta
from database import get_db, User, Job

from mail_utils import send_otp_email, send_notification_email
from auth import get_password_hash, verify_password, create_access_token, create_pending_token, verify_pending_token, SECRET_KEY, ALGORITHM
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



# Authentication Dependency
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        if token.startswith("Bearer "):
            token = token[7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")


# Routes
@app.get("/")
async def root():
    return {"status": "ok", "message": "Cloudfire IT Services API is running"}

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
        "profile_image_url": current_user.profile_image_url
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

@app.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = current_user.role
    all_users = db.query(User).all()
    jobseekers = [u for u in all_users if u.role == "jobseeker"]
    employers = [u for u in all_users if u.role == "employer"]
    admins = [u for u in all_users if u.role == "admin"]

    if role == "admin":
        return {
            "role": "admin",
            "total_users": len(all_users),
            "total_jobseekers": len(jobseekers),
            "total_employers": len(employers),
            "total_admins": len(admins),
            "active_users": len([u for u in all_users if u.is_active]),
            "profiles_with_resume": len([u for u in jobseekers if u.resume_url]),
            "recent_users": [{"full_name": u.full_name, "email": u.email, "role": u.role} for u in sorted(all_users, key=lambda x: x.id, reverse=True)[:5]],
        }
    elif role == "employer":
        return {
            "role": "employer",
            "available_talent": len(jobseekers),
            "talent_with_resume": len([u for u in jobseekers if u.resume_url]),
            "talent_with_skills": len([u for u in jobseekers if u.skills]),
            "total_employers": len(employers),
        }
    else:
        from database import Application, SavedJob
        profile_fields = [current_user.full_name, current_user.mobile, current_user.education, current_user.experience, current_user.skills, current_user.bio, current_user.resume_url]
        filled = len([f for f in profile_fields if f])
        
        apps_count = db.query(Application).filter(Application.user_id == current_user.id).count()
        saved_count = db.query(SavedJob).filter(SavedJob.user_id == current_user.id).count()
        
        return {
            "role": "jobseeker",
            "profile_completeness": round((filled / len(profile_fields)) * 100),
            "has_resume": bool(current_user.resume_url),
            "has_skills": bool(current_user.skills),
            "total_employers": len(employers),
            "total_jobseekers": len(jobseekers),
            "total_applications": apps_count,
            "total_saved_jobs": saved_count,
            "search_appearances": [
                {"name": "Week 1", "searches": random.randint(10, 20)},
                {"name": "Week 2", "searches": random.randint(15, 25)},
                {"name": "Week 3", "searches": random.randint(12, 22)},
                {"name": "Week 4", "searches": random.randint(20, 35)},
                {"name": "This Week", "searches": random.randint(25, 45)}
            ],
            "profile_views": [
                {"name": "Mon", "views": random.randint(2, 8)},
                {"name": "Tue", "views": random.randint(5, 12)},
                {"name": "Wed", "views": random.randint(8, 15)},
                {"name": "Thu", "views": random.randint(4, 10)},
                {"name": "Fri", "views": random.randint(10, 20)},
                {"name": "Sat", "views": random.randint(15, 25)},
                {"name": "Sun", "views": random.randint(12, 22)}
            ]
        }

@app.get("/notifications")
async def get_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    role = current_user.role
    notifications = []
    
    # Global notification
    notifications.append({
        "id": "welcome",
        "title": f"Welcome back, {current_user.full_name.split(' ')[0]}!",
        "time": "Just now",
        "icon": "👋",
        "priority": "low"
    })
    
    if role == "admin":
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        notifications.append({
            "id": "stats_users",
            "title": f"Platform has {total_users} registered users",
            "time": "Updated now",
            "icon": "📊",
            "priority": "medium"
        })
        if total_users > active_users:
            notifications.append({
                "id": "pending_users",
                "title": f"{total_users - active_users} users are pending verification",
                "time": "Action required",
                "icon": "⏳",
                "priority": "high"
            })
            
    elif role == "employer":
        jobseekers_count = db.query(User).filter(User.role == "jobseeker").count()
        resume_count = db.query(User).filter(User.role == "jobseeker", User.resume_url != None).count()
        notifications.append({
            "id": "talent_pool",
            "title": f"{jobseekers_count} candidates are available in the talent pool",
            "time": "1 hour ago",
            "icon": "👥",
            "priority": "medium"
        })
        if resume_count > 0:
            notifications.append({
                "id": "resumes",
                "title": f"{resume_count} candidates have uploaded their resumes",
                "time": "Check them out",
                "icon": "📄",
                "priority": "medium"
            })
            
    else: # jobseeker
        jobs_count = db.query(Job).count()
        employers_count = db.query(User).filter(User.role == "employer").count()
        notifications.append({
            "id": "jobs_count",
            "title": f"{jobs_count} active job openings found for you",
            "time": "Recently added",
            "icon": "💼",
            "priority": "high"
        })
        notifications.append({
            "id": "employer_count",
            "title": f"{employers_count} employers are currently hiring",
            "time": "Trending",
            "icon": "🏢",
            "priority": "medium"
        })
        
    return notifications

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
    db.commit()
    
    return {"message": f"Successfully applied for {job.title} at {job.company}"}

@app.get("/applications")
async def get_applications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "jobseeker":
        raise HTTPException(status_code=403, detail="Permission denied")
    from database import Application
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
    from database import SavedJob
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
    from database import SavedJob
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
    from database import SavedJob
    saved = db.query(SavedJob).filter(SavedJob.user_id == current_user.id, SavedJob.job_id == job_id).first()
    if saved:
        db.delete(saved)
        db.commit()
    return {"message": "Saved job removed"}

@app.get("/employer/jobseekers")
async def get_all_jobseekers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["employer", "admin"]:
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
    return {
        "message": "Account created successfully!", 
        "access_token": access_token, 
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
    return {"message": "Account created!", "access_token": access_token, "token_type": "bearer", "role": new_user.role}

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
        return {
            "access_token": access_token, 
            "token_type": "bearer", 
            "role": user_role
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
