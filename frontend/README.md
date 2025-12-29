# AWS AutoML Lite - Frontend

Next.js 16 frontend for AWS AutoML Lite platform.

## 🚀 Quick Start

### Prerequisites

- Node.js 20+ installed
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

> **Tip (v1.1.0):** For local development, `.env.development.local` is pre-configured with `http://localhost:8000` and only loads during `pnpm dev`. This keeps production settings safe.

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
│   ├── compare/                      # Model comparison page (v1.1.0)
│   └── history/                      # Training history list
├── components/
│   ├── FileUpload.tsx                # Drag & drop upload component
│   ├── Header.tsx                    # Navigation header with theme toggle
│   └── ThemeToggle.tsx               # Dark/light mode switcher
├── lib/
│   ├── api.ts                        # API client functions
│   ├── utils.ts                      # Utility functions
│   └── useJobPolling.ts              # Job status polling hook
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
   - Real-time status polling every 5 seconds
   - Progress visualization with stage indicators
   - Auto-redirect to results when complete

4. **Results (`/results/[jobId]`)**
   - Model metrics (accuracy, F1, R², RMSE, etc.)
   - Download model (.pkl and .onnx)
   - Download EDA report (.html)
   - Download Training report (.html) - includes feature importance charts
   - 🚀 **One-click Model Deploy** (v1.1.0) - serverless inference
   - 🎮 **Prediction Playground** (v1.1.0) - test predictions in-browser
     - Classification: shows predicted class with confidence percentage
     - Regression: shows predicted value with ± RMSE error margin and R² score

5. **Compare Models (`/compare`)** (v1.1.0)
   - Side-by-side comparison of up to 4 training runs
   - Metrics table with best values highlighted (🏆)
   - URL sharing: `/compare?jobs=id1,id2,id3`

6. **History (`/history`)**
   - Optimized 7-column table: Job ID, Target Column, Problem Type, Best Model, Metric, Tags, Completed At, Actions
   - Training time shown in tooltip on Job ID hover
   - Icon-based actions (👁️ view, 🗑️ delete) for space efficiency
   - Filter by status and tags
   - Quick access to results and compare

### UI Features (v1.1.0)

- 🌙 **Dark Mode**: System preference detection with manual toggle
- 🚀 **Model Deployment**: Deploy/undeploy models for serverless inference
- 🎮 **Prediction Playground**: Interactive UI to test predictions
- 📈 **Compare Link**: Quick access from history page

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

### State Management

#### Preserving Presigned URLs
- **Problem**: Polling for job updates could overwrite valid presigned URLs with expired ones, breaking download links.
- **Solution**: The `mergeJobPreservingUrls` utility intelligently merges new API data with existing state, preserving valid URLs while updating status and metrics.

#### Strict Cache Revalidation
- **Problem**: Browsers would serve cached "200 OK" responses for job details even after the job was deleted.
- **Solution**: `getJobDetails` uses `cache: 'no-cache'` to force ETag validation on every request. If the job is deleted, the server returns 404, and the browser correctly shows the "Not Found" page.

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
