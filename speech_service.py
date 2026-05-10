import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable

import imageio_ffmpeg
import streamlit as st
from dotenv import load_dotenv
from google.cloud import speech_v2 as speech
from openai import OpenAI

load_dotenv()

SUPPORTED_FORMATS = [
    ".mp3",
    ".mp4",
    ".mpeg",
    ".mpga",
    ".m4a",
    ".wav",
    ".webm",
    ".flac",
    ".ogg",
]
MAX_FILE_SIZE_MB = int(os.getenv("MAX_AUDIO_FILE_SIZE_MB", "200"))
CHUNK_SECONDS = int(os.getenv("AUDIO_CHUNK_SECONDS", "45"))
CHIRP_MODEL = os.getenv("GOOGLE_SPEECH_MODEL", "chirp_3")
CHIRP_LANGUAGE_CODE = os.getenv("GOOGLE_SPEECH_LANGUAGE", "vi-VN")
GOOGLE_SPEECH_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "asia-southeast1")
WHISPER_MODEL = "whisper-1"


@st.cache_resource
def get_chirp_client() -> speech.SpeechClient:
    return speech.SpeechClient()


@st.cache_resource
def get_whisper_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY khong tim thay trong .env")
    return OpenAI(api_key=api_key)


def validate_audio_file(uploaded_file) -> tuple[bool, str]:
    size_mb = uploaded_file.size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return (
            False,
            f"File qua lon ({size_mb:.1f} MB). Gioi han hien tai: {MAX_FILE_SIZE_MB} MB.",
        )

    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        return (
            False,
            f"Dinh dang '{ext}' khong duoc ho tro. Chap nhan: {', '.join(SUPPORTED_FORMATS)}",
        )

    return True, ""


def save_uploaded_audio(uploaded_file) -> str:
    ext = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return tmp.name


def transcribe_with_chirp(
    client: speech.SpeechClient,
    audio_path: str,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise EnvironmentError("GOOGLE_CLOUD_PROJECT khong tim thay trong .env")

    chunks_dir = tempfile.mkdtemp(prefix="chirp_chunks_")
    try:
        chunk_paths = split_audio_for_chirp(audio_path, chunks_dir)
        if not chunk_paths:
            raise ValueError("Khong tao duoc audio chunk de transcribe")

        recognizer = (
            f"projects/{project_id}/locations/{GOOGLE_SPEECH_LOCATION}/recognizers/_"
        )
        config = speech.RecognitionConfig(
            auto_decoding_config=speech.AutoDetectDecodingConfig(),
            language_codes=[CHIRP_LANGUAGE_CODE],
            model=CHIRP_MODEL,
            features=speech.RecognitionFeatures(enable_automatic_punctuation=True),
        )

        transcripts = []
        segments = []

        for index, chunk_path in enumerate(chunk_paths, 1):
            if progress_callback:
                progress_callback(
                    f"Đang transcribe chunk {index}/{len(chunk_paths)} bằng Chirp 3..."
                )

            with open(chunk_path, "rb") as audio_file:
                content = audio_file.read()

            request = speech.RecognizeRequest(
                recognizer=recognizer,
                config=config,
                content=content,
            )
            response = client.recognize(request=request)
            chunk_text = _extract_chirp_text(response)

            if chunk_text:
                transcripts.append(chunk_text)
                start = (index - 1) * CHUNK_SECONDS
                segments.append(
                    {
                        "start": float(start),
                        "end": float(start + CHUNK_SECONDS),
                        "text": chunk_text,
                    }
                )

        transcript = "\n".join(transcripts).strip()
        if not transcript:
            raise ValueError("Google Chirp khong tra ve transcript")

        return {
            "raw_transcript": transcript,
            "transcript": transcript,
            "transcript_segments": segments,
            "transcription_model": CHIRP_MODEL,
            "transcription_provider": "google_chirp",
            "chunk_count": len(chunk_paths),
        }
    finally:
        shutil.rmtree(chunks_dir, ignore_errors=True)


def split_audio_for_chirp(audio_path: str, output_dir: str) -> list[str]:
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    output_pattern = str(Path(output_dir) / "chunk_%03d.wav")

    command = [
        ffmpeg_exe,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        audio_path,
        "-ac",
        "1",
        "-ar",
        "16000",
        "-vn",
        "-f",
        "segment",
        "-segment_time",
        str(CHUNK_SECONDS),
        "-reset_timestamps",
        "1",
        output_pattern,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg khong xu ly duoc audio: {result.stderr.strip()}")

    return sorted(str(path) for path in Path(output_dir).glob("chunk_*.wav"))


def transcribe_with_whisper(client: OpenAI, audio_path: str) -> dict[str, Any]:
    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model=WHISPER_MODEL,
            language="vi",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    data = _to_dict(transcription)
    transcript = (data.get("text") or "").strip()
    if not transcript:
        raise ValueError("Whisper khong tra ve transcript")

    return {
        "raw_transcript": transcript,
        "transcript": transcript,
        "transcript_segments": data.get("segments", []),
        "transcription_model": WHISPER_MODEL,
        "transcription_provider": "openai_whisper",
    }


def should_fallback_to_gemini(error: Exception) -> bool:
    error_text = str(error).lower()
    return any(
        marker in error_text
        for marker in [
            "insufficient_quota",
            "exceeded your current quota",
            "429",
            "openai_api_key",
            "khong tim thay",
        ]
    )


def cleanup_audio_file(temp_path: str | None):
    if temp_path:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


def _extract_chirp_text(response) -> str:
    transcripts = []
    for result in response.results:
        if result.alternatives:
            text = result.alternatives[0].transcript.strip()
            if text:
                transcripts.append(text)
    return " ".join(transcripts).strip()


def _to_dict(value: Any) -> dict:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return dict(value)
