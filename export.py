"""
export.py — Tạo nội dung file để download.
Không import streamlit — thuần Python, dễ test độc lập.
"""

import json
from datetime import datetime


def to_markdown(data: dict, filename: str = "") -> str:
    """
    Chuyển kết quả phân tích thành Markdown đẹp, sẵn sàng download.
    """
    meta = data.get("metadata", {})
    topic = meta.get("topic", "N/A")
    duration = meta.get("estimated_duration_minutes", "?")
    difficulty_map = {
        "beginner": "Cơ bản",
        "intermediate": "Trung bình",
        "advanced": "Nâng cao",
    }
    difficulty = difficulty_map.get(meta.get("difficulty_level", ""), "N/A")
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    lines = []

    # Header
    lines += [
        f"# Kết quả phân tích bài giảng",
        f"",
        f"> **File:** {filename}  ",
        f"> **Chủ đề:** {topic}  ",
        f"> **Thời lượng ước tính:** {duration} phút  ",
        f"> **Độ khó:** {difficulty}  ",
        f"> **Tạo lúc:** {generated_at}",
        f"",
        "---",
        "",
    ]

    # Transcript
    transcript = data.get("transcript", "")
    lines += [
        "## 📝 Transcript",
        "",
        transcript,
        "",
    ]

    corrections = data.get("cleanup_corrections", [])
    if corrections:
        lines += ["### Các chỉnh sửa transcript", ""]
        for correction in corrections:
            lines.append(f"- {correction}")
        lines.append("")

    raw_transcript = data.get("raw_transcript", "")
    if raw_transcript and raw_transcript != transcript:
        lines += ["### Raw transcript trước cleanup", "", raw_transcript, ""]

    transcript_segments = data.get("transcript_segments", [])
    if transcript_segments:
        lines += ["### Segment transcript", ""]
        for segment in transcript_segments:
            start = segment.get("start", 0)
            end = segment.get("end", 0)
            text = segment.get("text", "").strip()
            lines.append(f"- **{start:.1f}s - {end:.1f}s:** {text}")
        lines.append("")

    lines += [
        "---",
        "",
    ]

    # Summary
    summary = data.get("summary", [])
    lines += ["## 📌 Tóm tắt ý chính", ""]
    for i, point in enumerate(summary, 1):
        lines.append(f"{i}. {point}")
    lines += ["", "---", ""]

    # Quiz
    quiz = data.get("quiz", [])
    lines += [f"## 📊 Câu hỏi trắc nghiệm ({len(quiz)} câu)", ""]
    for i, q in enumerate(quiz, 1):
        lines.append(f"### Câu {i}")
        lines.append(f"**{q.get('question', '')}**")
        lines.append("")
        for key, val in q.get("options", {}).items():
            lines.append(f"- **{key}.** {val}")
        lines.append("")
        answer = q.get("answer", "")
        explanation = q.get("explanation", "")
        lines.append(f"> ✅ **Đáp án: {answer}**")
        if explanation:
            lines.append(f">")
            lines.append(f"> 💡 {explanation}")
        lines.append("")

    return "\n".join(lines)


def to_json(data: dict) -> str:
    """
    Trả về JSON có format đẹp (indent 2), UTF-8 safe.
    """
    return json.dumps(data, ensure_ascii=False, indent=2)


def get_export_filename(original_filename: str, ext: str) -> str:
    """
    Tạo tên file download từ tên file gốc.
    Ví dụ: "bai_giang.mp3" + ".md" → "bai_giang_result.md"
    """
    import os

    base = os.path.splitext(original_filename)[0]
    # Làm sạch tên file: thay space bằng underscore
    base = base.replace(" ", "_")
    return f"{base}_result{ext}"
