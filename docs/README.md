# AWS AutoML Lite - Documentation

Complete documentation for AWS AutoML Lite platform.

---

## 📚 Documentation Index

### Getting Started
- **[QUICKSTART.md](./QUICKSTART.md)** - Complete deployment guide
  - Prerequisites setup
  - Infrastructure deployment
  - Training container build
  - Testing & verification

### Technical Reference
- **[PROJECT_REFERENCE.md](./PROJECT_REFERENCE.md)** - Complete technical documentation
  - Architecture overview
  - Project structure
  - Complete workflow
  - API endpoints
  - Data flows
  - Development status

### Specialized Guides
- **[SETUP_CICD.md](../.github/SETUP_CICD.md)** - CI/CD with GitHub Actions
  - OIDC setup
  - Workflows overview
  - Deployment strategies
  
- **[ARCHITECTURE_DECISIONS.md](../infrastructure/terraform/ARCHITECTURE_DECISIONS.md)** - Why containers for training
  - Lambda vs Containers analysis
  - Cost comparison
  - Technical justification

- **[Architecture Diagrams](./diagrams/)** - Visual architecture documentation
  - Main architecture overview
  - Data flow diagrams
  - CI/CD pipeline
  - Cost comparison

### Lessons & Analysis
- **[LESSONS_LEARNED.md](./LESSONS_LEARNED.md)** - Challenges, solutions & best practices
  - Docker & container management
  - Environment variables cascade
  - ML & feature engineering
  - Frontend deployment evolution (App Runner → Amplify)

- **[FRONTEND_DEPLOYMENT_ANALYSIS.md](./FRONTEND_DEPLOYMENT_ANALYSIS.md)** - Frontend deployment decision
  - Why Amplify was selected
  - App Runner, S3+CloudFront, ECS analysis
  - Cost comparison

### Component-Specific
- **[Backend README](../backend/README.md)** - API development guide *(pending)*
- **[Frontend README](../frontend/README.md)** - Next.js setup
- **[Terraform README](../infrastructure/terraform/README.md)** - Infrastructure basics

---

## 🗂️ Documentation Structure

```
docs/
├── README.md                    # This file - Documentation index
├── QUICKSTART.md                # Deployment guide (start here)
├── PROJECT_REFERENCE.md         # Complete technical docs
├── LESSONS_LEARNED.md           # Challenges & solutions
└── FRONTEND_DEPLOYMENT_ANALYSIS.md  # Frontend deployment decision

.github/
├── SETUP_CICD.md                # CI/CD setup
├── copilot-instructions.md      # AI coding guidelines
└── git-commit-messages-instructions.md

infrastructure/terraform/
├── README.md                    # Terraform basics
└── ARCHITECTURE_DECISIONS.md    # Container rationale

frontend/
└── README.md                    # Frontend setup
```

---

## 🚀 Quick Links

**New to the project?** Start with [QUICKSTART.md](./QUICKSTART.md)

**Need technical details?** See [PROJECT_REFERENCE.md](./PROJECT_REFERENCE.md)

**Setting up CI/CD?** Follow [SETUP_CICD.md](../.github/SETUP_CICD.md)

**Questions about architecture?** Read [ARCHITECTURE_DECISIONS.md](../infrastructure/terraform/ARCHITECTURE_DECISIONS.md)

**Ran into issues?** Check [LESSONS_LEARNED.md](./LESSONS_LEARNED.md)

**Frontend deployment?** See [FRONTEND_DEPLOYMENT_ANALYSIS.md](./FRONTEND_DEPLOYMENT_ANALYSIS.md)

---

**Last Updated:** 2025-12-01
