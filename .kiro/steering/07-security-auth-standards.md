# Security & Authentication Standards

## Authentication Flow
- Stateless JWT — no server-side sessions
- Access token: 24h expiry (`ACCESS_TOKEN_EXPIRE_MINUTES=1440`)
- Refresh token: 7 days expiry, stored in DB (allows revocation)
- Token type: `Bearer` in `Authorization` header
- Never accept tokens in query params or cookies (CSRF risk)

## Password Handling
```python
# auth/utils.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```
- bcrypt cost factor: **12** (secure, ~300ms — acceptable for login)
- Never log passwords, tokens, or hashed passwords
- Minimum password length: 8 characters (validate in Pydantic schema)
- Never return hashed passwords in API responses — ever

## JWT Implementation
```python
# auth/utils.py
import jwt
from datetime import UTC

def create_access_token(user_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## Authorization — Ownership Enforcement
**Every** service method that fetches user data must include `user_id` in the query. No exceptions.

```python
# WRONG — no ownership check
async def get_document(db, doc_id):
    return await db.get(Document, doc_id)

# RIGHT — always scope to user
async def get_document(db, doc_id: UUID, user_id: UUID) -> Document:
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == user_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise DocumentNotFoundError()   # 404, not 403 — don't leak existence
    return doc
```

## File Upload Security
```python
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024   # 50MB

async def validate_upload(file: UploadFile) -> None:
    # Check MIME type from content, not just filename
    content_start = await file.read(2048)
    await file.seek(0)
    detected_mime = magic.from_buffer(content_start, mime=True)
    
    if detected_mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, f"File type not allowed: {detected_mime}")
    
    # Check size via content-length header first, then stream check
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(413, "File too large. Maximum 50MB.")
```
- Always validate MIME from file content using `python-magic`, not just the filename extension
- Sanitize filename before saving: `secure_filename(file.filename)`
- Store files outside web root — never serve raw uploads via static files
- Generate a UUID-based path for storage: `uploads/{user_id}/{doc_id}/{secure_filename}`

## Rate Limiting
```python
# Use slowapi (FastAPI rate limiter)
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/sessions/{session_id}/messages")
@limiter.limit("60/minute")
async def send_message(...):
    ...
```
- Chat endpoint: 60 req/min per IP
- Auth endpoints (login/register): 10 req/min per IP (brute-force protection)
- Document upload: 10 req/min per user

## CORS Configuration
```python
# main.py — only allow known origins
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,   # e.g. ["http://localhost:3000"] in dev
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)
```
- Never use `allow_origins=["*"]` — always specify origins
- In prod: use env var `ALLOWED_ORIGINS` with the actual frontend domain

## Secrets Management
- All secrets in `.env` file — never committed to git
- `.env` in `.gitignore` — enforce this
- `.env.example` committed with placeholder values
- Required secrets: `JWT_SECRET_KEY`, `GROQ_API_KEY`, `DATABASE_URL`, `REDIS_URL`
- `JWT_SECRET_KEY` must be at least 32 random characters — generate with `openssl rand -hex 32`
