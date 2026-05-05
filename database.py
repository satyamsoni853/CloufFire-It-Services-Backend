from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment or fallback to SQLite
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback to SQLite if DATABASE_URL is not set or empty
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# SQLAlchemy 1.4+ requires 'postgresql://' instead of 'postgres://'
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Handle SQLite specific arguments
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connect_args,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    role = Column(String, default="jobseeker") # jobseeker, employer, admin
    mobile = Column(String, nullable=True)
    work_status = Column(String, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=False)
    otp = Column(String, nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    
    # Job Seeker Profile Fields
    education = Column(String, nullable=True)
    experience = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False) # For employers
    skills = Column(String, nullable=True)
    resume_url = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    location = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    availability = Column(String, default="Immediate") # Immediate, 15 Days, 30 Days
    is_featured = Column(Boolean, default=False) # For Profile Boost
    boost_expiry = Column(DateTime, nullable=True)
    projects = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    languages = Column(String, nullable=True)
    is_profile_public = Column(Boolean, default=True)
    search_status = Column(String, default="Actively Looking") # Actively Looking, Open to Offers, Not Looking

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    # Basic Job Details
    title = Column(String)
    company = Column(String)
    description = Column(String, nullable=True)
    location = Column(String)
    type = Column(String)  # Full-time, Contract, etc.
    experience_required = Column(String, nullable=True)
    skills_required = Column(String, nullable=True)
    openings = Column(Integer, nullable=True)
    
    # Compensation & Benefits
    salary = Column(String)
    perks = Column(String, nullable=True)
    
    # Candidate Requirements
    education_qualification = Column(String, nullable=True)
    preferred_skills = Column(String, nullable=True)
    certifications = Column(String, nullable=True)
    
    # Application Details
    deadline = Column(String, nullable=True)
    application_method = Column(String, nullable=True)
    application_email = Column(String, nullable=True)
    application_link = Column(String, nullable=True)
    hr_name = Column(String, nullable=True)
    hr_phone = Column(String, nullable=True)
    
    # Company Details
    company_description = Column(String, nullable=True)
    company_website = Column(String, nullable=True)
    company_logo_url = Column(String, nullable=True)
    
    # Advanced / Optional
    work_mode = Column(String, nullable=True) # Remote, Onsite, Hybrid
    shift_timing = Column(String, nullable=True)
    notice_period = Column(String, nullable=True)
    gender_preference = Column(String, nullable=True)
    industry_type = Column(String, nullable=True)
    department = Column(String, nullable=True)
    
    posted_by_id = Column(Integer)  # User ID of the employer
    created_at = Column(DateTime, default=datetime.utcnow)
    is_approved = Column(Boolean, default=True) # Default true for now, can be changed to false for moderation

class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True)
    saved_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    job_id = Column(Integer, index=True)
    cover_letter = Column(String, nullable=True)
    status = Column(String, default="Applied")  # Applied, Under Review, Shortlisted, Rejected, Hired
    applied_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, index=True)
    receiver_id = Column(Integer, index=True)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True)
    seeker_id = Column(Integer, index=True)
    employer_id = Column(Integer, index=True)
    title = Column(String)
    description = Column(String, nullable=True)
    scheduled_at = Column(DateTime)
    duration_minutes = Column(Integer, default=30)
    meeting_link = Column(String, nullable=True)
    status = Column(String, default="Scheduled") # Scheduled, Completed, Cancelled

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    title = Column(String)
    message = Column(String)
    type = Column(String) # application, interview, message, alert
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class JobAlert(Base):
    __tablename__ = "job_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    keyword = Column(String, nullable=True)
    location = Column(String, nullable=True)
    category = Column(String, nullable=True)
    min_salary = Column(String, nullable=True)
    frequency = Column(String, default="Daily") # Daily, Weekly

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, index=True)
    action = Column(String)
    target_id = Column(Integer, nullable=True)
    target_type = Column(String, nullable=True) # user, job, setting
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String, nullable=True)

class SiteSetting(Base):
    __tablename__ = "site_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)
    type = Column(String, default="text") # text, image, boolean

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Base.metadata.create_all(bind=engine) # Moved to main.py startup event

