from google import genai
from google.genai import types
import base64
import json
import os
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT VARIABLES
# Grabs the GEMINI_API_KEY from your .env file
load_dotenv()

# Initialize the new Google GenAI Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_ingredients_from_image(image_bytes: bytes) -> list[dict]:
    """
    Takes raw image bytes of a cosmetic label, sends it to Gemini Vision,
    and returns a structured list of dictionaries containing ingredient data.
    """
    
    # ==========================================
    # 2. THE FALLBACK STRATEGY (Highly robust!)
    # ==========================================
    # AI models can sometimes be busy, rate-limited, or fail to parse complex images.
    # Instead of the app crashing, we maintain a list of models to try one by one.
    models_to_try = [
        "gemini-2.5-flash",        # First choice: Lightning fast and highly capable
        "gemini-2.5-pro",          # Second choice: Heavier, smarter, great for complex labels
        "gemini-2.0-flash",        # Third choice: Older stable version
        "gemini-2.0-flash-lite",   # Fourth: Lightweight and quick
        "gemini-flash-latest",     # Fallback to whatever the current latest flash is
        "gemini-pro-latest",       # Fallback to whatever the current latest pro is
        "gemini-flash-lite-latest",# Absolute last resort
    ]
    
    

    for model_name in models_to_try:
        try:
            print(f"[DEBUG] Trying model: {model_name}")
            print(f"[DEBUG] Image size: {len(image_bytes)} bytes")

            # ==========================================
            # 3. MAGIC BYTES DETECTION (MIME Type)
            # ==========================================
            # Gemini needs to know if the image is a PNG or a JPEG.
            # Instead of relying on file extensions, we look at the first few bytes 
            # of the file (the "Magic Number" signature).
            if image_bytes[:4] == b'\x89PNG':
                media_type = "image/png"
            elif image_bytes[:3] == b'\xff\xd8\xff':
                media_type = "image/jpeg"
            else:
                media_type = "image/jpeg" # Default guess

            # ==========================================
            # 4. STRICT PROMPT ENGINEERING
            # ==========================================
            # We must be extremely strict with the AI so it doesn't return conversational 
            # text like "Sure, here are the ingredients!". We ONLY want JSON.
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

            # ==========================================
            # 5. THE API CALL
            # ==========================================
            # We pass BOTH the image (as bytes) and the text prompt to the model.
            
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=media_type),
                    prompt
                ]
            )

            # Get the raw text from the AI's response
            raw = response.text.strip()
            print(f"[DEBUG] Raw response: {raw[:300]}")

            # ==========================================
            # 6. JSON CLEANUP
            # ==========================================
            # Even if told not to, AI sometimes wraps JSON in markdown blocks like ```json ... ```
            # This logic strips those out so Python's json.loads() doesn't crash.
            if raw.startswith("```"):
                raw = raw.split("```")[1]     # Grab everything after the first ```
                if raw.startswith("json"):
                    raw = raw[4:]             # Remove the word 'json' if it's there

            # Convert the clean string into a real Python list of dictionaries
            parsed = json.loads(raw.strip())

            # ==========================================
            # 7. DATA NORMALIZATION (Safety Net)
            # ==========================================
            # AI hallucinations happen. Sometimes the AI will return a list instead of a string.
            # This loop forces all data into the exact format our FastAPI backend expects.
            normalized = []
            for item in parsed:
                # Edge case: If AI accidentally made 'name' a dictionary
                if isinstance(item.get("name"), dict):
                    item = item["name"]
                
                normalized.append({
                    "name": str(item.get("name", "Unknown")),
                    "safety_rating": str(item.get("safety_rating", "Moderate")),
                    "description": str(item.get("description", "")),
                    
                    # If AI returned a list like ["Oily", "Dry"], join it into a string "Oily, Dry"
                    "compatible_skin_types": ", ".join(item.get("compatible_skin_types", ["All"]))
                    if isinstance(item.get("compatible_skin_types"), list)
                    else str(item.get("compatible_skin_types", "All"))
                })

            print(f"[DEBUG] Parsed {len(normalized)} ingredients")
            
            # If everything succeeded, return the data and exit the function!
            return normalized

        # ==========================================
        # 8. CATCH ERRORS AND RETRY
        # ==========================================
        except Exception as e:
            print(f"[ERROR] Model {model_name} failed: {e}")
            continue  # This tells the 'for' loop to go to the next model in the list

    # If ALL models in the list failed, return an empty array to prevent a 500 Server Crash.
    return []