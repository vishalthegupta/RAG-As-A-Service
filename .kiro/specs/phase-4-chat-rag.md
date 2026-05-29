# Phase 4 — Chat / RAG

## Context
Phases 1–3 complete. Documents upload, process, and store chunks in ChromaDB.
Now build the RAG query pipeline and streaming chat endpoints.
Read all files in .kiro/steering/ before writing any code.

## Goal
Users can chat with their documents. Queries are embedded, relevant chunks
retrieved, and responses streamed token-by-token via SSE.

## Rules
- Feature 22 (RAG retrieval) must be tested independently before wiring into Feature 25 (SSE endpoint)
- Feature 23 (Groq) must work before adding Feature 24 (HuggingFace fallback)
- SSE stream must always emit a `done` or `error` event — never leave the client hanging
- Never let the LLM answer outside the provided context

---

## Feature 20 — POST /chat/sessions (Create Session)

### What to build

**`app/chat/schemas.py`**
```python
class SessionCreateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)

class SessionResponse(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SessionListItem(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    message_count: int
    last_message_at: datetime | None
```

**`app/chat/service.py`** — create_session()
```python
async def create_session(
    db: AsyncSession,
    current_user: User,
    request: SessionCreateRequest
) -> ChatSession:
    # 1. Check user has at least one document with status=READY
    #    If not: raise DocumentNotReadyError
    # 2. Create ChatSession record
    # 3. If title not provided: set title = "New chat" (auto-title on first message later)
    # 4. Return ChatSession
```

**Router:**
```python
POST /chat/sessions
  Auth: required
  Body: SessionCreateRequest
  Response 201: SessionResponse
```

### Tests to write
```python
async def test_create_session_success(client, auth_headers, ready_document):
    res = await client.post("/api/v1/chat/sessions", headers=auth_headers, json={})
    assert res.status_code == 201
    assert "id" in res.json()

async def test_create_session_no_ready_docs_fails(client, auth_headers):
    # user has no documents, or all are PENDING
    assert res.status_code == 409

async def test_create_session_requires_auth(client):
    assert res.status_code == 401

async def test_create_session_with_title(client, auth_headers, ready_document):
    res = await client.post("/api/v1/chat/sessions",
        headers=auth_headers, json={"title": "My session"})
    assert res.json()["title"] == "My session"
```

---

## Feature 21 — GET /chat/sessions (List Sessions)

**`app/chat/service.py`** — list_sessions()
```python
# Joins with chat_messages to get message_count and last_message_at
# Orders by updated_at DESC
# Only returns sessions for current_user
```

**Router:**
```python
GET /chat/sessions
  Auth: required
  Response 200: list[SessionListItem]
```

### Tests to write
```python
async def test_list_sessions_empty(client, auth_headers):
    assert res.json() == []

async def test_list_sessions_returns_own_only(client, auth_headers, other_user_session):
    # must not see other user's sessions
    assert len(res.json()) == 0

async def test_list_sessions_includes_message_count(client, auth_headers, session_with_messages):
    assert res.json()[0]["message_count"] == 2
```

---

## Feature 22 — RAG Pipeline (Retrieval)

### What to build
This is the core intelligence. Test it thoroughly in isolation before connecting to SSE.

**`app/chat/rag_pipeline.py`**

```python
@dataclass
class RetrievedChunk:
    text: str
    doc_id: str
    doc_name: str
    chunk_index: int
    score: float   # 1 - distance (higher = more similar)

def retrieve_context(
    user_id: str,
    query: str,
    top_k: int = None
) -> list[RetrievedChunk]:
    """
    1. Embed query: EmbeddingService.get_instance().encode_single(query)
    2. ChromaDB query: query_similar(user_id, embedding, top_k or settings.RAG_TOP_K)
    3. Filter: keep only chunks where distance < settings.RAG_SIMILARITY_THRESHOLD
    4. Deduplicate: if multiple chunks from same doc_id, keep highest score only
    5. Return sorted by score descending
    """

def build_prompt(
    retrieved: list[RetrievedChunk],
    chat_history: list[dict],
    user_query: str
) -> tuple[str, list[dict]]:
    """
    Returns (system_prompt, messages_list)

    system_prompt = the SYSTEM_PROMPT constant (see steering file 05)
    messages = last min(len(history), RAG_MAX_HISTORY_MESSAGES) messages
               + {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}

    context = "\n\n---\n\n".join([
        f"[Source: {c.doc_name}]\n{c.text}" for c in retrieved
    ])

    If retrieved is empty:
    content = "Context: No relevant information found.\n\nQuestion: {query}"
    """

SYSTEM_PROMPT = """You are a helpful assistant that answers questions strictly
based on the provided context documents.

Rules:
- Only answer from the context below.
- If the answer is not in the context, say: "I don't have enough information in the provided documents to answer that."
- Be concise and direct.
- When referencing information, you may mention which document it comes from.
- Do not make up facts or use outside knowledge."""
```

### Tests to write
```python
def test_retrieve_context_returns_chunks(mock_chroma, mock_embedder):
    # seed ChromaDB with known chunks
    # query with related text
    # verify returned chunks

def test_retrieve_context_empty_when_no_match(mock_chroma, mock_embedder):
    # query with completely unrelated text
    result = retrieve_context("user-id", "completely unrelated query")
    assert result == []

def test_retrieve_deduplicates_same_doc(mock_chroma, mock_embedder):
    # seed 3 chunks from same doc_id all scoring high
    # result should have at most 1 chunk from that doc

def test_build_prompt_with_context(sample_chunks):
    system, messages = build_prompt(sample_chunks, [], "What is X?")
    last_msg = messages[-1]
    assert "Context:" in last_msg["content"]
    assert "What is X?" in last_msg["content"]
    assert "[Source:" in last_msg["content"]

def test_build_prompt_empty_context():
    system, messages = build_prompt([], [], "What is X?")
    assert "No relevant information found" in messages[-1]["content"]

def test_build_prompt_trims_history():
    long_history = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    system, messages = build_prompt([], long_history, "query")
    # history messages should be capped at RAG_MAX_HISTORY_MESSAGES
    history_msgs = [m for m in messages if m != messages[-1]]
    assert len(history_msgs) <= settings.RAG_MAX_HISTORY_MESSAGES
```

### Done when
- All 6 tests pass
- Empty context handled gracefully
- History capped at MAX_HISTORY_MESSAGES

---

## Feature 23 — LLM Abstraction + Groq Provider

### What to build

**`app/llm/base.py`**
```python
class LLMProvider(ABC):
    @abstractmethod
    async def stream_chat(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.1
    ) -> AsyncGenerator[str, None]:
        """Yields token strings. Raises LLMUnavailableError on API failure."""
        ...

    @abstractmethod
    async def health_check(self) -> bool: ...
```

**`app/llm/groq_provider.py`**
```python
class GroqProvider(LLMProvider):
    MODEL = "llama3-8b-8192"
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

    async def stream_chat(self, system_prompt, messages, max_tokens=1024, temperature=0.1):
        # POST to Groq API with stream=True
        # Headers: Authorization: Bearer {settings.GROQ_API_KEY}
        # Parse SSE response line by line
        # Each line: "data: {...}" → extract choices[0].delta.content
        # Stop on "data: [DONE]"
        # Yield each non-empty content string
        # On HTTP error or timeout: raise LLMUnavailableError
```

**`app/llm/factory.py`**
```python
def get_llm_provider() -> LLMProvider:
    match settings.LLM_PROVIDER:
        case "groq": return GroqProvider()
        case "huggingface": return HuggingFaceProvider()
        case _: raise ValueError(f"Unknown LLM provider: {settings.LLM_PROVIDER}")
```

### Tests to write (mock HTTP calls — never call real Groq in tests)
```python
@pytest.fixture
def mock_groq_stream(monkeypatch):
    async def fake_stream(*args, **kwargs):
        for token in ["Hello", " ", "world"]:
            yield token
    monkeypatch.setattr(GroqProvider, "stream_chat", fake_stream)

async def test_groq_streams_tokens(mock_groq_stream):
    provider = GroqProvider()
    tokens = []
    async for token in provider.stream_chat("system", [{"role": "user", "content": "hi"}]):
        tokens.append(token)
    assert tokens == ["Hello", " ", "world"]

async def test_groq_raises_on_api_error(monkeypatch):
    # mock HTTP 429 response
    # verify LLMUnavailableError raised

async def test_factory_returns_groq_by_default(monkeypatch):
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    provider = get_llm_provider()
    assert isinstance(provider, GroqProvider)
```

---

## Feature 24 — HuggingFace Fallback Provider

### What to build

**`app/llm/huggingface_provider.py`**
```python
class HuggingFaceProvider(LLMProvider):
    BASE_URL = "https://api-inference.huggingface.co/models"
    MODEL = settings.HUGGINGFACE_MODEL

    async def stream_chat(self, system_prompt, messages, max_tokens=1024, temperature=0.1):
        # Format messages as a single prompt string
        # POST to HuggingFace Inference API
        # Stream response tokens
        # Raise LLMUnavailableError on failure
```

**Update `app/chat/rag_pipeline.py`** — add fallback:
```python
async def get_llm_response(
    system_prompt: str,
    messages: list[dict]
) -> AsyncGenerator[str, None]:
    """Try Groq first, fall back to HuggingFace on LLMUnavailableError."""
    providers = [get_llm_provider()]
    if settings.LLM_PROVIDER == "groq":
        providers.append(HuggingFaceProvider())

    last_error = None
    for provider in providers:
        try:
            async for token in provider.stream_chat(system_prompt, messages):
                yield token
            return
        except LLMUnavailableError as e:
            logger.warning("llm.provider.failed", provider=type(provider).__name__)
            last_error = e

    raise LLMUnavailableError("All providers failed") from last_error
```

### Tests to write
```python
async def test_fallback_used_when_groq_fails(monkeypatch):
    # mock Groq to raise LLMUnavailableError
    # mock HuggingFace to yield tokens
    # verify HuggingFace tokens received

async def test_raises_when_all_providers_fail(monkeypatch):
    # mock both providers to raise LLMUnavailableError
    with pytest.raises(LLMUnavailableError):
        async for _ in get_llm_response("sys", []):
            pass
```

---

## Feature 25 — POST /chat/sessions/{id}/messages (SSE Streaming)

### What to build
The main chat endpoint. Wires Feature 22 (retrieval) + Feature 23/24 (LLM) into a streaming response.

**`app/chat/service.py`** — send_message()
```python
async def send_message_stream(
    db: AsyncSession,
    current_user: User,
    session_id: UUID,
    message: str
) -> AsyncGenerator[str, None]:
    """
    1. Verify session belongs to current_user → raise DocumentNotFoundError if not
    2. Save user message to chat_messages
    3. Fetch last RAG_MAX_HISTORY_MESSAGES from this session
    4. retrieve_context(user_id, message)
    5. build_prompt(retrieved, history, message)
    6. Start timer
    7. Accumulate full response while streaming via get_llm_response()
    8. Yield SSE events: token, token, token... sources, done
    9. After stream: save assistant message with sources + latency to chat_messages
    10. If session title is "New chat": update title = first 50 chars of user message
    """
```

**SSE event format (exact):**
```
data: {"token": "Hello"}\n\n
data: {"token": " world"}\n\n
data: {"sources": [{"doc_name": "...", "chunk_text": "...", "score": 0.92}]}\n\n
data: {"done": true, "latency_ms": 340}\n\n
```
On error:
```
data: {"error": "AI service temporarily unavailable"}\n\n
```

**Router:**
```python
POST /chat/sessions/{session_id}/messages
  Auth: required
  Body: {"message": str (min_length=1, max_length=4000)}
  Response 200: StreamingResponse(media_type="text/event-stream")
  Headers: Cache-Control: no-cache, X-Accel-Buffering: no
  Rate limit: settings.CHAT_RATE_LIMIT
```

### Tests to write
```python
async def test_send_message_streams_tokens(client, auth_headers, session_with_ready_doc, mock_llm):
    res = await client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        headers=auth_headers, json={"message": "What is this doc about?"}
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "text/event-stream; charset=utf-8"
    # parse SSE events
    events = parse_sse(res.text)
    assert any("token" in e for e in events)
    assert any("done" in e for e in events)

async def test_send_message_saves_to_db(client, auth_headers, session_id, mock_llm, db):
    await client.post(...)
    messages = db.query(ChatMessage).filter_by(session_id=session_id).all()
    assert len(messages) == 2   # user + assistant

async def test_send_message_wrong_session_returns_404(client, auth_headers, other_session):
    assert res.status_code == 404

async def test_send_message_empty_message_returns_422(client, auth_headers, session_id):
    res = await client.post(..., json={"message": ""})
    assert res.status_code == 422

async def test_send_message_llm_failure_returns_error_event(client, auth_headers, session_id, mock_llm_fail):
    events = parse_sse(res.text)
    assert any("error" in e for e in events)
```

---

## Feature 26 — GET /chat/sessions/{id}/messages (History)

**`app/chat/service.py`** — get_messages()
```python
# Fetch all messages for session ordered by created_at ASC
# Verify session belongs to current_user
# Return list with sources included
```

**Tests:**
```python
async def test_get_messages_success(client, auth_headers, session_with_messages):
    res = await client.get(f"/api/v1/chat/sessions/{session_id}/messages", headers=auth_headers)
    assert res.status_code == 200
    assert len(res.json()) == 2   # user + assistant

async def test_get_messages_includes_sources(client, auth_headers, session_with_assistant_message):
    messages = res.json()
    assistant_msg = next(m for m in messages if m["role"] == "assistant")
    assert "sources" in assistant_msg

async def test_get_messages_wrong_session_404(client, auth_headers, other_session):
    assert res.status_code == 404
```

---

## Feature 27 — DELETE /chat/sessions/{id}

**`app/chat/service.py`** — delete_session()
```python
# Verify session belongs to current_user
# Delete all chat_messages for session (cascade handles this)
# Delete ChatSession
```

**Tests:**
```python
async def test_delete_session_success(client, auth_headers, session_id):
    res = await client.delete(f"/api/v1/chat/sessions/{session_id}", headers=auth_headers)
    assert res.status_code == 200
    # verify session gone from DB
    # verify all messages gone

async def test_delete_other_session_404(client, auth_headers, other_session):
    assert res.status_code == 404
```

---

## Phase 4 Complete — Checklist

Before moving to Phase 5, verify all of the following:

- [ ] `pytest tests/` exits with 0 failures
- [ ] End-to-end manual test: upload PDF → wait for READY → create session → send message → receive streamed response
- [ ] SSE response always ends with `done` or `error` event
- [ ] Chat messages saved to DB with sources JSON populated
- [ ] LLM fallback works: mock Groq failure, verify HuggingFace is tried
- [ ] Rate limiting active on chat endpoint

Report this summary when done:
```
✅ Phase 4 complete
   Features: 8/8 (cumulative: 27/37)
   Tests: N passed, 0 failed
   Ready for Phase 5: Frontend
```
