@echo off
REM Run only integration tests

set JWT_SECRET_KEY=test_secret_key_at_least_32_chars_long_for_testing
set DATABASE_URL=sqlite+aiosqlite:///:memory:
set SYNC_DATABASE_URL=sqlite:///:memory:

echo Running integration tests only...
.\venv\Scripts\python.exe -m pytest tests/integration/ -v --tb=short
