import os
import json
import re

from groq import Groq
from dotenv import load_dotenv

from backend.models import FinalReport

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# def extract_json(text: str):
#     match = re.search(r"\{.*\}", text, re.DOTALL)

#     if not match:
#         raise ValueError("No JSON found in AI response")

#     return match.group(0)

def extract_json(text: str) -> str:
    # Remove markdown code blocks if present
    text = re.sub(r"```json|```", "", text).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON found in response")
    
    # match = re.search(r"\{.*\}", text, re.DOTALL)
    # if not match:
    #     raise ValueError("No JSON found in response")
    
    # json_str = match.group(0)
    
    # # Fix single quotes → double quotes
    # json_str = json_str.replace("'", '"')
    
    # # Remove trailing commas before } or ]
    # json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
    
    #  # Fix missing comma between fields (e.g. "value" "key" → "value", "key")
    # json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)
    
    # # Remove any control characters that break JSON
    # json_str = re.sub(r'[\x00-\x1f\x7f](?<!["\n\r\t])', '', json_str)
    
    return text[start:end+1]

def calculate_skill_scores(scores):
    skill_scores = {}

    for skill, score_list in scores.items():
        if len(score_list) > 0:
            skill_scores[skill] = sum(score_list) / len(score_list)

    return skill_scores


def calculate_overall_score(evaluations):
    if len(evaluations) == 0:
        return 0

    total = 0

    for evaluation in evaluations:
        total += evaluation.score

    return round(total / len(evaluations))


def generate_final_report(session):
    resume_analysis = session["resume_analysis"]
    interview_plan = session["interview_plan"]
    answers = session["answers"]
    evaluations = session["evaluations"]
    scores = session["scores"]

    skill_scores = calculate_skill_scores(scores)
    overall_score = calculate_overall_score(evaluations)

#     prompt = f"""
# You are an expert interview assessor.

# Generate a final interview report for this candidate.

# Resume Analysis:
# {resume_analysis}

# Interview Plan:
# {interview_plan}

# Candidate Answers:
# {answers}

# Evaluations:
# {evaluations}

# Skill Scores:
# {skill_scores}

# Overall Score:
# {overall_score}

# Return ONLY valid JSON.

# Format:
# {{
#   "overall_score": {overall_score},
#   "recommendation": "Shortlist / Reject / Needs another round",
#   "skill_scores": {skill_scores},
#   "strengths": ["strength 1", "strength 2"],
#   "weaknesses": ["weakness 1", "weakness 2"],
#   "final_feedback": "short final feedback"
# }}
# """
    prompt = f"""
You are an expert technical interview assessor and hiring evaluator.

Generate a final interview report for the candidate using the provided resume analysis, interview plan, candidate answers, individual evaluations, skill scores, and overall score.

Your task is to assess:
- Candidate-job fit
- Technical competence
- Communication clarity
- Problem-solving ability
- Consistency between resume claims and interview performance
- Strengths, weaknesses, and hiring risk

Return ONLY valid JSON.
Do not include markdown, comments, explanations, or text outside the JSON.
Use double quotes for all JSON keys and string values.
Do not use trailing commas.
Ensure the JSON can be parsed directly with json.loads().

Recommendation rules:
- "Shortlist": Use only if the candidate shows strong role fit, solid answers, and acceptable skill scores.
- "Needs another round": Use if the candidate shows potential but has unclear, incomplete, or inconsistent performance.
- "Reject": Use if the candidate has major skill gaps, weak answers, or poor alignment with the role.

Input Data:

Resume Analysis:
{resume_analysis}

Interview Plan:
{interview_plan}

Candidate Answers:
{answers}

Evaluations:
{evaluations}

Skill Scores:
{skill_scores}

Overall Score:
{overall_score}

Return the JSON in exactly this structure:

{{
  "overall_score": {overall_score},
  "score_reason":"
  "recommendation": "Shortlist / Reject / Needs another round",
  "skill_scores": {skill_scores},
  "strengths": [],
  "weaknesses": [],
  "key_observations": [],
  "resume_interview_alignment": "",
  "communication_feedback": "",
  "technical_feedback": "",
  "hiring_risk": "Low / Medium / High",
  "final_feedback": "",
  "next_steps": []
}}

Field requirements:
- "overall_score": Use the provided overall score.
- "score_reason": Explain why the candidate received the overall score. Summarize the strongest and weakest areas that contributed to the score. Use evidence from the interview evaluations.
- "recommendation": Choose exactly one of: "Shortlist", "Reject", or "Needs another round".
- "skill_scores": Use the provided skill scores.
- "strengths": List 2-5 specific strengths shown by the candidate.
- "weaknesses": List 2-5 specific weaknesses or gaps.
- "key_observations": Include important patterns from answers and evaluations.
- "resume_interview_alignment": Explain whether interview performance supports the resume claims.
- "communication_feedback": Assess clarity, confidence, structure, and completeness of answers.
- "technical_feedback": Assess technical depth, correctness, and practical understanding.
- "hiring_risk": Choose exactly one of: "Low", "Medium", or "High".
- "final_feedback": Provide a concise professional summary of the candidate's performance.
- "next_steps": Suggest what should happen next, such as shortlist, reject, assign task, or conduct another round.

Important:
- Be fair, specific, and evidence-based.
- Do not invent achievements, skills, or experience.
- Base the report only on the provided data.
- If candidate answers are missing or incomplete, reflect that in the weaknesses and recommendation.
- Keep all array items concise and professional.
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

    try:
        content = response.choices[0].message.content

        # print("\nFINAL REPORT RAW RESPONSE:\n")
        # print(content)

        json_string = extract_json(content)

        data = json.loads(json_string)

        final_report = FinalReport(**data)

        return final_report

    except Exception as e:
        print("Error generating final report:", e)
        raise e