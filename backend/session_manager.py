import uuid
session_store = {}

def create_interview_session(resume_analysis, interview_plan, job=None):
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "status": "in_progress",
         "resume_analysis": resume_analysis,
        "interview_plan": interview_plan,
        "job": job,
        "current_skill_index": 0,
        "current_question_number": 0,
        "asked_questions": [],
        "answers": [],
        "evaluations": [],
        "scores": {},
        "current_difficulty": interview_plan.difficulty,
    }
    session_store[session_id] = session
    return session

def set_current_question(session_id, question):
    session_store[session_id]["current_question"] = question
    return session_store[session_id]

def save_answer_evaluation(session_id, answer, evaluation):
    session = session_store[session_id]

    current_question = session["current_question"]

    session["asked_questions"].append(current_question)
    session["answers"].append({
        "question_id": current_question.question_id,
        "answer": answer
    })
    session["evaluations"].append(evaluation)
    session.setdefault("communication_scores", [])
    
    # session["communication_scores"].append(
    # session.get("current_communication")
    # )
    # Only record a communication score for voice answers.
    # Text answers never set current_communication, so skip instead of storing None.
    current_communication = session.pop("current_communication", None)
    if current_communication is not None:
        session["communication_scores"].append(current_communication)

    skill = current_question.skill

    if skill not in session["scores"]:
        session["scores"][skill] = []

    session["scores"][skill].append(evaluation.score)

    session["current_difficulty"] = evaluation.next_difficulty

    session["current_skill_index"] = (
        session["current_skill_index"] + 1
    ) % len(session["interview_plan"].skills_to_test)
    return session

def should_continue_interview(session):
    MAX_QUESTIONS = session["interview_plan"].total_questions

    if len(session["answers"]) >= MAX_QUESTIONS:
        session["status"] = "completed"
        return False

    return True