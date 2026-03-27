# Contributing to CyberMind

## Getting Started

```bash
git clone https://github.com/durgasri-dotcom/cybermind.git
cd cybermind
pip install -r requirements.txt
cp .env.example .env
```

## Development Workflow

1. Create a branch: `git checkout -b feat/your-feature`
2. Make changes
3. Run tests: `pytest tests/ -v`
4. Run linter: `ruff check src/ configs/`
5. Commit using Conventional Commits format
6. Open a pull request

## Conventional Commits

```
feat(scope):     new feature
fix(scope):      bug fix
docs(scope):     documentation
refactor(scope): code restructure
test(scope):     adding tests
ci(scope):       CI/CD changes
data(scope):     data pipeline changes
```

## Running the Pipeline

```bash
python -m src.pipeline.ingest_mitre
python -m src.pipeline.transform_threats
python -m src.pipeline.build_vector_store
```

## Code Style

- Python 3.11+
- Ruff for linting
- Pydantic v2 for schemas
- Structlog for logging
- No hardcoded secrets — use `.env`
