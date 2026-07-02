import os
import json
import re

from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

from backend.models import EligibilityResult

# load_dotenv()

# client = Groq(
#     api_key=os.getenv("GROQ_API_KEY")
# )

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY not found. Check backend/.env")

client = Groq(api_key=api_key)


def extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found")

    return match.group(0)


def check_job_eligibility(
    resume_analysis,
    job
):
    prompt = f"""
You are an expert recruitment screening system.

Determine whether the candidate is eligible for the job.

Resume Analysis:
{resume_analysis}

Job Title:
{job.title}

Job Description:
{job.description}

Required Skills:
{job.required_skills}

Experience Level:
{job.experience_level}

Return ONLY valid JSON.

{{
    "eligible": true,
    "score": 0,
    "reasons": []
}}

Rules:

- Score from 0 to 100
- Compare skills carefully
- Compare experience level
- Compare job fit
- If score >= 85:
  eligible = true
- Else:
  eligible = false

Reasons should explain why.
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    json_string = extract_json(content)

    data = json.loads(json_string)

    return EligibilityResult(**data)