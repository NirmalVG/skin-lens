# Skin Lens 🌿🔍

**Clinical Precision AI for Skincare Ingredient Analysis**

![Skin Lens Hero Image](./screenshots/hero.png)
_(Note: Place a wide, beautiful screenshot of your app here to serve as the banner)_

Skin Lens is a full-stack, AI-powered web application designed to bring clinical transparency to the beauty industry. By leveraging advanced Computer Vision (OCR) and Large Language Models (Gemini Vision), the application allows users to upload a photo of any cosmetic label and instantly receive a detailed, scientifically-backed safety breakdown of its ingredients.

---

## 📸 Application Gallery

### 1. The Home Interface

The premium, minimalist landing page showcasing the "Chemical-to-Clear" AI capability.
![Home Page](./screenshots/home.png)

### 2. AI Ingredient Scanner (The "Lens")

Users can drag & drop or take a photo of a product label. The AI parses the image and cross-references the clinical database in real-time.
![Analyze Page](./screenshots/analyze.png)

### 3. Clinical Encyclopedia

A server-side paginated database of 350+ cosmetic ingredients. Users can search and filter by specific risk levels (Safe, Moderate, Irritant, Avoid).
![Encyclopedia Page](./screenshots/encyclopedia.png)

### 4. Interactive Skin Quiz

A dynamic assessment tool that determines the user's skin profile and fetches mathematically calculated ingredient recommendations.
![Quiz Page](./screenshots/quiz.png)

---

## 🚀 Key Features

- **Multimodal AI Scanning (The "Lens"):** Upload or take a picture of a product label. The backend utilizes Google's Gemini Vision API to extract text and simultaneously analyze complex chemical nomenclature, bypassing the limitations of traditional OCR.
- **Clinical Database Engine:** Features a highly optimized, seeded MySQL database of 350+ cosmetic ingredients, categorized by safety ratings (Safe, Moderate, Irritant, Avoid) and skin-type compatibility.
- **Hybrid Data Resolution Strategy:** If an ingredient scanned from a label exists in the clinical database, it serves verified data. If it is a rare or new chemical, it dynamically falls back to Gemini AI to generate a live clinical assessment.
- **Ingredient Encyclopedia:** A fully searchable, server-side paginated database explorer allowing users to filter chemicals by risk level.
- **Personalized Skin Quiz:** An interactive assessment that determines a user's skin profile and recommends safe, compatible ingredients.
- **Progressive Web App (PWA):** Built with modern caching strategies, allowing it to act like a native mobile app for on-the-go scanning in stores.

---

## 🛠️ Technology Stack

### Frontend (The "Face")

- **Framework:** React 18 (via Vite)
- **Routing:** React Router DOM
- **Styling:** Bootstrap 5, React-Bootstrap, Custom CSS Variables (Premium Minimalist UI)
- **Features:** PWA (Vite PWA Plugin), Drag-and-Drop Image Upload, Real-time Validation.
- **Deployment:** Netlify

### Backend (The "Brain")

- **Framework:** FastAPI (Python)
- **ORM:** SQLAlchemy
- **AI Integration:** Google GenAI SDK (Gemini 2.5 Flash/Pro)
- **Image Processing:** Pillow (PIL)
- **Database:** MySQL (Cloud-hosted via Render/Aiven)
- **Deployment:** Render

---

## 🏗️ Architecture & Deep Concepts

### 1. The Fallback Mechanism

The OCR service does not rely on a single point of failure. It utilizes a **Waterfall Fallback Strategy**, iterating through an array of Gemini models (from `gemini-2.5-flash` to `gemini-pro-latest`). If one model fails or hits a rate limit, it automatically switches to the next, ensuring high availability.

### 2. Database Resilience (`NullPool`)

To combat the "dropped connection" issue common in serverless cloud deployments, the SQLAlchemy engine utilizes `NullPool`. This disables connection pooling, forcing a fresh, guaranteed connection for every HTTP request, prioritizing application stability over slight speed advantages.

### 3. Magic Byte Detection

For image uploads, the backend does not rely on easily spoofed file extensions (like `.jpg`). Instead, it inspects the **Magic Bytes** of the binary stream (`\x89PNG` or `\xff\xd8\xff`) to programmatically verify the MIME type before passing it to the AI.

---

## 💻 Local Development Setup

### Prerequisites

- Node.js (v18+)
- Python (3.10+)
- MySQL Server (or a cloud MySQL database URI)
- Google Gemini API Key

### Step 1: Backend Setup

1. Navigate to the backend directory (or root if running a flat structure):
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:

```bash
python -m venv venv

# Windows:
.\venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install fastapi uvicorn sqlalchemy pymysql python-dotenv pillow google-genai requests
```

4. Create a `.env` file in the same directory and add your credentials:

```env
DATABASE_URL=mysql+pymysql://user:password@host:port/dbname
GEMINI_API_KEY=your_google_gemini_key_here
```

5. Seed the database (Run this once to populate the 350+ ingredients):

```bash
python seed.py
```

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The backend will be running at http://127.0.0.1:8000

### Step 2: Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node modules:

```bash
npm install
```

3. Create a `.env` file in the frontend folder:

```env
VITE_API_URL=[http://127.0.0.1:8000](http://127.0.0.1:8000)
```

Start the Vite development server:

```bash
npm run dev
```

The frontend will be running at http://localhost:5173

## 👨‍💻 Author

Built as a comprehensive full-stack capstone project to demonstrate proficiency in modern web architecture, AI integration, and robust database management.
