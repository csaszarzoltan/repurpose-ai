# RepurposeAI

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
# {"status":"ok","version":"0.4.0","timestamp":"..."}
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

Rate limiting is planned but not yet implemented. Production deployments should add rate limiting at the reverse proxy level (e.g., nginx, Cloudflare, or Railway edge middleware). The LLM layer already handles provider-level rate limits gracefully via the auto-fallback mechanism — if one provider hits rate limits, the router automatically tries the next available provider.

## Testing

```bash
# Run all tests (598 passing, 10 pre-existing xfailed)
.venv/bin/python -m pytest tests/ -v

# Run a specific test file
.venv/bin/python -m pytest tests/test_repurpose.py -v

# Lint check
.venv/bin/ruff check src/ tests/
```

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
│   │   ├── webhook.py         # Async webhook endpoints
│   │   └── subscription.py    # Stripe billing endpoints
│   ├── models/
│   │   ├── auth.py            # User, Token, API Key, BrandVoice models
│   │   ├── content.py         # Content + 20 ContentFormat enum + FormatInfo
│   │   ├── subscription.py    # Subscription models
│   │   └── webhook.py         # Webhook/async job models
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
│   │   ├── auth.py            # JWT, password hashing, user management
│   │   ├── api_key.py         # API key generation, hashing, validation
│   │   ├── repurpose.py       # Repurposing business logic (LLM-aware)
│   │   ├── brand_voice.py     # Brand voice customization
│   │   └── ssrf.py            # SSRF protection
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
