# Phase 2 — Auth

## Context
Phase 1 (Foundation) is complete. Database models, config, exceptions, and
logging are all working. Now build the full authentication system.
Read all files in .kiro/steering/ before writing any code.

## Goal
Complete JWT-based authentication — register, login, token refresh, and the
`get_current_user` dependency that every protected route will use.

## Rules
- Implement features in the exact order listed below
- After each feature: write tests, run them, confirm green, report, then proceed
- Services raise custom exceptions — never raise HTTPException in service layer
- Never return hashed passwords in any API response

---

## Feature 6 — POST /auth/register

### What to build

**`app/auth/schemas.py`**
```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

**`app/auth/utils.py`**
```python
# hash_password(password: str) -> str   — bcrypt, rounds=12
# verify_password(plain: str, hashed: str) -> bool
# create_access_token(user_id: UUID) -> str
# create_refresh_token(user_id: UUID) -> str
# decode_token(token: str) -> dict      — raises HTTPException on invalid/expired
```

**`app/auth/service.py`**
```python
# register_user(db, request: RegisterRequest) -> User
#   1. Check email not already taken → raise DuplicateEmailError if so
#   2. Hash password with hash_password()
#   3. Create and persist User record
#   4. Return User ORM object
```

**`app/auth/router.py`**
```python
POST /auth/register
  Body: RegisterRequest
  Calls: auth_service.register_user()
  Response 201: UserResponse
  On DuplicateEmailError: global handler returns 409
```

### Tests to write
```python
# test_auth_routes.py
async def test_register_success(client):
    res = await client.post("/api/v1/auth/register", json={
        "email": "user@test.com", "password": "password123"
    })
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "user@test.com"
    assert "hashed_password" not in body
    assert "id" in body

async def test_register_duplicate_email(client):
    # register twice with same email
    assert second_response.status_code == 409

async def test_register_weak_password(client):
    # password under 8 chars
    assert res.status_code == 422

async def test_register_invalid_email(client):
    assert res.status_code == 422
```

### Done when
- All 4 tests pass
- Hashed password never appears in response
- Duplicate email returns 409

---

## Feature 7 — POST /auth/login + JWT issue

### What to build

**`app/auth/schemas.py`** — add:
```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int   # seconds
```

**`app/auth/service.py`** — add:
```python
# login_user(db, request: LoginRequest) -> TokenResponse
#   1. Fetch user by email → raise HTTPException 401 if not found
#   2. verify_password() → raise HTTPException 401 if wrong
#   3. Check user.is_active → raise HTTPException 401 if inactive
#   4. create_access_token() + create_refresh_token()
#   5. Return TokenResponse
```

**`app/auth/router.py`** — add:
```python
POST /auth/login
  Body: LoginRequest
  Response 200: TokenResponse
  On wrong credentials: 401 {"detail": "Invalid credentials"}
```

### JWT token spec
- Access token payload: `{"sub": str(user_id), "type": "access", "iat": ..., "exp": ...}`
- Refresh token payload: `{"sub": str(user_id), "type": "refresh", "iat": ..., "exp": ...}`
- Algorithm: HS256, secret from `settings.JWT_SECRET_KEY`
- Access expiry: `settings.ACCESS_TOKEN_EXPIRE_MINUTES` (default 1440 = 24h)
- Refresh expiry: `settings.REFRESH_TOKEN_EXPIRE_DAYS` (default 7)

### Tests to write
```python
async def test_login_success(client, registered_user):
    res = await client.post("/api/v1/auth/login", json={
        "email": "user@test.com", "password": "password123"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert res.json()["token_type"] == "bearer"

async def test_login_wrong_password(client, registered_user):
    assert res.status_code == 401

async def test_login_nonexistent_email(client):
    assert res.status_code == 401

async def test_login_returns_valid_jwt(client, registered_user):
    token = res.json()["access_token"]
    decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    assert decoded["type"] == "access"
    assert "sub" in decoded
```

### Done when
- All 4 tests pass
- JWT payload has correct structure
- Wrong credentials always return 401

---

## Feature 8 — POST /auth/refresh

### What to build

**`app/auth/schemas.py`** — add:
```python
class RefreshRequest(BaseModel):
    refresh_token: str

class AccessTokenResponse(BaseModel):
    access_token: str
    expires_in: int
```

**`app/auth/service.py`** — add:
```python
# refresh_access_token(db, refresh_token: str) -> AccessTokenResponse
#   1. decode_token(refresh_token) — raises 401 if invalid/expired
#   2. Check payload["type"] == "refresh" — raise 401 if not
#   3. Fetch user by payload["sub"] — raise 401 if not found or inactive
#   4. Issue new access_token only (refresh token stays the same)
#   5. Return AccessTokenResponse
```

**`app/auth/router.py`** — add:
```python
POST /auth/refresh
  Body: RefreshRequest
  Response 200: AccessTokenResponse
```

### Tests to write
```python
async def test_refresh_success(client, auth_tokens):
    res = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": auth_tokens["refresh_token"]
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

async def test_refresh_with_access_token_fails(client, auth_tokens):
    # passing access token as refresh token must fail
    assert res.status_code == 401

async def test_refresh_with_invalid_token(client):
    assert res.status_code == 401

async def test_refresh_with_expired_token(client):
    # create token with past expiry
    assert res.status_code == 401
```

### Done when
- All 4 tests pass
- Passing an access token as refresh token correctly returns 401
- Expired tokens return 401

---

## Feature 9 — GET /auth/me + get_current_user dependency

### What to build

**`app/dependencies.py`**
```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_token(token)           # raises 401 on invalid
    user_id = UUID(payload["sub"])
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    return user
```

**`app/auth/router.py`** — add:
```python
GET /auth/me
  Header: Authorization: Bearer <token>
  Depends: get_current_user
  Response 200: UserResponse
```

### Tests to write
```python
async def test_get_me_success(client, auth_headers):
    res = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "user@test.com"

async def test_get_me_no_token(client):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401

async def test_get_me_invalid_token(client):
    res = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"})
    assert res.status_code == 401

async def test_get_me_expired_token(client):
    assert res.status_code == 401
```

Also write a unit test for `auth/utils.py`:
```python
def test_hash_and_verify_password():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed)
    assert not verify_password("wrongpassword", hashed)

def test_create_and_decode_access_token():
    user_id = uuid4()
    token = create_access_token(user_id)
    decoded = decode_token(token)
    assert decoded["sub"] == str(user_id)
    assert decoded["type"] == "access"
```

### Done when
- All tests pass
- `get_current_user` dependency works in Depends() injection
- `auth_headers` fixture available for all future test files

---

## Phase 2 Complete — Checklist

Before moving to Phase 3, verify all of the following:

- [ ] `pytest tests/` exits with 0 failures
- [ ] Register → Login → Refresh → Me full flow works end-to-end manually
- [ ] Hashed password never appears in any response
- [ ] Invalid tokens consistently return 401
- [ ] `get_current_user` dependency importable from `app.dependencies`
- [ ] Auth rate limiting applied: 10 req/min on register and login

Report this summary when done:
```
✅ Phase 2 complete
   Features: 4/4 (cumulative: 9/37)
   Tests: N passed, 0 failed
   Ready for Phase 3: Documents
```
