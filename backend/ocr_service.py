import requests
import re
import os
from PIL import Image
import io

OCR_API_KEY = os.getenv("OCR_API_KEY", "helloworld")

def preprocess_image(image_bytes: bytes) -> bytes:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB (handles HEIC, PNG, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Resize if too large — OCR.space has 1MB limit
        max_size = (1800, 1800)
        image.thumbnail(max_size, Image.LANCZOS)
        
        # Save as compressed JPEG
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85)
        return output.getvalue()
    except Exception as e:
        print(f"Preprocessing error: {e}")
        return image_bytes  # Return original if preprocessing fails

def extract_ingredients_from_image(image_bytes: bytes) -> list[str]:
    try:
        # Preprocess image before sending
        processed_bytes = preprocess_image(image_bytes)

        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": ("image.jpg", processed_bytes, "image/jpeg")},
            data={
                "apikey": OCR_API_KEY,
                "language": "eng",
                "isOverlayRequired": False,
                "detectOrientation": True,
                "scale": True,
                "isTable": False,
                "OCREngine": 2
            }
        )

        result = response.json()
        print(f"[DEBUG] OCR.space response: {result}")

        if result.get("IsErroredOnProcessing"):
            print(f"OCR Error: {result.get('ErrorMessage')}")
            return []

        parsed_results = result.get("ParsedResults", [])
        if not parsed_results:
            return []

        full_text = parsed_results[0].get("ParsedText", "")
        print(f"[DEBUG] Full text: {full_text}")

        if 'ingredient' in full_text.lower():
            idx = full_text.lower().find('ingredient')
            full_text = full_text[idx:]
            colon = full_text.find(':')
            if colon != -1:
                full_text = full_text[colon + 1:]

        full_text = full_text.replace('\n', ',').replace('\r', ',').replace(';', ',')

        parsed = []
        for ing in full_text.split(','):
            c = re.sub(r'[^a-zA-Z0-9\-\s\(\)]', '', ing).strip().title()
            if len(c) > 2:
                parsed.append(c)

        seen = set()
        unique_parsed = []
        for i in parsed:
            if i.lower() not in seen:
                seen.add(i.lower())
                unique_parsed.append(i)

        print(f"[DEBUG] Parsed ingredients: {unique_parsed}")
        return unique_parsed

    except Exception as e:
        print(f"OCR Error: {e}")
        return []