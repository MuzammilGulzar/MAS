# from resume_parser_agent import analyze_resume
import os
import json
import re

from groq import Groq
from dotenv import load_dotenv

from backend.models import QuestionObject
load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found in AI response")

    return match.group(0)


def generate_next_question(session):
    # interview_plan = session["interview_plan"]
    # resume_analysis = session["resume_analysis"]
    # current_skill_index = session["current_skill_index"]
    # current_skill = interview_plan.skills_to_test[current_skill_index]
    # difficulty = session["current_difficulty"]
    # previous_questions = session["asked_questions"]

    interview_plan = session["interview_plan"]
    resume_analysis = session["resume_analysis"]
    job = session.get("job")
    current_skill_index = session["current_skill_index"]
    current_skill = interview_plan.skills_to_test[current_skill_index]
    difficulty = session["current_difficulty"]
    previous_questions = session["asked_questions"]

    job_context = ""
    if job is not None:
        job_context = f"""
        This question is for a REAL interview for the job below. Prefer connecting the question to the candidate's
        actual project experience (from Resume Skills/Strengths) while testing the job's required skill.

        Job Title:
        {job.title}

        Job Description:
        {job.description}

        Job Required Skills:
        {job.required_skills}
        """

#     prompt = f"""
# You are an expert question generator for technical interviews.
# Generate one interview question. 
# Skill: {current_skill}
# Difficulty:{ difficulty}
# Target Role:{ interview_plan.target_role}
# Candidate Level:{ interview_plan.candidate_level}
# Previous Questions:{ previous_questions}
# Do not repeat previous questions.
# Return ONLY valid JSON.
# Format:
# {{
#     "question_id": "unique_question_id",
#     "skill": {current_skill},
#     "difficulty": {difficulty},
#     "question_type": "conceptual/practical/project_based/behavioral",
#     "question": "the interview question text",
#     "expected_answer_points": ["key point 1", "key point 2", "..."]
# }}
# """


    prompt = f"""
You are an expert technical interview question generator.

Generate exactly ONE interview question for the candidate.

Your question must be:
- Relevant to the target role
- Appropriate for the candidate level
- Matched to the given skill and difficulty
- Clear, specific, and interview-ready
- Different from all previous questions

Input Data:

Skill:
{current_skill}

Difficulty:
{difficulty}

Target Role:
{interview_plan.target_role}

Candidate Level:
{interview_plan.candidate_level}
{job_context}
Resume Skills:
{resume_analysis.skills}

Strengths:
{resume_analysis.strengths}

Weaknesses:
{resume_analysis.weaknesses}

Previous Questions:
{previous_questions}

Return ONLY valid JSON.
Do not include markdown, comments, explanations, or text outside the JSON.
Use double quotes for all JSON keys and string values.
Do not use trailing commas.
Ensure the JSON can be parsed directly with json.loads().

Question generation rules:
- Do not repeat or closely rephrase any previous question.
- The question must test the specified skill directly.
- The difficulty must match the requested difficulty.
- For beginner level, focus on fundamentals and simple practical understanding.
- For intermediate level, include applied reasoning, debugging, or real-world scenarios.
- For advanced level, include architecture, optimization, trade-offs, or edge cases.
- Prefer practical and role-relevant questions over generic textbook questions.
- Avoid overly broad questions.
- Avoid asking multiple unrelated questions in one question.
- Do not include the answer inside the question.

Choose exactly one question_type from:
- "conceptual"
- "practical"
- "project_based"
- "behavioral"

Return the JSON in exactly this structure:

{{
  "question_id": "unique_question_id",
  "skill": "{current_skill}",
  "difficulty": "{difficulty}",
  "question_type": "conceptual",
  "question": "the interview question text",
  "expected_answer_points": []
}}

Field requirements:
- "question_id": Generate a short unique ID using the skill and difficulty, for example "python_intermediate_001".
- "skill": Use the provided skill.
- "difficulty": Use the provided difficulty.
- "question_type": Choose the most suitable type from the allowed list.
- "question": Write one clear interview question.
- "expected_answer_points": Provide 3-6 concise points that a strong answer should cover.

Important:
- Base the question only on the provided skill, difficulty, role, and candidate level.
- Do not invent candidate experience.
- Keep the question professional and suitable for a real interview.
- Make expected_answer_points specific enough to support automated answer evaluation.
"""

    # Call the AI model with the prompt and return the generated question as a QuestionObject
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.5
    )
    try:
        content = response.choices[0].message.content
        json_string = extract_json(content)
        data = json.loads(json_string)
        question = QuestionObject(**data)
        return question
    except Exception as e:
        print("Error generating question:", e)
        return e