---
inclusion: manual
---

# Frontend Code Generation from Wireframes

## Purpose
Generate production-ready frontend code from wireframe specifications, following consistent patterns, accessibility standards, and the project's chosen tech stack.

## Tech Stack Configuration

Adapt these defaults to your project. Specify your stack when invoking this steering:

```yaml
frontend:
  framework: React | Next.js | Vue | Angular | Svelte
  language: TypeScript | JavaScript
  styling: Tailwind CSS | CSS Modules | Styled Components | SCSS
  state_management: React Context | Redux | Zustand | Pinia
  form_handling: React Hook Form | Formik | native
  http_client: Axios | fetch | TanStack Query
  component_library: shadcn/ui | MUI | Ant Design | custom
  testing: Vitest | Jest | Playwright
```

## Code Generation Rules

### File Structure
```
src/
├── components/          # Reusable UI components
│   ├── ui/             # Base UI primitives (Button, Input, etc.)
│   └── [feature]/      # Feature-specific components
├── pages/ or app/      # Route-level components
├── hooks/              # Custom hooks
├── services/           # API service layer
├── types/              # TypeScript interfaces/types
├── utils/              # Helper functions
└── constants/          # App constants, enums
```

### Component Generation Pattern

For each wireframe screen, generate:

1. **Page Component** — The route-level container
2. **Feature Components** — Logical sections of the page
3. **Form Components** — With validation, error handling, submission
4. **Types** — Interfaces for props, form data, API responses
5. **Service Functions** — API calls used by the screen
6. **Custom Hooks** — Shared logic (useAuth, useFormSubmit, etc.)

### Component Template
```typescript
// Pattern for every component:
// 1. Imports
// 2. Types/Interfaces
// 3. Component definition with props
// 4. Hooks at top of component
// 5. Event handlers
// 6. Render with semantic HTML
// 7. Export

interface ComponentProps {
  // Props derived from wireframe spec
}

export function ComponentName({ ...props }: ComponentProps) {
  // State and hooks
  // Handlers
  // Return JSX with:
  //   - Semantic HTML elements
  //   - ARIA attributes for accessibility
  //   - Loading/error/empty states
  //   - Responsive classes
}
```

### Form Generation Rules
- Every form field from wireframe gets: label, input, error message slot
- Validation rules from wireframe spec map to schema validation (Zod/Yup)
- Submit handler calls the mapped API endpoint
- Disable submit during loading
- Show inline errors on field blur and on submit
- Focus first error field on failed submission

### Accessibility Requirements
- All inputs have associated labels (htmlFor/id pairing)
- Form errors use aria-describedby linked to error messages
- Buttons have descriptive text (not just icons)
- Focus management on route changes and modal open/close
- Color contrast meets WCAG AA (4.5:1 text, 3:1 UI)
- Keyboard navigation works for all interactive elements
- Skip links for main content

### State Management Pattern
```typescript
// For each screen, define:
// 1. What data is fetched (server state)
// 2. What data is local (UI state)
// 3. What data is shared (global state)

// Server state → TanStack Query / SWR
// Local UI state → useState / useReducer
// Global state → Context / Zustand (only when truly shared)
```

### API Integration Pattern
```typescript
// services/[feature].service.ts
export const featureService = {
  getItems: async (params: GetItemsParams): Promise<ItemsResponse> => {
    const response = await httpClient.get('/api/items', { params });
    return response.data;
  },
  createItem: async (data: CreateItemData): Promise<Item> => {
    const response = await httpClient.post('/api/items', data);
    return response.data;
  },
};
```

### Responsive Implementation
- Mobile-first approach: base styles are mobile, add breakpoint modifiers for larger
- Use CSS Grid or Flexbox for layouts (from wireframe layout spec)
- Stack navigation on mobile, show sidebar on desktop
- Touch targets minimum 44x44px on mobile

## Output Per Screen

For each wireframe, generate:
1. Page component file
2. Child component files (one per logical section)
3. Types file for the feature
4. Service file with API functions
5. Custom hook if shared logic exists
6. Basic test file structure (describe blocks, key test cases named)
