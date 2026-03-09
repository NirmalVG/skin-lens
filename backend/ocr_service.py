import requests
import re
import os
from PIL import Image  # "Pillow" library for image manipulation
import io              # Handles byte streams (files in memory)

# Load the API Key safely. If not found, use the free 'helloworld' key.
OCR_API_KEY = os.getenv("OCR_API_KEY", "helloworld")

# ---------------------------------------------------------
# 1. IMAGE PREPROCESSING
# Why do we need this? 
# The OCR API has limits (file size < 1MB, specific dimensions).
# If a user uploads a 4K photo from an iPhone, it will be too big.
# This function shrinks and compresses the image BEFORE sending it.
# ---------------------------------------------------------
def preprocess_image(image_bytes: bytes) -> bytes:
    try:
        # Convert raw bytes into a Python Image object
        image = Image.open(io.BytesIO(image_bytes))
        
        # FIX: Convert PNG/HEIC to RGB. 
        # JPEGs don't support "Alpha" (Transparency). If we don't do this, 
        # saving a transparent PNG as JPEG will crash the app.
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # RESIZE: Shrink the image if it's huge.
        # 1800x1800 is large enough to read text, but small enough for the API.
        # Image.LANCZOS is a high-quality filter to keep text sharp during resizing.
        max_size = (1800, 1800)
        image.thumbnail(max_size, Image.LANCZOS)
        
        # COMPRESS: Save back to bytes as a compressed JPEG.
        # Quality=85 reduces file size significantly without making text blurry.
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85)
        return output.getvalue()
    
    except Exception as e:
        print(f"Preprocessing error: {e}")
        # Fail Safe: If optimization fails, just send the original image 
        # and hope the API accepts it.
        return image_bytes 

# ---------------------------------------------------------
# 2. THE MAIN OCR FUNCTION
# Orchestrates the Upload -> Read -> Clean process.
# ---------------------------------------------------------
def extract_ingredients_from_image(image_bytes: bytes) -> list[str]:
    try:
        # Step 1: Optimize the image
        processed_bytes = preprocess_image(image_bytes)

        # Step 2: Send to OCR.space API
        # We use a POST request, simulating a file upload form.
        response = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": ("image.jpg", processed_bytes, "image/jpeg")},
            data={
                "apikey": OCR_API_KEY,
                "language": "eng",      # English
                "isOverlayRequired": False,
                "detectOrientation": True, # Auto-rotate if user took photo sideways
                "scale": True,          # Auto-zoom if text is tiny
                "isTable": False,
                "OCREngine": 2          # Engine 2 is better for product labels/irregular text
            }
        )

        result = response.json()
        print(f"[DEBUG] OCR.space response: {result}")

        # Step 3: Error Handling
        if result.get("IsErroredOnProcessing"):
            print(f"OCR Error: {result.get('ErrorMessage')}")
            return []

        parsed_results = result.get("ParsedResults", [])
        if not parsed_results:
            return []

        # Get the raw text blob
        full_text = parsed_results[0].get("ParsedText", "")
        print(f"[DEBUG] Full text: {full_text}")

        # -----------------------------------------------------
        # Step 4: INTELLIGENT PARSING (The "Smart" Logic)
        # -----------------------------------------------------
        # Labels often have marketing fluff at the top ("New!", "Best Formula!").
        # We look for the word "Ingredients:" and ignore everything before it.
        if 'ingredient' in full_text.lower():
            idx = full_text.lower().find('ingredient')
            full_text = full_text[idx:] # Cut off the top part
            
            # Find the first colon ":" (e.g., "Ingredients: Water...")
            colon = full_text.find(':')
            if colon != -1:
                full_text = full_text[colon + 1:] # Start reading AFTER the colon

        # Step 5: Normalization
        # Ingredients can be separated by newlines, commas, or semicolons.
        # We turn them all into commas to make splitting easy.
        full_text = full_text.replace('\n', ',').replace('\r', ',').replace(';', ',')

        parsed = []
        for ing in full_text.split(','):
            # Step 6: Regex Cleaning (Regular Expressions)
            # Remove any character that IS NOT: a-z, A-Z, 0-9, hyphen, space, or parenthesis.
            # This removes emojis, weird lines, or scanning artifacts.
            c = re.sub(r'[^a-zA-Z0-9\-\s\(\)]', '', ing).strip().title()
            
            # Filter out tiny noise (e.g., "a", "1", ".")
            if len(c) > 2:
                parsed.append(c)

        # Step 7: Remove Duplicates
        # Use a 'set' to track what we've seen. 
        # (e.g., prevent ["Water", "Water", "Glycerin"] -> ["Water", "Glycerin"])
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