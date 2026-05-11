import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from prompts import TRANSCRIPT_PROMPT, SUMMARY_PROMPT, CLEANUP_TRANSCRIPT_PROMPT, QUIZ_PROMPT

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = os.getenv("GEMINI_MODEL")

def parse_json(text):
    try:
        return json.loads(text.replace("```json", "").replace("```", "").strip())
    except: return {}

def transcribe_audio(path):
    uploaded = client.files.upload(file=path)
    # Temperature = 0.0 để giảm sai số tối đa
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=[uploaded, TRANSCRIPT_PROMPT],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.0)
    )
    client.files.delete(name=uploaded.name)
    return parse_json(resp.text)

def cleanup_transcript(text):
    resp = client.models.generate_content(
        model=MODEL_NAME, contents=f"{CLEANUP_TRANSCRIPT_PROMPT}\n\n{text}",
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.0)
    )
    return parse_json(resp.text)

def summarize_lecture(text):
    resp = client.models.generate_content(
        model=MODEL_NAME, contents=f"{SUMMARY_PROMPT}\n\n{text}",
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2)
    )
    return parse_json(resp.text)

def generate_quiz(text, summary):
    prompt = f"{QUIZ_PROMPT}\n\nTranscript: {text}\nSummary: {json.dumps(summary)}"
    resp = client.models.generate_content(
        model=MODEL_NAME, contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.5)
    )
    return parse_json(resp.text)