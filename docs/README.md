# AWS AutoML Lite - Documentation

Complete documentation for AWS AutoML Lite platform.

**Last Updated:** December 24, 2025 (v1.1.0)

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
  - Project structure (updated with tests/)
  - Complete workflow
  - API endpoints
  - Data flows
  - Development status

### Roadmap & Planning
- **[ROADMAP.md](./ROADMAP.md)** - Product roadmap and feature planning
  - Phase 2: Enhanced UX (v1.1.0) - Completed
  - Phase 3: Multi-user Platform (v2.0.0)
  - Future considerations

- **[TECHNICAL_ANALYSIS.md](./TECHNICAL_ANALYSIS.md)** - Breaking changes and implementation details
  - Schema and database changes
  - Infrastructure requirements
  - Migration strategies
  - Risk assessment

### Testing
- **[UNIT_TESTING_ANALYSIS.md](./UNIT_TESTING_ANALYSIS.md)** - Testing strategy & implementation ✅
  - 263 total tests (104 API + 159 Training)
  - Coverage reports (69% API, 53%+ Training)
  - CI/CD integration
  - Lessons learned

### Project Management
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and notable changes
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Contribution guidelines

### Specialized Guides
- **[SETUP_CICD.md](../.github/SETUP_CICD.md)** - CI/CD with GitHub Actions
  - OIDC setup
  - Workflows overview (includes test stages)
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
  - **Unit & Integration Testing** (new section)

- **[FRONTEND_DEPLOYMENT_ANALYSIS.md](./FRONTEND_DEPLOYMENT_ANALYSIS.md)** - Frontend deployment decision
  - Why Amplify was selected
  - App Runner, S3+CloudFront, ECS analysis
  - Cost comparison

### Component-Specific
- **[Backend README](../backend/README.md)** - API development guide
  - Project structure
  - Local development
  - API endpoints
  - **Testing section** (new)
- **[Frontend README](../frontend/README.md)** - Next.js setup
- **[Terraform README](../infrastructure/terraform/README.md)** - Infrastructure basics

---

## 🗂️ Documentation Structure

```
docs/
├── README.md                    # This file - Documentation index
├── QUICKSTART.md                # Deployment guide (start here)
├── PROJECT_REFERENCE.md         # Complete technical docs
├── ROADMAP.md                   # Product roadmap & feature planning
├── TECHNICAL_ANALYSIS.md        # Breaking changes & implementation
├── LESSONS_LEARNED.md           # Challenges & solutions (13 sections)
├── UNIT_TESTING_ANALYSIS.md     # Testing strategy & implementation ✅
└── FRONTEND_DEPLOYMENT_ANALYSIS.md  # Frontend deployment decision

.github/
├── SETUP_CICD.md                # CI/CD setup
├── copilot-instructions.md      # AI coding guidelines
└── git-commit-messages-instructions.md

infrastructure/terraform/
├── README.md                    # Terraform basics
└── ARCHITECTURE_DECISIONS.md    # Container rationale

backend/
├── README.md                    # Backend setup & testing
└── tests/                       # 263 tests (API + Training)

frontend/
└── README.md                    # Frontend setup
```

---

## 🚀 Quick Links

**New to the project?** Start with [QUICKSTART.md](./QUICKSTART.md)

**Need technical details?** See [PROJECT_REFERENCE.md](./PROJECT_REFERENCE.md)

**What's coming next?** Check [ROADMAP.md](./ROADMAP.md)

**Setting up CI/CD?** Follow [SETUP_CICD.md](../.github/SETUP_CICD.md)

**Questions about architecture?** Read [ARCHITECTURE_DECISIONS.md](../infrastructure/terraform/ARCHITECTURE_DECISIONS.md)

**Ran into issues?** Check [LESSONS_LEARNED.md](./LESSONS_LEARNED.md)

**Frontend deployment?** See [FRONTEND_DEPLOYMENT_ANALYSIS.md](./FRONTEND_DEPLOYMENT_ANALYSIS.md)

**Testing strategy?** See [UNIT_TESTING_ANALYSIS.md](./UNIT_TESTING_ANALYSIS.md)

---

**Last Updated:** December 24, 2025
