import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=GEMINI_API_KEY)

# Primary model + fallback models
MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
    "gemini-2.5-flash",
]


def generate_gemini_recommendation(prompt: str) -> str:
    """
    Generate a business recommendation using Gemini.
    Automatically tries fallback models if the primary model
    is temporarily unavailable.
    """

    last_error = None

    for model in MODELS:
        try:
            print(f"Trying Gemini model: {model}")

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=1000,
                ),
            )

            if response and response.text:
                print(f"Gemini success: {model}")
                return response.text

        except Exception as e:
            last_error = e
            print(f"Gemini error with {model}: {e}")

    print(f"All Gemini models failed: {last_error}")

    return "Gemini recommendation could not be generated at this moment."