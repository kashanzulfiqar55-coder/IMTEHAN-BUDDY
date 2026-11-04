# 📚 Imtihan Buddy

AI exam-practice app for Pakistani Matric and Intermediate students.
Upload a chapter from your own textbook (PDF or TXT) and the app will:

1. Create practice questions (MCQ, short, long) **only from that chapter**
2. Check your answers against the chapter text
3. Explain the answers in **English, Roman Urdu, or both**

## Files
- `app.py` - the Streamlit app
- `requirements.txt` - Python packages
- `README.md` - this file

## Run locally
```bash
pip install -r requirements.txt
mkdir .streamlit
echo 'GEMINI_API_KEY = "your-key"' > .streamlit/secrets.toml
streamlit run app.py
```
(Never upload `.streamlit/secrets.toml` to GitHub.)

## Deploy on Streamlit Community Cloud
1. Upload these 3 files to a GitHub repo.
2. Go to https://share.streamlit.io -> **New app** -> pick your repo, branch `main`, file `app.py`.
3. Open **Advanced settings -> Secrets** and paste:
   ```
   GEMINI_API_KEY = "your-key"
   ```
4. Click **Deploy**.

## Model
The model name is set at the top of `app.py` (`MODEL = ...`). Get a free key from https://aistudio.google.com

## Limits
- Works with text-based PDFs (not scanned photos).
- Very long chapters are trimmed; upload in sections for best results.
