from pydantic import BaseModel
from typing import List, Dict

class ResumeAnalysis(BaseModel):
    score: int
    skills: List[str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    job_fit: str
    reason: str

# interview planner
class InterviewPlan(BaseModel):
    target_role: str
    candidate_level: str
    skills_to_test: List[str]
    difficulty: str
    total_questions: int
    evaluation_criteria: List[str]

# Questions
class QuestionObject(BaseModel):
    question_id: str
    skill: str
    difficulty: str
    question_type: str
    question: str
    expected_answer_points: List[str]

# Evaluation
# class EvaluationResult(BaseModel):
#     question_id: str
#     score: int
#     is_correct: bool
#     feedback: str
#     missing_points: List[str]
#     next_difficulty: str
#     should_ask_followup: bool
class EvaluationResult(BaseModel):
    question_id: str
    skill: str
    difficulty: str

    score: int
    is_correct: bool

    feedback: str

    missing_points: List[str]
    covered_points: List[str]
    incorrect_points: List[str]

    next_difficulty: str
    should_ask_followup: bool

    followup_reason: str
    # ---------
    # reason: str


# Report
class FinalReport(BaseModel):
    overall_score: int
    score_reason: str
    
    recommendation: str

    skill_scores: Dict[str, float]

    strengths: List[str]
    weaknesses: List[str]

    key_observations: List[str]

    resume_interview_alignment: str

    communication_feedback: str

    technical_feedback: str

    hiring_risk: str

    communication_metrics: Dict[str, float]

    final_feedback: str

    next_steps: List[str]

class EligibilityResult(BaseModel):
    eligible: bool
    score: int
    reasons: list[str]