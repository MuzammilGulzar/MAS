from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import json

from backend import db_models
from backend import interview_db_models
from backend.interview_db_models import (
    Candidate,
    Interview,
    InterviewQuestion,
    InterviewAnswer,
    InterviewReport,
    InterviewSession,
    Job,
    Application,
)

from backend import schemas
from backend.database import Base, get_db, engine
from backend.auth import hash_password, verify_password, create_access_token, decode_access_token
from backend.models import EligibilityResult
from backend.models import ResumeAnalysis
from backend.resume_parser import extract_resume_text
from backend.agents.resume_parser_agent import analyze_resume
from backend.agents.planner_agent import create_interview_plan
from backend.agents.question_agent import generate_next_question
from backend.agents.evaluator_agent import evaluate_answer
from backend.agents.report_agent import generate_final_report
from backend.agents.job_eligibility_agent import check_job_eligibility
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from backend.session_manager import (
    create_interview_session,
    set_current_question,
    save_answer_evaluation,
    should_continue_interview,
    session_store,
)
from pydantic import BaseModel

class InterviewStartRequest(BaseModel):
    application_id: int
# ------------------------------------------------------------------
# CREATE TABLES
# ------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"

app.mount(
    "/frontend",
    StaticFiles(directory=FRONTEND_DIR),
    name="frontend",
)

security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# AUTH HELPERS
# ------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """Extract and validate current user from JWT token."""
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(db_models.User).filter(
        db_models.User.username == username
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


def get_candidate_or_404(user_id: int, db: Session) -> Candidate:
    """Look up the Candidate row linked to a user. Raises 404 if missing."""
    candidate = db.query(Candidate).filter(
        Candidate.user_id == user_id
    ).first()

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate profile not found. Please register first."
        )

    return candidate


# ------------------------------------------------------------------
# HEALTH
# ------------------------------------------------------------------

@app.get("/")
def home():
    return {"message": "MAS backend is running"}


# ------------------------------------------------------------------
# AUTH — REGISTER & LOGIN
# ------------------------------------------------------------------

@app.post("/register")
def register(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """
    Register a new user.

    KEY FIX: Also creates a linked Candidate profile immediately.
    This ensures user_id -> candidate_id relationship exists
    before any job application is attempted.
    """
    # Check duplicate username
    if db.query(db_models.User).filter(
        db_models.User.username == user.username
    ).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check duplicate email
    if db.query(db_models.User).filter(
        db_models.User.email == user.email
    ).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create User row
    new_user = db_models.User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role=getattr(user, "role", "candidate"),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create Candidate profile linked to this user
    # (empty at first — resume gets filled in at check-eligibility / interview/start)
    if new_user.role.lower() == "candidate":
        candidate = Candidate(
            user_id=new_user.id,
            resume_score=0.0,
            candidate_level="Unknown",
            job_fit="Unknown",
            resume_text="",
            analysis_json="{}",
            resume_score_reason="Resume not yet uploaded",
        )
        db.add(candidate)
        db.commit()

    return {"message": "User registered successfully"}


@app.post("/login")
def login(
    request: schemas.LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate user and return a JWT token."""
    user = db.query(db_models.User).filter(
        db_models.User.username == request.username
    ).first()

    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user.username, "role": user.role})

    return {"access_token": token, "token_type": "bearer"}


# ------------------------------------------------------------------
# USER PROFILE
# ------------------------------------------------------------------

@app.get("/profile")
def profile(current_user: db_models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
    }


# ------------------------------------------------------------------
# JOBS
# ------------------------------------------------------------------

@app.get("/jobs")
def get_jobs(db: Session = Depends(get_db)):
    """Public — any visitor can browse jobs."""
    return db.query(Job).filter(Job.status == "active").all()


@app.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/jobs")
def create_job(
    job: schemas.JobCreate,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """HR only — create a new job posting."""
    if current_user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="HR access required")

    new_job = Job(
        title=job.title,
        description=job.description,
        required_skills=job.required_skills,
        experience_level=job.experience_level,
        hr_id=current_user.id,
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return {"message": "Job created successfully", "job_id": new_job.id}


@app.get("/hr/jobs")
def get_hr_jobs(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """HR only — list jobs posted by this HR user."""
    if current_user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="HR access required")

    return db.query(Job).filter(Job.hr_id == current_user.id).all()


# ------------------------------------------------------------------
# APPLY FOR A JOB
# ------------------------------------------------------------------

@app.post("/apply")
def apply_job(
    application: schemas.ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """
    Candidate applies for a job.

    KEY FIX: candidate_id is resolved from the JWT token — not sent
    by the frontend. The frontend only sends job_id.
    """
    # Resolve candidate from logged-in user
    candidate = get_candidate_or_404(current_user.id, db)

    # Check the job exists
    job = db.query(Job).filter(Job.id == application.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Prevent duplicate applications
    existing = db.query(Application).filter(
        Application.candidate_id == candidate.id,
        Application.job_id == application.job_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="You have already applied for this job")

    new_application = Application(
        candidate_id=candidate.id,
        job_id=application.job_id,
        status="applied",
    )
    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    return {
        "message": "Application submitted successfully",
        "application_id": new_application.id,
    }


# ------------------------------------------------------------------
# CHECK ELIGIBILITY
# ------------------------------------------------------------------

@app.post("/check-eligibility")
async def check_eligibility(
    file: UploadFile = File(...),
    job_id: int = Form(...),
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """
    Upload resume and check eligibility for a specific job.

    Flow:
    1. Parse and analyse the resume
    2. Update the existing Candidate profile with resume data
    3. Run the eligibility agent against the job
    4. Update the existing Application with eligibility result
    """
    # -- 1. Parse resume --
    file_bytes = await file.read()
    resume_text = extract_resume_text(
        file_bytes=file_bytes,
        filename=file.filename.lower(),
    )
    resume_analysis = analyze_resume(resume_text)

    # -- 2. Get existing candidate and update with resume data --
    candidate = get_candidate_or_404(current_user.id, db)

    candidate.resume_score = resume_analysis.score
    candidate.resume_score_reason = resume_analysis.reason
    candidate.job_fit = resume_analysis.job_fit
    candidate.resume_text = resume_text
    candidate.analysis_json = json.dumps(resume_analysis.model_dump())
    db.commit()

    # -- 3. Get job --
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # -- 4. Run eligibility check --
    result = check_job_eligibility(resume_analysis, job)

    # -- 5. Find existing Application or create one if candidate skipped /apply --
    application = db.query(Application).filter(
        Application.candidate_id == candidate.id,
        Application.job_id == job_id,
    ).first()

    if not application:
        application = Application(
            candidate_id=candidate.id,
            job_id=job_id,
            status="applied",
        )
        db.add(application)
        db.commit()
        db.refresh(application)

    # -- 6. Write eligibility result back to the application --
    application.eligibility_reason = ", ".join(result.reasons)

    if result.eligible:
        application.eligibility_status = "eligible"
        application.status = "interview_pending"
        db.commit()

        return {
            "eligible": True,
            "score": result.score,
            "reasons": result.reasons,
            "application_id": application.id,
        }
    else:
        application.eligibility_status = "not_eligible"
        application.status = "rejected"
        db.commit()

        return {
            "eligible": False,
            "score": result.score,
            "reasons": result.reasons,
        }


# ------------------------------------------------------------------
# RESUME ANALYSIS (standalone — no interview)
# ------------------------------------------------------------------

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    file_bytes = await file.read()
    resume_text = extract_resume_text(
        file_bytes=file_bytes,
        filename=file.filename.lower(),
    )
    return analyze_resume(resume_text)


# ------------------------------------------------------------------
# INTERVIEW — START
# ------------------------------------------------------------------

@app.post("/interview/start")
async def start_interview(
    request: InterviewStartRequest,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """
    Start an interview for a specific application.

    KEY FIX: Reuses the existing Candidate — never creates a new one.
    Links the new Interview row to both the Candidate and the Application.
    """
    # -- 1. Get existing candidate (never create here) --
    candidate = get_candidate_or_404(current_user.id, db)

    # -- 2. Validate the application belongs to this candidate --
    application = db.query(Application).filter(
        Application.id == request.application_id,
        Application.candidate_id == candidate.id,
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if application.eligibility_status != "eligible":
        raise HTTPException(
            status_code=403,
            detail="You must pass the eligibility check before starting the interview"
        )

    # -- 3. Parse and analyse resume --
    # file_bytes = await file.read()
    # resume_text = extract_resume_text(
    #     file_bytes=file_bytes,
    #     filename=file.filename.lower(),
    # )
    # analysis_result = analyze_resume(resume_text)

    # # Update candidate with latest resume data
    # candidate.resume_score = analysis_result.score
    # candidate.resume_score_reason = analysis_result.reason
    # candidate.job_fit = analysis_result.job_fit
    # candidate.resume_text = resume_text
    # candidate.analysis_json = json.dumps(analysis_result.model_dump())
    # db.commit()
    if not candidate.analysis_json:
      raise HTTPException(
        status_code=400,
        detail="Resume not found. Please complete eligibility first."
    )

    analysis_result = ResumeAnalysis.model_validate(
       json.loads(candidate.analysis_json)
)

    # -- 4. Create interview plan --
    interview_plan = create_interview_plan(analysis_result)

    # -- 5. Create Interview row linked to the EXISTING candidate --
    interview = Interview(
        candidate_id=candidate.id,
        status="in_progress",
        difficulty=interview_plan.difficulty,
        total_questions=interview_plan.total_questions,
        plan_json=json.dumps(interview_plan.model_dump()),
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    # -- 6. Link interview back to the application --
    application.interview_id = interview.id
    application.status = "interview_in_progress"
    db.commit()

    # -- 7. Create in-memory session --
    session = create_interview_session(analysis_result, interview_plan)
    session["candidate_db_id"] = candidate.id
    session["interview_db_id"] = interview.id

    # -- 8. Persist session to DB --
    session_db = InterviewSession(
        session_id=session["session_id"],
        interview_id=interview.id,
        current_skill_index=0,
        current_question_number=0,
        current_difficulty=interview_plan.difficulty,
        status="in_progress",
    )
    db.add(session_db)
    db.commit()

    # -- 9. Generate and save first question --
    first_question = generate_next_question(session)

    question_row = InterviewQuestion(
        interview_id=interview.id,
        question_id=first_question.question_id,
        skill=first_question.skill,
        difficulty=first_question.difficulty,
        question_text=first_question.question,
    )
    db.add(question_row)
    db.commit()

    set_current_question(session["session_id"], first_question)

    return {
        "session_id": session["session_id"],
        "resume_analysis": analysis_result,
        "interview_plan": interview_plan,
        "first_question": {
            "question_id": first_question.question_id,
            "skill": first_question.skill,
            "difficulty": first_question.difficulty,
            "question": first_question.question,
        },
    }


# ------------------------------------------------------------------
# INTERVIEW — SUBMIT ANSWER
# ------------------------------------------------------------------

@app.post("/interview/answer")
async def submit_answer(
    data: dict,
    db: Session = Depends(get_db),
):
    session_id = data.get("session_id")
    candidate_answer = data.get("answer")

    if not session_id or not candidate_answer:
        raise HTTPException(status_code=400, detail="session_id and answer are required")

    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    session = session_store[session_id]
    current_question = session["current_question"]

    # Evaluate answer
    evaluation = evaluate_answer(current_question, candidate_answer)

    # Find question row in DB
    question_row = db.query(InterviewQuestion).filter(
        InterviewQuestion.question_id == current_question.question_id,
    ).first()

    if not question_row:
        raise HTTPException(status_code=404, detail="Question not found in database")

    # Save answer row
    answer_row = InterviewAnswer(
        question_id=question_row.id,
        answer_text=candidate_answer,
        score=evaluation.score,
        feedback=evaluation.feedback,
        evaluation_json=json.dumps(evaluation.model_dump()),
    )
    db.add(answer_row)
    db.commit()

    # Update in-memory session
    updated_session = save_answer_evaluation(session_id, candidate_answer, evaluation)

    # Update DB session
    session_db = db.query(InterviewSession).filter(
        InterviewSession.session_id == session_id
    ).first()

    if session_db:
        session_db.current_question_number += 1
        session_db.current_difficulty = evaluation.next_difficulty
        db.commit()

    # Check if interview is complete
    if not should_continue_interview(updated_session):
        final_report = generate_final_report(updated_session)

        report_row = InterviewReport(
            interview_id=session["interview_db_id"],
            overall_score=final_report.overall_score,
            score_reason=final_report.score_reason,
            recommendation=final_report.recommendation,
            report_json=json.dumps(final_report.model_dump()),
        )
        db.add(report_row)

        # Mark session and interview completed
        if session_db:
            session_db.status = "completed"

        interview_row = db.query(Interview).filter(
            Interview.id == session["interview_db_id"]
        ).first()
        if interview_row:
            interview_row.status = "completed"

        # Update application status
        application = db.query(Application).filter(
            Application.interview_id == session["interview_db_id"]
        ).first()
        if application:
            application.status = "interview_completed"

        db.commit()

        return {
            "type": "completed",
            "evaluation": evaluation,
            "message": "Interview completed",
            "final_report": final_report,
        }

    # Generate next question
    next_question = generate_next_question(updated_session)

    next_question_row = InterviewQuestion(
        interview_id=session["interview_db_id"],
        question_id=next_question.question_id,
        skill=next_question.skill,
        difficulty=next_question.difficulty,
        question_text=next_question.question,
    )
    db.add(next_question_row)
    db.commit()

    set_current_question(session_id, next_question)

    return {
        "type": "question",
        "evaluation": evaluation,
        "next_question": {
            "question_id": next_question.question_id,
            "skill": next_question.skill,
            "difficulty": next_question.difficulty,
            "question": next_question.question,
        },
    }


# ------------------------------------------------------------------
# INTERVIEW — GET SESSION STATE
# ------------------------------------------------------------------

@app.get("/interview/{session_id}")
def get_interview_state(
    session_id: str,
    db: Session = Depends(get_db),
):
    session_db = db.query(InterviewSession).filter(
        InterviewSession.session_id == session_id
    ).first()

    if not session_db:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_db.session_id,
        "interview_id": session_db.interview_id,
        "current_question_number": session_db.current_question_number,
        "difficulty": session_db.current_difficulty,
        "status": session_db.status,
    }


# ------------------------------------------------------------------
# CANDIDATE — VIEW MY APPLICATIONS
# ------------------------------------------------------------------

@app.get("/candidate/applications")
def get_my_applications(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """
    Returns all applications for the currently logged-in candidate.
    No candidate_id in the URL — resolved from JWT token.
    """
    candidate = get_candidate_or_404(current_user.id, db)

    applications = db.query(Application).filter(
        Application.candidate_id == candidate.id
    ).all()

    result = []
    for app in applications:
        job = db.query(Job).filter(Job.id == app.job_id).first()
        result.append({
            "application_id": app.id,
            "job_id": app.job_id,
            "job_title": job.title if job else "Unknown",
            "status": app.status,
            "eligibility_status": app.eligibility_status,
            "applied_at": app.applied_at,
        })

    return result


# ------------------------------------------------------------------
# HR — VIEW APPLICATIONS FOR A JOB
# ------------------------------------------------------------------

@app.get("/hr/jobs/{job_id}/applications")
def get_job_applications(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """HR only — view all applications for one of their jobs."""
    if current_user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="HR access required")

    job = db.query(Job).filter(
        Job.id == job_id,
        Job.hr_id == current_user.id,
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    applications = db.query(Application).filter(
        Application.job_id == job_id
    ).all()

    result = []
    for app in applications:
        candidate = db.query(Candidate).filter(
            Candidate.id == app.candidate_id
        ).first()

        user = db.query(db_models.User).filter(
            db_models.User.id == candidate.user_id
        ).first() if candidate else None

        report = None
        if app.interview_id:
            report_row = db.query(InterviewReport).filter(
                InterviewReport.interview_id == app.interview_id
            ).first()
            if report_row:
                report = {
                    "overall_score": report_row.overall_score,
                    "recommendation": report_row.recommendation,
                }

        result.append({
            "application_id": app.id,
            "candidate_name": user.username if user else "Unknown",
            "candidate_email": user.email if user else "Unknown",
            "resume_score": candidate.resume_score if candidate else None,
            "status": app.status,
            "eligibility_status": app.eligibility_status,
            "applied_at": app.applied_at,
            "interview_report": report,
        })

    return result

# ------------------------------------------------------------------
# HR — CLOSE / REOPEN A JOB
# ------------------------------------------------------------------
 
@app.patch("/hr/jobs/{job_id}/status")
def update_job_status(
    job_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """HR only — close or reopen a job they own."""
    if current_user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="HR access required")
 
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.hr_id == current_user.id,
    ).first()
 
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
 
    new_status = body.get("status")
    if new_status not in ("active", "closed"):
        raise HTTPException(status_code=400, detail="Status must be 'active' or 'closed'")
 
    job.status = new_status
    db.commit()
 
    return {"message": f"Job status updated to {new_status}", "job_id": job_id}
 
 
# ------------------------------------------------------------------
# HR — DELETE A JOB
# ------------------------------------------------------------------
 
@app.delete("/hr/jobs/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """HR only — permanently delete a job they own."""
    if current_user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="HR access required")
 
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.hr_id == current_user.id,
    ).first()
 
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
 
    # Remove linked applications first to avoid FK constraint errors
    db.query(Application).filter(Application.job_id == job_id).delete()
    db.delete(job)
    db.commit()
 
    return {"message": "Job deleted successfully", "job_id": job_id}
 
 
# ------------------------------------------------------------------
# HR — STATS FOR DASHBOARD
# ------------------------------------------------------------------
 
@app.get("/hr/stats")
def get_hr_stats(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """HR only — stats for their own jobs only."""
    if current_user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="HR access required")
 
    my_jobs = db.query(Job).filter(Job.hr_id == current_user.id).all()
    my_job_ids = [j.id for j in my_jobs]
 
    total_jobs = len([j for j in my_jobs if j.status == "active"])
 
    total_applications = db.query(Application).filter(
        Application.job_id.in_(my_job_ids)
    ).count() if my_job_ids else 0
 
    completed_interviews = db.query(Application).filter(
        Application.job_id.in_(my_job_ids),
        Application.status == "interview_completed"
    ).count() if my_job_ids else 0
 
    shortlisted = 0
    if my_job_ids:
        apps_with_interviews = db.query(Application).filter(
            Application.job_id.in_(my_job_ids),
            Application.interview_id.isnot(None)
        ).all()
        for app in apps_with_interviews:
            report = db.query(InterviewReport).filter(
                InterviewReport.interview_id == app.interview_id
            ).first()
            if report and report.recommendation == "Shortlist":
                shortlisted += 1
 
    return {
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "completed_interviews": completed_interviews,
        "shortlisted": shortlisted,
    }
 
 
# ------------------------------------------------------------------
# HR — ALL APPLICATIONS ACROSS ALL MY JOBS (for applications.html)
# ------------------------------------------------------------------
 
@app.get("/hr/applications")
def get_all_hr_applications(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """HR only — all applications across all jobs this HR posted."""
    if current_user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="HR access required")
 
    my_jobs = db.query(Job).filter(Job.hr_id == current_user.id).all()
    my_job_ids = [j.id for j in my_jobs]
    job_map = {j.id: j for j in my_jobs}
 
    if not my_job_ids:
        return []
 
    applications = db.query(Application).filter(
        Application.job_id.in_(my_job_ids)
    ).all()
 
    result = []
    for app in applications:
        candidate = db.query(Candidate).filter(
            Candidate.id == app.candidate_id
        ).first()
 
        user = db.query(db_models.User).filter(
            db_models.User.id == candidate.user_id
        ).first() if candidate else None
 
        report = None
        if app.interview_id:
            report_row = db.query(InterviewReport).filter(
                InterviewReport.interview_id == app.interview_id
            ).first()
            if report_row:
                report = {
                    "overall_score": report_row.overall_score,
                    "recommendation": report_row.recommendation,
                    "report_json": report_row.report_json,
                }
 
        job = job_map.get(app.job_id)
 
        result.append({
            "application_id": app.id,
            "candidate_id": app.candidate_id,
            "candidate_name": user.username if user else "Unknown",
            "candidate_email": user.email if user else "Unknown",
            "job_id": app.job_id,
            "job_title": job.title if job else "Unknown",
            "resume_score": candidate.resume_score if candidate else None,
            "job_fit": candidate.job_fit if candidate else None,
            "status": app.status,
            "eligibility_status": app.eligibility_status,
            "applied_at": app.applied_at,
            "interview_report": report,
        })
 
    return result
 
 
# ------------------------------------------------------------------
# HR — SHORTLIST / HIRE / REJECT AN APPLICATION
# ------------------------------------------------------------------
 
@app.patch("/hr/applications/{application_id}/decision")
def make_hiring_decision(
    application_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
):
    """HR only — shortlist, hire, or reject a candidate after interview."""
    if current_user.role.lower() != "hr":
        raise HTTPException(status_code=403, detail="HR access required")
 
    decision = body.get("decision")
    if decision not in ("shortlisted", "hired", "rejected"):
        raise HTTPException(
            status_code=400,
            detail="Decision must be 'shortlisted', 'hired', or 'rejected'"
        )
 
    # Make sure the application belongs to one of this HR's jobs
    application = db.query(Application).join(
        Job, Job.id == Application.job_id
    ).filter(
        Application.id == application_id,
        Job.hr_id == current_user.id,
    ).first()
 
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
 
    application.status = decision
    db.commit()

    return {"message": f"Candidate {decision}", "application_id": application_id}


# ------------------------------------------------------------------
# PRACTICE INTERVIEW — no auth, no application required
# ------------------------------------------------------------------
 
@app.post("/practice/start")
async def practice_start(file: UploadFile = File(...)):
    """
    Practice interview — open to anyone, no login required.
    No database writes. Pure in-memory session.
    """
    try:
        file_bytes = await file.read()
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
 
        resume_text = extract_resume_text(
            file_bytes=file_bytes,
            filename=file.filename.lower(),
        )
        if not resume_text.strip():
            raise HTTPException(status_code=422, detail="Could not extract text from resume")
 
        analysis_result  = analyze_resume(resume_text)
        interview_plan   = create_interview_plan(analysis_result)
        session          = create_interview_session(analysis_result, interview_plan)
        first_question   = generate_next_question(session)
 
        set_current_question(session["session_id"], first_question)
 
        return {
            "session_id":      session["session_id"],
            "resume_analysis": analysis_result,
            "interview_plan":  interview_plan,
            "first_question": {
                "question_id":  first_question.question_id,
                "skill":        first_question.skill,
                "difficulty":   first_question.difficulty,
                "question":     first_question.question,
            },
            "progress": {
                "current": 1,
                "total":   interview_plan.total_questions,
                "current_skill": first_question.skill,
            }
        }
 
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start practice: {str(e)}")
 
 
@app.post("/practice/answer")
async def practice_answer(data: dict):
    """
    Submit an answer in a practice session.
    No DB writes — purely in-memory.
    """
    session_id       = data.get("session_id")
    candidate_answer = data.get("answer", "").strip()
 
    if not session_id or not candidate_answer:
        raise HTTPException(status_code=400, detail="session_id and answer are required")
 
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Practice session not found or expired")
 
    session          = session_store[session_id]
    current_question = session["current_question"]
 
    try:
        evaluation       = evaluate_answer(current_question, candidate_answer)
        updated_session  = save_answer_evaluation(session_id, candidate_answer, evaluation)
 
        if not should_continue_interview(updated_session):
            final_report = generate_final_report(updated_session)
            return {
                "type":         "completed",
                "evaluation":   evaluation,
                "final_report": final_report,
            }
 
        next_question = generate_next_question(updated_session)
        set_current_question(session_id, next_question)
 
        return {
            "type":       "question",
            "evaluation": evaluation,
            "next_question": {
                "question_id": next_question.question_id,
                "skill":       next_question.skill,
                "difficulty":  next_question.difficulty,
                "question":    next_question.question,
            },
            "progress": {
                "current": len(updated_session["answers"]) + 1,
                "total":   updated_session["interview_plan"].total_questions,
                "current_skill": next_question.skill,
            }
        }
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process answer: {str(e)}")
 