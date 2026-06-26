import os
import json
import re

from pathlib import Path
from groq import Groq
from dotenv import load_dotenv

from backend.models import ResumeAnalysis

# load_dotenv()

# client = Groq(
#     api_key=os.getenv("GROQ_API_KEY")
# )
# print(os.getenv("GROQ_API_KEY"))

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY not found. Check backend/.env")

client = Groq(api_key=api_key)

def extract_json(text: str):
    """
    Extract JSON object from AI response
    """

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found in AI response")

    return match.group(0)


def analyze_resume(resume_text: str):

#     prompt = f"""
# You are an expert resume reviewer.

# Analyze this student resume.

# Return ONLY valid JSON.

# Format:

# {{
#   "score": 80,
#   "skills": ["Python", "HTML"],
#   "strengths": ["Good projects"],
#   "weaknesses": ["No internships"],
#   "suggestions": ["Add certifications"],
#   "job_fit": "Frontend Developer",
#   "reason": "The resume demonstrates strong analytical skills and experience with data visualization tools, which are valuable for a Frontend Developer Internship. However, the lack of measurable achievements and limited technical skills may hinder the candidate's competitiveness for this role. By adding quantifiable results to the project section and expanding technical skills, the candidate can improve their chances of securing a Frontend Developer Internship."
# }}

# Resume:
# {resume_text}
# """

    prompt = f"""
You are an expert ATS resume reviewer and career coach specializing in student and entry-level resumes.

Analyze the resume text provided below and evaluate it for:
- Overall resume quality
- Technical and soft skills
- Project quality
- Internship/job readiness
- ATS compatibility
- Relevance to likely entry-level roles

Return ONLY valid JSON.
Do not include markdown, explanations, comments, or text outside the JSON.
Use double quotes for all JSON keys and string values.
Do not use trailing commas.

Scoring rules:
- Score must be an integer from 0 to 100.
- 90-100: Excellent, highly job-ready resume
- 75-89: Strong resume with minor improvements needed
- 60-74: Average resume with several gaps
- 40-59: Weak resume needing major improvements
- 0-39: Very poor or incomplete resume

Return the JSON in exactly this structure:

{{
  "score": 0,
  "skills": [],
  "strengths": [],
  "weaknesses": [],
  "suggestions": [],
  "job_fit": "",
  "reason": "",
  "ats_feedback": "",
  "missing_keywords": [],
  "improved_summary": "",
  "priority_improvements": []
}}

Field requirements:
- "skills": Extract only skills explicitly mentioned in the resume.
- "strengths": List the strongest parts of the resume.
- "weaknesses": List specific weaknesses or missing sections.
- "suggestions": Give practical, resume-focused improvement suggestions.
- "job_fit": Suggest the most suitable entry-level role or internship.
- "reason": Explain why this role fits the candidate based on the resume.
- "ats_feedback": Comment on ATS readability, keywords, formatting, and clarity.
- "missing_keywords": List important keywords the candidate should add for the suggested role.
- "improved_summary": Write a better 2-3 sentence resume summary for the candidate.
- "priority_improvements": List the top 3 improvements the candidate should make first.

Important:
- Be specific and constructive.
- Do not invent experience, internships, certifications, or skills that are not present.
- If information is missing, mention it clearly.
- Keep all array items concise.
- Ensure the output is valid JSON that can be parsed directly with json.loads().

Resume:
{resume_text}
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

    # print("\nAI RAW RESPONSE:\n")
    # print(content)

    # CLEAN RESPONSE

    json_string = extract_json(content)

    data = json.loads(json_string)

    return ResumeAnalysis(**data)

# print("\n\nTESTING RESUME ANALYSIS:\n")
# print(analyze_resume("").skills)