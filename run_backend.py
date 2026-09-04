import os
import sys
import uvicorn

if __name__ == "__main__":
    # Asegurar que el directorio raíz esté en sys.path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    os.environ["PYTHONPATH"] = project_root

    print("=" * 60)
    print(" INICIANDO SERVIDOR BACKEND FASTAPI")
    print(" URL: http://127.0.0.1:8000")
    print(" Documentacion Swagger: http://127.0.0.1:8000/docs")
    print(" Presione Ctrl+C para detener el servidor")
    print("=" * 60)

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
