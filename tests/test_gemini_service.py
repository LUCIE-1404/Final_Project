import unittest

from gemini_service import normalize_transcript_response, parse_json


class TestGeminiService(unittest.TestCase):
    def test_parse_json_handles_empty_response(self):
        self.assertEqual(parse_json(None), {})
        self.assertEqual(parse_json(""), {})

    def test_normalize_transcript_response_accepts_dict(self):
        data = normalize_transcript_response({"transcript": "Hello world"})

        self.assertEqual(data["transcript"], "Hello world")

    def test_normalize_transcript_response_accepts_string_list(self):
        data = normalize_transcript_response(["Part one", "Part two"])

        self.assertEqual(data["transcript"], "Part one\nPart two")
        self.assertEqual(len(data["transcript_segments"]), 2)

    def test_normalize_transcript_response_accepts_segment_list(self):
        data = normalize_transcript_response(
            [
                {"start": 0, "end": 1, "text": "Part one"},
                {"start": 1, "end": 2, "transcript": "Part two"},
            ]
        )

        self.assertEqual(data["transcript"], "Part one\nPart two")
        self.assertEqual(data["transcript_segments"][0]["start"], 0)


if __name__ == "__main__":
    unittest.main()
