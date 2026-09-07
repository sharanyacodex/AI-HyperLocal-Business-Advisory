from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found in .env")
    exit()

print("Gemini API key found.")
print("Connecting to Gemini...")

client = genai.Client(api_key=api_key)

chat = client.chats.create(
    model="gemini-3.7-flash"
)

response = chat.send_message(
    message="Give me one short business tip for a grocery shop."
)

print("\n==============================")
print("GEMINI TEST SUCCESS")
print("==============================")
print(response.text)