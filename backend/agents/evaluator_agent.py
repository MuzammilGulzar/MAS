# from resume_parser_agent import analyze_resume
import os
import json
import re

from groq import Groq
from dotenv import load_dotenv

from backend.models import EvaluationResult
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

def evaluate_answer(question_object, candidate_answer):
#     prompt = f"""
# You are an expert interviewer evaluating a candidate's answer to a technical interview question.
# Question ID: {question_object.question_id}
# Skill: {question_object.skill}
# Difficulty: {question_object.difficulty}
# Question: {question_object.question}
# expected_answer_points: {question_object.expected_answer_points}
# Candidate Answer: {candidate_answer}

# Evaluate the candidate's answer based on the expected answer points.
# give score out of 10
# say if correct
# give feedback
# list missing points
# decide next difficulty (easy/medium/hard)
# decide if follow-up question is needed

# Return ONLY valid JSON.
# The score must be an integer from 0 to 10.
# The next_difficulty must be one of: easy, medium, hard.
# Format:
# {{
#   "question_id": "{question_object.question_id}",
#   "score": 0,
#   "is_correct": true,
#   "feedback": "short useful feedback",
#   "missing_points": ["point 1", "point 2"],
#   "next_difficulty": "easy",
#   "should_ask_followup": false
# }}
# """
    

    prompt = f"""
You are an expert technical interview evaluator.

Evaluate the candidate's answer to the interview question using the expected answer points.

Your evaluation must assess:
- Technical correctness
- Coverage of expected answer points
- Clarity and completeness
- Practical understanding
- Any incorrect or misleading statements

Question Details:

Question ID:
{question_object.question_id}

Skill:
{question_object.skill}

Difficulty:
{question_object.difficulty}

Question:
{question_object.question}

Expected Answer Points:
{question_object.expected_answer_points}

Candidate Answer:
{candidate_answer}

Return ONLY valid JSON.
Do not include markdown, comments, explanations, or text outside the JSON.
Use double quotes for all JSON keys and string values.
Do not use trailing commas.
Ensure the JSON can be parsed directly with json.loads().

Scoring rules:
- Score must be an integer from 0 to 10.
- 10: Excellent answer covering all key points with clear explanation.
- 8-9: Strong answer with minor missing details.
- 6-7: Partially correct answer with some gaps.
- 4-5: Basic understanding but major points missing.
- 1-3: Weak answer with very limited correctness.
- 0: Incorrect, irrelevant, empty, or no meaningful answer.

Correctness rules:
- Set "is_correct" to true only if the answer is mostly correct and score is 7 or higher.
- Set "is_correct" to false if the answer is incorrect, incomplete, vague, or score is below 7.
- Do not give high scores for keyword matching alone.
- Penalize hallucinated, incorrect, or unrelated claims.

Difficulty adjustment rules:
- If score is 8-10, set "next_difficulty" one level higher when possible.
- If score is 5-7, keep the same difficulty.
- If score is 0-4, reduce difficulty by one level when possible.
- Difficulty levels are: "easy", "medium", "hard".
- Do not go below "easy" or above "hard".

Follow-up rules:
- Set "should_ask_followup" to true if the answer is partially correct, vague, missing important points, or needs clarification.
- Set "should_ask_followup" to false if the answer is clearly strong or clearly incorrect with no useful follow-up needed.

Return the JSON in exactly this structure:

{{
  "question_id": "{question_object.question_id}",
  "skill": "{question_object.skill}",
  "difficulty": "{question_object.difficulty}",
  "score": 0,
  "is_correct": false,
  "feedback": "",
  "missing_points": [],
  "covered_points": [],
  "incorrect_points": [],
  "next_difficulty": "easy",
  "should_ask_followup": false,
  "followup_reason": ""
}}

Field requirements:
- "question_id": Use the provided question ID.
- "skill": Use the provided skill.
- "difficulty": Use the provided difficulty.
- "score": Integer from 0 to 10.
- "is_correct": Boolean.
- "feedback": Short, useful, constructive feedback.
- "missing_points": Expected answer points not covered by the candidate.
- "covered_points": Expected answer points covered correctly.
- "incorrect_points": Any incorrect, vague, or misleading parts of the candidate answer.
- "next_difficulty": Choose exactly one of: "easy", "medium", or "hard".
- "should_ask_followup": Boolean.
- "followup_reason": Briefly explain why a follow-up is or is not needed.

Important:
- Base the evaluation only on the question, expected answer points, and candidate answer.
- Do not invent extra requirements beyond the expected answer points.
- Be fair but strict.
- Keep all array items concise.
- If the candidate answer is empty, irrelevant, or says "I don't know", give a score of 0.
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
        response_content = response.choices[0].message.content
        print("\nEVALUATION RAW RESPONSE:\n")
        print(response_content)
        json_string = extract_json(response_content)
        
        print("\n================ EXTRACTED JSON ================\n")
        print(json_string)
        
        data = json.loads(json_string)
        evaluation_result = EvaluationResult(**data)
        return evaluation_result
    except Exception as e:
        print("Error evaluating answer:", e)
        raise e