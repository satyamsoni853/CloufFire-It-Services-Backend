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
    pool_pre_ping=True,
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
    skills = Column(String, nullable=True)
    resume_url = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    location = Column(String, nullable=True)
    salary = Column(String, nullable=True)
    projects = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    dob = Column(String, nullable=True)
    languages = Column(String, nullable=True)

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


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

Base.metadata.create_all(bind=engine)
