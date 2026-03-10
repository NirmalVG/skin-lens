from google import genai
from google.genai import types
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_ingredients_from_image(image_bytes: bytes) -> list[dict]:
    models_to_try = [
    "gemini-2.5-flash",        # best quality, try first
    "gemini-2.5-pro",          # most powerful fallback
    "gemini-2.0-flash",        # fast and reliable
    "gemini-2.0-flash-lite",   # lightweight fallback
    "gemini-flash-latest",     # always points to latest flash
    "gemini-pro-latest",       # always points to latest pro
    "gemini-flash-lite-latest",# lightest fallback
]
    for model_name in models_to_try:
        try:
            print(f"[DEBUG] Trying model: {model_name}")
            print(f"[DEBUG] Image size: {len(image_bytes)} bytes")

            if image_bytes[:4] == b'\x89PNG':
                media_type = "image/png"
            elif image_bytes[:3] == b'\xff\xd8\xff':
                media_type = "image/jpeg"
            else:
                media_type = "image/jpeg"

            prompt = """This is a cosmetic product label.
Extract ALL ingredients and analyze each one.
All values must be plain strings, not arrays or objects.
compatible_skin_types must be a single string like "All" or "Oily, Dry".

Return ONLY a JSON array, no extra text, no markdown:
[
  {
    "name": "Ingredient Name",
    "safety_rating": "Safe" or "Moderate" or "Irritant" or "Avoid",
    "description": "One sentence clinical description",
    "compatible_skin_types": "All" or "Oily" or "Dry" or "Sensitive" or "Combination"
  }
]

If you cannot find an ingredients list in the image, return an empty array: []"""

            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                    prompt
                ]
            )

            raw = response.text.strip()
            print(f"[DEBUG] Raw response: {raw[:300]}")

            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            parsed = json.loads(raw.strip())

            # Normalize
            normalized = []
            for item in parsed:
                if isinstance(item.get("name"), dict):
                    item = item["name"]
                normalized.append({
                    "name": str(item.get("name", "Unknown")),
                    "safety_rating": str(item.get("safety_rating", "Moderate")),
                    "description": str(item.get("description", "")),
                    "compatible_skin_types": ", ".join(item.get("compatible_skin_types", ["All"]))
                    if isinstance(item.get("compatible_skin_types"), list)
                    else str(item.get("compatible_skin_types", "All"))
                })

            print(f"[DEBUG] Parsed {len(normalized)} ingredients")
            return normalized

        except Exception as e:
            print(f"[ERROR] Model {model_name} failed: {e}")
            continue  # try next model

    return []  # all models failed