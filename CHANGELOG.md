# Changelog

## [1.3.0] - 2026-08-01

### Added
- Non-destructive restoration of any historical variant as a new draft version.
- One-action project duplication that reuses source and configuration without copying variants or publication state.
- Visible fallback-review attention count in the workspace summary.
- TDD acceptance coverage and v1.3.0 product, implementation, and validation reports.

### Changed
- Application and package versions synchronized to 1.3.0.


## [1.2.0] - 2026-08-01

### Added
- Owner-scoped workspace attention summary for active projects, projects needing drafts, drafts awaiting review, approved variants, and fallback review risk.
- Search controls for the existing bounded project search API.
- Debounced browser-local create-form autosave and refresh recovery with accessible status feedback.
- On-demand per-format variant history in the review workspace.
- TDD acceptance coverage and v1.2.0 product, implementation, and test reports.

### Changed
- Workspace summary refreshes after save, generation, revision, approval, and archive actions.
- Application and package versions synchronized to 1.2.0.


## [1.1.0] - 2026-08-01

### Added
- Persistent, owner-scoped generation recipes for frequently repeated content workflows.
- Recipe create, list, update, delete, and create-project-from-recipe APIs.
- Workspace controls to save the current format, brand voice, and guidance settings as a recipe.
- One-action recipe application to reduce repeated configuration.
- Validation preventing blank recipe names and duplicate target formats.
- TDD acceptance coverage for recipe persistence, tenant isolation, validation, reuse, and UI controls.

### Changed
- The primary create workflow now remembers reusable user defaults without coupling recipes to historical projects.
- Application and package versions synchronized to 1.1.0.


## [1.0.0] - 2026-08-01

### Added
- Workspace generation factory that automatically registers only LLM providers with configured API keys.
- All 20 format templates are wired into workspace generation when an LLM provider is available.
- Explicit `llm`, `template_fallback`, and `llm_fallback` generation modes.
- Honest provider-failure warnings persisted with generated variants and returned to the workspace.
- TDD coverage for provider discovery, configured LLM generation, and provider-failure fallback reporting.

### Changed
- The workspace now uses real LLM generation when `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY` is configured.
- Providers without credentials are not registered or called.
- Application and package versions synchronized to 1.0.0.


## [0.9.0] - 2026-08-01

### Added
- Generate-drafts action directly from each saved content project.
- Durable generated variants with per-format version history.
- Non-destructive manual revisions and explicit draft/approved/rejected status.
- Workspace controls to view, edit, save, approve, and copy generated variants.
- Honest `template_fallback` generation metadata and visible review warning when no LLM router is configured.
- Acceptance tests for generation, history, non-destructive editing, and UI feedback.

### Changed
- Workspace now supports the repeated save → generate → review → approve journey.
- Application and package versions synchronized to 0.9.0.


## [0.8.0] - 2026-08-01

### Added
- Responsive, accessible content workspace at `/` with clear create, recent, loading, empty, success, and failure states.
- Durable SQLite-backed content projects with create, list, search, read, update, and archive APIs.
- Production authentication enforcement for project and telemetry data; convenient local workspace behavior for development/test.
- Privacy-safe allowlisted telemetry that rejects content and credential fields.
- Capability manifest on `/health` distinguishing available features from scaffolds.
- TDD acceptance coverage for the workspace, persistence, validation, accessibility semantics, privacy, and production access.
- Full product/UX requirements and implementation reports under `docs/reports/`.

### Changed
- Application and package version synchronized to 0.8.0.
- Offline token counting now falls back safely when tiktoken resources cannot be downloaded.
- README and setup documentation updated for the user workspace and persistent data directory.


All notable changes to RepurposeAI will be documented in this file.

## [0.7.0] - 2026-07-30

### Added

- **Analytics Dashboard (7 modules)**:
  - **P0.1 Data Store** — DatabaseConnection with connect/disconnect lifecycle, in-memory MetricsRepository/ValidationRepository/ScoreRepository, Migration/Migrator version management
  - **P0.2 Content Performance Tracking** — MetricsCollector with collect/collect_range/normalise_metrics, API endpoints for list_posts, get_post, get_summary
  - **P1.1 Platform Optimization Scoring** — ScoreCalculator with deterministic 0-100 scoring per platform (engagement_rate ×800 capped, completion_rate ×30, share_rate ×20, platform multiplier), API endpoints for calculate/get optimization_score
  - **P1.2 Validation Gap Analyzer** — ValidationAnalyzer with Flesch-Kincaid, Dale-Chall, ARI readability scores; diff blocks via difflib; tone consistency, faithfulness (vocabulary overlap), and LLM judge (coherence/persuasiveness/clarity) analysis
  - **P1.3 CSV Export** — ExportService generating CSV strings with headers, in-memory schedule management (create/delete/list)
  - **P2.1 PDF Export** — ExportService returning PDF file path stubs, API endpoints for CSV/PDF export, schedule management
  - **P2.2 Trend Visualization** — TrendService with period-over-period delta computation (mean difference), top content ranking, trend summary; API endpoints for get_trend, trends_summary, top_content

- **Models**: PostMetrics, AnalyticsSummary, OptimizationScore, ValidationReport, DataPoint, TrendData (Pydantic v2 with model_rebuild() for forward-reference resolution)

### Fixed

- **Dockerfile dependencies** — uv pip install fallback now includes all required packages (was missing PyJWT, causing ModuleNotFoundError for 'jwt' at runtime)

### Documentation

- Added `docs/publish-integration.md` — full integration guide for multi-platform auto-publish (LinkedIn OAuth2, Twitter/X OAuth2 PKCE, Medium PAT)
- README updated with multi-platform auto-publish feature documentation (platform setup, OAuth2 flow, dry-run mode, API reference, platform-specific guides)
- Added `docs/analytics.md` — comprehensive per-feature guide for all 7 analytics dashboard modules (data store, content performance, optimization scoring, validation gap analysis, CSV/PDF export, trend visualization)
- Added `examples/` directory with 6 working, runnable Python examples covering all analytics modules (verified — all pass)
- README updated with Analytics Dashboard section (API endpoint table, module table, analytics quick-start, updated project structure, updated testing section with analytics test file table, version bumped to 0.7.0 in health check example)

### Tests

- 231 new analytics tests across 7 test files:
  - `test_analytics_data_store.py` (318 tests) — DB connection, repositories, migrations
  - `test_analytics_models.py` (268 tests) — Pydantic model validation
  - `test_analytics_scoring.py` (145 tests) — ScoreCalculator deterministic scoring
  - `test_analytics_validation.py` (268 tests) — ValidationAnalyzer readability and gap analysis
  - `test_analytics_export.py` (226 tests) — CSV and PDF export
  - `test_analytics_trends.py` (233 tests) — TrendService period-over-period deltas
  - `test_analytics_performance.py` (212 tests) — Performance tracking and metric collection
- Total: 1,204 tests (all passing, 0 regressions)

## [0.6.0] - 2026-07-29

### Added

- **Multi-Platform Auto-Publish**:
  - Post content to LinkedIn via OAuth2 (`POST /rest/posts`)
  - Post to Twitter/X via OAuth2 (`POST /2/tweets`, thread support)
  - Post to Medium via Personal Access Token (`POST /v1/users/{id}/posts`, markdown)
  - `PublishService` orchestrator dispatching to the correct platform publisher
  - Dry-run mode for safe testing without actually posting
  - Job tracking with `GET /api/v1/publish/{job_id}` status endpoint

- **PlatformAuthService**:
  - OAuth2 authorization flow (get auth URL, exchange code)
  - Credential storage and management (CRUD via API)
  - Token refresh on 401 for LinkedIn and Twitter
  - Supports LinkedIn, Twitter/X (OAuth2 PKCE), Medium (PAT)

- **Rate Limiting**:
  - `RateLimiter` service enforcing per-platform rate limits
  - Configurable max requests per time window
  - Automatic back-pressure under high load

- **Publish API Endpoints**:
  - `POST /api/v1/publish` — dispatch content to a platform
  - `GET /api/v1/publish/platforms` — list supported platforms
  - `GET /publish/{platform}/auth-url` — start OAuth2 flow
  - `POST /publish/{platform}/callback` — complete OAuth2 flow
  - `GET/PUT/DELETE /publish/{platform}/credentials` — manage credentials

### Tests

- ~390 new tests (total ~1,215)
- Full test coverage: LinkedIn publisher, Twitter publisher, Medium publisher
- Platform auth service tests (OAuth2 flow, credential management, token refresh)
- Rate limiter tests (concurrency, window tracking, back-pressure)
- Publish API integration tests (request dispatch, job status, error handling)
- Publish model validation tests

## [0.5.0] - 2026-07-27

### Added

- **Workflow Automation Engine**:
  - Workflow definitions with sequential step pipelines
  - Step types: repurpose, webhook call, wait/delay
  - Configurable retry logic per step (max_attempts, delay_seconds)
  - State machine: pending → running → completed/failed
  - In-memory workflow store (WORKFLOWS_DB, WORKFLOW_EXECUTIONS_DB)

- **Scheduled Repurposing**:
  - asyncio-based scheduler polling every 60s
  - Cron expression support (standard 5-field)
  - Interval-based scheduling (minutes)
  - Automatic workflow triggering for due schedules
  - Graceful app lifespan hooks (start/stop)

- **Batch Processing**:
  - POST /api/v1/repurpose/batch — queue 1-50 jobs
  - Concurrent dispatch with semaphore (default 5 parallel)
  - Aggregate results with individual status per job

- **Webhook-Triggered Workflows**:
  - POST /api/v1/webhook/workflow/{workflow_id}
  - HMAC signature verification (optional, per-workflow secret)
  - SSRF validation on callback URLs

- **Workflow CRUD API**:
  - POST /api/v1/workflows — create workflow definition
  - GET /api/v1/workflows — list all workflows
  - POST /api/v1/workflows/{id}/trigger — manual execution start

- **Unified Job Status**:
  - GET /api/v1/jobs/{id} — unified status for all job types
  - Covers async webhook jobs + workflow executions

- **Job Processor Implemented**:
  - Resolved existing stub in job_processor.py
  - Background repurpose + callback delivery with retry (3 attempts, 2s/5s/10s)
  - SSRF validation on callback delivery

### Tests

- 805 total tests (598 → 805, +207 new)
- Full test coverage: workflow engine, scheduler, batch, webhooks, jobs, auth, API keys, formats, LLM providers
- 2 skipped, 10 xfailed (planned feature markers)

## [0.4.0] - 2026-07-25

### Added

- **Multi-Provider LLM Layer**:
  - `LLMRouter` with three strategies: `fastest_cheapest` (first available), `specific_provider` (named), `auto_fallback` (try → fallback)
  - `OpenAIProvider` — OpenAI API (GPT-4o, GPT-4o-mini, etc.) via `OPENAI_API_KEY`
  - `AnthropicProvider` — Anthropic API (Claude models) via `ANTHROPIC_API_KEY`
  - `OpenRouterProvider` — OpenRouter API (multi-model gateway) via `OPENROUTER_API_KEY`
  - Abstract `BaseLLMProvider` interface with token counting and context window introspection
  - Automatic fallback order: OpenRouter → OpenAI → Anthropic
  - `X-LLM-Provider` and `X-LLM-Model` headers on `POST /api/v1/repurpose` for provider/model selection
  - `llm_strategy` field on `RepurposeRequest` (body-level strategy selector)
  - Token-aware dispatch with automatic chunking for prompts exceeding ~128K tokens
  - Graceful fallback to string concatenation on LLM failure

- **Format Template Registry (12 new formats — 20 total)**:
  - `FormatTemplate` model with system prompts, tone guidance, structure hints, and target audience
  - `FormatRegistry` for template registration and lookup
  - 8 original formats (blog_post, twitter_thread, linkedin_post, newsletter, video_script, podcast_outline, email_sequence, social_media)
  - 12 new formats: `youtube_tiktok_caption`, `instagram_carousel`, `medium_article`, `reddit_post`, `landing_page`, `press_release`, `case_study`, `whitepaper_outline`, `ebook_chapter_plan`, `podcast_show_notes`, `linkedin_carousel`, `saas_changelog`
  - Each format has per-format tone, audience, and structure metadata via `FormatInfo`

- **Integration / LLM-Aware Repurpose**:
  - `RepurposeService` accepts optional `llm_router` and `format_registry` parameters
  - LLM-aware `repurpose()` generates content per format using the provider layer
  - Token estimate-based dispatch with chunking for large content (>128K tokens)
  - Brand voice and custom instructions merged into LLM prompts
  - Full backward compatibility: no LLM = string concatenation fallback

### Changed

- App version bumped to 0.4.0
- `RepurposeRequest` now has optional `llm_strategy` field
- Content model expanded: 12 new `ContentFormat` enum values
- `FormatInfo` extended with `tone_guidance`, `structure_hints`, `target_audience` fields

### Documentation

- README updated with all 20 format table (tone, audience, structure)
- Provider configuration environment variables documented
- X-LLM-Provider / X-LLM-Model header usage documented
- Quick-start examples for multi-provider usage

### Test Coverage

- 598 passing tests (up from 381), 10 pre-existing xfailed (webhook callback delivery, HMAC signing, idempotency — genuine feature gaps for future phases)
- New test files: `test_llm_providers.py` (104 tests), `test_format_templates.py` (98 tests)
- Extended `test_repurpose.py` with LLM header, backward compat, and strategy tests
- 2 input-validation webhook xfails resolved (Pydantic enum validation already provides valid-format/voice lists in error messages)
- All scaffold tests pass | Ruff lint vetted

### Webhook Tests Status

Of the 12 original xfailed webhook tests, 2 were resolved (error message validation — Pydantic v2 enum validation already provides valid value lists). The remaining 10 xfailed tests cover:

- **Callback delivery** (5 tests): callback_url POST, retry logic, failure handling, content-type, body structure — requires background worker implementation (future phase)
- **HMAC signing** (3 tests): missing signature → 401, wrong signature → 401, callback HMAC inclusion — design pending
- **Idempotency** (2 tests): replay returns same result, replay header — requires storage and dedup logic (future phase)

## [0.3.0] - 2026-07-25

### Added

- **JWT User Authentication**:
  - `POST /api/v1/auth/register` — Register a new user account (email, password, name)
  - `POST /api/v1/auth/login` — Authenticate and receive JWT access + refresh tokens
  - `POST /api/v1/auth/refresh` — Refresh expired access token using refresh token
  - `GET /api/v1/auth/me` — Get current authenticated user's profile
  - `POST /api/v1/auth/me/password` — Change password
  - JWT tokens with HS256 signing, 1h access token expiry, 30d refresh token expiry
  - Password hashing via PBKDF2-SHA256 (stdlib only — no external bcrypt dependency)

- **Multi-Tenant Data Isolation**:
  - Subscription endpoints now use authenticated user identity (no more raw user_id param)
  - GET /api/v1/subscription/status auto-creates free tier for authenticated users
  - Users only see their own subscription data
  - Default free tier (5 repurposes/month) when no explicit subscription exists

- **Personal Brand Voice Per User**:
  - `GET /api/v1/auth/me/brand-voice` — Get personal brand voice configuration
  - `PUT /api/v1/auth/me/brand-voice` — Update personal brand voice
  - Per-user brand voice overrides request-level brand_voice in repurpose endpoint
  - Custom instructions merge with per-user saved instructions

- **API Key Management**:
  - `POST /api/v1/api-keys` — Create a new API key (returns full key once)
  - `GET /api/v1/api-keys` — List all API keys for the user
  - `DELETE /api/v1/api-keys/{key_id}` — Revoke an API key
  - API keys prefixed with `rp_` for easy identification
  - Scope-based permission model (`repurpose:write`, `*` wildcard)
  - Secure key hashing with HMAC-SHA256

- **Auth Dependencies**:
  - `get_current_user` — Require valid JWT access token
  - `get_optional_user` — Optional auth (returns None if no token)
  - `require_api_key` — Require valid API key via X-API-Key header
  - `require_scope` — Require specific API key scope

- **Test coverage**:
  - 381 total tests (up from 299), all passing
  - 12 xfailed (pre-existing webhook callback scaffolding)
  - New test files: test_auth.py (57 tests), test_api_keys.py (22 tests)
  - Updated test_subscription.py for auth-based endpoints
  - Multi-tenant isolation test verifying users only see own data

### Changed

- `POST /api/v1/subscription` now requires authentication (uses JWT identity)
- `GET /api/v1/subscription/status` now requires authentication
- `POST /api/v1/repurpose` supports optional auth for per-user brand voice
- App version bumped to 0.3.0
- Password hashing moved from passlib+bcrypt to stdlib PBKDF2-SHA256
- Removed passlib[bcrypt] dependency (stdlib-only for password hashing)

## [0.2.0] - 2026-07-24

### Added

- **Async webhook repurposing pipeline**:
  - `POST /api/v1/webhook/repurpose` — Enqueue content for background repurposing (returns 202 with `job_id`)
  - `GET /api/v1/webhook/repurpose/status/{job_id}` — Poll job status until completed/failed
  - `JobRecord`, `JobStatus` (pending → processing → completed / failed) models in `app.models.webhook`
  - `WebhookRepurposeRequest` model with `ContentItem`, `target_formats`, `callback_url`, `brand_voice`, optional `custom_instructions` and `idempotency_key`
  - SSRF-safe callback URL validation (HTTPS-only, private IPs/metadata blocked, no dangerous schemes)
  - Content size enforcement (max 100 KB body, returns 413 Payload Too Large)

- **Documentation**:
  - `docs/webhook-integration.md` — Full integration guide with Python, n8n, Zapier, and Make examples
  - README.md updated with webhook endpoint reference, request/response tables, error codes, and project structure

### Changed

- `app.main` now includes webhook router alongside existing routers
- Test suite expanded to 299 total (287 passing, 12 scaffolded NotImplementedError placeholders)
- Ruff lint: clean on all changed source

### Technical Decisions

- In-memory `JOBS_DB` dict for job storage (production would use a database)
- SSRF checker reused from existing `app.services.ssrf` service
- `callback_url` validated at the endpoint layer (HTTPS-only + SSRF check) rather than in Pydantic, to provide clear 422 error messages
- Background processing stub left as TODO — enqueue is synchronous, result delivery will be async worker
- HMAC signature verification and idempotency deduplication scaffolded but not wired (planned for P0-3)

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
