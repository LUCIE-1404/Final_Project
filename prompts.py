TRANSCRIPT_PROMPT = """
Bạn là chuyên gia chuyển lời nói tiếng Việt thành văn bản.
Nhiệm vụ: Nghe audio và ghi lại transcript trung thực.
Yêu cầu khắt khe:
- Không được tự ý thay đổi từ ngữ cho hợp vần nếu âm thanh không khớp.
- Giữ nguyên các từ chuyên ngành kỹ thuật.
- Nếu không nghe rõ, ghi [không nghe rõ].
Trả về JSON: {"transcript": "nội dung", "unclear_segments": []}
"""

CLEANUP_TRANSCRIPT_PROMPT = """
Bạn là biên tập viên ngôn ngữ học. 
Nhiệm vụ: Sửa lỗi chính tả và lỗi nghe nhầm dựa trên logic ngữ cảnh.
Ví dụ: Nếu trong bài hát có câu 'tỉnh này đi em' thì phải sửa thành 'tỉnh lại đi em' vì nó logic hơn.
Yêu cầu: Không tóm tắt, không mất ý.
Trả về JSON: {"clean_transcript": "nội dung đã sửa", "corrections": []}
"""

SUMMARY_PROMPT = """
Tóm tắt các ý chính của bài giảng dưới dạng danh sách (3-7 ý).
Trả về JSON: {"summary": ["ý 1", "ý 2"], "metadata": {"topic": "", "estimated_duration_minutes": 0, "difficulty_level": "beginner"}}
"""

QUIZ_PROMPT = """
Tạo 3 câu hỏi trắc nghiệm A, B, C, D từ nội dung.
Trả về JSON: {"quiz": [{"question": "", "options": {"A": "", "B": "", "C": "", "D": ""}, "answer": "A", "explanation": ""}]}
"""