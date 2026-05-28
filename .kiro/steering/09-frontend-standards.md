# Frontend (React) Standards

## Project Setup
- **Vite** as build tool — never CRA
- **React 18** with functional components and hooks only — no class components
- **Tailwind CSS** for styling — no CSS modules, no styled-components
- **React Router v6** for routing
- **Zustand** for global state — no Redux, no Context for global state
- **Axios** for HTTP — interceptors handle JWT refresh automatically
- **React Query (TanStack Query)** for server state (document list, chat history)

## File Naming & Structure
```
src/
├── api/           ← API call functions (not hooks — just async functions)
├── store/         ← Zustand stores
├── pages/         ← Route-level components (one per route)
├── components/    ← Reusable components, organized by domain
├── hooks/         ← Custom hooks (useSSE, useDocumentPolling, etc.)
└── lib/           ← Utilities, constants, helpers
```
- Component files: `PascalCase.jsx`
- Hook files: `useCamelCase.js`
- Utility files: `camelCase.js`
- One component per file — no barrel re-exports for components

## Component Rules
```jsx
// Always use named exports for components (easier refactoring)
export function DocumentCard({ document, onDelete }) {
    ...
}

// Props: destructure immediately, never use props.x inside component body
// Always define PropTypes or use TypeScript

// Default values via destructuring
export function ChatWindow({ sessionId, maxHeight = "600px" }) {
    ...
}
```
- No inline styles — use Tailwind classes only
- No magic number `px` values — use Tailwind scale
- All user-facing strings: use constants from `lib/strings.js` (i18n-ready)

## State Management
```javascript
// store/documentStore.js — Zustand
import { create } from "zustand"

export const useDocumentStore = create((set, get) => ({
    documents: [],
    isLoading: false,
    error: null,
    
    fetchDocuments: async () => {
        set({ isLoading: true, error: null })
        try {
            const docs = await documentApi.list()
            set({ documents: docs, isLoading: false })
        } catch (err) {
            set({ error: err.message, isLoading: false })
        }
    },
    
    // Optimistic update pattern for deletes
    deleteDocument: async (docId) => {
        const prev = get().documents
        set({ documents: prev.filter(d => d.id !== docId) })  // optimistic
        try {
            await documentApi.delete(docId)
        } catch (err) {
            set({ documents: prev, error: err.message })       // rollback
        }
    }
}))
```
- Global state (auth, documents): Zustand
- Server cache (lists, details): React Query
- Local UI state (modal open, form values): `useState`
- Never put server data in Zustand — that's React Query's job

## API Client
```javascript
// api/client.js
import axios from "axios"
import { useAuthStore } from "../store/authStore"

export const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL + "/api/v1",
    timeout: 30000,
})

// Attach JWT to every request
apiClient.interceptors.request.use((config) => {
    const token = useAuthStore.getState().accessToken
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// Auto-refresh on 401
apiClient.interceptors.response.use(null, async (error) => {
    if (error.response?.status === 401) {
        const refreshed = await useAuthStore.getState().refreshToken()
        if (refreshed) return apiClient(error.config)
        useAuthStore.getState().logout()
    }
    return Promise.reject(error)
})
```

## SSE Streaming (Chat)
```javascript
// hooks/useSSE.js — for streaming chat responses
export function useSSE(sessionId) {
    const [streamingText, setStreamingText] = useState("")
    const [sources, setSources] = useState([])
    const [isStreaming, setIsStreaming] = useState(false)
    
    const sendMessage = async (message) => {
        setIsStreaming(true)
        setStreamingText("")
        
        const token = useAuthStore.getState().accessToken
        const response = await fetch(`${API_URL}/api/v1/chat/sessions/${sessionId}/messages`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
            body: JSON.stringify({ message })
        })
        
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        
        while (true) {
            const { done, value } = await reader.read()
            if (done) break
            
            const lines = decoder.decode(value).split("\n")
            for (const line of lines) {
                if (line.startsWith("data: ")) {
                    const data = JSON.parse(line.slice(6))
                    if (data.token) setStreamingText(prev => prev + data.token)
                    if (data.sources) setSources(data.sources)
                }
            }
        }
        setIsStreaming(false)
    }
    
    return { streamingText, sources, isStreaming, sendMessage }
}
```

## Protected Routes
```jsx
// components/layout/ProtectedRoute.jsx
export function ProtectedRoute({ children }) {
    const { user, isLoading } = useAuthStore()
    
    if (isLoading) return <LoadingSpinner />
    if (!user) return <Navigate to="/login" replace />
    return children
}
```

## Document Status Polling
```javascript
// hooks/useDocumentPolling.js
export function useDocumentPolling(docId, enabled) {
    return useQuery({
        queryKey: ["document-status", docId],
        queryFn: () => documentApi.getStatus(docId),
        enabled: enabled,
        refetchInterval: (data) => {
            // Stop polling when terminal state reached
            if (data?.status === "READY" || data?.status === "FAILED") return false
            return 3000   // poll every 3 seconds while PENDING/PROCESSING
        }
    })
}
```

## Error Boundaries
```jsx
// Wrap each page in an ErrorBoundary
// components/ErrorBoundary.jsx — class component (required by React for error boundaries)
// Shows friendly error UI, logs to console in dev
```
Every page must be wrapped with an error boundary — never let unhandled errors show a white screen.

## Environment Variables
- All env vars prefixed with `VITE_` (Vite requirement)
- `VITE_API_URL` — backend URL
- Never hardcode URLs or API endpoints in components
- Access via `import.meta.env.VITE_API_URL`
