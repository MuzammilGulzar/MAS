from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Form
# login import
from sqlalchemy.orm import Session

# import db_models as db_models
from backend import db_models

from backend import interview_db_models
import json
from backend.interview_db_models import Candidate, Interview
from backend.interview_db_models import (
    InterviewQuestion,
    InterviewAnswer
)

from backend.interview_db_models import InterviewReport, InterviewSession, Job, Application

from backend.agents.job_eligibility_agent import check_job_eligibility

from backend.models import EligibilityResult

from backend import schemas

from backend.database import Base
from backend.database import get_db,engine 

from backend.auth import hash_password, verify_password, create_access_token,decode_access_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# ------------------------------------------------------------------
# CREATE TABLES
# ------------------------------------------------------------------
# Reads all SQLAlchemy models
# and creates missing tables.
#
Base.metadata.create_all(bind=engine)
# end login import
from fastapi.middleware.cors import CORSMiddleware

from backend.resume_parser import extract_resume_text
from backend.agents.resume_parser_agent import analyze_resume
from backend.agents.planner_agent import create_interview_plan
from backend.agents.question_agent import generate_next_question
from backend.agents.evaluator_agent import evaluate_answer
from backend.agents.report_agent import generate_final_report
# from backend.agents.voice_evaluater_agent import evaluate_voice

import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

from backend.session_manager import create_interview_session, set_current_question, save_answer_evaluation, should_continue_interview
from backend.session_manager import session_store



app = FastAPI()
# login
# Security scheme
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message":"AI Resume Analyzer backend is running"}

# login system
@app.post("/register")
def register(
    user: schemas.UserCreate,
    db: Session=Depends(get_db)
):
    """Register a new user"""

    # Search db for existing username
    existing_user = db.query(db_models.User).filter(
        db_models.User.username == user.username).first()
    
    # username already exists
    if existing_user:
        
        raise HTTPException(
            status_code= 400,
            detail="Username already exists"
        )
    
    new_user = db_models.User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role=user.role  # use role sent by client
    )

    #add object to session
    db.add(new_user)

    #execute insert
    db.commit()

    #refresh object, from db, with new id
    db.refresh(new_user)

    return{
        "message": "User registered successfully",
    }

@app.post("/login")
def login(
    request: schemas.LoginRequest,
    db: Session=Depends(get_db)
):
    """Authenticate user and generate JWT token"""

    # Find user
    user = db.query(db_models.User).filter(
        db_models.User.username == request.username).first()
    
    # User not found
    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # Verify password
    if not verify_password(
        request.password,
        user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    # Generate JWT token
    token = create_access_token(
        {
            "sub": user.username,
            "role": user.role
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }
    

# dependency to get current user from token
def get_current_user(
    credentials:
    HTTPAuthorizationCredentials =
    Depends(security)
):
    """
    Extract user information
    from JWT token.
    """

    # Extract token string
    token = credentials.credentials

    # Decode token
    payload = decode_access_token(token)

    if payload is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    return payload

# authorization (admin-only endpoint)
def admin_only(
    current_user=Depends(
        get_current_user
    )
):
    """
    Allow only admins.
    """

    # Check role
    if current_user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    return current_user

# Example of protected endpoint

@app.get("/profile")
def profile(
    current_user=Depends(
        get_current_user
    )
):
    """
    Any logged-in user can access.
    """

    return {
        "username": current_user["sub"],
        "role": current_user["role"]
    }


@app.get("/admin")
def admin_dashboard(
    current_user=Depends(admin_only)
):
    """
    Only admins can access.
    """

    return {
        "message": "Welcome Admin",
        "user": current_user
    }


@app.post("/analyze")
async def analyze(file: UploadFile=File(...)):
    file_bytes = await file.read()

    resume_text = extract_resume_text(
        file_bytes=file_bytes,
        filename=file.filename.lower()
    )

    result = analyze_resume(resume_text)
    return result

@app.post("/interview/start")
async def start_interview(
    file: UploadFile=File(...),
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
    ):
    file_bytes = await file.read()

    resume_text = extract_resume_text(
        file_bytes=file_bytes,
        filename=file.filename.lower()
    )

    analysis_result = analyze_resume(resume_text)

    candidate = Candidate(
        user_id=current_user.id,
        resume_score=analysis_result.score,
        resume_score_reason=analysis_result.reason,
        candidate_level="Unknown",
        job_fit=analysis_result.job_fit,
        resume_text=resume_text,
        analysis_json=json.dumps(
            analysis_result.model_dump()
        )
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    interview_plan = create_interview_plan(
        analysis_result
    )

    interview = Interview(
        candidate_id=candidate.id,
        status="in_progress",
        difficulty=interview_plan.difficulty,
        total_questions=interview_plan.total_questions,
        plan_json = json.dumps(
            interview_plan.model_dump()
        )
    )

    db.add(interview)
    db.commit()
    db.refresh(interview)

    session = create_interview_session(
    analysis_result,
    interview_plan
    )

    session_db = InterviewSession(
        session_id = session["session_id"],
        interview_id = interview.id,
        current_skill_index = 0,
        current_question_number=0,
        current_difficulty=interview_plan.difficulty,
        status="in_progress"
    )

    db.add(session_db)
    db.commit()

    # session = create_interview_session(
    #     analysis_result,
    #     interview_plan
    # )

    session["candidate_db_id"] = candidate.id
    session["interview_db_id"] = interview.id

    first_question = generate_next_question(session)
    from backend.interview_db_models import InterviewQuestion

    question_row = InterviewQuestion(
    interview_id=interview.id,
    question_id=first_question.question_id,
    skill=first_question.skill,
    difficulty=first_question.difficulty,
    question_text=first_question.question
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
        "question": first_question.question
        }
    }

@app.post("/interview/start-practice")
async def start_practice_interview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Standalone practice interview — no job application required.
    Candidate uploads CV, AI assesses their skills and conducts
    a tailored interview purely for self-assessment.
    """
    file_bytes = await file.read()

    resume_text = extract_resume_text(
        file_bytes=file_bytes,
        filename=file.filename.lower()
    )

    analysis_result = analyze_resume(resume_text)

    # Save candidate record
    candidate = Candidate(
        resume_score=analysis_result.score,
        resume_score_reason=analysis_result.reason,
        candidate_level="Unknown",
        job_fit=analysis_result.job_fit,
        resume_text=resume_text,
        analysis_json=json.dumps(analysis_result.model_dump())
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    interview_plan = create_interview_plan(analysis_result)

    interview = Interview(
        candidate_id=candidate.id,
        status="in_progress",
        difficulty=interview_plan.difficulty,
        total_questions=interview_plan.total_questions,
        plan_json=json.dumps(interview_plan.model_dump())
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    session = create_interview_session(analysis_result, interview_plan)

    session_db = InterviewSession(
        session_id=session["session_id"],
        interview_id=interview.id,
        current_skill_index=0,
        current_question_number=0,
        current_difficulty=interview_plan.difficulty,
        status="in_progress"
    )
    db.add(session_db)
    db.commit()

    session["candidate_db_id"] = candidate.id
    session["interview_db_id"] = interview.id
    session["is_practice"] = True  # flag so frontend can show practice label

    first_question = generate_next_question(session)

    question_row = InterviewQuestion(
        interview_id=interview.id,
        question_id=first_question.question_id,
        skill=first_question.skill,
        difficulty=first_question.difficulty,
        question_text=first_question.question
    )
    db.add(question_row)
    db.commit()

    set_current_question(session["session_id"], first_question)

    return {
        "session_id": session["session_id"],
        "resume_analysis": analysis_result,
        "interview_plan": interview_plan,
        "is_practice": True,
        "first_question": {
            "question_id": first_question.question_id,
            "skill": first_question.skill,
            "difficulty": first_question.difficulty,
            "question": first_question.question
        }
    }


@app.get("/interview/{session_id}")
def get_interview_state(
    session_id: str,
    db: Session = Depends(get_db)
):
    session_db = db.query(
        InterviewSession
    ).filter(
        InterviewSession.session_id == session_id
    ).first()
    
    if not session_db:
        raise HTTPException(
            status_code=400,
            detail="session not found"
        )
    
    return{
        "session_id" : session_db.session_id,
        "interview_id": session_db.interview_id,
        "current_question_number":session_db.current_question_number,
        "difficulty":session_db.current_difficulty,
        "status":session_db.status
    }


@app.post("/interview/answer")
async def submit_answer(
    data: dict,
    db: Session = Depends(get_db)
):
    session_id = data["session_id"]
    candidate_answer = data["answer"]

    session = session_store[session_id]

    current_question = session["current_question"]

    evaluation = evaluate_answer(
        current_question,
        candidate_answer
    )

    question_row = db.query(
        InterviewQuestion
    ).filter(
        InterviewQuestion.question_id == current_question.question_id,
    ).first()

    if question_row is None:
        raise HTTPException(
            status_code=404,
            detail="Question not found in database"
        )

    answer_row = InterviewAnswer(
        question_id=question_row.id,
        answer_text=candidate_answer,
        score=evaluation.score,
        feedback=evaluation.feedback,
        evaluation_json=json.dumps(
            evaluation.model_dump()
        )
    )
    db.add(answer_row)
    db.commit()

    updated_session = save_answer_evaluation(
        session_id,
        candidate_answer,
        evaluation
    )

    # Voice evaluation — scores communication quality from the answer text
    # Estimate duration from word count (avg speaking pace: 130 wpm)
    word_count = len(candidate_answer.split())
    estimated_duration = max((word_count / 130) * 60, 5)
    # voice_eval = evaluate_voice(
    #     transcript=candidate_answer,
    #     duration_seconds=estimated_duration
    # )
    # updated_session["voice_evaluations"].append(voice_eval)

    session_db = db.query(
        InterviewSession
    ).filter(
        InterviewSession.session_id == session_id
    ).first()

    session_db.current_question_number += 1
    session_db.current_difficulty = evaluation.next_difficulty

    db.commit()

    if not should_continue_interview(updated_session):
        final_report = generate_final_report(updated_session)

        report_row = InterviewReport(
            interview_id=session["interview_db_id"],
            overall_score=final_report.overall_score,
            score_reason=final_report.score_reason,
            recommendation=final_report.recommendation,
            report_json=json.dumps(
                final_report.model_dump()
            )
        )

        db.add(report_row)
        session_db.status = "completed"

        interview_row = db.query(Interview).filter(
            Interview.id == session["interview_db_id"]
        ).first()
        if interview_row:
            from datetime import datetime
            interview_row.status = "completed"
            interview_row.completed_at = datetime.utcnow()

        db.commit()

        return {
            "type": "completed",
            "evaluation": evaluation,
            # "voice_evaluation": voice_eval,
            "message": "Interview completed",
            "final_report": final_report
        }

    next_question = generate_next_question(updated_session)

    question_row = InterviewQuestion(
        interview_id=session["interview_db_id"],
        question_id=next_question.question_id,
        skill=next_question.skill,
        difficulty=next_question.difficulty,
        question_text=next_question.question
    )

    db.add(question_row)
    db.commit()
    db.refresh(question_row)

    set_current_question(session_id, next_question)

    return {
        "type": "question",
        "evaluation": evaluation,
        # "voice_evaluation": voice_eval,
        "next_question": {
            "question_id": next_question.question_id,
            "skill": next_question.skill,
            "difficulty": next_question.difficulty,
            "question": next_question.question
        }
    }


# ------------
# Post jobs
@app.post("/jobs")
def create_job(
    job: schemas.JobCreate,
    db: Session = Depends(get_db)
):
    new_job = Job(
        title=job.title,
        description=job.description,
        required_skills=job.required_skills,
        experience_level=job.experience_level
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return{
        "message":"Job created sucessfully",
        "job_id":new_job.id
    }

@app.get("/jobs")
def get_jobs(
    db: Session = Depends(get_db)
):
    jobs = db.query(Job).all()

    return jobs

@app.get("/jobs/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db)
): 
    job = db.query(Job).filter(
        Job.id == job_id
    ).first()

    if not job: 
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    
    return job


@app.post("/apply")
def apply_job(
    application: schemas.ApplicationCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(Application).filter(
        Application.candidate_id == application.candidate_id,
        Application.job_id == application.job_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Already applied"
        )

    new_application = Application(
        candidate_id = application.candidate_id,
        job_id = application.job_id
    )

    db.add(new_application)
    db.commit()
    db.refresh(new_application)

    return{
        "message":"Application submitted",
        "application_id": new_application.id
    }


@app.get("/applications/{candidate_id}")
def get_candidate_applications_simple(
    candidate_id: int,
    db: Session = Depends(get_db)
):
    applications = db.query(Application).filter(
        Application.candidate_id == candidate_id
    ).all()

    return applications


@app.post("/speech-to-text")
async def speech_to_text(file: UploadFile = File(...)):
    """
    Accepts an audio file and returns the transcribed text
    using Groq's Whisper model.
    """
    try:
        audio_bytes = await file.read()

        transcription = client.audio.transcriptions.create(
            file=(file.filename, audio_bytes),
            model="whisper-large-v3"
        )

        return {"text": transcription.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/check_eligibility")
async def check_eligibility(
    file: UploadFile = File(...),
    job_id: int = Form(...),
    db: Session = Depends(get_db)
):
    file_bytes = await file.read()

    resume_text = extract_resume_text(
        file_bytes=file_bytes,
        filename=file.filename.lower()
    )

    resume_analysis = analyze_resume(
        resume_text
    )

    job = db.query(Job).filter(
        Job.id == job_id
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    result = check_job_eligibility(
        resume_analysis,
        job
    )

    # Save candidate record first so we have a real candidate_id
    candidate = Candidate(
        resume_score=resume_analysis.score,
        resume_score_reason=resume_analysis.reason,
        candidate_level="Unknown",
        job_fit=resume_analysis.job_fit,
        resume_text=resume_text,
        analysis_json=json.dumps(resume_analysis.model_dump())
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    application = Application(
        candidate_id=candidate.id,
        job_id=job_id,
        eligibility_status="eligible" if result.eligible else "ineligible",
        eligibility_reason=", ".join(result.reasons),
        status="interview_pending" if result.eligible else "rejected"
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "eligible": result.eligible,
        "score": result.score,
        "reasons": result.reasons,
        "application_id": application.id,
        "candidate_id": candidate.id
    }


@app.get("/candidate/applications/{candidate_id}")
def get_candidate_applications_detailed(
    candidate_id: int,
    db: Session = Depends(get_db)
):

    applications = db.query(Application).filter(
        Application.candidate_id == candidate_id
    ).all()

    result = []

    for app in applications:

        job = db.query(Job).filter(
            Job.id == app.job_id
        ).first()

        result.append({
            "application_id": app.id,
            "job_title": job.title if job else "Unknown Job",
            "status": app.status,
            "eligibility_status": app.eligibility_status,
            "applied_at": app.applied_at
        })

    return result

@app.get("/report/{application_id}")
def get_report(
    application_id: int,
    db: Session = Depends(get_db)
):
    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    if not application.interview_id:
        raise HTTPException(
            status_code=404,
            detail="No interview linked to this application"
        )

    report = db.query(InterviewReport).filter(
        InterviewReport.interview_id == application.interview_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    report_data = json.loads(report.report_json) if report.report_json else {}

    return {
        "overall_score": report.overall_score,
        "score_reason": report.score_reason,
        "recommendation": report.recommendation,
        **report_data
    }


# ============================================================
# HR ENDPOINTS
# ============================================================

@app.get("/hr/stats")
def get_hr_stats(db: Session = Depends(get_db)):
    """Summary stats for HR dashboard"""

    total_jobs = db.query(Job).count()

    total_applications = db.query(Application).count()

    completed_interviews = db.query(Application).filter(
        Application.status == "interview_completed"
    ).count()

    shortlisted = db.query(Application).filter(
        Application.status == "shortlisted"
    ).count()

    return {
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "completed_interviews": completed_interviews,
        "shortlisted": shortlisted
    }


@app.get("/hr/applications")
def get_all_applications(db: Session = Depends(get_db)):
    """All applications with candidate and job info for HR"""

    applications = db.query(Application).all()

    result = []

    for app in applications:

        job = db.query(Job).filter(Job.id == app.job_id).first()
        candidate = db.query(Candidate).filter(Candidate.id == app.candidate_id).first()

        result.append({
            "application_id": app.id,
            "candidate_id": app.candidate_id,
            "job_title": job.title if job else "Unknown",
            "job_id": app.job_id,
            "status": app.status,
            "eligibility_status": app.eligibility_status,
            "eligibility_reason": app.eligibility_reason,
            "applied_at": app.applied_at,
            "resume_score": candidate.resume_score if candidate else None,
            "job_fit": candidate.job_fit if candidate else None
        })

    return result


@app.get("/hr/application/{application_id}")
def get_application_detail(application_id: int, db: Session = Depends(get_db)):
    """Full detail of one application for HR review"""

    app = db.query(Application).filter(Application.id == application_id).first()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    job = db.query(Job).filter(Job.id == app.job_id).first()
    candidate = db.query(Candidate).filter(Candidate.id == app.candidate_id).first()

    report = None
    if app.interview_id:
        report_row = db.query(InterviewReport).filter(
            InterviewReport.interview_id == app.interview_id
        ).first()
        if report_row:
            report = {
                "overall_score": report_row.overall_score,
                "score_reason": report_row.score_reason,
                "recommendation": report_row.recommendation,
                **(json.loads(report_row.report_json) if report_row.report_json else {})
            }

    return {
        "application_id": app.id,
        "status": app.status,
        "applied_at": app.applied_at,
        "eligibility_status": app.eligibility_status,
        "eligibility_reason": app.eligibility_reason,
        "job": {
            "id": job.id if job else None,
            "title": job.title if job else "Unknown",
            "experience_level": job.experience_level if job else None
        },
        "candidate": {
            "id": candidate.id if candidate else None,
            "resume_score": candidate.resume_score if candidate else None,
            "resume_score_reason": candidate.resume_score_reason if candidate else None,
            "candidate_level": candidate.candidate_level if candidate else None,
            "job_fit": candidate.job_fit if candidate else None
        },
        "report": report
    }


@app.patch("/hr/application/{application_id}/status")
def update_application_status(
    application_id: int,
    data: dict,
    db: Session = Depends(get_db)
):
    """HR can shortlist or reject a candidate"""

    allowed = ["shortlisted", "rejected", "interview_pending", "interview_completed"]

    new_status = data.get("status")
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {allowed}")

    app = db.query(Application).filter(Application.id == application_id).first()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = new_status
    db.commit()

    return {"message": "Status updated", "status": new_status}


@app.delete("/hr/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """HR can remove a job"""

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(job)
    db.commit()

    return {"message": "Job deleted"}


@app.patch("/hr/jobs/{job_id}/status")
def update_job_status(job_id: int, data: dict, db: Session = Depends(get_db)):
    """HR can close/reopen a job"""

    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = data.get("status", "active")
    db.commit()

    return {"message": "Job status updated", "status": job.status}
