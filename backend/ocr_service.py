import os
import re
import json
from dotenv import load_dotenv

load_dotenv()


# ── GEMINI EXTRACTION ────────────────────────────────────────────────────────
def extract_with_gemini(image_bytes: bytes) -> list[dict]:
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-flash-latest",
            "gemini-pro-latest",
            "gemini-flash-lite-latest",
        ]

        prompt = """This is a cosmetic product label. Extract ALL ingredients.
All values must be plain strings. compatible_skin_types must be a single string.
Return ONLY a JSON array:
[{"name": "...", "safety_rating": "Safe/Moderate/Irritant/Avoid",
  "description": "one sentence", "compatible_skin_types": "All/Oily/Dry/Sensitive"}]
If no ingredients found, return: []"""

        media_type = "image/png" if image_bytes[:4] == b'\x89PNG' else "image/jpeg"

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                        prompt
                    ]
                )
                raw = response.text.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]

                parsed = json.loads(raw.strip())
                normalized = []
                for item in parsed:
                    if isinstance(item.get("name"), dict):
                        item = item["name"]
                    normalized.append({
                        "name": str(item.get("name", "Unknown")),
                        "safety_rating": str(item.get("safety_rating", "Moderate")),
                        "description": str(item.get("description", "")),
                        "compatible_skin_types": (
                            ", ".join(item.get("compatible_skin_types", ["All"]))
                            if isinstance(item.get("compatible_skin_types"), list)
                            else str(item.get("compatible_skin_types", "All"))
                        ),
                        "source": "gemini"
                    })

                if normalized:
                    return normalized

            except Exception:
                continue

    except Exception:
        pass

    return []


# ── MAIN FUNCTION (called by main.py) ────────────────────────────────────────
def extract_ingredients_from_image(image_bytes: bytes) -> list[dict]:
    return extract_with_gemini(image_bytes)