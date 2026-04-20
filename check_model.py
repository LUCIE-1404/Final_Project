import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("--- DANH SÁCH CÁC MÔ HÌNH ---")
try:
    for model in client.models.list():
        print(f"- {model.name}")
except Exception as e:
    print("Lỗi:", e)