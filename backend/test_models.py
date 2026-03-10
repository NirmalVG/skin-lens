# Import the official Google GenAI SDK to interact with Gemini
from google import genai

# Import tools to handle secret environment variables
from dotenv import load_dotenv
import os

# 1. LOAD SECRETS
# This reads your hidden '.env' file and loads the variables into Python's memory.
# It ensures your private API key isn't accidentally uploaded to GitHub.
load_dotenv()

# 2. INITIALIZE THE CLIENT
# The 'Client' is your secure connection to Google's AI servers.
# os.getenv("GEMINI_API_KEY") fetches the secret key you stored in your .env file.
# If the key is missing or invalid, this is where the app would crash.
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 3. FETCH AND ITERATE
# client.models.list() sends a quick request to Google asking: 
# "What AI models does this API key have permission to use?"
# It returns a list of model objects (like gemini-1.5-pro, gemini-2.5-flash, etc.)
for model in client.models.list():
    
    # 4. PRINT THE RESULTS
    # We only want to see the actual string name of the model so we can 
    # copy/paste it into our main app (like we did in the ocr_service.py file!)
    print(model.name)