# Script para iniciar el Backend FastAPI localmente en Windows
$env:PYTHONPATH = "."
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
