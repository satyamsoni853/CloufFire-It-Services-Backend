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
from database import get_db, User
from mail_utils import send_otp_email
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
    return {"message": "Profile updated successfully"}

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{file_ext}"
    file_path = f"uploads/resumes/{file_name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    current_user.resume_url = f"http://localhost:8000/{file_path}"
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
    current_user.profile_image_url = f"http://localhost:8000/{file_path}"
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
        profile_fields = [current_user.full_name, current_user.mobile, current_user.education, current_user.experience, current_user.skills, current_user.bio, current_user.resume_url]
        filled = len([f for f in profile_fields if f])
        return {
            "role": "jobseeker",
            "profile_completeness": round((filled / len(profile_fields)) * 100),
            "has_resume": bool(current_user.resume_url),
            "has_skills": bool(current_user.skills),
            "total_employers": len(employers),
            "total_jobseekers": len(jobseekers),
        }

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
    db_user = db.query(User).filter(User.email == user_data.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])
    hashed_pwd = get_password_hash(user_data.password)
    pending_data = {
        "full_name": user_data.full_name,
        "email": user_data.email,
        "mobile": user_data.mobile,
        "work_status": user_data.work_status,
        "role": user_data.role,
        "hashed_password": hashed_pwd,
        "otp": otp
    }
    pending_token = create_pending_token(pending_data)
    try:
        await send_otp_email(user_data.email, otp)
        return {"message": "OTP sent to your email.", "pending_token": pending_token}
    except Exception as e:
        return {"message": "OTP generated (check terminal).", "pending_token": pending_token, "debug_otp": otp}

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
    except Exception as e:
        return {"message": "OTP generated (check terminal).", "debug_otp": otp}

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
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Please verify your email first")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
