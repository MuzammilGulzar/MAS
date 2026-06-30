from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def evaluate_communication(transcript: str):
    """
    AI-based communication analysis.
    """

    word_count = len(transcript.split())

    prompt = f"""
Evaluate the communication quality of this interview answer.

Transcript:
{transcript}

Return ONLY valid JSON in this format:

{{
    "clarity": 0,
    "confidence": 0,
    "fluency": 0
}}

Rules:
- Scores must be integers from 1 to 10.
- Be realistic.
- Short or meaningless answers should receive low scores.
- Do not include explanations.
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

    data = json.loads(response.choices[0].message.content)

    data["word_count"] = word_count

    return data