# Contributing to AWS AutoML Lite

Thanks for your interest in AWS AutoML Lite! This project is primarily educational and designed for individual use, but contributions are welcome.

## 🎯 Project Purpose

This is an **educational project** demonstrating serverless AutoML on AWS. Most users will:
- Clone and deploy to their own AWS account
- Use as a reference for their own projects
- Learn about serverless architecture patterns

## 🔧 Quick Setup for Local Development

### Prerequisites
- AWS Account with credentials configured
- Terraform >= 1.9
- Docker installed
- Node.js 20+
- Python 3.11+

### Local Development
```bash
# 1. Deploy infrastructure first
cd infrastructure/terraform
terraform init
terraform apply

# 2. Run backend locally
cd ../../backend
cp .env.example .env
# Edit .env with your AWS resource names from terraform output
docker-compose up

# 3. Run frontend locally (separate terminal)
cd frontend
cp .env.local.example .env.local
# Edit .env.local with API URL
pnpm install && pnpm dev
```

See [QUICKSTART.md](./docs/QUICKSTART.md) for full deployment instructions.

## 📝 Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/). Please read [git-commit-messages-instructions.md](.github/git-commit-messages-instructions.md) for detailed guidelines.

**Quick reference:**
```bash
feat(api): add new endpoint          # New feature
fix(training): resolve memory issue  # Bug fix
docs: update README                  # Documentation only
build(terraform): add S3 bucket      # Infrastructure changes
ci: update GitHub Actions workflow   # CI/CD changes
```

## 🧪 Testing Your Changes

### Backend API
```bash
cd backend
pytest
# Or test locally with docker-compose
docker-compose up
```

### Frontend
```bash
cd frontend
pnpm lint
pnpm build
```

### Infrastructure
```bash
cd infrastructure/terraform
terraform fmt -recursive
terraform validate
terraform plan
```

## 📋 Pull Request Process

1. **Fork the repository**
2. **Create a feature branch** from `dev`
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. **Make your changes** following commit conventions
4. **Test locally** (deploy to your AWS account)
5. **Push to your fork** and create a PR to `dev` branch
6. **Wait for review** (this is a personal project, reviews may take time)

## 🚫 What We're NOT Looking For

- Large architectural changes (this is an educational example)
- Additional ML frameworks (keep it simple with FLAML)
- Complex features that increase cost significantly
- Changes that require manual infrastructure setup

## ✅ What We ARE Looking For

- **Bug fixes** - especially in training container or data preprocessing
- **Documentation improvements** - typos, clarity, better examples
- **Cost optimizations** - ways to reduce AWS costs
- **Error handling** - better error messages and validation
- **Minor features** - small improvements that don't change architecture

## 📚 Key Documentation

Before contributing, please read:
- [copilot-instructions.md](.github/copilot-instructions.md) - Architecture patterns and guidelines
- [ARCHITECTURE_DECISIONS.md](infrastructure/terraform/ARCHITECTURE_DECISIONS.md) - Why containers only for training
- [LESSONS_LEARNED.md](docs/LESSONS_LEARNED.md) - Common pitfalls and solutions

## 🐛 Reporting Issues

If you find a bug:
1. Check [LESSONS_LEARNED.md](docs/LESSONS_LEARNED.md) first - it might be documented
2. Open an issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - CloudWatch logs if available
   - Your AWS region and Terraform version

## 💡 Suggesting Features

For feature requests:
1. Open an issue first to discuss
2. Explain the use case
3. Consider the cost impact
4. Keep it aligned with the educational purpose

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## ❓ Questions?

- Check [docs/README.md](docs/README.md) for documentation index
- Review [QUICKSTART.md](docs/QUICKSTART.md) for deployment help
- See [LESSONS_LEARNED.md](docs/LESSONS_LEARNED.md) for troubleshooting

---

**Remember:** This is an educational project. The goal is simplicity and learning, not production-grade enterprise software. Keep contributions aligned with this philosophy.
