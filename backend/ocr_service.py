import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file into Python's memory
# This lets us safely access GEMINI_API_KEY without hardcoding it
load_dotenv()


def extract_with_gemini(image_bytes: bytes) -> list[dict]:
    """
    Main function that takes raw image bytes, sends it to Gemini AI,
    and returns a list of ingredients with safety ratings.
    
    Returns: list of dicts like:
    [{"name": "Niacinamide", "safety_rating": "Safe", ...}]
    """
    try:
        # Import Google's GenAI SDK inside the function so that if the
        # library is missing, the whole server doesn't crash on startup
        from google import genai
        from google.genai import types

        # Create a client connection to Google's AI servers
        # os.getenv reads the API key from our .env file
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # List of Gemini models to try, ordered from best to fallback
        # If the first model fails (rate limit, unavailable), we try the next one
        # This "fallback cascade" ensures the app keeps working even if one model is down
        models_to_try = [
            "gemini-2.5-flash",       # Best — try first
            "gemini-2.5-pro",         # Second choice
            "gemini-2.0-flash",       # Third choice
            "gemini-2.0-flash-lite",  # Lighter version
            "gemini-flash-latest",    # Latest flash
            "gemini-pro-latest",      # Latest pro
            "gemini-flash-lite-latest", # Last resort
        ]

        # The system prompt — tells Gemini exactly what to do and how to format output
        # We ask for a strict JSON array so our Python code can parse it reliably
        # Without this strict format, AI might return text in different structures each time
        prompt = """This is a cosmetic product label. Extract ALL ingredients.
All values must be plain strings. compatible_skin_types must be a single string.
Return ONLY a JSON array:
[{"name": "...", "safety_rating": "Safe/Moderate/Irritant/Avoid",
  "description": "one sentence", "compatible_skin_types": "All/Oily/Dry/Sensitive"}]
If no ingredients found, return: []"""

        # Detect image type by checking the first 4 bytes ("magic numbers")
        # PNG files always start with \x89PNG
        # Everything else is treated as JPEG
        # This avoids importing heavy image libraries like Pillow just for this check
        media_type = "image/png" if image_bytes[:4] == b'\x89PNG' else "image/jpeg"

        # Loop through models one by one until one succeeds
        for model_name in models_to_try:
            try:
                # Send the image + prompt to Gemini and wait for response
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        # Attach the image as bytes with its media type
                        types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                        # Attach our instruction prompt
                        prompt
                    ]
                )

                # Gemini often wraps JSON in markdown code blocks like:
                # ```json
                # [{"name": "..."}]
                # ```
                # We need to strip that markdown before parsing
                raw = response.text.strip()
                if raw.startswith("```"):
                    # Split on ``` and take the middle part
                    raw = raw.split("```")[1]
                    # Remove the "json" language tag if present
                    if raw.startswith("json"):
                        raw = raw[4:]

                # Convert the cleaned JSON string into a Python list of dicts
                parsed = json.loads(raw.strip())

                # List to store our cleaned, validated ingredients
                normalized = []

                for item in parsed:
                    # Safety check: sometimes AI nests the data incorrectly
                    # e.g. {"name": {"name": "Niacinamide", ...}} instead of {"name": "Niacinamide"}
                    if isinstance(item.get("name"), dict):
                        item = item["name"]

                    normalized.append({
                        # str() forces everything to be a string
                        # .get() with a default value prevents KeyError if AI misses a field
                        "name": str(item.get("name", "Unknown")),
                        "safety_rating": str(item.get("safety_rating", "Moderate")),
                        "description": str(item.get("description", "")),

                        # compatible_skin_types can sometimes come back as a list
                        # e.g. ["Oily", "Dry"] — we join it into a single string "Oily, Dry"
                        # If it's already a string, we use it directly
                        "compatible_skin_types": (
                            ", ".join(item.get("compatible_skin_types", ["All"]))
                            if isinstance(item.get("compatible_skin_types"), list)
                            else str(item.get("compatible_skin_types", "All"))
                        ),

                        # Tag the source so frontend knows this was AI-analyzed
                        # Used to show the "✨ AI Analyzed" badge in the UI
                        "source": "gemini"
                    })

                # If we got valid results, return them immediately
                # No need to try the remaining models
                if normalized:
                    return normalized

            except Exception:
                # This model failed (rate limit, parse error, network issue, etc.)
                # Silently continue to the next model in the list
                continue

    except Exception:
        # Gemini SDK import failed or client initialization failed
        # Return empty list — main.py will handle the 422 "no ingredients found" response
        pass

    # All models failed — return empty list
    return []


def extract_ingredients_from_image(image_bytes: bytes) -> list[dict]:
    """
    Entry point called by main.py when a user uploads an image.
    Delegates to extract_with_gemini and returns the result.
    """
    return extract_with_gemini(image_bytes)