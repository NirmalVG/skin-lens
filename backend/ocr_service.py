import requests
import re
import os

OCR_API_KEY = os.getenv("OCR_API_KEY", "helloworld")  # helloworld is OCR.space's free demo key

def extract_ingredients_from_image(image_bytes: bytes) -> list[str]:
    try:
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": ("image.jpg", image_bytes, "image/jpeg")},
            data={
                "apikey": OCR_API_KEY,
                "language": "eng",
                "isOverlayRequired": False,
                "detectOrientation": True,
                "scale": True,
                "isTable": False,
                "OCREngine": 2  # Engine 2 is better for complex images
            }
        )

        result = response.json()
        print(f"[DEBUG] OCR.space response: {result}")

        if result.get("IsErroredOnProcessing"):
            print(f"OCR Error: {result.get('ErrorMessage')}")
            return []

        # Extract full text
        parsed_results = result.get("ParsedResults", [])
        if not parsed_results:
            return []

        full_text = parsed_results[0].get("ParsedText", "")
        print(f"[DEBUG] Full text: {full_text}")

        # Find ingredients section
        if 'ingredient' in full_text.lower():
            idx = full_text.lower().find('ingredient')
            full_text = full_text[idx:]
            colon = full_text.find(':')
            if colon != -1:
                full_text = full_text[colon + 1:]

        # Normalize separators
        full_text = full_text.replace('\n', ',').replace('\r', ',').replace(';', ',')

        # Split and clean
        parsed = []
        for ing in full_text.split(','):
            c = re.sub(r'[^a-zA-Z0-9\-\s\(\)]', '', ing).strip().title()
            if len(c) > 2:
                parsed.append(c)

        # Remove duplicates
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