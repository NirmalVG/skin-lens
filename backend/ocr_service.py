import os
import re
import json
from dotenv import load_dotenv

load_dotenv()

def extract_with_gemini(image_bytes: bytes) -> list[dict]:
    """
    Takes the raw byte data of an uploaded image, sends it to Google's Gemini AI, 
    and asks the AI to act as a chemist to extract and classify the ingredients.
    """
    try:
        # Import the official new Google GenAI SDK. We put it inside the try block 
        # so the server doesn't crash on startup if the library isn't installed.
        from google import genai
        from google.genai import types

        # Initialize the client. It automatically looks for the GEMINI_API_KEY we loaded from .env
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # AI model availability can change, or you might hit rate limits on a specific model.
        # This list creates a "fallback cascade." It tries the newest/best model first, 
        # and if it fails (or isn't available), it seamlessly tries the next one down the list.
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-flash-latest",
            "gemini-pro-latest",
            "gemini-flash-lite-latest",
        ]

        # The "System Prompt". This is crucial. It tells the AI exactly what persona to adopt, 
        # what data to look for, and exactly how we want the output formatted so our app doesn't break.
        prompt = """This is a cosmetic product label. Extract ALL ingredients.
All values must be plain strings. compatible_skin_types must be a single string.
Return ONLY a JSON array:
[{"name": "...", "safety_rating": "Safe/Moderate/Irritant/Avoid",
  "description": "one sentence", "compatible_skin_types": "All/Oily/Dry/Sensitive"}]
If no ingredients found, return: []"""

        # Gemini requires us to tell it what kind of image we are sending. 
        # This quick check looks at the first 4 bytes of the file (the "magic numbers") 
        # to determine if it's a PNG or JPEG without needing heavy image processing libraries.
        media_type = "image/png" if image_bytes[:4] == b'\x89PNG' else "image/jpeg"

        # Start the cascade: loop through the list of models
        for model_name in models_to_try:
            try:
                # Ask the current model to analyze the image and the prompt
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                        prompt
                    ]
                )
                
                # The AI usually wraps its JSON in markdown formatting (like ```json ... ```).
                # This block strips away that markdown so Python's JSON parser doesn't crash.
                raw = response.text.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]

                # Convert the raw text string from the AI into an actual Python dictionary/list
                parsed = json.loads(raw.strip())
                
                # A place to store the clean, verified data
                normalized = []
                
                # Sometimes the AI gets "creative" and changes the structure of our JSON.
                # This loop acts as a filter, forcing every item into the exact structure we need.
                for item in parsed:
                    # Failsafe: If the AI accidentally nested the name in a dict, pull it out
                    if isinstance(item.get("name"), dict):
                        item = item["name"]
                        
                    normalized.append({
                        # Force everything to be a string. If a field is missing, use a safe default.
                        "name": str(item.get("name", "Unknown")),
                        "safety_rating": str(item.get("safety_