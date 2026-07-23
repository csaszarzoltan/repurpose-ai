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
# Run all tests (211 tests)
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
│   │   └── subscription.py    # Stripe billing endpoints
│   ├── models/
│   │   ├── content.py         # Content and format models
│   │   └── subscription.py    # Subscription models
│   ├── services/
│   │   └── repurpose.py       # Repurposing business logic
│   ├── constants.py           # App constants (version)
│   └── main.py                # FastAPI app factory
├── tests/
│   ├── test_deployment.py     # Deployment tests (9)
│   ├── test_subscription.py   # Billing tests (30)
│   ├── test_health.py         # Health endpoint tests (15)
│   ├── test_repurpose.py      # Core repurpose tests (22)
│   └── ...                    # Other test modules
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
