---
inclusion: manual
---

# How to Create Kiro Steering Files

This is a reference guide for authoring effective steering files. Use this when you need to create a new steering file for any topic.

## What Steering Files Are

Steering files are markdown documents placed in `.kiro/steering/` that inject context, rules, and instructions into Kiro agent interactions. They are the mechanism for giving the agent project-specific knowledge, team conventions, and specialized workflows.

## File Location

All steering files go in: `.kiro/steering/*.md`

## Inclusion Modes (Frontmatter)

Every steering file can optionally have YAML frontmatter that controls when it's loaded:

### Always (default — no frontmatter needed)

```markdown
# My Rules

These instructions are included in every agent interaction...
```

Or explicitly:

```markdown
---
inclusion: always
---

# My Rules
```

Use for: coding standards, architecture constraints, team norms, build/test commands.

### Conditional (fileMatch)

```markdown
---
inclusion: fileMatch
fileMatchPattern: "**/*.tsx"
---

# React Component Guidelines

When working with React components...
```

Use for: language-specific patterns, framework conventions, file-type-specific rules.

Common patterns:
- `"**/*.tsx"` — React/TypeScript components
- `"**/*.test.*"` — test files
- `"**/routes/**"` — API route files
- `"**/*schema*"` — database schemas
- `"**/migrations/**"` — migration files
- `"**/*.py"` — Python files

### Manual (user opts in via # in chat)

```markdown
---
inclusion: manual
---

# Deployment Procedures

Heavy reference material loaded only when needed...
```

Use for: large reference docs, infrequent workflows, specialized procedures.

## Writing Effective Content

### Structure Template

```markdown
---
inclusion: <always|fileMatch|manual>
fileMatchPattern: "<glob>" # only for fileMatch
---

# Topic Name

## Rules
- Rule 1: Be specific and imperative
- Rule 2: Use concrete examples

## Patterns

### Correct
```code
// show the right way
```

### Incorrect
```code
// show what to avoid
```

## Commands
- Build: `npm run build`
- Test: `npm run test`
```

### Content Principles

1. Be imperative — write commands, not suggestions
   - Good: "Use Drizzle ORM for all database queries"
   - Bad: "You might want to consider using Drizzle ORM"

2. Be specific — include concrete examples
   - Good: "Name test files as `*.test.ts` co-located with source"
   - Bad: "Follow good testing practices"

3. Be concise — the agent needs actionable direction, not essays
   - Keep always-on files under 100 lines ideally
   - Move detailed reference to manual-inclusion files

4. Be non-redundant — don't tell the agent things it already knows
   - Skip: "Write clean, readable code"
   - Include: "All API responses must use the `ApiResponse<T>` wrapper type"

5. Reference project files when useful:
   - `#[[file:swagger.yaml]]` — links to your OpenAPI spec
   - `#[[file:drizzle.config.ts]]` — links to DB config
   - This pulls real file content into context without duplicating it

## Sizing Guidelines

| Inclusion Mode | Recommended Size | Reason |
|---|---|---|
| always | < 100 lines | Loaded every interaction, burns context |
| fileMatch | < 200 lines | Loaded conditionally, moderate budget |
| manual | < 500 lines | User-triggered, can be larger |

If a file exceeds these limits, split it into multiple focused files.

## Naming Conventions

Use descriptive kebab-case filenames:
- `coding-standards.md`
- `react-patterns.md`
- `api-design-rules.md`
- `testing-strategy.md`
- `deployment-guide.md`
- `security-requirements.md`
- `database-conventions.md`

## Common Steering File Categories

### 1. Project Conventions (always)
Team coding standards, naming rules, architecture decisions.

### 2. Technology Patterns (fileMatch)
Framework-specific patterns triggered by relevant file types.

### 3. Build & Test Commands (always)
How to build, test, lint, deploy this specific project.

### 4. Security & Compliance (always)
Mandatory security patterns, compliance requirements.

### 5. Workflow Guides (manual)
Step-by-step procedures for complex tasks (deployment, migrations, releases).

### 6. Domain Knowledge (manual)
Business logic, domain terminology, business rules.

## Anti-Patterns to Avoid

- Contradictory rules across files (agent gets confused)
- Generic advice the model already knows
- Huge always-on files that waste context
- Duplicating content that exists in project files (use `#[[file:...]]` instead)
- Frequently changing content in always-on files (use manual mode)
- Deeply nested references to other steering files

## Example: Creating a New Steering File

Task: "I want the agent to follow our API design conventions"

1. Decide inclusion mode → `fileMatch` (only relevant when editing route files)
2. Pick a filename → `api-design-rules.md`
3. Write focused, imperative content:

```markdown
---
inclusion: fileMatch
fileMatchPattern: "**/routes/**"
---

# API Design Rules

## Response Format
- All endpoints return `{ success: boolean, data?: T, error?: string }`
- Use HTTP status codes correctly: 200 success, 201 created, 400 bad input, 401 unauthorized, 404 not found, 500 server error

## Naming
- Use plural nouns for resources: `/users`, `/documents`
- Use kebab-case for multi-word paths: `/user-profiles`
- Nest sub-resources: `/users/:id/documents`

## Validation
- Validate all input using Zod schemas
- Return specific validation error messages
- Never trust client-side validation alone

## Authentication
- All routes except `/auth/*` require Bearer token
- Use the `authMiddleware` from `src/api/middleware/auth.ts`
```

4. Save to `.kiro/steering/api-design-rules.md`

## Quick Checklist Before Saving

- [ ] Correct inclusion mode chosen?
- [ ] fileMatchPattern correct (if using fileMatch)?
- [ ] Content is imperative and specific?
- [ ] No redundancy with other steering files?
- [ ] File size within recommended limits?
- [ ] Filename is descriptive kebab-case?
