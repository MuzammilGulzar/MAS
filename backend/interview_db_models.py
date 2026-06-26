from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text, DateTime
from datetime import datetime

from backend.database import Base

# ------------------------------------------------------------------
# candidate TABLE
class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, nullable=True) # Link to User table
    
    resume_score = Column(Float)
    
    candidate_level = Column(String)
    
    job_fit = Column(String)
    
    resume_text = Column(Text)
    
    analysis_json = Column(Text)

    resume_score_reason = Column(Text)

    created_at = Column(
        DateTime, 
        default=datetime.utcnow
    )

# ------------------------------------------------------------------
# interview results TABLE
class InterviewReport(Base):
    __tablename__ = "interview_reports"

    id = Column(Integer, primary_key=True)

    interview_id = Column(Integer, ForeignKey("interviews.id"))

    overall_score = Column(Float)
    score_reason = Column(Text)

    recommendation = Column(String)
    report_json = Column(Text) # Store the full report as JSON string

# ------------------------------------------------------------------
# interview TABLE
class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True)

    candidate_id = Column(
        Integer, 
        ForeignKey("candidates.id")
    )

    status = Column(
        String, 
        default="in_progress"
    )

    difficulty = Column(String)

    total_questions = Column(Integer)

    plan_json = Column(Text)

    started_at = Column(
        DateTime, 
        default=datetime.utcnow
    )

    completed_at = Column(
        DateTime, 
        nullable=True
    )

# ------------------------------------------------------------------
# INTERVIEW QUESTIONS
class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True)

    interview_id = Column(
        Integer,
        ForeignKey("interviews.id")
    )

    question_id = Column(String)

    skill = Column(String)

    difficulty = Column(String)

    question_text = Column(Text)

# ------------------------------------------------------------------
# ANSWERS
class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True)

    question_id = Column(
        Integer,
        ForeignKey("interview_questions.id")
    )

    answer_text = Column(Text)

    score = Column(Float)

    feedback = Column(Text)

    evaluation_json = Column(Text) # Store full evaluation details as JSON string   


# ----------------------------------------------------
# INTERVIEW SESSION LOGS

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True)

    session_id = Column(
        String,
        unique=True,
        index=True
    )

    interview_id = Column(
        Integer,
        ForeignKey("interviews.id")
    )

    current_skill_index = Column(Integer)

    current_question_number = Column(Integer)

    current_difficulty = Column(String)

    status = Column(
        String,
        default="in_progress"
    )

    last_question_id = Column(
        String,
        nullable=True
    )


# ---------------------------------------------
# JOBS
# ------------------------------------------------------------------
# JOBS
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)

    title = Column(String)

    description = Column(Text)

    required_skills = Column(Text)

    experience_level = Column(String)

    status = Column(
        String,
        default="active"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    hr_id = Column(Integer, ForeignKey("users.id"))

# ------------------------------------------------------------------
# JOB APPLICATIONS
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)

    candidate_id = Column(
        Integer,
        ForeignKey("candidates.id")
    )

    job_id = Column(
        Integer,
        ForeignKey("jobs.id")
    )

    interview_id = Column(
        Integer,
        ForeignKey("interviews.id"),
        nullable=True
    )
    
    status = Column(
        String,
        default="applied"
    )

    applied_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    eligibility_status = Column(
        String,
        nullable=True
    )

    eligibility_reason = Column(
        Text,
        nullable=True
    )