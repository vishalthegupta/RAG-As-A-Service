@echo off
REM Test runner script for Phase 1

echo ========================================
echo RAG-as-a-Service - Test Runner
echo ========================================
echo.

REM Set required environment variables for tests
set JWT_SECRET_KEY=test_secret_key_at_least_32_chars_long_for_testing
set DATABASE_URL=sqlite+aiosqlite:///:memory:
set SYNC_DATABASE_URL=sqlite:///:memory:

echo Setting up test environment...
echo.

REM Check if pytest is installed
.\venv\Scripts\python.exe -c "import pytest" 2>nul
if errorlevel 1 (
    echo [ERROR] pytest not found. Installing test dependencies...
    .\venv\Scripts\pip.exe install pytest pytest-asyncio aiosqlite pyyaml
    if errorlevel 1 (
        echo [ERROR] Failed to install test dependencies
        exit /b 1
    )
)

echo Running tests...
echo.

REM Run all tests with verbose output
.\venv\Scripts\python.exe -m pytest tests/ -v --tb=short

if errorlevel 1 (
    echo.
    echo [FAILED] Some tests failed. See output above.
    exit /b 1
) else (
    echo.
    echo [SUCCESS] All tests passed!
    exit /b 0
)
