@app.get("/search")
async def global_search(q: str, db: Session = Depends(get_db)):
    # Search jobs
    jobs = db.query(Job).filter(
        (Job.title.ilike(f"%{q}%")) | 
        (Job.company.ilike(f"%{q}%")) | 
        (Job.skills_required.ilike(f"%{q}%")) |
        (Job.description.ilike(f"%{q}%"))
    ).limit(20).all()
    
    # Search talents (jobseekers)
    talents = db.query(User).filter(
        (User.role == "jobseeker"),
        (User.is_active == True),
        (
            (User.full_name.ilike(f"%{q}%")) | 
            (User.skills.ilike(f"%{q}%")) |
            (User.bio.ilike(f"%{q}%"))
        )
    ).limit(20).all()
    
    return {
        "jobs": jobs,
        "talents": talents
    }
