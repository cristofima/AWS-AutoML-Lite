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

### Component-Specific
- **[Backend README](../backend/README.md)** - API development guide *(pending)*
- **[Frontend README](../frontend/README.md)** - Next.js setup
- **[Terraform README](../infrastructure/terraform/README.md)** - Infrastructure basics
- **[Tools README](../tools/README.md)** - Manual operations

---

## 🗂️ Documentation Structure

```
docs/
├── README.md                    # This file - Documentation index
├── QUICKSTART.md                # Deployment guide (start here)
└── PROJECT_REFERENCE.md         # Complete technical docs

.github/
├── SETUP_CICD.md                # CI/CD setup
├── copilot-instructions.md      # AI coding guidelines
└── git-commit-messages-instructions.md

infrastructure/terraform/
├── README.md                    # Terraform basics
└── ARCHITECTURE_DECISIONS.md    # Container rationale

frontend/
└── README.md                    # Frontend setup

tools/
└── README.md                    # Manual tools
```

---

## 🚀 Quick Links

**New to the project?** Start with [QUICKSTART.md](./QUICKSTART.md)

**Need technical details?** See [PROJECT_REFERENCE.md](./PROJECT_REFERENCE.md)

**Setting up CI/CD?** Follow [SETUP_CICD.md](../.github/SETUP_CICD.md)

**Questions about architecture?** Read [ARCHITECTURE_DECISIONS.md](../infrastructure/terraform/ARCHITECTURE_DECISIONS.md)

---

**Last Updated:** 2025-11-28
