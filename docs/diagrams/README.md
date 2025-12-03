# Architecture Diagrams

Auto-generated AWS architecture diagrams for AWS AutoML Lite.

## Available Diagrams

| Diagram | Description | Used In |
|---------|-------------|---------|
| `architecture-main.png` | Main architecture overview | README, docs |
| `architecture-dataflow.png` | Data flow: Upload → Train → Download | PROJECT_REFERENCE |
| `architecture-cost.png` | Cost comparison with SageMaker | Documentation |
| `architecture-cicd.png` | CI/CD pipeline with GitHub Actions | SETUP_CICD.md |
| `architecture-training.png` | Training container internal flow | PROJECT_REFERENCE |

## Regenerating Diagrams

To regenerate or modify diagrams:

```bash
# Requirements
pip install diagrams
# Also install Graphviz: https://graphviz.org/download/

# Generate all diagrams
python scripts/generate_architecture_diagram.py
```

## Diagram Previews

### Main Architecture
![Main Architecture](./architecture-main.png)

### Data Flow
![Data Flow](./architecture-dataflow.png)

### Cost Comparison
![Cost Comparison](./architecture-cost.png)

### CI/CD Pipeline
![CI/CD](./architecture-cicd.png)

### Training Container
![Training](./architecture-training.png)

## Customization

Edit `scripts/generate_architecture_diagram.py` to:
- Change colors (`bgcolor`, `fontcolor`)
- Adjust layout (`direction`: LR, TB, RL, BT)
- Modify spacing (`nodesep`, `ranksep`)
- Add new diagrams

## Tools Used

- **[diagrams](https://diagrams.mingrammer.com/)** - Python library for cloud architecture diagrams
- **[Graphviz](https://graphviz.org/)** - Graph visualization software (required dependency)
