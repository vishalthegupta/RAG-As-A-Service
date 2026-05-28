---
inclusion: always
---

# Coding Principles

These rules apply to ALL code changes. Follow them without exception.

## No Hardcoding

- Never hardcode values that could change: URLs, ports, credentials, feature flags, thresholds, file paths
- Use environment variables, config files, or constants for all configurable values
- If a value appears more than once, extract it to a single source of truth

## Protect Existing Functionality

- Before modifying any function, understand all its callers and dependents
- Run existing tests after every change to confirm nothing broke
- If no tests exist for affected code, write them before modifying
- When refactoring, preserve the public API contract unless explicitly asked to change it
- Never silently remove or alter behavior that other parts of the system depend on

## Maximize Code Reuse

- Before writing new code, search the codebase for existing utilities, helpers, or patterns that solve the same problem
- Extract shared logic into reusable functions/modules rather than duplicating
- Use existing project abstractions (services, utils, shared types) — don't reinvent them
- If similar code exists in 2+ places, refactor into a shared implementation

## Follow Standard Practices

- Use established patterns already present in this codebase — match existing style, naming, and structure
- Follow language/framework idioms (e.g., React hooks patterns, Express middleware chains, Drizzle query patterns)
- Use proper error handling: try/catch, error boundaries, meaningful error messages
- Write self-documenting code with clear naming; add comments only for non-obvious "why" decisions
- Use TypeScript types/interfaces properly — avoid `any`, prefer strict typing

## Security First

- Never expose secrets, API keys, tokens, or credentials in code, logs, or error messages
- Use environment variables for all sensitive configuration
- Validate and sanitize all external input (user input, API responses, file content)
- Use parameterized queries — never concatenate user input into SQL or commands
- Follow principle of least privilege for permissions and access scopes
- Never log sensitive data (passwords, tokens, PII)

## Ask Before Big Changes

- Get explicit confirmation before:
  - Changing database schemas or migrations
  - Modifying authentication/authorization flows
  - Altering shared interfaces or types used across multiple modules
  - Restructuring folder/file organization
  - Changing build/deploy configuration
  - Introducing new architectural patterns
- Explain the impact and tradeoffs before proceeding

## Minimal Dependencies

- Do not install new packages unless absolutely necessary
- Before adding a dependency, check if the functionality can be achieved with:
  - Built-in language/runtime features
  - Existing project dependencies
  - A small utility function
- If a dependency is truly needed, prefer well-maintained packages with minimal sub-dependencies
- Use exact versions, not ranges

## Think Big Picture

- Don't just fix the immediate symptom — understand and address the root cause
- Consider how changes affect the broader system: performance, scalability, maintainability
- Ensure changes align with the existing architecture and don't create inconsistencies
- Think about edge cases: what happens with empty data, concurrent access, network failures, large datasets?
- Consider future developers: will this change make the codebase easier or harder to work with?

## Code Quality Essentials

- Keep functions small and single-purpose
- Avoid deep nesting — use early returns and guard clauses
- Don't leave dead code, commented-out blocks, or TODO items without context
- Handle all promise rejections and async errors
- Use meaningful variable names — no single letters except in trivial loops
- Prefer immutability: use `const`, avoid mutating function arguments

## Testing Discipline

- Write tests for new functionality — not optional
- Test behavior, not implementation details
- Cover the happy path, error cases, and boundary conditions
- Don't mock what you don't own unless absolutely necessary
- Keep tests independent — no shared mutable state between tests

## Incremental & Safe Changes

- Make changes in small, verifiable steps — not one massive commit
- Ensure the app compiles and runs after each logical change
- Don't leave the codebase in a broken intermediate state
- If a change spans multiple files, complete the full chain (type → service → controller → route → frontend) before moving on

## Performance Awareness

- Don't introduce N+1 queries or unbounded loops over data
- Use pagination for list endpoints — never return unbounded results
- Avoid blocking the event loop with synchronous heavy operations
- Use lazy loading, caching, or debouncing where appropriate
- Consider database indexes for new query patterns

## Error Handling & Resilience

- Every external call (API, DB, file system) must have error handling
- Provide meaningful error messages that help debugging without leaking internals
- Use typed errors or error codes — not just string messages
- Implement graceful degradation: if a non-critical feature fails, the app should still work
- Never swallow errors silently (empty catch blocks)

## Backward Compatibility

- Don't break existing API contracts — add new fields, don't rename or remove existing ones
- If a breaking change is unavoidable, flag it explicitly and propose a migration path
- Database migrations must be additive when possible (add columns, don't drop them without confirmation)
- Preserve existing URL routes and query parameter behavior

## Documentation & Context

- Update relevant comments, JSDoc, or README sections when behavior changes
- If adding a new pattern or utility, add a brief usage example in a comment
- Name things so documentation becomes less necessary — `getUserByEmail` not `getUser2`
- Leave a comment explaining "why" for any non-obvious business logic or workaround

## Consistency Over Cleverness

- Match the existing codebase patterns even if you know a "better" way — consistency wins
- Don't mix paradigms: if the project uses callbacks, don't introduce observables in one file
- Use the same error handling pattern throughout (if the project uses Result types, use them everywhere)
- Follow existing file/folder naming conventions exactly
