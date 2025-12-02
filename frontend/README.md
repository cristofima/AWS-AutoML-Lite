# AWS AutoML Lite - Frontend

Next.js 16 frontend for AWS AutoML Lite platform.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ installed
- Backend API deployed and running

### Setup

1. Install dependencies:
```bash
pnpm install
```

2. Create environment file:
```bash
cp .env.local.example .env.local
```

3. Edit `.env.local` with your API URL (from `terraform output api_gateway_url`):
```env
# For deployed API:
NEXT_PUBLIC_API_URL=https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/dev

# For local development with docker-compose:
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Run development server:
```bash
pnpm dev
```

5. Open [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
frontend/
├── app/
│   ├── page.tsx                      # Home/Upload page
│   ├── configure/[datasetId]/        # Column selection & config
│   ├── training/[jobId]/             # Training status page
│   ├── results/[jobId]/              # Results & download page
│   └── history/                      # Training history list
├── components/
│   └── FileUpload.tsx                # Drag & drop upload component
├── lib/
│   ├── api.ts                        # API client functions
│   └── utils.ts                      # Utility functions
├── public/                           # Static assets
└── package.json
```

## 🎨 Features

### Pages

1. **Home/Upload (`/`)**
   - Drag & drop CSV file upload
   - File validation (CSV, max 100MB)
   - Feature overview

2. **Configure (`/configure/[datasetId]`)**
   - Column selection with unique value counts
   - Target column picker
   - Smart problem type detection (Classification vs Regression)
   - Optional time budget configuration (auto-calculated if empty)

3. **Training Status (`/training/[jobId]`)**
   - Real-time status updates (polling every 5s)
   - Progress visualization
   - Training details
   - Auto-redirect to results when complete

4. **Results (`/results/[jobId]`)**
   - Model metrics (accuracy, F1, R², RMSE, etc.)
   - Feature importance chart
   - Download model (.pkl)
   - Download EDA report (.html)

5. **History (`/history`)**
   - List all training jobs
   - Filter by status
   - Quick access to results

## 🔧 Tech Stack

- **Framework**: Next.js 16 with App Router
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Charts**: Recharts
- **HTTP Client**: Native Fetch API

## 🌐 API Integration

All API calls are centralized in `lib/api.ts`:

```typescript
// Upload workflow
const metadata = await uploadAndConfirm(file);

// Start training
const job = await startTraining({
  dataset_id: datasetId,
  target_column: 'price',
  config: { time_budget: 300 }
});

// Check status
const jobDetails = await getJobDetails(jobId);

// List jobs
const { jobs, next_token } = await listJobs(10);
```

## 🎯 Development

### Smart Features

#### Problem Type Detection
The UI automatically detects and displays the problem type for each column:
- **Classification** (purple badge): Categorical columns OR numeric columns with < 20 unique values or < 5% unique ratio
- **Regression** (blue badge): Numeric columns with many unique values

Each column shows the number of unique values to help users make informed decisions.

#### Time Budget
- Optional field with placeholder showing recommended value (300s)
- Validation: 60-3600 seconds
- If left empty, backend auto-calculates based on dataset size
- Real-time validation with error messages

### Run Development Server
```bash
pnpm dev
```

### Build for Production
```bash
pnpm build
```

### Start Production Server
```bash
pnpm start
```

### Lint Code
```bash
pnpm lint
```

## 📚 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [Recharts Documentation](https://recharts.org/en-US)

---

**Built with ❤️ for AWS Community Builder Year 5**

## 🚀 Deployment

### AWS Amplify (Production)

This frontend is deployed using **AWS Amplify** with automatic deployments from GitHub.

**Key Configuration:**
- `amplify.yml` in repo root (monorepo format)
- `.npmrc` with `node-linker=hoisted` for pnpm
- Platform: `WEB_COMPUTE` (required for Next.js SSR)
- Auto-deploy on push to `dev`/`main` branches

**Environment Variables (set in Amplify Console):**
- `NEXT_PUBLIC_API_URL` - API Gateway URL
- `AMPLIFY_MONOREPO_APP_ROOT` - `frontend`

See [FRONTEND_DEPLOYMENT_ANALYSIS.md](../docs/FRONTEND_DEPLOYMENT_ANALYSIS.md) for deployment decision rationale.

### Why Not Vercel?

We use AWS Amplify to keep all infrastructure within AWS ecosystem, enabling:
- Terraform management via `aws_amplify_app`
- Consistent IAM and security
- Single cloud provider billing
