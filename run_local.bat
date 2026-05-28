@echo off
REM Quick start script for local development (Windows)

echo ========================================
echo RAG-as-a-Service Local Development
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo Please copy .env.example to .env and configure it.
    echo.
    echo Run: copy .env.example .env
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist backend\venv (
    echo [INFO] Creating virtual environment...
    cd backend
    python -m venv venv
    cd ..
)

REM Activate virtual environment and install dependencies
echo [INFO] Activating virtual environment...
call backend\venv\Scripts\activate.bat

echo [INFO] Installing dependencies...
cd backend
pip install -q -r requirements.txt

echo.
echo [INFO] Running environment verification...
python test_setup.py

echo.
echo ========================================
echo Starting FastAPI development server...
echo ========================================
echo.
echo API will be available at:
echo   - http://localhost:8000
echo   - http://localhost:8000/docs (Swagger UI)
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
