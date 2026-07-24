# RepurposeAI

AI-powered content repurposing tool that transforms one piece of content into 10+ platform-optimized formats.

[![Deployed on Railway](https://img.shields.io/badge/Deployed-Railway-1B2A4A?logo=railway)](https://repurposeai-production-d688.up.railway.app)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Features

- Content repurposing engine (blog post → 10+ platforms)
- Brand voice customization
- SSRF protection for safe API calls
- Multi-platform output formatting (Twitter, LinkedIn, Instagram, etc.)
- Stripe billing integration with Free and Pro tiers
- Railway cloud deployment

## Tech Stack

- Python 3.11+ / FastAPI
- Pydantic v2 for data validation
- httpx for HTTP client
- Railway for cloud hosting
- Stripe for billing (integration scaffold)

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/csaszarzoltan/repurpose-ai.git
cd repurpose-ai

# Install dependencies
pip install -e ".[dev]"

# Start the dev server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Live Deployment

The API is live at: **https://repurposeai-production-d688.up.railway.app**

## API Endpoints

### Health Check

```bash
curl https://repurposeai-production-d688.up.railway.app/health
# {"status":"ok","version":"0.1.0","timestamp":"..."}
```

### Subscription (Billing)

Create a subscription:

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/subscription \
  -H "Content-Type: application/json" \
  -d '{"tier": "free", "user_id": "user-123"}'
# {"subscription_id":"sub_abc123","user_id":"user-123","tier":"free","status":"active","monthly_limit":5,"current_usage":0}
```

Check subscription status:

```bash
curl "https://repurposeai-production-d688.up.railway.app/api/v1/subscription/status?user_id=user-123"
# {"user_id":"user-123","tier":"free","status":"active","monthly_limit":5,"current_usage":0,"repurposes_remaining":5}
```

Create a Pro subscription (unlimited repurposes):

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/subscription \
  -H "Content-Type: application/json" \
  -d '{"tier": "pro", "user_id": "user-123"}'
# {"subscription_id":"sub_xyz789","user_id":"user-123","tier":"pro","status":"active","monthly_limit":-1,"current_usage":0}
```

### Stripe Webhook

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/webhook \
  -H "Content-Type: application/json" \
  -H "stripe-signature: whsec_your_signature" \
  -d '{"type":"invoice.payment_succeeded","id":"evt_123","data":{}}'
# {"received":true}
```

### Content Repurposing

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/repurpose \
  -H "Content-Type: application/json" \
  -d '{"content": "Your blog post text here", "target_formats": ["twitter_thread", "linkedin_post"]}'
```

### Async Webhook Repurposing

Submit content for async processing and poll for results via callback. Designed for large payloads or when you don't want to block on repurposing.

**`POST /api/v1/webhook/repurpose`** — Enqueue a repurpose job (returns immediately with `202 Accepted`).

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/webhook/repurpose \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "title": "AI in Healthcare",
      "body": "AI is transforming diagnostics.",
      "source_format": "blog_post",
      "tags": ["ai"]
    },
    "target_formats": ["twitter_thread"],
    "callback_url": "https://example.com/webhook-receiver",
    "brand_voice": "professional"
  }'
# Response: 202 Accepted
# {"job_id":"b191d726-...","status_url":"/api/v1/webhook/repurpose/status/b191d726-..."}
```

Request fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | object | yes | `{title, body, source_format, tags}` |
| `target_formats` | string[] | yes | At least one format from the [available list](#available-formats) |
| `callback_url` | string (HTTPS) | yes | Webhook callback destination (only HTTPS allowed) |
| `brand_voice` | enum | no | Defaults to `professional` |
| `custom_instructions` | string | no | Free-form instructions for the repurpose engine |
| `Idempotency-Key` | header | no | UUID/string to prevent duplicate submissions |

> **Callback URL security**: Only `https://` URLs are accepted. Private IPs (127.0.0.1, 192.168.x.x, etc.), `localhost`, `file://`, and metadata endpoints are blocked by SSRF protection.

**`GET /api/v1/webhook/repurpose/status/{job_id}`** — Check job progress.

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/webhook/repurpose/status/b191d726-d45e-4690-a940-68e9270d59b6
# Response: 200 OK
# {"job_id":"b191d726-...","status":"pending","created_at":"2026-07-24T12:51:28.885531","completed_at":null,"result":null,"error":null}
```

Status values: `pending` → `processing` → `completed` / `failed`.

Error responses:

| Status | When |
|--------|------|
| `413 Payload Too Large` | Content body exceeds 100 KB |
| `422 Unprocessable Entity` | Missing required fields, invalid format/voice, or blocked callback URL |
| `404 Not Found` | Unknown job_id |

### Available Formats

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/formats
```

## Billing Tiers

| Tier | Price | Monthly Repurposes | Status |
|------|-------|-------------------|--------|
| Free | $0/month | 5 | Active |
| Pro | $49/month | Unlimited | Active |

- **Free tier**: 5 content repurposes per month
- **Pro tier**: Unlimited repurposes for $49/month
- Subscriptions are created via `POST /api/v1/subscription`
- Status is checked via `GET /api/v1/subscription/status?user_id=<id>`
- Stripe webhook events are handled at `POST /api/v1/webhook`

## Testing

```bash
# Run all tests (299 tests — 287 passing)
pytest tests/ -v

# Lint check
ruff check src/ tests/
```

## Project Structure

```
repurpose-ai/
├── src/app/
│   ├── api/
│   │   ├── health.py          # Health check endpoint
│   │   ├── repurpose.py       # Content repurposing endpoint
│   │   ├── formats.py         # Format listing endpoint
│   │   ├── webhook.py         # Async webhook endpoints
│   │   └── subscription.py    # Stripe billing endpoints
│   ├── models/
│   │   ├── content.py         # Content and format models
│   │   ├── subscription.py    # Subscription models
│   │   └── webhook.py         # Webhook/async job models
│   ├── services/
│   │   └── repurpose.py       # Repurposing business logic
│   ├── constants.py           # App constants (version)
│   └── main.py                # FastAPI app factory
├── tests/
│   ├── test_deployment.py         # Deployment tests (9)
│   ├── test_subscription.py       # Billing tests (30)
│   ├── test_health.py             # Health endpoint tests (15)
│   ├── test_repurpose.py          # Core repurpose tests (22)
│   └── test_webhook_repurpose.py  # Webhook endpoint tests (76 passing, 12 TODO)
├── Dockerfile                 # Railway container build
├── railway.toml               # Railway deployment config
├── pyproject.toml             # Project metadata and dependencies
└── README.md
```

## Deployment

RepurposeAI is deployed on Railway using a Dockerfile-based build. The deployment config is in `railway.toml`.

**Deployment URL**: https://repurposeai-production-d688.up.railway.app

To redeploy, push to the `main` branch on GitHub — Railway auto-builds from the latest commit.

## License

MIT
