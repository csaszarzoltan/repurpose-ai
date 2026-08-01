# RepurposeAI

> **v1.1.0:** RepurposeAI now includes a responsive content workspace at `/`, reusable saved recipes for frequent workflows, configured OpenRouter/OpenAI/Anthropic generation, honest fallback reporting, durable project and variant history, review controls, production authentication enforcement, and privacy-safe telemetry. The existing API remains available at `/docs`.

## User workspace quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
export REPURPOSEAI_DATA_DIR=./data
uvicorn app.main:app --reload
```

Open `http://localhost:8000/` to create and resume projects. In production, set `ENVIRONMENT=production`; project and telemetry routes then require JWT authentication. See [`docs/v1.1.0-workspace.md`](docs/v1.1.0-workspace.md) and [`docs/reports/implementation-report.md`](docs/reports/implementation-report.md).


AI-powered content repurposing tool that transforms one piece of content into 20+ platform-optimized formats, powered by multi-provider LLM support (OpenAI, Anthropic, OpenRouter).

[![Deployed on Railway](https://img.shields.io/badge/Deployed-Railway-1B2A4A?logo=railway)](https://repurposeai-production-d688.up.railway.app)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Features

- Content repurposing engine (blog post → 20+ platform formats)
- **Multi-provider LLM support** — OpenAI, Anthropic, or OpenRouter
- **Smart routing** — fastest/cheapest, specific provider, or auto-fallback
- **20 content formats** — from Twitter threads to SaaS changelogs
- Brand voice customization (per-request or per-user)
- **X-LLM-Provider / X-LLM-Model headers** for per-request provider selection
- Token-aware dispatch with automatic chunking for large content
- JWT user authentication (register, login, token refresh)
- Multi-tenant data isolation (users only see their own content)
- Personal brand voice configuration per user
- API key management for programmatic access
- Async webhook repurposing pipeline with job polling
- SSRF protection for safe API calls
- Stripe billing integration with Free and Pro tiers
- Railway cloud deployment
- **Multi-Platform Auto-Publish** — Post to LinkedIn, Twitter/X, and Medium via API
- **OAuth2 platform auth** — LinkedIn OAuth2, Twitter/X OAuth2 PKCE, Medium PAT
- **Per-platform rate limiting** — configurable token-bucket with automatic back-pressure
- **Dry-run mode** — validate publish requests without posting
- **Publish job tracking** — query publish status by job ID
- **Analytics Dashboard** — content performance tracking, optimization scoring, and trend visualization
- **Validation Gap Analyzer** — readability analysis (Flesch-Kincaid, Dale-Chall, ARI), diff blocks, tone consistency, faithfulness scoring, and LLM-based quality judging
- **Platform Optimization Scoring** — deterministic 0–100 algorithm-readiness score per platform
- **CSV & PDF Export** — scheduled analytics exports with in-memory schedule management
- **Trend Visualization** — period-over-period delta computation, top content ranking, per-metric time-series trends

## Tech Stack

- Python 3.11+ / FastAPI
- Pydantic v2 for data validation
- httpx for HTTP client
- OpenAI SDK (OpenAI + OpenRouter providers)
- Anthropic SDK (Claude provider)
- tiktoken for token counting
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

## Provider Configuration

RepurposeAI supports three LLM providers. Configure them via environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | For OpenAI provider | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | For Anthropic provider | — | Anthropic API key |
| `OPENROUTER_API_KEY` | For OpenRouter provider | — | OpenRouter API key |
| `DEFAULT_LLM_PROVIDER` | No | `openrouter` | Default provider name |
| `DEFAULT_LLM_MODEL` | No | auto | Default model (overridden by X-LLM-Model header) |

At least one API key must be set for LLM-powered repurposing. Without any, the service falls back to string-concatenation (backward compatible).

### Provider-Specific Details

| Provider | SDK | Default Model | Fallback Order |
|----------|-----|---------------|----------------|
| **OpenRouter** | OpenAI-compatible | `openai/gpt-4o-mini` | 1st (default) |
| **OpenAI** | `openai` | `gpt-4o-mini` | 2nd |
| **Anthropic** | `anthropic` | `claude-sonnet-4` | 3rd |

The fallback order (OpenRouter → OpenAI → Anthropic) is used by the `auto_fallback` and `fastest_cheapest` strategies.

### Using Different Providers per Request

Pass `X-LLM-Provider` and `X-LLM-Model` headers to select a specific provider and model for individual requests:

```bash
# Use Anthropic Claude
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/repurpose \
  -H "Content-Type: application/json" \
  -H "X-LLM-Provider: anthropic" \
  -H "X-LLM-Model: claude-sonnet-4" \
  -d '{"content": {"title": "AI in Healthcare", "body": "AI is transforming diagnostics.", "source_format": "blog_post"}, "target_formats": ["twitter_thread"]}'

# Use OpenAI GPT-4o
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/repurpose \
  -H "Content-Type: application/json" \
  -H "X-LLM-Provider: openai" \
  -H "X-LLM-Model: gpt-4o" \
  -d '{"content": {...}, "target_formats": ["linkedin_post"]}'
```

### Routing Strategies

Set the `llm_strategy` field in the request body to control how providers are selected:

| Strategy | Behavior |
|----------|----------|
| `auto_fallback` (default) | Try providers in fallback order; move to next on failure |
| `fastest_cheapest` | Pick first available provider in fallback order |
| `specific_provider` | Route exclusively to the named provider (requires `X-LLM-Provider`) |

```bash
curl -X POST ... \
  -H "X-LLM-Provider: openai" \
  -d '{"content": {...}, "target_formats": ["blog_post"], "llm_strategy": "specific_provider"}'
```

## API Endpoints

### Health Check

```bash
curl https://repurposeai-production-d688.up.railway.app/health
# {"status":"ok","version":"0.7.0","timestamp":"..."}
```

### Authentication (JWT)

Register a new user:

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!", "name": "John"}'
# {"user_id":"uuid","email":"user@example.com","name":"John","role":"user","is_active":true,"created_at":"..."}
```

Login to get JWT tokens:

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "SecurePass123!"}'
# {"access_token":"eyJ...","refresh_token":"eyJ...","token_type":"bearer","expires_in":3600}
```

Refresh an expired access token:

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJ..."}'
```

Get your profile (authenticated):

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/auth/me \
  -H "Authorization: Bearer ***"
```

### Personal Brand Voice (per user)

Get your brand voice config:

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/auth/me/brand-voice \
  -H "Authorization: Bearer ***"
```

Update your brand voice:

```bash
curl -X PUT https://repurposeai-production-d688.up.railway.app/api/v1/auth/me/brand-voice \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"brand_voice": "casual", "custom_instructions": "Keep it light"}'
```

### API Key Management

Create an API key:

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/api-keys \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "scopes": ["repurpose:write"]}'
# {"key_id":"uuid","name":"My API Key","scopes":["repurpose:write"],"is_active":true,"key_prefix":"rp_abc...","key_value":"rp_abc123..."}
```

> **Note**: The full `key_value` is only returned once. Store it securely.

Use an API key for programmatic access:

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/repurpose \
  -H "X-API-Key: *** \
  -H "Content-Type: application/json" \
  -d '{"content": {...}, "target_formats": ["twitter_thread"]}'
```

### Subscription (Billing)

Create a subscription (requires auth):

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/subscription \
  -H "Authorization: Bearer ***" \
  -H "Content-Type: application/json" \
  -d '{"tier": "free"}'
# {"subscription_id":"sub_abc123","user_id":"...","tier":"free","status":"active","monthly_limit":5,"current_usage":0}
```

Check subscription status (requires auth):

```bash
curl "https://repurposeai-production-d688.up.railway.app/api/v1/subscription/status" \
  -H "Authorization: Bearer ***"
# {"user_id":"...","tier":"free","status":"active","monthly_limit":5,"current_usage":0,"repurposes_remaining":5}
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
  -d '{"content": {"title": "AI in Healthcare", "body": "AI is transforming diagnostics.", "source_format": "blog_post"}, "target_formats": ["twitter_thread", "linkedin_post"]}'
```

> If authenticated via `Authorization` header, the user's personal brand voice configuration is applied automatically.

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

**`GET /api/v1/webhook/repurpose/status/{job_id}`** — Check job progress.

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/webhook/repurpose/status/b191d726-...
# {"job_id":"b191d726-...","status":"pending","created_at":"...","completed_at":null,"result":null,"error":null}
```

Status values: `pending` → `processing` → `completed` / `failed`.

## Workflow Automation

Schedule, batch, and webhook-trigger content repurposing via configurable step pipelines.

Three trigger types:

- **Manual** — Trigger on demand via API
- **Schedule** — Cron expression or interval-based scheduling
- **Webhook** — Incoming webhook with HMAC-SHA256 signature verification

### POST /api/v1/workflows — Create Workflow

Create a new workflow definition with sequential steps.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Workflow name |
| `description` | string | No | Optional description |
| `trigger_type` | string | No | `manual` (default), `schedule`, or `webhook` |
| `steps` | array | Yes | Non-empty list of step objects (see below) |
| `schedule` | object | No | Schedule configuration for trigger_type=`schedule` |
| `webhook_config` | object | No | Webhook config for trigger_type=`webhook` |
| `is_active` | bool | No | Default `true` |

**Step object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step_id` | string | Yes | Unique step identifier within the workflow |
| `step_type` | string | Yes | `repurpose`, `webhook`, or `wait` |
| `config` | object | No | Step-specific configuration |
| `retry_config` | object | No | Optional retry policy |

**Step types:**

| Step Type | Description | Config keys |
|-----------|-------------|-------------|
| `repurpose` | Run content repurposing | `source_content`, `target_formats`, `brand_voice`, `custom_instructions` |
| `webhook` | Call an external URL | `callback_url`, `method` (POST/GET/PUT), `payload`, `headers` |
| `wait` | Pause for a delay | `delay_seconds` |

**Retry config:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_attempts` | int | 3 | Max retry attempts on failure |
| `delay_seconds` | int | 30 | Seconds between retries |

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Blog → Social + Newsletter",
    "description": "Repurpose a blog post into social media and email",
    "trigger_type": "manual",
    "steps": [
      {
        "step_id": "twitter",
        "step_type": "repurpose",
        "config": {
          "target_formats": ["twitter_thread", "linkedin_post"],
          "brand_voice": "professional"
        }
      },
      {
        "step_id": "wait_1",
        "step_type": "wait",
        "config": {"delay_seconds": 10}
      },
      {
        "step_id": "newsletter",
        "step_type": "repurpose",
        "config": {
          "target_formats": ["newsletter"],
          "brand_voice": "professional"
        }
      }
    ]
  }'
# Response: 201 Created
# {"workflow_id": "a1b2c3d4-..."}
```

### GET /api/v1/workflows — List Workflows

List all workflow definitions with optional active filter.

```bash
# List all workflows
curl https://repurposeai-production-d688.up.railway.app/api/v1/workflows

# Filter by active status
curl "https://repurposeai-production-d688.up.railway.app/api/v1/workflows?active=true"
```

Response: Array of workflow definition objects.

### POST /api/v1/workflows/{id}/trigger — Manual Trigger

Trigger a workflow execution manually. The workflow must exist and be active.

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/workflows/a1b2c3d4-.../trigger
# Response: 202 Accepted
# {"execution_id": "e5f6g7h8-..."}
```

### POST /api/v1/webhook/workflow/{workflow_id} — Webhook Trigger

Trigger a workflow via incoming webhook. If the workflow's `webhook_config` has a `secret`, HMAC-SHA256 verification is performed via the `X-Hub-Signature-256` header.

```bash
# Without HMAC (no secret configured)
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/webhook/workflow/a1b2c3d4-... \
  -H "Content-Type: application/json"
# Response: 202 Accepted
# {"execution_id": "e5f6g7h8-..."}

# With HMAC signing
echo -n '{"payload":"data"}' | openssl dgst -sha256 -hmac "your-secret"
# Produces: sha256=abc123...

curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/webhook/workflow/a1b2c3d4-... \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=abc123..." \
  -d '{"payload": "data"}'
```

### POST /api/v1/repurpose/batch — Batch Repurposing

Repurpose multiple content items in a single request. Processes jobs concurrently with a configurable concurrency limit.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `jobs` | array | Yes | List of job objects (1–50 items) |
| `concurrency` | int | No | Max parallel jobs (default 5, min 1) |

**Job object:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | object | Yes | Content with `title`, `body`, `source_format` |
| `target_formats` | array | Yes | List of format IDs |
| `brand_voice` | string | No | `professional` (default), `casual`, `humorous`, `formal` |
| `custom_instructions` | string | No | Optional per-job custom instructions |

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/repurpose/batch \
  -H "Content-Type: application/json" \
  -d '{
    "jobs": [
      {
        "content": {"title": "AI in Healthcare", "body": "AI is transforming diagnostics.", "source_format": "blog_post"},
        "target_formats": ["twitter_thread"],
        "brand_voice": "professional"
      },
      {
        "content": {"title": "Quantum Computing", "body": "Quantum computing advances in 2026.", "source_format": "blog_post"},
        "target_formats": ["linkedin_post", "newsletter"],
        "brand_voice": "casual"
      },
      {
        "content": {"title": "DevOps Best Practices", "body": "CI/CD pipelines in 2026.", "source_format": "blog_post"},
        "target_formats": ["linkedin_carousel"],
        "brand_voice": "formal"
      }
    ],
    "concurrency": 3
  }'
# Response:
# {"batch_id":"b1c2d3e4-...","total":3,"completed":3,"failed":0,"results":[...],"errors":[]}
```

### GET /api/v1/jobs/{id} — Unified Job Status

Check the status of any job — both async webhook repurpose jobs and workflow executions — via a single endpoint.

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/jobs/b191d726-...
# Response:
# {"job_id":"b191d726-...","status":"completed","created_at":"...","completed_at":"...","result":{...}}
```

### Scheduling Configuration

Environment variables for the background workflow scheduler:

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKFLOW_SCHEDULER_INTERVAL` | `60` | Scheduler poll interval in seconds |
| `WORKFLOW_MAX_CONCURRENCY` | `5` | Max concurrent workflow executions |

### API Endpoint Table — Workflow Automation

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/workflows | POST | Optional | Create workflow definition |
| /api/v1/workflows | GET | Optional | List workflows |
| /api/v1/workflows/{id}/trigger | POST | Optional | Trigger workflow manually |
| /api/v1/webhook/workflow/{workflow_id} | POST | None (HMAC) | Trigger via webhook |
| /api/v1/repurpose/batch | POST | Optional | Batch repurpose |
| /api/v1/jobs/{id} | GET | None | Unified job status |

## Multi-Platform Auto-Publish

Publish content directly to social platforms via a unified API. Supported platforms:

| Platform | Auth Method | Post Types |
|----------|-------------|------------|
| **LinkedIn** | OAuth2 (`w_member_social`) | Text commentary, article links, image posts |
| **Twitter / X** | OAuth2 PKCE (`tweet.write`, `users.read`, `offline.access`) | Single tweet, threaded tweets with media |
| **Medium** | Personal Access Token | Draft or published articles (markdown) |

### Dry-Run Mode

Pass `dry_run=true` to validate a publish request without actually posting:

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/publish?dry_run=true \
  -H "Content-Type: application/json" \
  -d '{"platform": "linkedin", "content": "Hello world!", "title": "Test"}'
# {"job_id":"...","platform":"linkedin","status":"dry-run","errors":[],"created_at":"..."}
```

In dry-run mode the request is validated, a job ID is returned with status `dry-run`, and no HTTP calls are made to the platform.

### Publish API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/publish | POST | Platform credentials | Dispatch content to a platform |
| /api/v1/publish?dry_run=true | POST | Platform credentials | Validate without posting |
| /api/v1/publish/{job_id} | GET | None | Query publish job status |
| /api/v1/publish/platforms | GET | None | List supported platforms |
| /publish/{platform}/auth-url | GET | None | Get OAuth2 authorization URL |
| /publish/{platform}/callback | POST | Auth code | Complete OAuth2 token exchange |
| /publish/{platform}/credentials | GET | None | List stored credentials |
| /publish/{platform}/credentials | PUT | None | Store or update credentials |

### Platform Setup

#### LinkedIn

1. Create an app at [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps)
2. Request the **`w_member_social`** scope under Products → "Share on LinkedIn"
3. Note your **Client ID** and **Client Secret** from the Auth tab
4. Set the OAuth2 redirect URI to your callback handler
5. Get the auth URL:

```bash
curl "https://repurposeai-production-d688.up.railway.app/publish/linkedin/auth-url?redirect_uri=https://yourapp.com/callback"
# {"url":"https://www.linkedin.com/oauth/v2/authorization?...","auth_url":"...","platform":"linkedin"}
```

6. User authorizes → receives a `code` → exchange it:

```bash
curl -X POST "https://repurposeai-production-d688.up.railway.app/publish/linkedin/callback?code=AUTH_CODE&state=..."
# {"status":"success","platform":"linkedin","access_token":"AQV..."}
```

#### Twitter / X

1. Create a project at [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Enable **OAuth 2.0 PKCE** with **Confidential Client** type
3. Add scopes: `tweet.write`, `users.read`, `offline.access`
4. Note your **Client ID** (PKCE code challenge/challenge method managed by the app)
5. Get the auth URL:

```bash
curl "https://repurposeai-production-d688.up.railway.app/publish/twitter/auth-url?redirect_uri=https://yourapp.com/callback"
```

6. Exchange the authorization code for credentials via the callback endpoint.

#### Medium

1. Go to **Settings → Security and apps → Integration tokens** on [Medium](https://medium.com/me/settings)
2. Generate a **Personal Access Token**
3. Store it via the credentials API:

```bash
curl -X PUT "https://repurposeai-production-d688.up.railway.app/publish/medium/credentials" \
  -H "Content-Type: application/json" \
  -d '{"platform": "medium", "access_token": "YOUR_PAT", "is_active": true}'
```

### Rate Limiting

> **Important**: Platform credentials are stored in-memory and are lost on service restart. For production use, configure a persistent credential store.

The `RateLimiter` service enforces per-platform rate limits using a token-bucket algorithm:

| Platform | Default Limit | Window |
|----------|--------------|--------|
| All platforms | 100 requests | 60 seconds |

Rate limits are configurable via the `max_calls` and `period` parameters on the `RateLimiter` class. When a publisher receives HTTP 429 responses, it applies exponential backoff (0.5s → 1s → 2s) and retries automatically.

## Analytics Dashboard

Track content performance, compute optimization scores, validate AI-generated content, export reports, and visualize trends. All endpoints are under `/api/v1/analytics`.

### Analytics API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/analytics/posts` | GET | List all tracked posts with metrics |
| `/api/v1/analytics/posts/{post_id}` | GET | Get detailed metrics for a specific post |
| `/api/v1/analytics/summary` | GET | Aggregate summary over a date range |
| `/api/v1/analytics/optimization-score/calculate` | POST | Calculate 0–100 algorithm-readiness score |
| `/api/v1/analytics/optimization-score/{post_id}` | GET | Get stored optimization score for a post |
| `/api/v1/analytics/validate` | POST | Validate AI-generated content vs published |
| `/api/v1/analytics/validation/{job_id}` | GET | Get validation report by job ID |
| `/api/v1/analytics/export/csv` | POST | Export analytics data as CSV |
| `/api/v1/analytics/export/pdf` | POST | Export analytics report as PDF |
| `/api/v1/analytics/export/schedule` | POST | Create a scheduled export |
| `/api/v1/analytics/export/schedule/{schedule_id}` | DELETE | Delete an export schedule |
| `/api/v1/analytics/export/{export_id}` | GET | Get export status by ID |
| `/api/v1/analytics/trends/{metric}` | GET | Time-series trend data for a metric |
| `/api/v1/analytics/trends/summary` | GET | Summary of all trend metrics |
| `/api/v1/analytics/trends/top-content` | GET | Top-performing content across all platforms |

### Analytics Modules

The dashboard is organized into 7 internal modules (see `docs/analytics.md` for full guide):

| Module | Priority | Service | Description |
|--------|----------|---------|-------------|
| P0.1 | Data Store | `DatabaseConnection`, `MetricsRepository`, `ValidationRepository`, `ScoreRepository`, `Migrator` | Connection lifecycle, versioned schema migrations, in-memory CRUD |
| P0.2 | Content Performance | `MetricsCollector` | Fetch and normalise per-post metrics (engagement, completion, share, growth rates) |
| P1.1 | Optimization Scoring | `ScoreCalculator` | Deterministic 0–100 scoring per platform with weighted signal contributions |
| P1.2 | Validation Gap Analyzer | `ValidationAnalyzer` | Readability (Flesch-Kincaid, Dale-Chall, ARI), diff blocks (difflib), tone consistency, faithfulness, LLM quality judge |
| P1.3 | CSV Export | `ExportService` | CSV generation with headers, schedule management (create/delete/list) |
| P2.1 | PDF Export | `ExportService` | PDF file path stubs, schedule management, export status tracking |
| P2.2 | Trend Visualization | `TrendService` | Period-over-period delta, top content ranking, per-metric time-series |

### Analytics Quick-Start

```bash
# List tracked posts
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/posts

# Get aggregate summary
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/summary

# Calculate optimization score
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/analytics/optimization-score/calculate

# Validate content
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/analytics/validate

# Export as CSV
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/analytics/export/csv

# Get trend data for engagement_rate
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/trends/engagement_rate

# Get top-performing content
curl https://repurposeai-production-d688.up.railway.app/api/v1/analytics/trends/top-content
```

## All 20 Content Formats

Each format has tailored tone guidance, structure hints, and target audience for LLM generation.

| # | Format ID | Name | Max Length | Img | Links | Tone Guidance | Structure | Target Audience |
|---|-----------|------|-----------|-----|-------|---------------|-----------|-----------------|
| 1 | `blog_post` | Blog Post | 5000 | ✓ | ✓ | Professional, engaging, authoritative | Intro → H2 sections → bullet points → conclusion → CTA | General readers |
| 2 | `twitter_thread` | Twitter Thread | 1400 | ✓ | ✓ | Conversational, punchy, opinionated | Hook tweet → numbered points → insight → CTA | Twitter/X users |
| 3 | `linkedin_post` | LinkedIn Post | 3000 | ✓ | ✓ | Professional, thought-leadership, authentic | Hook → story/insight → takeaways → CTA | LinkedIn professionals |
| 4 | `newsletter` | Newsletter | 10000 | ✓ | ✓ | Friendly, personal, value-driven | Greeting → main story → quick hits → CTA → sign-off | Email subscribers |
| 5 | `video_script` | Video Script | 5000 | ✗ | ✗ | Conversational, visual, dynamic | Hook → context → main → demonstration → CTA | Video viewers |
| 6 | `podcast_outline` | Podcast Outline | 3000 | ✗ | ✓ | Structured, guiding, conversational | Intro → topic → segments → takeaways → outro | Podcast hosts |
| 7 | `email_sequence` | Email Sequence | 8000 | ✓ | ✓ | Nurturing, persuasive, value-first | Welcome → value → social proof → offer → close | Nurture subscribers |
| 8 | `social_media` | Social Media | 500 | ✓ | ✓ | Concise, catchy, platform-native | Hook → body → CTA + hashtags | Platform users |
| 9 | `youtube_tiktok_caption` | YouTube/TikTok Caption | 300 | ✗ | ✗ | Energetic, punchy, hook-driven | Hook → context → payoff → engagement CTA | Short-form video viewers |
| 10 | `instagram_carousel` | Instagram Carousel | 2200 | ✓ | ✗ | Visual-first, educational, scroll-stopping | Cover → educational slides → CTA slide | Instagram users |
| 11 | `medium_article` | Medium Article | 10000 | ✓ | ✓ | Reflective, authoritative, story-driven | Title → anecdote → body → reflection → clap CTA | Medium readers |
| 12 | `reddit_post` | Reddit Post | 40000 | ✓ | ✓ | Authentic, conversational, community-aware | Title → context → take → discussion prompt | Reddit community members |
| 13 | `landing_page` | Landing Page | 3000 | ✓ | ✓ | Persuasive, benefit-driven, clear | Hero → pain → solution → features → proof → CTA → FAQ | Potential customers |
| 14 | `press_release` | Press Release | 2000 | ✓ | ✓ | Formal, factual, newsworthy | Headline → dateline → lead → quotes → boilerplate | Journalists, media |
| 15 | `case_study` | Case Study | 4000 | ✓ | ✓ | Story-driven, results-focused, credible | Background → challenge → solution → results → testimonial | Prospective customers |
| 16 | `whitepaper_outline` | Whitepaper Outline | 5000 | ✓ | ✓ | Academic, authoritative, research-driven | Executive summary → problem → method → findings → conclusion | Industry professionals |
| 17 | `ebook_chapter_plan` | eBook Chapter Plan | 5000 | ✓ | ✓ | Educational, encouraging, structured | Overview → objectives → sections → takeaways → exercises | In-depth learners |
| 18 | `podcast_show_notes` | Podcast Show Notes | 2500 | ✗ | ✓ | Informative, scannable, engaging | Summary → timestamps → quotes → resources → CTA | Podcast listeners |
| 19 | `linkedin_carousel` | LinkedIn Carousel | 3000 | ✓ | ✓ | Professional, educational, scannable | Title → problem → insight → data → solution → CTA | LinkedIn connections |
| 20 | `saas_changelog` | SaaS Changelog | 1500 | ✓ | ✓ | Clear, user-focused, celebratory | Version → headline → what's new → fixes → upgrade CTA | SaaS users |

List available formats via the API:

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
- Status is checked via `GET /api/v1/subscription/status`
- Stripe webhook events are handled at `POST /api/v1/webhook`

## Rate Limiting

Per-platform rate limiting is implemented via the `RateLimiter` service using a token-bucket algorithm (see [Multi-Platform Auto-Publish](#multi-platform-auto-publish) for defaults). Each platform has an isolated rate-limit bucket. When a publisher receives HTTP 429 responses, exponential backoff (0.5s → 1s → 2s) is applied with automatic retries.

Additionally, the LLM layer handles provider-level rate limits gracefully via the auto-fallback mechanism — if one LLM provider hits rate limits, the router automatically tries the next available provider.

## Testing

```bash
# Run all tests (1,204 total, all passing)
.venv/bin/python -m pytest tests/ -v

# Run a specific test file
.venv/bin/python -m pytest tests/test_repurpose.py -v

# Run publish-specific tests
.venv/bin/python -m pytest tests/test_publish.py tests/test_publish_api.py -v

# Run analytics tests
.venv/bin/python -m pytest tests/test_analytics_*.py -v

# Lint check
.venv/bin/ruff check src/ tests/
```

Tests: 1,204 total across 34 test files (all passing, 0 regressions). Includes:

| Test File | Tests | Area |
|-----------|-------|------|
| `test_analytics_data_store.py` | 318 | Data Store — DB connection, repositories, migrations |
| `test_analytics_models.py` | 268 | Pydantic analytics model validation |
| `test_analytics_scoring.py` | 145 | ScoreCalculator deterministic scoring |
| `test_analytics_validation.py` | 268 | ValidationAnalyzer readability & gap analysis |
| `test_analytics_export.py` | 226 | CSV & PDF export |
| `test_analytics_trends.py` | 233 | TrendService period-over-period deltas |
| `test_analytics_performance.py` | 212 | Performance tracking & metric collection |
| Other test files | ~973 | Auth, API keys, subscriptions, publish, workflows, LLM, webhooks |

## Project Structure

```
repurpose-ai/
├── src/app/
│   ├── api/
│   │   ├── auth.py            # JWT auth: register, login, refresh, profile
│   │   ├── api_keys.py        # API key management (create, list, revoke)
│   │   ├── health.py          # Health check endpoint
│   │   ├── repurpose.py       # Content repurposing endpoint (LLM-aware)
│   │   ├── formats.py         # Format listing endpoint
│   │   ├── webhook.py         # Async webhook + workflow trigger endpoints
│   │   ├── subscription.py    # Stripe billing endpoints
│   │   ├── workflows.py       # Workflow CRUD + manual trigger
│   │   ├── batch.py           # Batch repurpose endpoint
│   │   ├── jobs.py            # Unified job status endpoint
│   │   ├── publish.py         # Multi-platform publish + OAuth2 endpoints
│   │   └── analytics.py       # Analytics dashboard (15 endpoints)
│   ├── models/
│   │   ├── auth.py            # User, Token, API Key, BrandVoice models
│   │   ├── content.py         # Content + 20 ContentFormat enum + FormatInfo
│   │   ├── subscription.py    # Subscription models
│   │   ├── webhook.py         # Webhook/async job models
│   │   ├── workflow.py        # Workflow models + enums
│   │   ├── publish.py         # Publish models + PlatformCredentials
│   │   └── analytics.py       # PostMetrics, AnalyticsSummary, OptimizationScore, ValidationReport, DataPoint, TrendData
│   ├── services/
│   │   ├── llm/               # Multi-Provider LLM Layer
│   │   │   ├── base.py        # BaseLLMProvider abstract interface
│   │   │   ├── openai_provider.py     # OpenAI provider
│   │   │   ├── anthropic_provider.py  # Anthropic provider
│   │   │   ├── openrouter_provider.py # OpenRouter provider
│   │   │   └── router.py      # LLMRouter with strategies
│   │   ├── formats/
│   │   │   ├── registry.py    # FormatTemplate + FormatRegistry
│   │   │   └── templates.py   # All 20 format prompt templates
│   │   ├── publishers/        # NEW: Platform publisher implementations
│   │   │   ├── linkedin.py    # LinkedIn Posts API
│   │   │   ├── twitter.py     # Twitter/X API v2
│   │   │   └── medium.py      # Medium API v1
│   │   ├── auth.py            # JWT, password hashing, user management
│   │   ├── api_key.py         # API key generation, hashing, validation
│   │   ├── repurpose.py       # Repurposing business logic (LLM-aware)
│   │   ├── brand_voice.py     # Brand voice customization
│   │   ├── ssrf.py            # SSRF protection
│   │   ├── publish.py         # NEW: PublishService orchestrator
│   │   ├── platform_auth.py   # NEW: OAuth2 auth service
│   │   ├── rate_limiter.py    # NEW: Token-bucket rate limiter
│   │   ├── workflow_engine.py # Workflow execution engine
│   │   ├── scheduler.py      # asyncio scheduler
│   │   ├── workflow_store.py  # In-memory workflow store
│   │   └── analytics/         # Analytics Dashboard modules
│   │       ├── db/
│   │       │   ├── connection.py    # DatabaseConnection lifecycle
│   │       │   ├── repository.py    # MetricsRepository, ValidationRepository, ScoreRepository
│   │       │   └── migrations.py    # Migration/Migrator version management
│   │       ├── metrics_collector.py     # MetricsCollector (P0.2)
│   │       ├── score_calculator.py      # ScoreCalculator (P1.1)
│   │       ├── validation_analyzer.py   # ValidationAnalyzer (P1.2)
│   │       ├── export_service.py        # ExportService CSV/PDF (P1.3, P2.1)
│   │       └── trend_service.py         # TrendService (P2.2)
│   ├── dependencies.py        # Auth dependencies (get_current_user, etc.)
│   ├── constants.py           # App constants (version)
│   └── main.py                # FastAPI app factory
├── tests/
│   ├── test_auth.py                # Auth tests (57)
│   ├── test_api_keys.py            # API key tests (22)
│   ├── test_subscription.py        # Billing tests (30)
│   ├── test_health.py              # Health endpoint tests (15)
│   ├── test_repurpose.py           # Core repurpose + LLM header tests
│   ├── test_llm_providers.py       # Multi-provider LLM tests (104)
│   ├── test_format_templates.py    # Format template tests (98)
│   ├── test_webhook_repurpose.py   # Webhook endpoint tests (88)
│   ├── test_analytics_data_store.py   # 318 tests — Data Store
│   ├── test_analytics_models.py       # 268 tests — Pydantic models
│   ├── test_analytics_scoring.py      # 145 tests — Score calculation
│   ├── test_analytics_validation.py   # 268 tests — Validation
│   ├── test_analytics_export.py       # 226 tests — CSV/PDF export
│   ├── test_analytics_trends.py       # 233 tests — Trend service
│   ├── test_analytics_performance.py  # 212 tests — Performance tracking
│   └── ...                         # Additional test files
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
