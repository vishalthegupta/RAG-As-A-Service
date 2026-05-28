---
inclusion: manual
---

# Debugging Support

## Purpose
Provide systematic debugging assistance for code generated through the wireframe-to-code pipeline. This steering helps identify, diagnose, and resolve errors efficiently across frontend, backend, and integration layers.

## Debugging Workflow

### Step 1: Error Classification

Classify the error into one of these categories:

| Category | Symptoms | First Actions |
|---|---|---|
| **Build/Compile** | Red squiggles, TypeScript errors, import failures | Check types, imports, missing dependencies |
| **Runtime** | Console errors, crashes, unhandled exceptions | Check stack trace, reproduce minimally |
| **Logic** | Wrong behavior, incorrect data, bad state | Add logging, trace data flow, check conditions |
| **Integration** | API failures, CORS, auth issues, timeout | Check network tab, verify endpoint, check payload |
| **Styling/Layout** | Visual bugs, responsive issues, overflow | Inspect element, check breakpoints, verify classes |
| **Performance** | Slow renders, memory leaks, large bundles | Profile, check re-renders, analyze bundle |

### Step 2: Information Gathering

When a user reports an error, collect:

```yaml
debugging_context:
  error_message: "exact error text"
  error_location: "file:line or component name"
  reproduction_steps: "what triggers it"
  expected_behavior: "what should happen"
  actual_behavior: "what actually happens"
  environment: "browser/node version, OS"
  recent_changes: "what was modified before error appeared"
```

### Step 3: Systematic Diagnosis

#### Frontend Errors

```
1. Check browser console for errors
2. Verify component props match expected types
3. Check if state is initialized correctly
4. Verify API responses match expected shape
5. Check for null/undefined access on async data
6. Verify event handlers are bound correctly
7. Check conditional rendering logic
8. Verify imports and exports match
```

**Common Frontend Issues from Generated Code:**
- Missing null checks on API response data before render
- Form state not resetting after submission
- useEffect dependency array missing values (stale closures)
- Event handler not preventing default on form submit
- Async state not handled (loading/error states missing)
- Route params not parsed correctly
- Environment variables not prefixed correctly (NEXT_PUBLIC_, VITE_)

#### Backend Errors

```
1. Check server logs for stack trace
2. Verify request payload matches validation schema
3. Check database connection and query
4. Verify environment variables are set
5. Check middleware order (auth before route handler)
6. Verify error handling catches the case
7. Check for async/await missing (unhandled promise)
8. Verify response shape matches frontend expectation
```

**Common Backend Issues from Generated Code:**
- Missing await on async operations
- Validation schema mismatch with frontend form
- Database migration not run after schema change
- Environment variable undefined (not in .env)
- CORS not configured for frontend origin
- Auth middleware not applied to protected routes
- File upload middleware not configured (multer/formidable)
- Response status code wrong (200 instead of 201, etc.)

#### Integration Errors

```
1. Verify frontend API URL matches backend route
2. Check request method (GET vs POST)
3. Verify Content-Type header matches body format
4. Check auth token is being sent
5. Verify CORS allows the request origin
6. Check request/response payload shape alignment
7. Verify error response handling on frontend
8. Check for network issues (DNS, firewall, proxy)
```

### Step 4: Fix Patterns

#### Quick Fix Templates

**TypeScript type error:**
```typescript
// Problem: Property 'x' does not exist on type 'Y'
// Fix: Check if the type definition matches the actual data
// Common cause: API response shape changed, type not updated

// Before (error)
const name = response.data.user.name;

// After (safe access with type)
interface ApiResponse {
  data: { user: { name: string } };
}
const name = (response as ApiResponse).data?.user?.name ?? '';
```

**Async state race condition:**
```typescript
// Problem: Component unmounts before async completes
// Fix: Abort controller or mounted check

useEffect(() => {
  const controller = new AbortController();
  fetchData({ signal: controller.signal })
    .then(setData)
    .catch(err => {
      if (err.name !== 'AbortError') setError(err);
    });
  return () => controller.abort();
}, []);
```

**API validation mismatch:**
```typescript
// Problem: Frontend sends data that backend rejects
// Fix: Ensure frontend form schema matches backend validation

// 1. Check backend schema
const backendSchema = z.object({ email: z.string().email() });

// 2. Ensure frontend sends matching shape
const formData = { email: formValues.email.trim().toLowerCase() };
```

### Step 5: Verification

After applying a fix:
1. **Reproduce**: Confirm the original error no longer occurs
2. **Regression**: Check that related functionality still works
3. **Edge cases**: Test boundary conditions (empty input, large data, network failure)
4. **Types**: Run type checker to ensure no new type errors
5. **Tests**: Run existing tests to catch regressions

## Debugging Commands Reference

```bash
# Frontend
npm run type-check          # TypeScript errors
npm run lint                # Linting issues
npm run build               # Build errors
npx why-is-this-here       # Unused exports

# Backend
npm run dev 2>&1 | head -50 # Startup errors
curl -X POST localhost:3000/api/endpoint -H "Content-Type: application/json" -d '{}'  # Test endpoint
npx prisma studio           # Inspect database

# General
git diff                    # What changed recently
git log --oneline -10       # Recent commits
```

## Error Message Decoder

Common cryptic errors and what they actually mean:

| Error | Likely Cause | Fix |
|---|---|---|
| `Cannot read properties of undefined` | Accessing nested property before data loads | Add optional chaining `?.` or loading state |
| `Hydration mismatch` (Next.js) | Server/client render different content | Wrap dynamic content in `useEffect` or `<ClientOnly>` |
| `ECONNREFUSED` | Backend not running or wrong port | Start server, check PORT env var |
| `413 Payload Too Large` | File upload exceeds limit | Increase body parser limit in backend config |
| `CORS policy blocked` | Backend not allowing frontend origin | Add frontend URL to CORS whitelist |
| `JWT malformed` | Token corrupted or wrong format | Check token storage, verify signing |
| `Unique constraint failed` | Duplicate entry in database | Add proper error handling, check upsert logic |
| `Module not found` | Missing dependency or wrong import path | `npm install` or fix relative import |

## When to Escalate

If after systematic debugging the issue persists:
1. Isolate the minimal reproduction case
2. Check if it's a known issue in the library/framework (search GitHub issues)
3. Consider if the generated architecture needs restructuring
4. Document the issue clearly for further investigation
