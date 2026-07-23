# Changelog

All notable changes to RepurposeAI will be documented in this file.

## [0.1.0] - 2026-07-23

### Added

- **Railway deployment**: FastAPI app deployed on Railway cloud hosting
  - Dockerfile-based build with uv for fast dependency resolution
  - Non-root container user for security
  - Health check endpoint for deployment monitoring
  - Auto-deploys from `main` branch on GitHub
  - Live at: https://repurposeai-production-d688.up.railway.app

- **Stripe billing integration**:
  - `POST /api/v1/subscription` — Create or update user subscription
  - `GET /api/v1/subscription/status` — Query subscription status and remaining usage
  - `POST /api/v1/webhook` — Handle Stripe webhook events (payment succeeded, failed, canceled)
  - Free tier: 5 repurposes/month
  - Pro tier: $49/month, unlimited repurposes
  - Input validation: invalid tier values return 400 (not 422)
  - Webhook signature validation (rejects missing/invalid signatures with 403)

- **Health endpoint enhancement**:
  - Returns version info (`0.1.0`) and UTC timestamp
  - Used by Railway for deployment health checks

- **Test suite expansion**:
  - 9 new deployment tests (Railway config, Dockerfile, health endpoint)
  - 30 new subscription/billing tests (interface + behavioral)
  - Total: 211 tests (up from 172), all passing
  - Ruff lint: clean

### Changed

- `app.main` now includes subscription router alongside health, repurpose, and formats routers
- `APP_VERSION` extracted to `constants.py` to avoid circular imports
- Health endpoint returns structured JSON with version and timestamp

### Technical Decisions

- In-memory dict storage for subscriptions (production would use a database)
- Tier validated as string in handler (returns 400) rather than Pydantic enum (returns 422)
- Webhook handler accepts raw `Request` body to support Stripe signature verification pattern
- Railway free-plan: deploying under existing `locust-performance-kit` project (new project name unavailable on free plan)
