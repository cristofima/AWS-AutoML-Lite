# GitHub Copilot Custom Instructions - Next.js Frontend Code Generation

These instructions guide GitHub Copilot in generating clean, maintainable, scalable, and type-safe code for Next.js 16+ projects following industry best practices and SOLID principles.

---

## Version Requirements

| Dependency | Version | Notes |
|------------|---------|-------|
| Next.js | 16.0.0+ | App Router, Server Components, Server Actions |
| React | 19.0.0+ | Concurrent features, use() hook |
| TypeScript | 5.0.0+ | Strict mode required |
| Node.js | 20.0.0+ | Required for Next.js 16 |

---

## I. Core Design Principles

### 1. DRY (Don't Repeat Yourself)

- **Avoid duplicating code**: Extract repeated logic into reusable functions, components, or hooks
- **Centralize logic**: Keep business logic in dedicated service files or custom hooks
- **Reusable components**: Create generic UI components that accept props for customization
- **Shared utilities**: Store common functions in `lib/` or `utils/` directory

**Examples:**

```typescript
// ❌ BAD - Repeated logic
function DatasetList() {
  const [datasets, setDatasets] = useState([]);

  useEffect(() => {
    fetch("/api/datasets")
      .then((r) => r.json())
      .then(setDatasets);
  }, []); // Duplicated fetch logic
  // ... render datasets
}

function DatasetSummary() {
  const [datasets, setDatasets] = useState([]);

  useEffect(() => {
    fetch("/api/datasets")
      .then((r) => r.json())
      .then(setDatasets);
  }, []); // Same duplicated fetch logic
  // ... render summary
}

// ✅ GOOD - Centralized logic in custom hook
// hooks/useDatasets.ts
export function useDatasets() {
  return useSWR("/api/datasets", fetcher);
}

// components/DatasetList.tsx
function DatasetList() {
  const { data: datasets } = useDatasets(); // Reusing hook
  // ... render datasets
}

// components/DatasetSummary.tsx  
function DatasetSummary() {
  const { data: datasets } = useDatasets(); // Reusing same hook
  // ... render summary
}
```

### 2. KISS (Keep It Simple, Stupid)

- **Aim for simplicity**: Write straightforward solutions that are easy to understand
- **Avoid over-engineering**: Don't add unnecessary abstractions or layers
- **Question complexity**: If code requires extensive comments to explain, simplify it
- **Prefer clarity over cleverness**: Readable code is better than "clever" code

**Examples:**

```typescript
// ❌ BAD - Over-engineered
class JobStatusStrategyFactory {
  createStrategy(status: string): IStatusStrategy {
    switch (status) {
      case "SUBMITTED":
        return new SubmittedStatusStrategy();
      case "RUNNING":
        return new RunningStatusStrategy();
      case "SUCCEEDED":
        return new SucceededStatusStrategy();
      default:
        throw new Error("Unknown strategy");
    }
  }
}

// ✅ GOOD - Simple and direct
function getJobStatusIcon(status: string) {
  const icons: Record<string, string> = {
    SUBMITTED: "📋",
    RUNNING: "🔄",
    SUCCEEDED: "✅",
    FAILED: "❌",
  };
  return icons[status] ?? "❓";
}
```

### 3. YAGNI (You Aren't Gonna Need It)

- **Build only what you need today**: Don't implement features for hypothetical future use
- **Avoid premature optimization**: Don't optimize for performance problems you don't have yet
  - Exception: Use Next.js built-in optimizations by default (Image component, code splitting)
- **No speculative abstractions**: Don't create frameworks for "future flexibility"
- **Iterative development**: Add complexity only when requirements demand it

**What to optimize from the start:**

- ✅ Use Next.js `<Image>` component (built-in optimization, no extra work)
- ✅ Use Server Components by default (framework default, better performance)
- ✅ Dynamic imports for heavy admin components (simple `dynamic()` call)

**What NOT to optimize prematurely:**

- ❌ Complex caching strategies before measuring slow queries
- ❌ Micro-optimizations (e.g., for-loop vs forEach) without benchmarks
- ❌ Over-engineering state management before knowing requirements

**Examples:**

```typescript
// ❌ BAD - Hypothetical features
interface TrainingJob {
  jobId: string;
  status: string;
  // Future features that may never be used:
  distributedTraining?: boolean;
  gpuClusterConfig?: object;
  autoScalingPolicy?: object;
  costOptimization?: object;
}

// ✅ GOOD - Current requirements only
interface TrainingJob {
  jobId: string;
  datasetId: string;
  targetColumn: string;
  status: "SUBMITTED" | "RUNNING" | "SUCCEEDED" | "FAILED";
  metrics?: {
    accuracy: number;
    f1Score: number;
    trainingTime: number;
  };
  createdAt: string;
  updatedAt: string;
}
```

### 4. LOD (Law of Demeter / Principle of Least Knowledge)

- **Talk only to immediate neighbors**: Avoid chaining multiple method calls
- **Reduce coupling**: Components shouldn't know internal structure of objects they use
- **Use dependency injection**: Pass dependencies explicitly rather than reaching through objects
- **Limit method chaining**: Maximum 2 levels (e.g., `user.profile.name` is OK, `user.profile.settings.theme.color` is not)

**Examples:**

```typescript
// ❌ BAD - Violates Law of Demeter
function TaskCard({ conversation }) {
  const agentName = conversation.thread.agent.config.name; // Too deep
  const lastMessage = conversation.thread.messages.last.content; // Too deep
}

// ✅ GOOD - Respects Law of Demeter
function TaskCard({ agentName, lastMessage }) {
  // Props are direct dependencies
  return (
    <Card>
      {agentName}: {lastMessage}
    </Card>
  );
}
```

### 5. SRP (Single Responsibility Principle)

- **One responsibility per class/function**: Each module should have only one reason to change
- **Focused components**: Components should do one thing well
- **Separate concerns**: Keep data fetching, business logic, and presentation separate
- **Small, cohesive modules**: Functions/components should be under 100 lines when possible

**Examples:**

```typescript
// ❌ BAD - Multiple responsibilities
function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [threadId, setThreadId] = useState<string>();

  // Data fetching
  useEffect(() => {
    if (threadId) {
      fetch(`/api/chat/${threadId}`)
        .then((r) => r.json())
        .then(setMessages);
    }
  }, [threadId]);

  // Message sending logic
  const sendMessage = async (message: string) => {
    /* complex logic */
  };

  // Rendering + styling + event handling
  return <div>{/* 200 lines of JSX */}</div>;
}

// ✅ GOOD - Single responsibilities
// hooks/useChat.ts
export function useChat(threadId?: string) {
  return useSWR(threadId ? `/api/chat/${threadId}` : null, fetcher);
}

// lib/chat-service.ts
export async function sendChatMessage(message: string, threadId?: string) {
  // Sending logic only
}

// components/ChatPage.tsx
export function ChatPage({ initialThreadId }: ChatPageProps) {
  const { data: messages } = useChat(initialThreadId);
  const { sendMessage } = useChatActions();
  return <ChatView messages={messages} onSend={sendMessage} />;
}
```

### 6. OCP (Open/Closed Principle)

- **Open for extension, closed for modification**: Use composition and interfaces
- **Extend via props**: Allow behavior customization through component props
- **Plugin architecture**: Design for extensibility without modifying core code
- **Use TypeScript generics**: Make components work with multiple types

**Examples:**

```typescript
// ❌ BAD - Must modify for new button types
function Button({ variant }) {
  if (variant === "primary")
    return <button className="bg-blue-500">...</button>;
  if (variant === "secondary")
    return <button className="bg-gray-500">...</button>;
  if (variant === "danger") return <button className="bg-red-500">...</button>;
  // Must edit this file for every new variant
}

// ✅ GOOD - Open for extension via className prop
function Button({ className, ...props }: ButtonProps) {
  return <button className={cn("base-styles", className)} {...props} />;
}

// Extend without modifying Button component
<Button className="bg-purple-500">Custom</Button>;
```

### 7. LSP (Liskov Substitution Principle)

- **Subtypes must be substitutable**: Child components should work wherever parent works
- **Consistent interfaces**: Don't break expected behavior in derived components
- **Honor contracts**: Subclasses shouldn't weaken preconditions or strengthen postconditions
- **Polymorphic components**: Use composition over inheritance in React

**Examples:**

```typescript
// ❌ BAD - Violates LSP
interface BaseButton {
  onClick: () => void;
  label: string;
}

// SubmitButton requires additional data that BaseButton doesn't have
function SubmitButton({
  onClick,
  label,
  formData,
}: BaseButton & { formData: any }) {
  if (!formData) throw new Error("formData required"); // Breaks substitution
}

// ✅ GOOD - Respects LSP through composition
interface ButtonProps {
  onClick: () => void;
  children: React.ReactNode;
}

function Button({ onClick, children }: ButtonProps) {
  return <button onClick={onClick}>{children}</button>;
}

// SubmitButton can wrap Button without breaking its contract
function SubmitButton({
  onSubmit,
  children,
}: {
  onSubmit: (data: FormData) => void;
}) {
  const handleClick = () => {
    const data = collectFormData();
    onSubmit(data);
  };
  return <Button onClick={handleClick}>{children}</Button>;
}
```

### 8. ISP (Interface Segregation Principle)

- **Many small interfaces over one large interface**: Don't force clients to depend on unused methods
- **Focused prop types**: Components should only receive props they actually use
- **Split large interfaces**: Break down complex types into smaller, composable ones
- **Optional props carefully**: Prefer multiple specific interfaces over optional props

**Examples:**

```typescript
// ❌ BAD - Fat interface with unused props
interface ChatMessageProps {
  message: ChatMessage;
  showTimestamp: boolean;
  onEdit: () => void; // Only used in admin
  onDelete: () => void; // Only used in admin
  onCopy: () => void; // Only used by users
  onShare: () => void; // Only used by users
  isAdminMode: boolean;
}

// ✅ GOOD - Segregated interfaces
interface MessageDisplayProps {
  message: ChatMessage;
  showTimestamp: boolean;
}

interface AdminActionsProps {
  onEdit: () => void;
  onDelete: () => void;
}

interface UserActionsProps {
  onCopy: () => void;
  onShare: () => void;
}

// Compose as needed
function AdminChatMessage(props: MessageDisplayProps & AdminActionsProps) {}
function UserChatMessage(props: MessageDisplayProps & UserActionsProps) {}
```

### 9. DIP (Dependency Inversion Principle)

- **Depend on abstractions, not concretions**: High-level modules shouldn't depend on low-level details
- **Inject dependencies**: Pass services/clients as props or context rather than importing directly
- **Abstract external services**: Wrap third-party APIs behind your own interfaces
- **Use interfaces**: Define contracts, not implementations

**Examples:**

```typescript
// ❌ BAD - Direct dependency on implementation
import { AzureOpenAIClient } from "@azure/openai";

function ChatService() {
  const client = new AzureOpenAIClient(endpoint, credential); // Tightly coupled

  async function sendMessage(message: string) {
    return client.chat(message); // Implementation detail leaked
  }
}

// ✅ GOOD - Dependency on abstraction
interface ChatRepository {
  sendMessage(message: string, threadId?: string): Promise<ChatResponse>;
  getHistory(threadId: string): Promise<ChatMessage[]>;
}

// Implementation can be swapped without changing consumers
class ApiChatRepository implements ChatRepository {
  constructor(private baseUrl: string) {}

  async sendMessage(message: string, threadId?: string): Promise<ChatResponse> {
    // API implementation details hidden
  }
}

// High-level component depends on interface, not concrete class
function ChatPage({ repository }: { repository: ChatRepository }) {
  const response = await repository.sendMessage("Create a task");
}
```

---

## II. Next.js Best Practices

### 1. TypeScript: Mandatory for Type Safety

**Always use TypeScript** for all Next.js projects:

- ✅ Catches errors at compile time, not runtime
- ✅ Enables better IDE autocomplete and refactoring
- ✅ Self-documenting code through type annotations
- ✅ Safer refactoring across large codebases

**Configuration:**

```json
// tsconfig.json
{
  "compilerOptions": {
    "strict": true, // Enable all strict type checks
    "noUncheckedIndexedAccess": true, // Safer array/object access
    "noImplicitAny": true, // No implicit any types
    "strictNullChecks": true, // Explicit null handling
    "target": "ES2017"
  }
}
```

**Examples:**

```typescript
// ✅ GOOD - Explicit types
interface ChatPageProps {
  initialThreadId?: string;
  userId?: string;
  onMessageSent?: (message: ChatMessage) => void;
}

export function ChatPage({
  initialThreadId,
  userId,
  onMessageSent,
}: ChatPageProps) {
  // TypeScript prevents runtime errors
}

// ❌ BAD - Implicit any
export function ChatPage(props) {
  // No type safety
}
```

### 2. Server Components vs Client Components

**Default to Server Components** (React Server Components):

- ✅ Faster initial page loads (less JavaScript sent to client)
- ✅ Direct database/API access without exposing credentials
- ✅ Better SEO (fully rendered HTML)
- ✅ Reduced bundle size

**Only use Client Components (`"use client"`) when you need:**

- Event handlers (`onClick`, `onChange`, etc.)
- React hooks (`useState`, `useEffect`, `useContext`)
- Browser APIs (`window`, `localStorage`, `navigator`)
- Third-party libraries that depend on client-side features

**Examples:**

```typescript
// ✅ GOOD - Server Component (default)
// app/tasks/page.tsx
export default async function TasksPage() {
  const tasks = await fetchTasksFromDB(); // Direct DB access
  return <TaskList tasks={tasks} />;
}

// ✅ GOOD - Client Component (when needed)
// components/ChatInput.tsx
("use client");

export function ChatInput({ onSend }: { onSend: (msg: string) => void }) {
  const [message, setMessage] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSend(message);
    setMessage("");
  };

  return (
    <form onSubmit={handleSubmit}>
      <input value={message} onChange={(e) => setMessage(e.target.value)} />
    </form>
  );
}

// ❌ BAD - Unnecessary Client Component
("use client"); // Not needed!

export function TaskCard({ task }: { task: TaskItem }) {
  return <Card>{task.title}</Card>; // No interactivity
}
```

### 3. Data Fetching Strategies

Choose the right rendering method based on data requirements:

#### Static Site Generation (SSG) - `generateStaticParams` + async components

**Use for:** Pages with data that rarely changes

- Blog posts, documentation, marketing pages
- Questions bank (generate at build time)

```typescript
// ✅ GOOD - Pre-render at build time
export async function generateStaticParams() {
  const statuses = ["SUBMITTED", "RUNNING", "SUCCEEDED", "FAILED"];
  return statuses.map((status) => ({ status }));
}

// ⚠️ Next.js 16: params is now a Promise - must await!
export default async function JobsByStatusPage({
  params,
}: {
  params: Promise<{ status: string }>;
}) {
  const { status } = await params; // Required in Next.js 16+
  const jobs = await getJobsByStatus(status);
  return <JobsView jobs={jobs} />;
}
```

#### Server-Side Rendering (SSR) - async Server Components

**Use for:** Pages requiring fresh data on every request

- User dashboards, personalized content
- Real-time data, authenticated pages

```typescript
// ✅ GOOD - Fresh data on every request (Next.js 16 pattern)
export default async function DashboardPage({
  params,
}: {
  params: Promise<{ userId: string }>;
}) {
  const { userId } = await params;
  const [datasets, jobs] = await Promise.all([
    getDatasets(userId),
    getTrainingJobs(userId),
  ]);

  return <Dashboard datasets={datasets} jobs={jobs} />;
}
```

#### Client-Side Fetching - SWR for Polling

**Use for:** Data that changes frequently or requires user interaction

- Real-time updates, polling (e.g., job status)
- Mutations (create, update, delete)

```typescript
// ✅ GOOD - Client-side polling for job status
"use client";

import useSWR from "swr";

export function JobStatus({ jobId }: { jobId: string }) {
  const { data: job, error } = useSWR(
    `/api/jobs/${jobId}`,
    fetcher,
    {
      refreshInterval: (data) => 
        // Poll every 3s while running, stop when complete
        data?.status === "RUNNING" ? 3000 : 0,
    }
  );

  if (error) return <ErrorState />;
  if (!job) return <LoadingState />;

  return <JobStatusCard job={job} />;
}
```

#### Server Actions (Next.js 14+)

**Use for:** Form submissions and mutations from Server Components

```typescript
// ✅ GOOD - Server Action for file upload
// app/actions/upload.ts
"use server";

import { revalidatePath } from "next/cache";

export async function uploadDataset(formData: FormData) {
  const file = formData.get("file") as File;
  const filename = formData.get("filename") as string;

  // Get presigned URL from backend
  const { uploadUrl, datasetId } = await fetch(
    `${process.env.API_URL}/upload`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename }),
    }
  ).then((r) => r.json());

  // Upload to S3
  await fetch(uploadUrl, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": "text/csv" },
  });

  // Revalidate datasets page
  revalidatePath("/datasets");

  return { datasetId };
}

// Usage in component
export function UploadForm() {
  return (
    <form action={uploadDataset}>
      <input type="file" name="file" accept=".csv" />
      <input type="hidden" name="filename" value="dataset.csv" />
      <button type="submit">Upload</button>
    </form>
  );
}
```

### 4. Folder Structure and Organization

**Recommended structure for AutoML project:**

```
app/                          # App Router (Next.js 14+)
├── (main)/                   # Route group (URL not affected)
│   ├── layout.tsx            # Shared layout
│   ├── page.tsx              # Home (file upload)
│   ├── configure/
│   │   └── [datasetId]/
│   │       └── page.tsx      # Configure training params
│   ├── training/
│   │   └── [jobId]/
│   │       └── page.tsx      # Training progress
│   ├── results/
│   │   └── [jobId]/
│   │       └── page.tsx      # Model results & metrics
│   └── history/
│       └── page.tsx          # Training history
├── api/                      # API routes (backend proxy)
│   ├── health/
│   │   └── route.ts
│   ├── upload/
│   │   └── route.ts          # Presigned URL generation
│   ├── datasets/
│   │   └── route.ts
│   ├── train/
│   │   └── route.ts
│   └── jobs/
│       └── [jobId]/
│           └── route.ts
├── globals.css
└── layout.tsx                # Root layout

components/                   # Reusable components
├── ui/                       # shadcn/ui components
│   ├── button.tsx
│   ├── card.tsx
│   └── progress.tsx
├── FileUpload.tsx            # Dataset upload component
├── Header.tsx                # Navigation header
├── JobStatusCard.tsx         # Training job status
├── MetricsChart.tsx          # Model metrics visualization
└── DatasetPreview.tsx        # Dataset columns preview

lib/                          # Utilities and configurations
├── api.ts                    # API client (typed fetch)
├── utils.ts                  # Helper functions (cn, etc.)
└── constants.ts              # App constants

hooks/                        # Custom React hooks
├── useJob.ts                 # Job status polling
├── useDataset.ts             # Dataset fetching
└── useUpload.ts              # File upload with progress

types/                        # TypeScript type definitions
├── index.ts                  # Re-exports
├── api.ts                    # API response types
└── job.ts                    # Job-related types

public/                       # Static assets
└── images/
```

**Key principles:**

- **Co-locate related files**: Keep components, styles, and tests together
- **Domain-driven structure**: Group by feature (chat, tasks) not by type (components, hooks)
- **Shallow hierarchies**: Avoid deep nesting (max 3-4 levels)
- **Consistent naming**: Use PascalCase for components, camelCase for utilities

### 5. Component Design Patterns

#### A. Composition over Inheritance

React components should compose smaller components, not extend classes.

```typescript
// ❌ BAD - Inheritance (avoid in React)
class BaseCard extends React.Component {
  render() {
    return <div className="card">{this.props.children}</div>;
  }
}

class QuestionCard extends BaseCard {
  render() {
    return (
      <div className="question-card">
        {super.render()}
        {/* Additional content */}
      </div>
    );
  }
}

// ✅ GOOD - Composition
function Card({ children, className }: CardProps) {
  return <div className={cn("card", className)}>{children}</div>;
}

function TaskCard({ task }: { task: TaskItem }) {
  return (
    <Card className="task-card">
      <TaskHeader title={task.title} priority={task.priority} />
      <TaskStatus status={task.status} />
    </Card>
  );
}
```

#### B. Prop Drilling vs Context vs State Management

**Prop drilling** (passing props through multiple levels):

- ✅ Use for 1-2 levels depth
- ✅ Explicit and easy to trace
- ❌ Avoid for deep component trees

**Context API**:

- ✅ Use for global state (auth, theme)
- ✅ Low-frequency updates
- ❌ Avoid for frequently changing data (performance issues)

**State Management Libraries** (Zustand, Redux):

- ✅ Use for complex global state
- ✅ Frequent updates across many components
- ❌ Avoid for simple apps (over-engineering)

```typescript
// ✅ GOOD - Context for global auth state
const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  return (
    <AuthContext.Provider value={{ user, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

// ✅ GOOD - Zustand for complex state
import { create } from "zustand";

interface ChatStore {
  currentThreadId: string | null;
  messages: ChatMessage[];
  isStreaming: boolean;
  setThreadId: (threadId: string) => void;
  addMessage: (message: ChatMessage) => void;
  setStreaming: (isStreaming: boolean) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  currentThreadId: null,
  messages: [],
  isStreaming: false,
  setThreadId: (threadId) => set({ currentThreadId: threadId }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setStreaming: (isStreaming) => set({ isStreaming }),
}));
```

### 6. Performance Optimization

#### A. Code Splitting and Lazy Loading

```typescript
// ✅ GOOD - Dynamic imports for heavy components
import dynamic from "next/dynamic";

const AdminPanel = dynamic(() => import("@/components/admin/AdminPanel"), {
  loading: () => <LoadingSkeleton />,
  ssr: false, // Disable SSR for client-only components
});

export function AdminPage() {
  return <AdminPanel />;
}
```

#### B. Image Optimization

```typescript
// ✅ GOOD - Use Next.js Image component
import Image from "next/image";

export function QuestionImage({ src, alt }: { src: string; alt: string }) {
  return (
    <Image
      src={src}
      alt={alt}
      width={600}
      height={400}
      placeholder="blur"
      blurDataURL="/placeholder.png"
      priority={false} // Lazy load by default
    />
  );
}

// ❌ BAD - Using <img> tag directly
<img src={src} alt={alt} />; // No optimization
```

#### C. Memoization

```typescript
// ✅ GOOD - Memoize expensive calculations
"use client";

import { useMemo } from "react";

export function QuizResults({ answers, questions }: QuizResultsProps) {
  const score = useMemo(() => {
    return calculateScore(answers, questions); // Expensive calculation
  }, [answers, questions]);

  return <div>Your score: {score}%</div>;
}

// ✅ GOOD - Memoize components that render often
import { memo } from "react";

export const QuestionCard = memo(function QuestionCard({ question }: Props) {
  return <Card>{question.text}</Card>;
});
```

### 7. Error Handling and Loading States

#### A. Error Boundaries (Next.js 13+)

```typescript
// app/error.tsx - Handles errors in route segments
"use client";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div>
      <h2>Something went wrong!</h2>
      <button onClick={() => reset()}>Try again</button>
    </div>
  );
}

// app/global-error.tsx - Handles root layout errors
("use client");

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body>
        <h2>Global Error!</h2>
        <button onClick={() => reset()}>Try again</button>
      </body>
    </html>
  );
}
```

#### B. Loading States

```typescript
// app/chat/loading.tsx - Automatic loading UI
export default function Loading() {
  return <ChatSkeleton />;
}

// Or use Suspense boundaries
import { Suspense } from "react";

export default function ChatPage() {
  return (
    <Suspense fallback={<ChatSkeleton />}>
      <ChatContent />
    </Suspense>
  );
}
```

### 8. API Routes Best Practices

```typescript
// ✅ GOOD - Proper error handling and status codes
// app/api/train/route.ts
import { NextResponse } from "next/server";
import { z } from "zod";

const trainSchema = z.object({
  datasetId: z.string().min(1),
  targetColumn: z.string().min(1),
  timeBudget: z.number().min(60).max(3600).optional().default(300),
});

export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Validate input
    const validated = trainSchema.parse(body);

    // Call backend API
    const response = await fetch(`${process.env.API_URL}/train`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(validated),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const job = await response.json();
    return NextResponse.json(job, { status: 202 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "Invalid input", details: error.errors },
        { status: 400 }
      );
    }

    console.error("Training request failed:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

// ✅ GOOD - Dynamic route with async params (Next.js 16)
// app/api/jobs/[jobId]/route.ts
export async function GET(
  request: Request,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params; // Must await in Next.js 16+

  const response = await fetch(`${process.env.API_URL}/jobs/${jobId}`);
  
  if (!response.ok) {
    return NextResponse.json(
      { error: "Job not found" },
      { status: 404 }
    );
  }

  return NextResponse.json(await response.json());
}
```

### 9. Form Handling and Validation

```typescript
// ✅ GOOD - React Hook Form + Zod validation
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const taskSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title too long"),
  description: z.string().optional(),
  priority: z.enum(["Low", "Medium", "High"]),
});

type TaskFormData = z.infer<typeof taskSchema>;

export function TaskForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<TaskFormData>({
    resolver: zodResolver(taskSchema),
  });

  const onSubmit = async (data: TaskFormData) => {
    const response = await fetch("/api/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      // Handle error
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("title")} />
      {errors.title && <span>{errors.title.message}</span>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Creating..." : "Create Task"}
      </button>
    </form>
  );
}
```

### 10. SEO Optimization

```typescript
// ✅ GOOD - Metadata API (Next.js 14+)
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "AutoML Lite - Serverless Machine Learning",
  description:
    "Train machine learning models automatically with a serverless platform powered by AWS",
  openGraph: {
    title: "AutoML Lite - No-Code ML Training",
    description: "Upload your data, select a target, get a trained model",
    images: ["/og-image.png"],
  },
  twitter: {
    card: "summary_large_image",
    title: "AutoML Lite",
    description: "Serverless AutoML on AWS",
  },
};

// ✅ GOOD - Dynamic metadata with async params (Next.js 16)
export async function generateMetadata({
  params,
}: {
  params: Promise<{ jobId: string }>;
}): Promise<Metadata> {
  const { jobId } = await params;
  const job = await getJob(jobId);

  return {
    title: `Training ${job.status} - AutoML Lite`,
    description: `Model trained on ${job.targetColumn} with ${job.metrics?.accuracy?.toFixed(2) ?? "pending"}% accuracy`,
  };
}
```

---

## III. Code Quality Standards

### 1. Naming Conventions

```typescript
// ✅ GOOD Naming Patterns

// Components: PascalCase
function QuestionCard() {}
function UserProfile() {}

// Functions/Variables: camelCase
const calculateScore = () => {};
const userProgress = getUserProgress();

// Constants: SCREAMING_SNAKE_CASE
const MAX_QUESTIONS = 50;
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

// Types/Interfaces: PascalCase
interface QuizSession {}
type ExamType = "Developer-Associate" | "Solutions-Architect-Associate";

// Files:
// - Components: PascalCase.tsx (QuestionCard.tsx)
// - Utilities: kebab-case.ts (quiz-scorer.ts)
// - Hooks: camelCase.ts (useQuizSession.ts)
```

### 2. Comments and Documentation

```typescript
// ✅ GOOD - JSDoc for public APIs
/**
 * Calculates the task completion percentage for a user.
 *
 * @param tasks - User's tasks with status information
 * @returns The completion percentage (0-100)
 *
 * @example
 * const percentage = calculateCompletionPercentage([
 *   { id: 1, status: 'Completed' },
 *   { id: 2, status: 'Pending' }
 * ]);
 */
export function calculateCompletionPercentage(tasks: TaskItem[]): number {
  // Implementation
}

// ✅ GOOD - Self-documenting code (minimize comments)
const completedTasks = tasks.filter((t) => t.status === "Completed");

// ❌ BAD - Obvious comments
// Loop through tasks
for (const task of tasks) {
  // Check if completed
  if (task.status === "Completed") {
    // Increment count
    count++;
  }
}
```

### 3. Testing Strategy

```typescript
// ✅ GOOD - Unit tests for utilities
// lib/__tests__/task-helpers.test.ts
import { describe, it, expect } from "vitest";
import { calculateCompletionPercentage } from "../task-helpers";

describe("calculateCompletionPercentage", () => {
  it("returns 100 for all completed tasks", () => {
    const tasks = [
      { id: 1, status: "Completed" },
      { id: 2, status: "Completed" },
    ];

    expect(calculateCompletionPercentage(tasks)).toBe(100);
  });

  it("returns 0 for no completed tasks", () => {
    const tasks = [
      { id: 1, status: "Pending" },
      { id: 2, status: "Pending" },
    ];

    expect(calculateCompletionPercentage(tasks)).toBe(0);
  });
});

// ✅ GOOD - Component tests with React Testing Library
// components/__tests__/TaskCard.test.tsx
import { render, screen } from "@testing-library/react";
import { TaskCard } from "../TaskCard";

describe("TaskCard", () => {
  const mockTask = {
    id: 1,
    title: "Complete project documentation",
    status: "InProgress",
    priority: "High",
  };

  it("renders task title", () => {
    render(<TaskCard task={mockTask} />);
    expect(
      screen.getByText("Complete project documentation")
    ).toBeInTheDocument();
  });

  it("displays correct priority badge", () => {
    render(<TaskCard task={mockTask} />);
    expect(screen.getByText("🔴 High")).toBeInTheDocument();
  });
});
```

### 4. Linting and Formatting

```typescript
// eslint.config.mjs (ESLint 9+ flat config)
import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      "@typescript-eslint/no-unused-vars": "error",
      "@typescript-eslint/no-explicit-any": "error",
      "prefer-const": "error",
    },
  },
];

export default eslintConfig;
```

```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2
}
```

---

## IV. Security Best Practices

### 1. Input Validation and Sanitization

```typescript
// ✅ GOOD - Always validate user input
import { z } from "zod";

const userInputSchema = z.object({
  questionId: z.string().uuid(),
  answer: z.array(z.string()).max(6),
});

export async function POST(request: Request) {
  const body = await request.json();
  const validated = userInputSchema.parse(body); // Throws if invalid

  // Safe to use validated data
}

// ❌ BAD - No validation
export async function POST(request: Request) {
  const body = await request.json();
  // Directly using user input (SQL injection, XSS risk)
  await db.query(`SELECT * FROM questions WHERE id = ${body.id}`);
}
```

### 2. Authentication and Authorization

```typescript
// ✅ GOOD - Server-side auth checks
import { getServerSession } from "next-auth";

export default async function AdminPage() {
  const session = await getServerSession();

  if (!session || !session.user.isAdmin) {
    redirect("/login");
  }

  // Admin content here
}

// ❌ BAD - Client-side only auth check
("use client");

export default function AdminPage() {
  const { user } = useAuth();

  if (!user?.isAdmin) {
    return <div>Access denied</div>; // Can be bypassed!
  }

  // Admin content still sent to client
}
```

### 3. Environment Variables

```typescript
// ✅ GOOD - Type-safe environment variables
// lib/env.ts
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  NEXTAUTH_SECRET: z.string().min(32),
  NEXT_PUBLIC_API_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);

// ❌ BAD - Unvalidated env variables
const apiUrl = process.env.NEXT_PUBLIC_API_URL; // Could be undefined!
```

---

## V. Accessibility (a11y)

```typescript
// ✅ GOOD - Semantic HTML and ARIA labels
export function TaskCard({ task }: Props) {
  return (
    <article aria-labelledby="task-title">
      <h2 id="task-title">{task.title}</h2>

      <div role="group" aria-label="Task metadata">
        <span aria-label={`Priority: ${task.priority}`}>
          {getPriorityIcon(task.priority)} {task.priority}
        </span>
        <span aria-label={`Status: ${task.status}`}>
          {getStatusIcon(task.status)} {task.status}
        </span>
      </div>

      <p>{task.description}</p>
    </article>
  );
}

// ✅ GOOD - Keyboard navigation
export function ChatInput({ onSend, disabled }: Props) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <textarea
      onKeyDown={handleKeyDown}
      aria-label="Chat message input"
      placeholder="Type your message..."
      disabled={disabled}
    />
  );
}
```

---

## VI. Summary Checklist

Before committing code, verify:

- [ ] **TypeScript**: All code uses TypeScript with strict mode
- [ ] **Server Components**: Used by default unless interactivity needed
- [ ] **DRY**: No duplicated logic; extracted to functions/hooks
- [ ] **KISS**: Simple, readable solutions; no over-engineering
- [ ] **YAGNI**: Only implemented current requirements
- [ ] **SOLID**: Single responsibility, proper abstractions
- [ ] **Performance**: Images optimized, code split, memoized when needed
- [ ] **Error Handling**: Try-catch blocks, error boundaries, loading states
- [ ] **Security**: Input validation, auth checks, env variables secured
- [ ] **Accessibility**: Semantic HTML, ARIA labels, keyboard navigation
- [ ] **Testing**: Unit tests for utilities, component tests for UI
- [ ] **Linting**: No ESLint errors, Prettier formatted
- [ ] **Documentation**: JSDoc for public APIs, README updated

---

## VII. Common Anti-Patterns to Avoid

### ❌ DON'T: Use Client Components Everywhere

```typescript
// ❌ BAD
"use client"; // Unnecessary!

export function StaticContent({ text }: { text: string }) {
  return <div>{text}</div>; // No interactivity
}
```

### ❌ DON'T: Fetch Data in useEffect

```typescript
// ❌ BAD
"use client";

export function Tasks() {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    fetch("/api/tasks")
      .then((r) => r.json())
      .then(setTasks);
  }, []); // Race conditions, no error handling
}

// ✅ GOOD - Use SWR or Server Component
("use client");

export function Tasks() {
  const { data, error } = useSWR("/api/tasks", fetcher);
  // Handles caching, revalidation, errors
}
```

### ❌ DON'T: Use `any` Type

```typescript
// ❌ BAD
function processData(data: any) {
  return data.map((item: any) => item.value); // No type safety
}

// ✅ GOOD
interface DataItem {
  id: string;
  value: number;
}

function processData(data: DataItem[]) {
  return data.map((item) => item.value); // Type-safe
}
```

### ❌ DON'T: Ignore Error Handling

```typescript
// ❌ BAD
async function saveTask(task: Task) {
  await fetch("/api/tasks", {
    method: "POST",
    body: JSON.stringify(task),
  }); // What if it fails?
}

// ✅ GOOD
async function saveTask(task: Task) {
  try {
    const response = await fetch("/api/tasks", {
      method: "POST",
      body: JSON.stringify(task),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Failed to save task");
    }

    return await response.json();
  } catch (error) {
    console.error("Save failed:", error);
    throw error; // Re-throw for caller to handle
  }
}
```

### ❌ DON'T: Over-Complicate State Management

```typescript
// ❌ BAD - Redux/Zustand for simple LOCAL component state
const store = configureStore({
  reducer: {
    chat: chatReducer,
    tasks: tasksReducer,
    messages: messagesReducer,
  },
});

function ChatPage() {
  const dispatch = useDispatch();
  const currentMessage = useSelector((state) => state.chat.currentMessage);
  // Over-engineered for local state
}

// ✅ GOOD - React state for simple LOCAL state
function ChatPage() {
  const [currentMessage, setCurrentMessage] = useState("");
  const [threadId, setThreadId] = useState<string>();
  // Simple and sufficient for component-only state
}

// ✅ ALSO GOOD - Zustand for SHARED global state (as shown in section 5.B)
// When state is shared across multiple unrelated components
export const useChatStore = create<ChatStore>((set) => ({
  currentThreadId: null,
  messages: [],
  isStreaming: false,
  setThreadId: (threadId) => set({ currentThreadId: threadId }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setStreaming: (isStreaming) => set({ isStreaming }),
}));

// Rule of thumb:
// - Local state (one component) → useState
// - Shared state (multiple components) → Context API or Zustand
// - Complex global state (many features) → Redux or Zustand
```

---

## VIII. Resources and Learning

- **Official Next.js Documentation**: https://nextjs.org/docs
- **TypeScript Handbook**: https://www.typescriptlang.org/docs/handbook/
- **React Server Components**: https://nextjs.org/docs/app/building-your-application/rendering/server-components
- **SOLID Principles**: https://en.wikipedia.org/wiki/SOLID
- **Clean Code by Robert C. Martin**: Book on writing maintainable code
- **Next.js Best Practices**: https://nextjs.org/docs/app/building-your-application/optimizing

---

**Remember**: Clean code is not just about making it work—it's about making it maintainable, testable, and scalable for future developers (including future you!).