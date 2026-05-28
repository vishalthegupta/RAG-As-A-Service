---
inclusion: manual
---

# Backend Code Generation from Wireframes

## Purpose
Generate production-ready backend code from wireframe interaction specifications, ensuring every frontend action has a corresponding API endpoint with proper validation, error handling, and data persistence.

## Tech Stack Configuration

Adapt to your project:

```yaml
backend:
  runtime: Node.js | Python | Java | Go
  framework: Express | Fastify | NestJS | FastAPI | Django | Spring Boot | Gin
  language: TypeScript | Python | Java | Go
  database: PostgreSQL | MongoDB | MySQL | DynamoDB
  orm: Prisma | TypeORM | Sequelize | SQLAlchemy | Mongoose
  auth: JWT | Session | OAuth2 | Passport
  validation: Zod | Joi | class-validator | Pydantic
  testing: Vitest | Jest | Pytest | JUnit
  api_style: REST | GraphQL
```

## Code Generation Rules

### File Structure (Node.js/TypeScript example)
```
src/
├── modules/
│   └── [feature]/
│       ├── [feature].controller.ts    # Route handlers
│       ├── [feature].service.ts       # Business logic
│       ├── [feature].repository.ts    # Data access
│       ├── [feature].validator.ts     # Request validation schemas
│       ├── [feature].types.ts         # Interfaces and DTOs
│       └── [feature].test.ts          # Tests
├── middleware/
│   ├── auth.middleware.ts
│   ├── error-handler.middleware.ts
│   └── validation.middleware.ts
├── config/
│   ├── database.ts
│   └── env.ts
├── utils/
│   ├── errors.ts                      # Custom error classes
│   └── response.ts                    # Standard response helpers
└── database/
    ├── migrations/
    └── schema/ or models/
```

### Endpoint Generation from Wireframe Interactions

Map each wireframe interaction to an endpoint:

```yaml
# Wireframe says:
interaction:
  trigger: form_submit
  endpoint: POST /api/auth/register
  payload: { name, email, password }
  success: navigate_to("/verify-email")
  error: show_inline_errors

# Generate:
# 1. Route definition
# 2. Validation schema for payload
# 3. Controller handler
# 4. Service method with business logic
# 5. Repository method for data access
# 6. Error responses matching frontend expectations
```

### Controller Pattern
```typescript
// Always follow: validate → authenticate → authorize → execute → respond
export class FeatureController {
  async create(req: Request, res: Response, next: NextFunction) {
    try {
      // 1. Validation already handled by middleware
      const data = req.validatedBody as CreateFeatureDTO;

      // 2. Call service (business logic)
      const result = await this.featureService.create(data, req.user);

      // 3. Standard response
      res.status(201).json({
        success: true,
        data: result,
        message: "Feature created successfully"
      });
    } catch (error) {
      next(error); // Handled by error middleware
    }
  }
}
```

### Validation Schema Generation
```typescript
// Derive from wireframe field specifications:
// field: { label: "Email", required: true, validation: [{ rule: "email" }] }

export const createUserSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
});

export type CreateUserDTO = z.infer<typeof createUserSchema>;
```

### Database Schema Generation

From wireframe data requirements, generate:
```typescript
// Identify entities from:
// - Form fields (what's being stored)
// - Table displays (what's being queried)
// - Relationships (navigation between screens)

model User {
  id        String   @id @default(uuid())
  name      String
  email     String   @unique
  password  String   // hashed
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  // Relations derived from screen navigation
  sessions  InterviewSession[]
  resumes   Resume[]
}
```

### Error Response Standard
```typescript
// All errors follow this shape (matches frontend error handling):
{
  success: false,
  error: {
    code: "VALIDATION_ERROR" | "NOT_FOUND" | "UNAUTHORIZED" | "FORBIDDEN" | "INTERNAL",
    message: "Human-readable message",
    details: [
      { field: "email", message: "Email already exists" }  // For validation errors
    ]
  }
}
```

### Security Rules
- Hash passwords before storage (bcrypt, argon2)
- Validate and sanitize all inputs
- Use parameterized queries (ORM handles this)
- Rate limit auth endpoints (5 attempts/minute)
- Validate file uploads: type, size, scan for malware
- Never expose internal errors to client
- Use CORS with explicit origin whitelist
- Validate JWT on every protected route
- Implement request size limits

### API Response Standard
```typescript
// Success response
{ success: true, data: T, message?: string, meta?: { page, total, limit } }

// Error response
{ success: false, error: { code: string, message: string, details?: any[] } }

// List response
{ success: true, data: T[], meta: { page: number, limit: number, total: number } }
```

## Output Per Wireframe Screen

For each screen's interactions, generate:
1. Controller with route handlers
2. Service with business logic
3. Repository with data access methods
4. Validation schemas for all inputs
5. TypeScript types/DTOs
6. Database migration if new entities needed
7. Test file with key scenarios outlined
