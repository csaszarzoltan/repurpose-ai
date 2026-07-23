# RepurposeAI

AI-powered content repurposing tool that transforms one piece of content into 10+ platform-optimized formats.

## Features

- Content repurposing engine (blog → multi-platform)
- Brand voice customization
- SSRF protection for safe API calls
- Multi-platform output formatting

## Tech Stack

- Python 3.11+ / FastAPI
- Railway deployment

## API Endpoints

- `GET /health` — Health check
- `POST /api/v1/repurpose` — Repurpose content
- `GET /api/v1/formats` — List available formats
- `GET /api/v1/formats/{format_id}` — Format details

## Development

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```
