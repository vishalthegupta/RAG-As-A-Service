# Git Workflow & Code Quality Standards

## Commit Message Convention (Conventional Commits)
Format: `<type>(<scope>): <description>`

Types:
- `feat` — new feature
- `fix` — bug fix
- `refactor` — code change that neither fixes a bug nor adds a feature
- `test` — adding or updating tests
- `docs` — documentation only
- `chore` — build process, dependency updates
- `perf` — performance improvement

Scopes (this project): `auth`, `documents`, `chat`, `processing`, `vector-store`, `llm`, `frontend`, `docker`, `db`

Examples:
```
feat(documents): add document delete endpoint
fix(processing): handle empty pages in PDF parser
refactor(llm): extract base provider interface
test(auth): add JWT expiry edge case tests
chore(docker): upgrade postgres to 15.4
feat(chat): add SSE streaming for chat responses
```

## Branch Naming
- Feature: `feat/document-upload`
- Bug fix: `fix/jwt-refresh-loop`
- Chore: `chore/upgrade-deps`

## What Goes in .gitignore
```
# Always ignore:
.env
*.pyc
__pycache__/
.pytest_cache/
model_cache/          # downloaded ML model — large, reproducible
chroma_data/          # vector DB data — environment-specific
uploads/              # user files — never commit user data
node_modules/
dist/
.vite/
coverage/
*.egg-info/
```

## Pre-commit Hooks
Set up with `pre-commit` library:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: check-added-large-files   # catches model files
      - id: check-merge-conflict
      - id: detect-private-key        # catches accidental secret commits
```

## Required Files at Project Root
```
.env.example          ← every variable documented with a comment
.gitignore
README.md             ← how to run the project locally (5 commands max)
docker-compose.yml
docker-compose.override.yml   ← dev overrides
CHANGELOG.md          ← updated with each meaningful change
```

## README Must Include
1. One-paragraph description
2. Architecture diagram (link to HLD.md)
3. Prerequisites (Docker, Docker Compose version)
4. Quickstart: `cp .env.example .env` → fill values → `docker compose up`
5. API docs URL: `http://localhost:8000/docs`
6. How to run tests
