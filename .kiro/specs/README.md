# Specs — How to Use With Kiro

## What These Are
Each file here is a Kiro spec — a detailed feature-by-feature implementation
plan for one phase of the RAG-as-a-Service build.

## Phase Overview
| File | Phase | Features | Builds |
|---|---|---|---|
| `phase-1-foundation.md` | Foundation | 1–5 | Project scaffold, DB, config, exceptions |
| `phase-2-auth.md` | Auth | 6–9 | Register, login, JWT, get_current_user |
| `phase-3-documents.md` | Documents | 10–19 | Upload, parse, chunk, embed, ChromaDB, CRUD |
| `phase-4-chat-rag.md` | Chat / RAG | 20–27 | Sessions, RAG pipeline, LLM, SSE streaming |
| `phase-5-frontend.md` | Frontend | 28–33 | React SPA, auth, upload wizard, chat UI |
| `phase-6-polish-infra.md` | Polish | 34–37 | Health checks, rate limiting, Docker, README |

## How to Start Each Phase in Kiro

Paste this into Kiro's agent chat at the start of each phase:

```
Read all files in .kiro/steering/ first.
Then implement the spec at .kiro/specs/phase-[N]-[name].md

Rules:
- One feature at a time
- Write tests after each feature
- Run tests, confirm green, report, then proceed
- Do not start the next phase until I confirm
```

## One Golden Rule
Never give Kiro two phases at once.
Finish Phase N → verify manually → then start Phase N+1.
