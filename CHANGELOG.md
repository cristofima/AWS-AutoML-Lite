# Changelog

All notable changes to AWS AutoML Lite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Nothing yet - preparing for v1.1.0

## [1.0.0] - 2025-12-03

### Added
- Complete serverless AutoML platform on AWS
- FastAPI backend with Lambda deployment
- FLAML AutoML integration for automatic model training
- Next.js 16 frontend with SSR support via AWS Amplify
- AWS Batch + Fargate Spot for cost-effective training
- Automatic problem type detection (classification/regression)
- EDA report generation with Sweetviz
- Training history and job tracking with DynamoDB
- Model download and export (.pkl format)
- Docker-based prediction script
- CI/CD with GitHub Actions + OIDC
- Comprehensive documentation and architecture diagrams

### Infrastructure
- S3 buckets for datasets, models, and reports
- DynamoDB tables for metadata and job tracking
- Lambda function for API endpoints (direct ZIP deployment)
- API Gateway for REST API
- AWS Batch with Fargate Spot for training jobs
- ECR repository for training container
- CloudWatch logging and monitoring
- AWS Amplify for frontend hosting

### Features
- CSV file upload with drag & drop
- Auto-calculated time budget based on dataset size
- Smart column detection (ID columns automatically excluded)
- Feature importance visualization
- Training progress monitoring
- Portable model export for local use

### Documentation
- Complete quickstart guide
- Architecture decision records
- Terraform best practices analysis
- Lessons learned document
- CI/CD setup guide with OIDC
- Git commit message conventions (713 lines)
- Table of contents for long documents
- CONTRIBUTING.md for collaboration
- CHANGELOG.md for version tracking
- Version badges in README

### Cost Optimization
- ~$10-25/month total cost for moderate usage
- Fargate Spot pricing (70% discount)
- No always-on infrastructure
- Training cost: ~$0.02/job

---

## Version History

- **v1.0.0** (2025-12-03) - Initial release with full serverless architecture and comprehensive documentation

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Links

- [Documentation](./docs/README.md)
- [Quickstart Guide](./docs/QUICKSTART.md)
- [Architecture Decisions](./infrastructure/terraform/ARCHITECTURE_DECISIONS.md)
- [Lessons Learned](./docs/LESSONS_LEARNED.md)
