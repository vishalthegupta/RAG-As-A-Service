@echo off
echo ========================================
echo Starting RAG-as-a-Service Backend
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Start the server
echo Starting FastAPI server...
echo API will be available at:
echo   - http://localhost:8000
echo   - http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
