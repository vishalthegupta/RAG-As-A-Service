# Feature Development Workflow

## The Golden Rule
**One feature at a time. No exceptions.**
Implement → Test → Confirm passing → Only then move to the next feature.
Never start the next feature while tests are red or untested code exists.

## The Workflow (Repeat for Every Feature)

```
┌─────────────────────────────────────┐
│  1. IMPLEMENT the feature           │
│     Write the actual code           │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│  2. WRITE tests for it              │
│     Unit + integration as needed    │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│  3. RUN the tests                   │
│     pytest / npm test               │
└────────────────┬────────────────────┘
                 │
        ┌────────▼────────┐
        │  All passing?   │
        └────┬───────┬────┘
             │ YES   │ NO
             │       │
             │  ┌────▼──────────────────┐
             │  │ FIX the code or test  │
             │  │ Re-run until green    │
             │  └────────────┬──────────┘
             │               │ (loop back to RUN)
             │◄──────────────┘
             │
┌────────────▼────────────────────────┐
│  4. CONFIRM & summarize             │
│     State what was built + tested   │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│  5. MOVE to the next feature        │
└─────────────────────────────────────┘
```

## Feature Implementation Order (This Project)

Work through features in this exact sequence. Do not reorder.

### Phase 1 — Foundation
1. Project scaffolding (folder structure, Docker Compose, `.env.example`)
2. Database setup (SQLAlchemy engine, Base model, Alembic init)
3. All DB models + initial migration (`users`, `documents`, `processing_jobs`, `chat_sessions`, `chat_messages`)
4. Config (`pydantic_settings`, all env vars)
5. Global exception handlers + logging setup

### Phase 2 — Auth
6. `POST /auth/register`
7. `POST /auth/login` + JWT issue
8. `POST /auth/refresh`
9. `GET /auth/me` + `get_current_user` dependency

### Phase 3 — Documents
10. File upload endpoint (`POST /documents`) — save file + DB record + queue Celery task
11. Document parser (PDF, DOCX, TXT)
12. Text chunker
13. Embedding service (singleton model load + encode)
14. ChromaDB client + upsert operations
15. Celery `process_document` task (wires parser → chunker → embedder → ChromaDB → DB update)
16. `GET /documents` — list user's documents
17. `GET /documents/{id}` — single document detail
18. `GET /documents/{id}/status` — polling endpoint
19. `DELETE /documents/{id}` — delete file + ChromaDB chunks + DB record

### Phase 4 — Chat / RAG
20. `POST /chat/sessions` — create session
21. `GET /chat/sessions` — list sessions
22. RAG pipeline (embed query → ChromaDB search → prompt build)
23. LLM provider abstraction + Groq implementation
24. HuggingFace fallback provider
25. `POST /chat/sessions/{id}/messages` — SSE streaming endpoint
26. `GET /chat/sessions/{id}/messages` — fetch history
27. `DELETE /chat/sessions/{id}`

### Phase 5 — Frontend
28. React project setup (Vite, Tailwind, Router, Zustand, Axios)
29. Auth pages (Login, Register) + auth store + protected routes
30. API client with JWT interceptors + auto-refresh
31. Dashboard page
32. Document upload page (upload wizard + progress polling)
33. Chat page (session list + chat window + SSE streaming)

### Phase 6 — Polish
34. Health check endpoints (`/health`, `/health/detailed`)
35. Rate limiting (slowapi)
36. Full Docker Compose wiring + production Dockerfiles
37. README + `.env.example` finalization

## What Counts as "Tests Passing"

### Backend feature
```bash
# Run only tests related to the feature just built
pytest tests/ -k "test_register or test_login" -v

# All output must show:
# PASSED ✓
# No FAILED, no ERROR

# Zero warnings treated as errors:
pytest tests/ -k "..." -v -W error
```

### Frontend feature
```bash
npm test -- --run    # Vitest, no watch mode
# All: PASS
```

### Minimum test coverage per feature before moving on
| Feature | Required Tests |
|---|---|
| Any auth endpoint | happy path + wrong password + duplicate email + missing fields |
| Any document endpoint | success + auth required + wrong user (404) + validation failure |
| Celery task | success + file not found + DB update verification |
| RAG pipeline | with context + without context (empty results) + history included |
| Any SSE endpoint | stream starts + token events received + done event fires |
| Any frontend form | submit success + validation errors shown + loading state |

## Hard Stops — Never Proceed If:

- Any test is `FAILED` or `ERROR`
- A test was skipped with `@pytest.mark.skip` without a comment explaining why
- The feature being tested calls code that isn't implemented yet (no placeholder returns)
- Coverage for the new module is below 70%
- The Celery task hasn't been tested with `.apply()` (sync test mode)

## After Every Feature: The Checklist

Before marking a feature done and starting the next:

- [ ] Implementation complete (no `TODO`, no `pass`, no `raise NotImplementedError`)
- [ ] Tests written and cover happy path + at least 2 failure cases
- [ ] `pytest` (or `npm test`) exits with code 0
- [ ] No new Ruff/mypy warnings introduced
- [ ] Relevant steering rules were followed (check 02–13)
- [ ] If a new DB model was added: migration exists and applies cleanly

## What to Do When a Test Fails

1. Read the full error message — do not guess
2. Fix the **implementation** first (tests are the source of truth for expected behavior)
3. Only fix the **test** if the test itself has a bug (wrong assertion, wrong mock)
4. Re-run immediately after each fix — do not batch fixes
5. Do not move on with a `# type: ignore` or a silenced assertion

## Communicating Progress

After each feature is complete and green, output this summary before starting the next:

```
✅ Feature complete: <feature name>
   Built: <what was implemented in 1-2 lines>
   Tests: <N> passed, 0 failed
   Coverage: <module>: <X>%
   Next: <next feature name from the list above>
```