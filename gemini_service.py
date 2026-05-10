import json
import os
import time
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from google import genai

from prompts import (
    CLEANUP_TRANSCRIPT_PROMPT,
    QUIZ_PROMPT,
    SUMMARY_PROMPT,
    TRANSCRIPT_PROMPT,
)

load_dotenv()

MAX_RETRIES = 3
RETRY_BASE_DELAY = 4  # seconds
MODEL_ALIASES = {
    "gemini-3-flash-lite": "gemini-3.1-flash-lite",
    "gemini-3.1-flash": "gemini-3.1-flash-lite",
    "gemini-3-pro-preview": "gemini-3.1-pro-preview",
    "gemini-3.1-pro": "gemini-3.1-pro-preview",
}
SUMMARY_MODEL = None
QUIZ_MODEL = None
TRANSCRIPT_CLEANUP_MODEL = None
TRANSCRIPT_FALLBACK_MODEL = os.getenv(
    "GEMINI_TRANSCRIPT_FALLBACK_MODEL", "gemini-3-flash-preview"
)


def _model_from_env(env_name: str, default: str) -> str:
    model = os.getenv(env_name, default).strip()
    return MODEL_ALIASES.get(model, model)


SUMMARY_MODEL = _model_from_env("GEMINI_SUMMARY_MODEL", "gemini-3.1-flash-lite")
QUIZ_MODEL = _model_from_env("GEMINI_QUIZ_MODEL", "gemini-3.1-pro-preview")
TRANSCRIPT_CLEANUP_MODEL = _model_from_env(
    "GEMINI_TRANSCRIPT_CLEANUP_MODEL", "gemini-3.1-flash-lite"
)
TRANSCRIPT_FALLBACK_MODEL = MODEL_ALIASES.get(
    TRANSCRIPT_FALLBACK_MODEL, TRANSCRIPT_FALLBACK_MODEL
)


@st.cache_resource
def get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY không tìm thấy trong .env")
    return genai.Client(api_key=api_key)


def transcribe_with_gemini_audio(client: genai.Client, audio_path: str) -> dict:
    gemini_file = None

    try:
        gemini_file = client.files.upload(file=audio_path)
        raw = _generate_content_with_model_fallback(
            client=client,
            models=[TRANSCRIPT_FALLBACK_MODEL, "gemini-3-flash-preview", "gemini-2.5-flash"],
            contents=[gemini_file, TRANSCRIPT_PROMPT],
            step_name="tạo transcript bằng Gemini",
        )
        data = _parse_json_response(raw)
        transcript = data.get("transcript", "")

        if not isinstance(transcript, str) or not transcript.strip():
            raise ValueError("Gemini không trả về transcript hợp lệ")

        unclear_segments = data.get("unclear_segments", [])
        if not isinstance(unclear_segments, list):
            unclear_segments = []

        return {
            "transcript": transcript.strip(),
            "unclear_segments": unclear_segments,
            "transcription_model": TRANSCRIPT_FALLBACK_MODEL,
            "transcription_provider": "gemini",
        }
    finally:
        if gemini_file:
            try:
                client.files.delete(name=gemini_file.name)
            except Exception:
                pass


def generate_summary(client: genai.Client, model: str, transcript: str) -> str:
    prompt = f"{SUMMARY_PROMPT}\n\nTRANSCRIPT:\n{transcript}"
    return _generate_content_with_model_fallback(
        client=client,
            models=[
                model,
                "gemini-3.1-flash-lite",
                "gemini-2.5-flash-lite",
                "gemini-3-flash-preview",
                "gemini-2.5-flash",
            ],
        contents=[prompt],
        step_name="tóm tắt",
    )


def cleanup_transcript(
    client: genai.Client, model: str, raw_transcript: str, glossary: str = ""
) -> dict:
    glossary_section = f"\n\nGLOSSARY/THUẬT NGỮ:\n{glossary}" if glossary else ""
    prompt = (
        f"{CLEANUP_TRANSCRIPT_PROMPT}"
        f"{glossary_section}"
        f"\n\nRAW_TRANSCRIPT:\n{raw_transcript}"
    )
    raw = _generate_content_with_model_fallback(
        client=client,
        models=[
            model,
            "gemini-3.1-flash-lite",
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
        ],
        contents=[prompt],
        step_name="làm sạch transcript",
    )
    data = _parse_json_response(raw)
    clean_transcript = data.get("clean_transcript", "")

    if not isinstance(clean_transcript, str) or not clean_transcript.strip():
        raise ValueError("Response cleanup thiếu field 'clean_transcript'")

    corrections = data.get("corrections", [])
    if not isinstance(corrections, list):
        corrections = []

    return {
        "transcript": clean_transcript.strip(),
        "cleanup_corrections": corrections,
    }


def parse_summary_response(raw: str) -> dict:
    data = _parse_json_response(raw)
    summary = data.get("summary", [])

    if not isinstance(summary, list) or not summary:
        raise ValueError("Response summary phải có field 'summary' là list không rỗng")

    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    difficulty_level = metadata.get("difficulty_level", "")
    if difficulty_level not in {"beginner", "intermediate", "advanced"}:
        difficulty_level = "beginner"

    return {
        "summary": [str(point).strip() for point in summary if str(point).strip()],
        "metadata": {
            "topic": metadata.get("topic") or "N/A",
            "estimated_duration_minutes": metadata.get(
                "estimated_duration_minutes", "?"
            ),
            "difficulty_level": difficulty_level,
        },
    }


def generate_quiz(
    client: genai.Client, model: str, transcript: str, summary: list[str]
) -> str:
    summary_text = json.dumps(summary, ensure_ascii=False, indent=2)
    prompt = f"{QUIZ_PROMPT}\n\nSUMMARY:\n{summary_text}\n\nTRANSCRIPT:\n{transcript}"
    return _generate_content_with_model_fallback(
        client=client,
        models=[
            model,
            "gemini-3.1-pro-preview",
            "gemini-2.5-pro",
            "gemini-3.1-flash-lite",
            "gemini-2.5-flash",
        ],
        contents=[prompt],
        step_name="tạo trắc nghiệm",
    )


def parse_quiz_response(raw: str) -> dict:
    data = _parse_json_response(raw)
    quiz = data.get("quiz", [])

    if not isinstance(quiz, list) or not quiz:
        raise ValueError("Response quiz phải có field 'quiz' là list không rỗng")

    for index, question in enumerate(quiz, 1):
        if not isinstance(question, dict):
            raise ValueError(f"Câu hỏi {index} không đúng định dạng object")

        options = question.get("options", {})
        if not isinstance(options, dict) or set(options.keys()) != {"A", "B", "C", "D"}:
            raise ValueError(f"Câu hỏi {index} phải có đủ lựa chọn A, B, C, D")

        answer = question.get("answer")
        if answer not in options:
            raise ValueError(f"Câu hỏi {index} có đáp án không hợp lệ")

    return {"quiz": quiz}


def _generate_content(
    client: genai.Client, model: str, contents: list[Any], step_name: str
) -> str:
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(model=model, contents=contents)
            text = getattr(response, "text", "") or ""
            if not text.strip():
                raise ValueError(f"Gemini không trả về nội dung ở bước {step_name}")
            return text

        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            is_overload = (
                "503" in str(e) or "overloaded" in err_str or "unavailable" in err_str
            )

            if is_overload and attempt < MAX_RETRIES - 1:
                wait = RETRY_BASE_DELAY * (2**attempt)
                st.toast(
                    f"Server quá tải ở bước {step_name}, thử lại sau {wait}s "
                    f"({attempt + 1}/{MAX_RETRIES})",
                    icon="⏳",
                )
                time.sleep(wait)
            else:
                break

    raise Exception(
        f"Không thể hoàn tất bước {step_name} sau {MAX_RETRIES} lần thử.\n"
        f"Chi tiết: {last_error}"
    )


def _generate_content_with_model_fallback(
    client: genai.Client, models: list[str], contents: list[Any], step_name: str
) -> str:
    last_error = None

    for model in _unique_models(models):
        try:
            return _generate_content(
                client=client,
                model=model,
                contents=contents,
                step_name=step_name,
            )
        except Exception as e:
            last_error = e
            if not (_is_model_not_found(e) or _is_quota_exhausted(e)):
                raise

            if _is_quota_exhausted(e):
                st.warning(
                    f"Model `{model}` hết quota/rate limit cho bước {step_name}. "
                    "Đang thử model dự phòng nhẹ hơn."
                )
            else:
                st.warning(
                    f"Model `{model}` không khả dụng cho bước {step_name}. "
                    "Đang thử model dự phòng."
                )

    raise Exception(
        f"Không có model khả dụng cho bước {step_name}.\n"
        f"Chi tiết: {last_error}"
    )


def _parse_json_response(raw: str) -> dict:
    clean = _extract_json(raw)

    try:
        data = json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini trả về JSON không hợp lệ: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("Gemini phải trả về JSON object")

    return data


def _extract_json(raw: str) -> str:
    clean = raw.strip()

    if clean.startswith("```"):
        for part in clean.split("```"):
            candidate = part.strip()
            if candidate.lower().startswith("json"):
                candidate = candidate[4:].strip()
            if candidate.startswith("{") and candidate.endswith("}"):
                return candidate

    start = clean.find("{")
    end = clean.rfind("}")
    if start != -1 and end != -1 and start < end:
        return clean[start : end + 1]

    return clean


def _unique_models(models: list[str]) -> list[str]:
    result = []
    for model in models:
        normalized = MODEL_ALIASES.get(model, model)
        if normalized and normalized not in result:
            result.append(normalized)
    return result


def _is_model_not_found(error: Exception) -> bool:
    error_text = str(error).lower()
    return (
        "404" in error_text
        or "not_found" in error_text
        or "is not found" in error_text
    )


def _is_quota_exhausted(error: Exception) -> bool:
    error_text = str(error).lower()
    return (
        "429" in error_text
        or "resource_exhausted" in error_text
        or "exceeded your current quota" in error_text
        or "rate limit" in error_text
    )
