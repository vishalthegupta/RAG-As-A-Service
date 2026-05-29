# Phase 5 — Frontend

## Context
Phases 1–4 complete. The entire backend API is working and tested.
Now build the React frontend that users interact with.
Read all files in .kiro/steering/ before writing any code.

## Goal
A clean, functional React SPA — auth, document upload with live status,
and a streaming chat interface. No CSS frameworks other than Tailwind.

## Rules
- Implement features in the exact order listed below
- After each feature: verify in browser, write component tests, confirm passing
- No class components — functional components and hooks only
- No inline styles — Tailwind classes only
- All API URLs from `import.meta.env.VITE_API_URL` — never hardcoded

---

## Feature 28 — React Project Setup

### What to build

**Initialize with Vite:**
```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
```

**Install dependencies:**
```bash
npm install react-router-dom@6 zustand axios @tanstack/react-query
npm install -D tailwindcss postcss autoprefixer vitest @testing-library/react @testing-library/jest-dom msw
npx tailwindcss init -p
```

**`tailwind.config.js`:**
```js
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: {} },
  plugins: [],
}
```

**`src/main.jsx`:**
```jsx
import { BrowserRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } }
})

createRoot(document.getElementById("root")).render(
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </QueryClientProvider>
)
```

**`src/App.jsx`** — route definitions:
```jsx
<Routes>
  <Route path="/login" element={<LoginPage />} />
  <Route path="/register" element={<RegisterPage />} />
  <Route path="/" element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
    <Route index element={<DashboardPage />} />
    <Route path="upload" element={<UploadPage />} />
    <Route path="chat" element={<ChatPage />} />
    <Route path="chat/:sessionId" element={<ChatPage />} />
  </Route>
</Routes>
```

**`src/lib/constants.js`:**
```js
export const API_URL = import.meta.env.VITE_API_URL + "/api/v1"
export const ALLOWED_FILE_TYPES = ["application/pdf", "text/plain",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
export const MAX_FILE_SIZE_MB = 50
```

**`.env` (frontend):**
```
VITE_API_URL=http://localhost:8000
```

### Tests to write
```jsx
// src/App.test.jsx
test("renders without crashing", () => {
  render(<App />)
})

test("redirects to login when unauthenticated", () => {
  // mock auth store with no user
  // verify /login route rendered
})
```

### Done when
- `npm run dev` starts without errors
- Routes render without crashing
- Tailwind classes apply correctly

---

## Feature 29 — Auth Pages + Store + Protected Routes

### What to build

**`src/store/authStore.js`** — Zustand
```js
export const useAuthStore = create((set, get) => ({
  user: null,
  accessToken: localStorage.getItem("access_token"),
  refreshToken: localStorage.getItem("refresh_token"),
  isLoading: true,

  login: async (email, password) => {
    const res = await authApi.login(email, password)
    localStorage.setItem("access_token", res.access_token)
    localStorage.setItem("refresh_token", res.refresh_token)
    set({ accessToken: res.access_token, refreshToken: res.refresh_token })
    await get().loadUser()
  },

  logout: () => {
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    set({ user: null, accessToken: null, refreshToken: null })
  },

  loadUser: async () => {
    try {
      const user = await authApi.getMe()
      set({ user, isLoading: false })
    } catch {
      get().logout()
      set({ isLoading: false })
    }
  },

  refreshAccessToken: async () => {
    const { refreshToken } = get()
    if (!refreshToken) return false
    try {
      const res = await authApi.refresh(refreshToken)
      localStorage.setItem("access_token", res.access_token)
      set({ accessToken: res.access_token })
      return true
    } catch {
      get().logout()
      return false
    }
  }
}))
```

**`src/api/auth.js`:**
```js
export const authApi = {
  register: (email, password, fullName) =>
    apiClient.post("/auth/register", { email, password, full_name: fullName }).then(r => r.data),
  login: (email, password) =>
    apiClient.post("/auth/login", { email, password }).then(r => r.data),
  refresh: (refreshToken) =>
    apiClient.post("/auth/refresh", { refresh_token: refreshToken }).then(r => r.data),
  getMe: () => apiClient.get("/auth/me").then(r => r.data),
}
```

**`src/pages/LoginPage.jsx`:**
- Email + password fields
- Submit calls `authStore.login()`
- Show error message on 401
- Show loading state on submit
- Link to /register
- Redirect to / on success

**`src/pages/RegisterPage.jsx`:**
- Email, password, full name (optional) fields
- Client-side validation: password ≥ 8 chars
- Show field-level error messages
- Link to /login

**`src/components/layout/ProtectedRoute.jsx`:**
```jsx
export function ProtectedRoute({ children }) {
  const { user, isLoading } = useAuthStore()
  if (isLoading) return <div className="flex h-screen items-center justify-center">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  return children
}
```

### Tests to write
```jsx
test("login form submits and stores token", async () => {
  // mock authApi.login to return tokens
  // fill form, submit
  // verify localStorage has token
})

test("register form shows validation error for short password", async () => {
  // fill form with 4-char password
  // verify error message visible
})

test("protected route redirects to login when no user", () => {
  // mock authStore with user=null, isLoading=false
  // verify Navigate to /login
})
```

---

## Feature 30 — API Client with JWT Interceptors

### What to build

**`src/api/client.js`:**
```js
import axios from "axios"
import { useAuthStore } from "../store/authStore"

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL + "/api/v1",
  timeout: 30000,
})

// Attach token to every request
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auto-refresh on 401
let isRefreshing = false
let failedQueue = []

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          original.headers.Authorization = `Bearer ${token}`
          return apiClient(original)
        })
      }
      original._retry = true
      isRefreshing = true
      const refreshed = await useAuthStore.getState().refreshAccessToken()
      isRefreshing = false
      if (refreshed) {
        const token = useAuthStore.getState().accessToken
        failedQueue.forEach(p => p.resolve(token))
        failedQueue = []
        original.headers.Authorization = `Bearer ${token}`
        return apiClient(original)
      }
      failedQueue.forEach(p => p.reject(error))
      failedQueue = []
    }
    return Promise.reject(error)
  }
)
```

### Tests to write
```js
test("attaches authorization header to requests", async () => {
  // set token in store
  // make request
  // verify Authorization header present
})

test("retries request after token refresh on 401", async () => {
  // mock first request returns 401
  // mock refresh returns new token
  // mock retry succeeds
  // verify original request completed
})

test("logs out when refresh fails", async () => {
  // mock 401, mock refresh failure
  // verify logout called
})
```

---

## Feature 31 — Dashboard Page

### What to build

**`src/store/documentStore.js`** — Zustand
```js
export const useDocumentStore = create((set, get) => ({
  documents: [],
  isLoading: false,
  error: null,

  fetchDocuments: async () => { ... },
  deleteDocument: async (docId) => {
    // Optimistic update — remove from state immediately, rollback on error
  },
}))
```

**`src/api/documents.js`:**
```js
export const documentApi = {
  list: () => apiClient.get("/documents").then(r => r.data),
  getStatus: (id) => apiClient.get(`/documents/${id}/status`).then(r => r.data),
  delete: (id) => apiClient.delete(`/documents/${id}`).then(r => r.data),
  upload: (file, name, description) => {
    const form = new FormData()
    form.append("file", file)
    form.append("name", name)
    if (description) form.append("description", description)
    return apiClient.post("/documents", form, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress: (e) => Math.round(e.loaded / e.total * 100)
    }).then(r => r.data)
  }
}
```

**`src/pages/DashboardPage.jsx`:**
- Heading: "Your Documents"
- Button: "Upload Document" → links to /upload
- If no documents: empty state with prompt to upload
- List of DocumentCard components
- Shows count of READY documents

**`src/components/documents/DocumentCard.jsx`:**
```jsx
// Props: document, onDelete
// Shows: name, status badge (color-coded), chunk_count if READY
// Status colors: PENDING=yellow, PROCESSING=blue, READY=green, FAILED=red
// Actions: delete button (confirm before deleting)
// If PROCESSING: shows progress bar from processing_job.progress_pct
```

### Tests to write
```jsx
test("dashboard shows empty state when no documents", () => {
  // mock documentStore with documents=[]
  // verify empty state message visible
})

test("document card shows correct status badge color", () => {
  // render card with status=READY
  // verify green badge
})

test("delete confirms before calling API", async () => {
  // click delete
  // verify confirmation shown before API called
})
```

---

## Feature 32 — Upload Page

### What to build

**`src/pages/UploadPage.jsx`** — 3-step wizard:

**Step 1 — Select file:**
- Drag-and-drop zone OR click to browse
- Client-side validation: file type (PDF/DOCX/TXT only), size (≤ 50MB)
- Show file name and size after selection
- Error if invalid type or too large

**Step 2 — Add details:**
- "Name" text input (required, maps to document.name)
- "Description" textarea (optional)
- Back button + "Upload" button

**Step 3 — Processing:**
- Shows upload progress bar (from axios onUploadProgress)
- After upload: shows processing status (PENDING → PROCESSING → READY)
- Polls `GET /documents/{id}/status` every 3 seconds via `useDocumentPolling` hook
- On READY: success message + "Start chatting" button → /chat
- On FAILED: error message + retry option

**`src/hooks/useDocumentPolling.js`:**
```js
export function useDocumentPolling(docId, enabled) {
  return useQuery({
    queryKey: ["doc-status", docId],
    queryFn: () => documentApi.getStatus(docId),
    enabled: !!docId && enabled,
    refetchInterval: (data) => {
      if (!data) return 3000
      if (data.status === "READY" || data.status === "FAILED") return false
      return 3000
    },
  })
}
```

### Tests to write
```jsx
test("rejects non-PDF/DOCX/TXT files", async () => {
  // simulate dropping an .exe file
  // verify error message shown
  // verify upload button disabled
})

test("rejects files over 50MB", async () => {
  // simulate large file
  // verify error shown
})

test("shows processing state after upload", async () => {
  // mock upload API success
  // verify step 3 shown with PENDING status
})

test("polling stops when status is READY", async () => {
  // mock getStatus to return READY
  // verify success message shown
  // verify no more polling calls
})
```

---

## Feature 33 — Chat Page

### What to build

**`src/store/chatStore.js`** — Zustand
```js
export const useChatStore = create((set) => ({
  sessions: [],
  activeSessionId: null,
  messages: {},   // {[sessionId]: Message[]}
  isStreaming: false,
  streamingText: "",
  sources: [],

  fetchSessions: async () => { ... },
  createSession: async () => { ... },
  setActiveSession: (id) => set({ activeSessionId: id }),
  appendStreamToken: (token) => set(s => ({ streamingText: s.streamingText + token })),
  finalizeMessage: (sessionId, fullText, sources) => { ... },
}))
```

**`src/api/chat.js`:**
```js
export const chatApi = {
  createSession: (title) => apiClient.post("/chat/sessions", { title }).then(r => r.data),
  listSessions: () => apiClient.get("/chat/sessions").then(r => r.data),
  getMessages: (id) => apiClient.get(`/chat/sessions/${id}/messages`).then(r => r.data),
  deleteSession: (id) => apiClient.delete(`/chat/sessions/${id}`).then(r => r.data),
}
```

**`src/hooks/useSSE.js`:**
```js
export function useSSE() {
  const sendMessage = async (sessionId, message, onToken, onSources, onDone, onError) => {
    const token = useAuthStore.getState().accessToken
    const res = await fetch(`${API_URL}/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ message })
    })
    const reader = res.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const lines = decoder.decode(value, { stream: true }).split("\n")
      for (const line of lines) {
        if (!line.startsWith("data: ")) continue
        const data = JSON.parse(line.slice(6))
        if (data.token) onToken(data.token)
        if (data.sources) onSources(data.sources)
        if (data.done) onDone(data)
        if (data.error) onError(data.error)
      }
    }
  }
  return { sendMessage }
}
```

**`src/pages/ChatPage.jsx`:**
- Left sidebar: list of sessions + "New chat" button
- Main area: chat window for active session
- Empty state if no session selected

**`src/components/chat/ChatWindow.jsx`:**
- Message list (scrollable, auto-scroll to bottom on new message)
- Input textarea (Enter to send, Shift+Enter for newline)
- Send button (disabled while streaming)
- Shows streaming message as it arrives token-by-token

**`src/components/chat/MessageBubble.jsx`:**
- User messages: right-aligned, gray background
- Assistant messages: left-aligned, white background
- Streaming message: shows cursor animation while streaming

**`src/components/chat/SourceAccordion.jsx`:**
- Collapsible panel below assistant message
- Shows retrieved document chunks with doc name and score
- "Sources (3)" heading that expands on click

### Tests to write
```jsx
test("new chat button creates session and sets active", async () => {
  // mock createSession API
  // click "New chat"
  // verify session list updated and active session set
})

test("send button disabled while streaming", async () => {
  // set isStreaming=true in store
  // verify button has disabled attribute
})

test("messages auto-scroll to bottom", async () => {
  // add messages to store
  // verify scroll position at bottom
})

test("source accordion expands on click", async () => {
  // render MessageBubble with sources
  // click sources heading
  // verify chunk text visible
})
```

---

## Phase 5 Complete — Checklist

Before moving to Phase 6, verify all of the following:

- [ ] All component tests pass (`npm test -- --run`)
- [ ] Full manual flow: register → login → upload PDF → wait for READY → chat → receive streamed response
- [ ] Token refresh works: expire access token manually, verify request still succeeds
- [ ] File validation blocks wrong types and oversized files before upload
- [ ] Polling stops correctly on READY and FAILED states
- [ ] Chat input disabled while streaming response
- [ ] Sources accordion shows retrieved chunks

Report this summary when done:
```
✅ Phase 5 complete
   Features: 6/6 (cumulative: 33/37)
   Tests: N passed, 0 failed
   Ready for Phase 6: Polish & Infra
```
