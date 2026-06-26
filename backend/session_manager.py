import uuid
session_store = {}

def create_interview_session(resume_analysis, interview_plan):
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "status": "in_progress",
         "resume_analysis": resume_analysis,
        "interview_plan": interview_plan,
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
    total_answered = len(session["answers"])
    total_questions = session["interview_plan"].total_questions

    if total_answered >= total_questions:
        session["status"] = "completed"
        return False

    return True