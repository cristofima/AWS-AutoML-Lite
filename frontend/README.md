# AWS AutoML Lite - Frontend

Next.js 14 frontend for AWS AutoML Lite platform.

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
   - Column selection
   - Target column picker
   - Problem type detection
   - Training time budget configuration

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

- **Framework**: Next.js 14 with App Router
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


## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
