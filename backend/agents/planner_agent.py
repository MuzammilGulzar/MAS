# # from resume_parser_agent import analyze_resume
# import os
# import json
# import re
# from huggingface_hub import InferenceClient

# from groq import Groq
# from dotenv import load_dotenv

# from backend.models import InterviewPlan
# load_dotenv()

# # client = Groq(
# #     api_key=os.getenv("GROQ_API_KEY")
# # )
# client = InferenceClient(
#     api_key=os.getenv("HF_TOKEN")
# )

# api_url = "https://router.huggingface.co/v1/chat/completions"

# def extract_json(text: str):
#     match = re.search(r"\{.*\}", text, re.DOTALL)

#     if not match:
#         raise ValueError("No JSON found in AI response")

#     return match.group(0)

# def create_interview_plan(resume_analysis):
#     prompt = f"""
# You are an expert interview planner.
# Create a detailed interview plan for a candidate based on their resume analysis.
# Resume Analysis:
# skills: {resume_analysis.skills}
# score: {resume_analysis.score}
# job_fit: {resume_analysis.job_fit}
# strengths: {resume_analysis.strengths}
# weaknesses: {resume_analysis.weaknesses}

# Task: Create an interview plan.
# Return ONLY valid JSON with these fields:
# target_role, candidate_level, skills_to_test, difficulty, total_questions, evaluation_criteria
# """
#     response = client.chat.completions.create(
#         model="openai/gpt-oss-120b",
#         messages=[
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ],
#         temperature=0
#     )
#     try:
#         content = response.choices[0].message.content

#         print("\nINTERVIEW PLAN RAW RESPONSE:\n")
#         print(content)

#         json_string = extract_json(content)

#         data = json.loads(json_string)

#         interview_plan = InterviewPlan(**data)

#         return interview_plan
#     except Exception as e:
#         print("Error parsing interview plan:", e)
#         raise e

import os
import json
import re
from pathlib import Path

from huggingface_hub import InferenceClient
from dotenv import load_dotenv

from backend.models import InterviewPlan


# Load backend/.env explicitly
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

hf_token = os.getenv("HF_TOKEN")

if not hf_token:
    raise RuntimeError("HF_TOKEN not found. Check backend/.env")

client = InferenceClient(api_key=hf_token)


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found in AI response")

    return match.group(0)


def normalize_interview_plan_data(data: dict) -> dict:
    """
    Makes AI output match the Pydantic InterviewPlan schema.
    This prevents crashes when the model returns slightly different JSON shapes.
    """

    # Fix evaluation_criteria if model returns a dictionary
    criteria = data.get("evaluation_criteria")

    if isinstance(criteria, dict):
        data["evaluation_criteria"] = [
            f"{key}: {value}" for key, value in criteria.items()
        ]

    elif isinstance(criteria, str):
        data["evaluation_criteria"] = [criteria]

    # Fix skills_to_test if model returns a string or dictionary
    skills = data.get("skills_to_test")

    if isinstance(skills, dict):
        data["skills_to_test"] = [
            f"{key}: {value}" for key, value in skills.items()
        ]

    elif isinstance(skills, str):
        data["skills_to_test"] = [skills]

    # Fix total_questions if model returns "10" instead of 10
    total_questions = data.get("total_questions")

    if isinstance(total_questions, str):
        number_match = re.search(r"\d+", total_questions)
        if number_match:
            data["total_questions"] = int(number_match.group(0))

    return data


def create_interview_plan(resume_analysis):
#     prompt = f"""
# You are an expert interview planner.

# Create a detailed interview plan for a candidate based on their resume analysis.

# Resume Analysis:
# skills: {resume_analysis.skills}
# score: {resume_analysis.score}
# job_fit: {resume_analysis.job_fit}
# strengths: {resume_analysis.strengths}
# weaknesses: {resume_analysis.weaknesses}

# Return ONLY valid JSON.

# The JSON must follow this exact structure:

# {{
#   "target_role": "string",
#   "candidate_level": "string",
#   "skills_to_test": [
#     "string"
#   ],
#   "difficulty": "string",
#   "total_questions": 10,
#   "evaluation_criteria": [
#     "string"
#   ]
# }}

# Important:
# - evaluation_criteria must be a list of strings.
# - skills_to_test must be a list of strings.
# - total_questions must be an integer.
# - Do not return markdown.
# - Do not return explanations.
# - Do not wrap JSON in ```json.
# """

    prompt = f"""
You are an expert technical interview planner and hiring evaluator.

Create a structured interview plan for a candidate based only on the provided resume analysis.

Your goal is to design an interview plan that tests:
- The candidate's strongest claimed skills
- The candidate's weaker or unclear areas
- Practical readiness for the suggested role
- Communication and problem-solving ability
- Role-specific technical fundamentals

Resume Analysis:
Skills:
{resume_analysis.skills}

Resume Score:
{resume_analysis.score}

Suggested Job Fit:
{resume_analysis.job_fit}

Strengths:
{resume_analysis.strengths}

Weaknesses:
{resume_analysis.weaknesses}

Return ONLY valid JSON.
Do not include markdown, comments, explanations, or text outside the JSON.
Use double quotes for all JSON keys and string values.
Do not use trailing commas.
Ensure the JSON can be parsed directly with json.loads().

The JSON must follow this exact structure:

{{
  "target_role": "",
  "candidate_level": "",
  "skills_to_test": [],
  "difficulty": "",
  "total_questions": 0,
  "question_distribution": {{
    "technical": 0,
    "practical": 0,
    "project_based": 0,
    "behavioral": 0
  }},
  "evaluation_criteria": [],
  "focus_areas": [],
  "red_flags_to_check": []
}}

Field requirements:
- "target_role": Use the suggested job fit from the resume analysis.
- "candidate_level": Choose exactly one of: "Beginner", "Entry-level", "Intermediate", or "Advanced".
- "skills_to_test": Include 4-8 skills selected from the resume analysis and role requirements.
- "difficulty": Choose exactly one of: "Easy", "Medium", or "Hard".
- "total_questions": Determine dynamically based on candidate level.

Rules:
- Beginner: 8 questions
- Entry-level/Fresher: 12 questions
- Intermediate: 18 questions
- Advanced: 25 questions
- "question_distribution": The values must add up to 10.
- "evaluation_criteria": Include 4-7 concise criteria used to judge interview performance.
- "focus_areas": Include the most important areas the interview should explore.
- "red_flags_to_check": Include possible concerns based on resume weaknesses.

Difficulty rules:
- If resume score is 85 or above, use "Hard" unless weaknesses are significant.
- If resume score is between 65 and 84, use "Medium".
- If resume score is below 65, use "Easy".
- For student resumes or candidates with no internship/job experience, prefer "Easy" or "Medium".
- Do not choose "Advanced" candidate level unless the resume shows strong professional experience.

Question Count Rules:

- Beginner → 8 questions
- Entry-level → 12 questions
- Intermediate → 18 questions
- Advanced → 25 questions

Candidates with:
- no experience
- student projects only
- fresher resumes

should usually be Beginner or Entry-level.

Candidates with:
- multiple internships
- 1-3 years experience

should usually be Intermediate.

Candidates with:
- 4+ years professional experience
- leadership responsibilities
- strong production experience

should usually be Advanced.

Important:
- Base the plan only on the provided resume analysis.
- Do not invent skills, jobs, internships, or achievements.
- Prioritize practical, role-relevant assessment.
- Include weaker areas in "red_flags_to_check" instead of ignoring them.
- Keep all array items concise and professional.
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    try:
        content = response.choices[0].message.content

        # print("\nINTERVIEW PLAN RAW RESPONSE:\n")
        # print(content)

        json_string = extract_json(content)

        data = json.loads(json_string)

        data = normalize_interview_plan_data(data)

        level = data.get("candidate_level", "").lower()
        
        if level == "beginner":
            data["total_questions"] = 8

        elif level == "entry-level":
            data["total_questions"] = 15

        elif level == "intermediate":
            data["total_questions"] = 18

        elif level == "advanced":
            data["total_questions"] = 25

        else:
            data["total_questions"] = 6

        interview_plan = InterviewPlan(**data)

        return interview_plan

    except Exception as e:
        print("Error parsing interview plan:", e)
        raise e