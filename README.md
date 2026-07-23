# RepurposeAI

AI-powered content repurposing tool.

## Features

- Transform content across formats (blog → thread, article → script, etc.)
- AI-powered content analysis and adaptation
- RESTful API with OpenAPI docs

## Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest -v

# Lint
ruff check src tests
ruff format src tests

# Type check
mypy src
```

## API Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
repurposeai/
├── src/
│   └── app/
│       ├── api/           # API route handlers
│       ├── models/        # Data models
│       ├── services/      # Business logic
│       └── utils/         # Shared utilities
├── tests/
├── pyproject.toml
└── README.md
```

## License

MIT
