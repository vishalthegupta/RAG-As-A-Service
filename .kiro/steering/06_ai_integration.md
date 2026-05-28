---
inclusion: manual
---

# AI/LLM Integration

## Purpose
Guide the generation of code that integrates with LLM providers (OpenAI, Anthropic, Google, etc.) for features like question generation, answer evaluation, scoring, and conversational interactions.

## Tech Stack Configuration

```yaml
ai:
  provider: OpenAI | Anthropic | Google Gemini | Azure OpenAI | AWS Bedrock
  model: gpt-4o | claude-sonnet | gemini-pro
  sdk: openai | @anthropic-ai/sdk | @google/generative-ai | aws-sdk
  streaming: true | false
  fallback_provider: optional secondary provider
  embedding_model: text-embedding-3-small (if RAG needed)
  vector_store: Pinecone | Weaviate | pgvector | ChromaDB (if RAG needed)
```

## Architecture Pattern

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Frontend   │────▶│  Backend API     │────▶│  LLM Provider│
│  (User UI)  │◀────│  (Orchestrator)  │◀────│  (AI Model)  │
└─────────────┘     └──────────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  Database   │
                    │  (Context,  │
                    │   History)  │
                    └─────────────┘
```

**Key rule**: Never call LLM directly from frontend. Always route through backend to protect API keys, enforce rate limits, and control costs.

## File Structure

```
src/
├── modules/ai/
│   ├── ai.service.ts            # Main orchestration service
│   ├── ai.controller.ts         # API endpoints for AI features
│   ├── providers/
│   │   ├── provider.interface.ts # Common interface for all providers
│   │   ├── openai.provider.ts   # OpenAI implementation
│   │   ├── anthropic.provider.ts# Anthropic implementation
│   │   └── index.ts             # Provider factory
│   ├── prompts/
│   │   ├── prompt.builder.ts    # Prompt construction utilities
│   │   ├── templates/           # Prompt templates by feature
│   │   │   ├── question-generation.ts
│   │   │   ├── answer-evaluation.ts
│   │   │   └── scorecard-generation.ts
│   │   └── schemas/             # Structured output schemas
│   │       ├── questions.schema.ts
│   │       └── evaluation.schema.ts
│   ├── guards/
│   │   ├── rate-limiter.ts      # Per-user rate limiting
│   │   ├── token-budget.ts      # Token usage tracking
│   │   └── content-filter.ts    # Input/output safety
│   └── ai.types.ts              # All AI-related types
```

## Provider Abstraction

Always abstract the LLM provider so you can swap models without rewriting business logic:

```typescript
// providers/provider.interface.ts
export interface AIProvider {
  generateCompletion(params: CompletionParams): Promise<CompletionResult>;
  generateStructuredOutput<T>(params: StructuredParams<T>): Promise<T>;
  streamCompletion(params: CompletionParams): AsyncIterable<string>;
  countTokens(text: string): number;
}

export interface CompletionParams {
  systemPrompt: string;
  userMessage: string;
  temperature?: number;       // 0-1, lower = more deterministic
  maxTokens?: number;
  responseFormat?: 'text' | 'json';
}

export interface CompletionResult {
  content: string;
  usage: { promptTokens: number; completionTokens: number; totalTokens: number };
  model: string;
  finishReason: 'stop' | 'length' | 'content_filter';
}
```

```typescript
// providers/openai.provider.ts
export class OpenAIProvider implements AIProvider {
  private client: OpenAI;

  constructor() {
    this.client = new OpenAI({ apiKey: config.OPENAI_API_KEY });
  }

  async generateCompletion(params: CompletionParams): Promise<CompletionResult> {
    const response = await this.client.chat.completions.create({
      model: config.AI_MODEL,
      messages: [
        { role: 'system', content: params.systemPrompt },
        { role: 'user', content: params.userMessage },
      ],
      temperature: params.temperature ?? 0.7,
      max_tokens: params.maxTokens ?? 2000,
      response_format: params.responseFormat === 'json'
        ? { type: 'json_object' }
        : undefined,
    });

    return {
      content: response.choices[0].message.content ?? '',
      usage: {
        promptTokens: response.usage?.prompt_tokens ?? 0,
        completionTokens: response.usage?.completion_tokens ?? 0,
        totalTokens: response.usage?.total_tokens ?? 0,
      },
      model: response.model,
      finishReason: response.choices[0].finish_reason as any,
    };
  }
}
```

## Prompt Engineering Patterns

### Prompt Template Structure

```typescript
// prompts/templates/question-generation.ts
export function buildQuestionGenerationPrompt(context: QuestionGenContext): CompletionParams {
  return {
    systemPrompt: `You are an expert technical interviewer.
Your task is to generate interview questions based on the candidate's resume and preferences.

RULES:
- Generate exactly ${context.questionCount} questions
- Difficulty: ${context.difficulty}
- Focus areas: ${context.focusAreas.join(', ')}
- Mix question types: conceptual, practical, scenario-based
- Questions should be progressively harder
- Each question must be answerable in 2-3 minutes verbally

OUTPUT FORMAT:
Respond in JSON matching this schema:
${JSON.stringify(context.outputSchema, null, 2)}`,

    userMessage: `CANDIDATE RESUME:
${context.resumeText}

CANDIDATE PREFERENCES:
- Role: ${context.targetRole}
- Experience Level: ${context.experienceLevel}
- Topics to focus on: ${context.preferredTopics.join(', ')}
- Topics to avoid: ${context.avoidTopics.join(', ')}

Generate the interview questions now.`,

    temperature: 0.7,
    maxTokens: 3000,
    responseFormat: 'json',
  };
}
```

### Structured Output with Validation

```typescript
// schemas/questions.schema.ts
import { z } from 'zod';

export const GeneratedQuestionSchema = z.object({
  id: z.number(),
  question: z.string().min(10),
  type: z.enum(['conceptual', 'practical', 'scenario', 'behavioral']),
  difficulty: z.enum(['easy', 'medium', 'hard']),
  topic: z.string(),
  expectedKeyPoints: z.array(z.string()).min(2),
  followUpQuestions: z.array(z.string()).optional(),
  maxScorePoints: z.number(),
});

export const QuestionSetSchema = z.object({
  questions: z.array(GeneratedQuestionSchema).length(10),
  metadata: z.object({
    totalDuration: z.number(),
    difficultyDistribution: z.record(z.number()),
  }),
});

export type GeneratedQuestion = z.infer<typeof GeneratedQuestionSchema>;
export type QuestionSet = z.infer<typeof QuestionSetSchema>;
```

### Answer Evaluation Prompt

```typescript
export function buildAnswerEvaluationPrompt(context: EvaluationContext): CompletionParams {
  return {
    systemPrompt: `You are an expert interview evaluator.
Score the candidate's answer against the expected criteria.

SCORING RUBRIC:
- Accuracy (0-10): Factual correctness of the answer
- Depth (0-10): Level of detail and understanding shown
- Clarity (0-10): How well the answer is communicated
- Relevance (0-10): How directly the answer addresses the question

RULES:
- Be fair but rigorous
- Provide specific feedback, not generic praise
- Note both strengths and areas for improvement
- If the answer is completely off-topic, score 0 for relevance

OUTPUT: JSON matching the provided schema.`,

    userMessage: `QUESTION:
${context.question.question}

EXPECTED KEY POINTS:
${context.question.expectedKeyPoints.map((p, i) => `${i + 1}. ${p}`).join('\n')}

CANDIDATE'S ANSWER:
${context.answer}

Evaluate this answer.`,

    temperature: 0.3,  // Lower temperature for consistent scoring
    maxTokens: 1500,
    responseFormat: 'json',
  };
}
```

## Error Handling & Resilience

```typescript
// ai.service.ts
export class AIService {
  private provider: AIProvider;
  private fallbackProvider?: AIProvider;

  async generateWithRetry<T>(
    buildPrompt: () => CompletionParams,
    schema: z.ZodSchema<T>,
    options: { maxRetries?: number; timeoutMs?: number } = {}
  ): Promise<T> {
    const { maxRetries = 3, timeoutMs = 30000 } = options;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const params = buildPrompt();
        const result = await this.withTimeout(
          this.provider.generateCompletion(params),
          timeoutMs
        );

        // Parse and validate structured output
        const parsed = JSON.parse(result.content);
        const validated = schema.parse(parsed);

        // Log token usage for cost tracking
        await this.logUsage(result.usage);

        return validated;
      } catch (error) {
        if (attempt === maxRetries) {
          // Try fallback provider on final attempt
          if (this.fallbackProvider) {
            return this.tryFallback(buildPrompt, schema, timeoutMs);
          }
          throw new AIServiceError(
            'AI generation failed after all retries',
            { cause: error, attempts: maxRetries }
          );
        }

        // Retry on transient errors
        if (this.isRetryable(error)) {
          await this.delay(Math.pow(2, attempt) * 1000); // Exponential backoff
          continue;
        }

        throw error; // Non-retryable error, fail immediately
      }
    }
  }

  private isRetryable(error: unknown): boolean {
    if (error instanceof Error) {
      // Rate limit, timeout, or server errors are retryable
      return /rate.limit|timeout|5\d{2}/i.test(error.message);
    }
    return false;
  }

  private withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
    return Promise.race([
      promise,
      new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error(`AI request timed out after ${ms}ms`)), ms)
      ),
    ]);
  }
}
```

## Token & Cost Management

```typescript
// guards/token-budget.ts
export class TokenBudgetGuard {
  // Estimate tokens before sending (avoid surprise costs)
  estimateTokens(text: string): number {
    return Math.ceil(text.length / 4); // Rough estimate: 1 token ≈ 4 chars
  }

  // Check if request is within budget
  async checkBudget(userId: string, estimatedTokens: number): Promise<boolean> {
    const usage = await this.getUserUsage(userId);
    const limit = await this.getUserLimit(userId);
    return (usage.totalTokens + estimatedTokens) <= limit.maxTokensPerDay;
  }

  // Track usage after completion
  async recordUsage(userId: string, usage: TokenUsage): Promise<void> {
    await this.usageRepository.increment(userId, {
      promptTokens: usage.promptTokens,
      completionTokens: usage.completionTokens,
      totalTokens: usage.totalTokens,
      estimatedCost: this.calculateCost(usage),
      timestamp: new Date(),
    });
  }

  private calculateCost(usage: TokenUsage): number {
    // Adjust per model pricing
    const inputCostPer1K = 0.005;   // Example: GPT-4o input
    const outputCostPer1K = 0.015;  // Example: GPT-4o output
    return (
      (usage.promptTokens / 1000) * inputCostPer1K +
      (usage.completionTokens / 1000) * outputCostPer1K
    );
  }
}
```

## Content Safety

```typescript
// guards/content-filter.ts
export class ContentFilter {
  // Sanitize user input before sending to LLM
  sanitizeInput(text: string): string {
    // Remove potential prompt injection attempts
    const cleaned = text
      .replace(/ignore (previous|above|all) instructions/gi, '[filtered]')
      .replace(/you are now/gi, '[filtered]')
      .replace(/system:/gi, '[filtered]');

    // Truncate to reasonable length
    return cleaned.slice(0, 10000);
  }

  // Validate LLM output before returning to user
  validateOutput(output: string): { safe: boolean; reason?: string } {
    // Check for hallucinated harmful content
    // Check for PII leakage
    // Check for off-topic responses
    return { safe: true };
  }
}
```

## Streaming Pattern (for real-time interview feel)

```typescript
// For conversational interview experience
export class StreamingAIService {
  async *streamResponse(params: CompletionParams): AsyncGenerator<string> {
    const stream = await this.provider.streamCompletion(params);

    for await (const chunk of stream) {
      yield chunk;
    }
  }
}

// Controller endpoint for streaming
app.post('/api/interview/stream-question', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const stream = aiService.streamResponse(params);

  for await (const chunk of stream) {
    res.write(`data: ${JSON.stringify({ text: chunk })}\n\n`);
  }

  res.write('data: [DONE]\n\n');
  res.end();
});
```

## Context Window Management

When dealing with large resumes or conversation history:

```typescript
export class ContextManager {
  private maxContextTokens: number = 6000; // Reserve space for output

  // Summarize long documents to fit context window
  async fitToContext(documents: string[], maxTokens: number): Promise<string> {
    const totalTokens = documents.reduce(
      (sum, doc) => sum + this.estimateTokens(doc), 0
    );

    if (totalTokens <= maxTokens) {
      return documents.join('\n\n');
    }

    // Strategy: Summarize older/longer documents, keep recent ones full
    return this.summarizeToFit(documents, maxTokens);
  }

  // For multi-turn interviews, manage conversation history
  buildConversationContext(
    history: Message[],
    maxTokens: number
  ): Message[] {
    // Keep system prompt + last N messages that fit
    const messages: Message[] = [];
    let tokenCount = 0;

    // Always include system prompt
    // Then add messages from most recent backwards
    for (let i = history.length - 1; i >= 0; i--) {
      const msgTokens = this.estimateTokens(history[i].content);
      if (tokenCount + msgTokens > maxTokens) break;
      messages.unshift(history[i]);
      tokenCount += msgTokens;
    }

    return messages;
  }
}
```

## Environment Variables

```env
# Required
AI_PROVIDER=openai
AI_MODEL=gpt-4o
AI_API_KEY=sk-...

# Optional
AI_FALLBACK_PROVIDER=anthropic
AI_FALLBACK_API_KEY=sk-ant-...
AI_MAX_TOKENS_PER_REQUEST=4000
AI_RATE_LIMIT_PER_USER=20       # requests per minute
AI_DAILY_TOKEN_BUDGET=1000000   # per user per day
AI_REQUEST_TIMEOUT_MS=30000
AI_TEMPERATURE_DEFAULT=0.7
```

## Testing AI Features

```typescript
// Use deterministic responses in tests
export class MockAIProvider implements AIProvider {
  private responses: Map<string, string> = new Map();

  setResponse(promptContains: string, response: string) {
    this.responses.set(promptContains, response);
  }

  async generateCompletion(params: CompletionParams): Promise<CompletionResult> {
    for (const [key, response] of this.responses) {
      if (params.userMessage.includes(key)) {
        return {
          content: response,
          usage: { promptTokens: 100, completionTokens: 50, totalTokens: 150 },
          model: 'mock-model',
          finishReason: 'stop',
        };
      }
    }
    throw new Error(`No mock response configured for prompt`);
  }
}
```
