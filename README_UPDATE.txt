CNIS UPDATED SOURCE
===================

IMPORTANT: This is a source-code update only. It does NOT include your .env,
database, uploaded PDFs, or virtual environment.

BEFORE REPLACING:
1. Close the Flask server (Ctrl+C).
2. Make a backup copy of your existing project folder.
3. Keep your existing .env file, instance/cnis.db, and uploads folder.
4. Copy these replacement files/folders into your existing project and allow
   replacement of matching source files only.
5. Do not replace or delete your existing database or uploads.
6. Ensure .env contains SECRET_KEY and GEMINI_API_KEY. Never share it.

RUN:
  venv\Scripts\Activate.ps1
  python -m pip install -r requirements.txt
  python app.py

Open http://127.0.0.1:5000

Existing pending notices remain pending. Admin can review them and publish them.
Students see only published notices.

SECURITY:
- The uploaded archive included a .env file. Rotate the Gemini API key in
  Google AI Studio and update your local .env before running this update.
- This is intended for local development. Before public deployment, configure
  HTTPS, set SESSION_COOKIE_SECURE=True, disable debug mode, and add production
  security hardening.
