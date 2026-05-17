import json
import logging
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from prompts import CLEANUP_TRANSCRIPT_PROMPT, QUIZ_PROMPT, SUMMARY_PROMPT, TRANSCRIPT_PROMPT


load_dotenv()

logger = logging.getLogger(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

DEFAULT_MODEL = "gemini-2.5-flash"
GENERAL_FALLBACK_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash"]
TRANSCRIPT_MODEL = (
    os.getenv("GEMINI_TRANSCRIPT_MODEL")
    or os.getenv("GEMINI_TRANSCRIPT_FALLBACK_MODEL")
    or os.getenv("GEMINI_MODEL")
    or DEFAULT_MODEL
)
CLEANUP_MODEL = (
    os.getenv("GEMINI_TRANSCRIPT_CLEANUP_MODEL")
    or os.getenv("GEMINI_SUMMARY_MODEL")
    or os.getenv("GEMINI_MODEL")
    or DEFAULT_MODEL
)
SUMMARY_MODEL = os.getenv("GEMINI_SUMMARY_MODEL") or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL
QUIZ_MODEL = os.getenv("GEMINI_QUIZ_MODEL") or os.getenv("GEMINI_MODEL") or SUMMARY_MODEL


def unique_models(*models):
    result = []
    for model in models:
        if not model:
            continue
        if model not in result:
            result.append(model)
    return result


def generate_content_with_fallback(models, contents, config):
    last_error = None
    for model in unique_models(*models, *GENERAL_FALLBACK_MODELS):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as exc:
            last_error = exc
            logger.warning("Gemini model %s failed: %s", model, exc)

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}") from last_error


def parse_json(text):
    try:
        return json.loads(text.replace("```json", "").replace("```", "").strip())
    except json.JSONDecodeError as exc:
        logger.warning("Failed to parse Gemini JSON response: %s", exc)
        return {}


def transcribe_audio(path):
    uploaded = None
    try:
        uploaded = client.files.upload(file=path)
        # Temperature = 0.0 de giam sai so toi da khi chuyen audio thanh text.
        resp = generate_content_with_fallback(
            models=[TRANSCRIPT_MODEL, DEFAULT_MODEL],
            contents=[uploaded, TRANSCRIPT_PROMPT],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        return parse_json(resp.text)
    finally:
        if uploaded:
            try:
                client.files.delete(name=uploaded.name)
            except Exception as exc:
                logger.warning("Failed to delete uploaded Gemini file %s: %s", uploaded.name, exc)


def cleanup_transcript(text):
    resp = generate_content_with_fallback(
        models=[CLEANUP_MODEL, SUMMARY_MODEL],
        contents=f"{CLEANUP_TRANSCRIPT_PROMPT}\n\n{text}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
        ),
    )
    return parse_json(resp.text)


def summarize_lecture(text):
    resp = generate_content_with_fallback(
        models=[SUMMARY_MODEL],
        contents=f"{SUMMARY_PROMPT}\n\n{text}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    return parse_json(resp.text)


def generate_quiz(text, summary):
    prompt = f"{QUIZ_PROMPT}\n\nTranscript: {text}\nSummary: {json.dumps(summary)}"
    resp = generate_content_with_fallback(
        models=[QUIZ_MODEL, SUMMARY_MODEL],
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )
    return parse_json(resp.text)
