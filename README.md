# AI Hospital

This project is a Streamlit application. Start it from the project folder so its relative data and SQLite paths resolve correctly.

## Run on Windows

Install Python 3.10 or newer, then open PowerShell in this folder and run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Streamlit prints a local URL (usually http://localhost:8501); open it in your browser. If PowerShell blocks environment activation, skip the activation line and use `\.venv\Scripts\python.exe -m pip ...` and `\.venv\Scripts\python.exe -m streamlit run app.py` for the remaining commands.

The existing `venv` folder was created for macOS and is not usable on Windows. The commands above create a Windows environment in `.venv`.

## Optional services

Some AI, email, and SMS features require external credentials. Set `GROQ_API_KEY`, `SMTP_EMAIL`, `SMTP_PASSWORD`, and/or the Twilio settings in your environment as needed. The app may start without these, but those integrations will not work. Image text extraction also needs the Tesseract OCR application installed separately.

## Notes

- The app creates/updates `hospital.db` and initializes local datasets when it starts. Keep a backup if this folder contains data you need.
- This is a demo application, not a clinically validated diagnostic or emergency response system. Do not use it to make real medical decisions.
