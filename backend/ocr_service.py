import os
import re
import json
import easyocr
from dotenv import load_dotenv

load_dotenv()

# ── EasyOCR reader (loads once, reused for all requests) ────────────────────
_ocr_reader = None

def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        print("[OCR] Loading EasyOCR model...")
        _ocr_reader = easyocr.Reader(['en'], gpu=False)
        print("[OCR] EasyOCR ready")
    return _ocr_reader


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
                print(f"[GEMINI] Trying model: {model_name}")
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
                    print(f"[GEMINI] ✅ Success with {model_name} — {len(normalized)} ingredients")
                    return normalized

            except Exception as e:
                print(f"[GEMINI] ❌ Model {model_name} failed: {e}")
                continue

    except Exception as e:
        print(f"[GEMINI] ❌ Gemini import/setup failed: {e}")

    return []  # All Gemini models failed


# ── EASYOCR EXTRACTION ───────────────────────────────────────────────────────
def extract_with_easyocr(image_bytes: bytes) -> list[str]:
    try:
        print("[EASYOCR] Gemini failed. Switching to EasyOCR backup...")
        reader = get_ocr_reader()

        # EasyOCR reads from bytes directly
        results = reader.readtext(image_bytes, detail=0)
        full_text = " ".join(results)

        print(f"[EASYOCR] Raw text: {full_text[:200]}")

        # Find ingredients section
        if "ingredient" in full_text.lower():
            parts = re.split(
                r'ingredients\s*[:\.]?\s*',
                full_text,
                flags=re.IGNORECASE
            )
            if len(parts) > 1:
                full_text = parts[1]

        # Split by comma
        raw_list = full_text.split(",")
        cleaned  = []
        for item in raw_list:
            name = item.strip().strip(".")
            name = re.sub(r'\s+', ' ', name)
            if len(name) > 2:
                cleaned.append(name)

        print(f"[EASYOCR] ✅ Found {len(cleaned)} ingredients")
        return cleaned

    except Exception as e:
        print(f"[EASYOCR] ❌ EasyOCR also failed: {e}")
        return []


# ── MAIN FUNCTION (called by main.py) ────────────────────────────────────────
def extract_ingredients_from_image(image_bytes: bytes) -> list[dict]:
    """
    1. Try Gemini first (7 models)
    2. If all fail → fallback to EasyOCR automatically
    3. EasyOCR returns name-only list → main.py does DB lookup
    """

    # Step 1 — Try Gemini
    gemini_results = extract_with_gemini(image_bytes)
    if gemini_results:
        return gemini_results

    # Step 2 — Gemini failed, use EasyOCR
    print("[FALLBACK] 🔄 Switching to EasyOCR...")
    ocr_names = extract_with_easyocr(image_bytes)

    if not ocr_names:
        return []

    # Step 3 — Convert OCR name strings to same dict format as Gemini
    # main.py will do DB lookup to fill in safety_rating etc.
    return [
        {
            "name": name,
            "safety_rating": "Unknown",
            "description": "Extracted via OCR. Search our encyclopedia for details.",
            "compatible_skin_types": "All",
            "source": "easyocr"
        }
        for name in ocr_names
    ]