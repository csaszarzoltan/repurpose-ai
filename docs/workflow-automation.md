# Workflow Automation Guide

> RepurposeAI v0.5.0 — Schedule, batch, and webhook-triggered content repurposing.

## Overview

Workflow Automation lets you build multi-step content repurposing pipelines that run on a schedule, on demand, or triggered by incoming webhooks. Each workflow is a sequential chain of **steps** — repurpose content, call an external URL, or pause for a delay — with configurable retry per step.

### Trigger Types

| Trigger | Description | Best For |
|---------|-------------|----------|
| **Manual** | Trigger via `POST /api/v1/workflows/{id}/trigger` | Ad-hoc runs, testing |
| **Schedule** | Cron expression or interval-based auto-run | Daily digests, weekly roundups |
| **Webhook** | Incoming webhook with optional HMAC signing | CI/CD pipelines, integrations |

## Workflow Definition

A workflow is a JSON document with a name, trigger configuration, and an ordered list of steps.

### Minimal Example

```json
{
  "name": "Daily Blog Repurpose",
  "trigger_type": "schedule",
  "schedule": {
    "cron_expression": "0 6 * * *",
    "start_at": "2026-07-28T00:00:00Z"
  },
  "steps": [
    {
      "step_id": "social_repurpose",
      "step_type": "repurpose",
      "config": {
        "target_formats": ["twitter_thread", "linkedin_post", "newsletter"],
        "brand_voice": "professional"
      }
    }
  ]
}
```

### Request Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | string | Yes | — | Human-readable workflow name |
| `description` | string | No | — | Optional description |
| `trigger_type` | string | No | `manual` | `manual`, `schedule`, or `webhook` |
| `steps` | array | Yes | — | Non-empty list of step definitions |
| `schedule` | object | No | — | Schedule config (required if `trigger_type=schedule`) |
| `webhook_config` | object | No | — | Webhook config (required if `trigger_type=webhook`) |
| `is_active` | bool | No | `true` | Whether the workflow is active |
| `created_by` | string | No | — | Optional user identifier |

## Step Types

### repurpose

Run content repurposing via the LLM pipeline. The step's `config` can contain:

| Config Key | Type | Description |
|------------|------|-------------|
| `source_content` | string | The content body to repurpose |
| `source_title` | string | Optional content title |
| `source_format` | string | Source format ID (default: `blog_post`) |
| `target_formats` | array | List of target format IDs |
| `brand_voice` | string | `professional`, `casual`, `humorous`, `formal` |
| `custom_instructions` | string | Optional LLM prompt instructions |

### webhook

Call an external URL (SSRF-validated). The step's `config` can contain:

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `callback_url` | string | — | Target URL (must be HTTPS) |
| `method` | string | `POST` | HTTP method: `GET`, `POST`, `PUT` |
| `payload` | object | `{}` | JSON body to send |
| `headers` | object | `{}` | Additional HTTP headers |

> **SSRF protection**: All callback URLs are checked against private IP ranges, metadata services, and blocked schemes. Only HTTPS URLs are permitted.

### wait

Pause pipeline execution for a configurable delay.

| Config Key | Type | Default | Description |
|------------|------|---------|-------------|
| `delay_seconds` | int | `0` | Seconds to pause before the next step |

## Retry Configuration

Each step can optionally include a `retry_config`:

```json
{
  "step_id": "step_1",
  "step_type": "webhook",
  "config": {
    "callback_url": "https://example.com/hook",
    "method": "POST"
  },
  "retry_config": {
    "max_attempts": 5,
    "delay_seconds": 60
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_attempts` | int | 3 | Max retries on failure (default for all steps, overridable per step) |
| `delay_seconds` | int | 30 | Seconds between retry attempts |

### Retry Behavior

- The engine retries a step immediately after its `delay_seconds` on failure.
- If all attempts fail, the step is marked **failed** and the execution continues to the next step.
- A workflow is marked **failed** if *any* of its steps failed after exhausting retries.
- Individual `retry_config` values override the defaults per step.

## Execution Lifecycle

```
pending → running → completed
                  ↘ failed
```

| Status | Description |
|--------|-------------|
| `pending` | Execution created, queued for processing |
| `running` | Steps are being executed sequentially |
| `completed` | All steps succeeded |
| `failed` | One or more steps failed after retries |

Each execution records per-step results including attempt count, timestamps, output, and error details.

## Scheduling

### Cron Expressions

Use standard 5-field cron syntax:

```
┌───────── minute (0-59)
│ ┌──────── hour (0-23)
│ │ ┌─────── day of month (1-31)
│ │ │ ┌────── month (1-12)
│ │ │ │ ┌───── day of week (0-6, 0=Sunday)
* * * * *
```

| Expression | Meaning |
|------------|---------|
| `0 6 * * *` | Every day at 06:00 UTC |
| `0 9 * * 1-5` | Weekdays at 09:00 UTC |
| `*/30 * * * *` | Every 30 minutes |
| `0 0 * * 0` | Every Sunday at midnight UTC |

### Interval Scheduling

Instead of cron, use `interval_minutes` for simple repeat cycles:

```json
{
  "schedule": {
    "interval_minutes": 120,
    "start_at": "2026-07-28T06:00:00Z"
  }
}
```

### Timezone Notes

- Scheduler operates in **UTC**.
- All `start_at` values should be provided as UTC timestamps (ISO 8601 with `Z` suffix or `+00:00`).
- For timezone-aware scheduling, convert your local time to UTC before setting `cron_expression` or `start_at`.

## Webhook Integration

### Creating a Webhook-Triggered Workflow

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Repurpose",
    "trigger_type": "webhook",
    "webhook_config": {
      "secret": "your-hmac-secret"
    },
    "steps": [
      {
        "step_id": "repurpose_step",
        "step_type": "repurpose",
        "config": {
          "target_formats": ["twitter_thread", "linkedin_post"]
        }
      }
    ]
  }'
```

### HMAC Signature Verification

When a workflow's `webhook_config.secret` is set, incoming webhooks **must** include the `X-Hub-Signature-256` header.

The signature is the hex digest of an HMAC-SHA256 computed over the request body using the configured secret, formatted as `sha256=<hex_digest>`.

**Python**:
```python
import hashlib
import hmac

secret = b"your-hmac-secret"
body = b'{"payload": "data"}'
signature = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
# → "sha256=a1b2c3d4e5f6..."
```

**Node.js**:
```javascript
const crypto = require('crypto');
const secret = 'your-hmac-secret';
const body = JSON.stringify({payload: 'data'});
const sig = 'sha256=' + crypto.createHmac('sha256', secret).update(body).digest('hex');
```

**cURL**:
```bash
echo -n '{"payload":"data"}' | openssl dgst -sha256 -hmac "your-hmac-secret"
# Produces: sha256=abc123...

curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/webhook/workflow/a1b2c3d4-... \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=abc123..." \
  -d '{"payload": "data"}'
```

### Signature Verification Errors

| HTTP Status | Meaning |
|-------------|---------|
| 401 | Missing `X-Hub-Signature-256` header when secret is configured |
| 403 | Invalid HMAC signature (payload tampered or wrong secret) |

### Webhook Request Body

The webhook endpoint accepts any JSON body. URL-like fields (`callback_url`, `callback`, `url`, `webhook_url`) are extracted for SSRF validation, but the full body is passed to the workflow engine as context.

## Batch Processing

### Endpoint

`POST /api/v1/repurpose/batch`

### Request

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `jobs` | array | Yes | — | 1–50 repurpose job definitions |
| `concurrency` | int | No | 5 | Max parallel jobs |

Each job object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | object | Yes | `{title, body, source_format}` |
| `target_formats` | array | Yes | Format IDs (e.g. `["twitter_thread", "linkedin_post"]`) |
| `brand_voice` | string | No | Voice style (default: `professional`) |
| `custom_instructions` | string | No | Per-job LLM instructions |

### Response

```json
{
  "batch_id": "b1c2d3e4-...",
  "total": 3,
  "completed": 2,
  "failed": 1,
  "results": [
    {"status": "completed", "result": {"twitter_thread": "...", "linkedin_post": "..."}},
    {"status": "completed", "result": {"newsletter": "..."}}
  ],
  "errors": [
    "Invalid target format: unknown_format"
  ]
}
```

### Best Practices

- **Concurrency tuning**: Start with `concurrency: 3` for rate-limited LLM providers. Increase for batch sizes under 10 when using fast models.
- **Error isolation**: Each job runs independently — one failure doesn't affect others.
- **Max batch size**: Hard limit of 50 jobs per request. For larger batches, split into multiple requests.
- **Idempotency**: Use a unique batch job ID strategy for safe retries.

## Error Handling

### Status Transitions

```
           ┌──────────────┐
           │   pending    │
           └──────┬───────┘
                  │
           ┌──────▼───────┐
           │   running    │
           └──┬────────┬──┘
              │        │
     ┌────────▼──┐  ┌──▼─────────┐
     │ completed │  │   failed   │
     └───────────┘  └────────────┘
```

### Error Sources

| Source | Handling |
|--------|----------|
| LLM provider failure | Step returns `failed`; retry with backoff |
| Webhook URL unreachable | Step returns `failed` after timeout (30s) |
| SSRF-blocked URL | Step fails immediately with blocked-URL error |
| Invalid step configuration | Workflow creation returns 422 |

### Viewing Errors

Check job/execution status via the unified endpoint:

```bash
curl https://repurposeai-production-d688.up.railway.app/api/v1/jobs/{execution_id}
```

Failed steps include an `error` field with the failure reason.

## Migration from Single-Shot to Scheduled Workflows

If you're currently using `POST /api/v1/webhook/repurpose` for async repurposing, here's how to migrate to scheduled workflows:

### Before (Single-Shot)

```bash
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/webhook/repurpose \
  -H "Content-Type: application/json" \
  -d '{
    "content": {...},
    "target_formats": ["twitter_thread"],
    "callback_url": "https://example.com/webhook-receiver"
  }'
```

### After (Scheduled Workflow)

```bash
# 1. Create a scheduled workflow
curl -X POST https://repurposeai-production-d688.up.railway.app/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Repurpose",
    "trigger_type": "schedule",
    "schedule": {"cron_expression": "0 8 * * *"},
    "steps": [
      {
        "step_id": "repurpose_1",
        "step_type": "repurpose",
        "config": {"target_formats": ["twitter_thread"]}
      },
      {
        "step_id": "notify",
        "step_type": "webhook",
        "config": {
          "callback_url": "https://example.com/webhook-receiver",
          "method": "POST",
          "payload": {
            "source": "repurposeai",
            "workflow_name": "Daily Repurpose"
          }
        }
      }
    ]
  }'
```

### Key Differences

| Aspect | Single-Shot | Workflow |
|--------|-------------|----------|
| Content | Provided per request | Extracted from step config or passed in trigger payload |
| Callback | Dedicated endpoint | Webhook step can send results anywhere |
| Scheduling | Manual trigger only | Cron or interval |
| Retries | N/A | Configurable per step |
| Error handling | Status poll | Execution record with step-level detail |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WORKFLOW_SCHEDULER_INTERVAL` | `60` | Scheduler poll interval in seconds |
| `WORKFLOW_MAX_CONCURRENCY` | `5` | Max concurrent workflow executions |

## Architecture Notes

- **In-memory store**: Workflows and executions are stored in-memory (`WORKFLOWS_DB`, `WORKFLOW_EXECUTIONS_DB`). Data is lost on restart. Production use should replace with a persistent database.
- **No last-run tracking**: The alpha scheduler does not track last-run timestamps. Workflows with `interval_minutes` trigger on every poll cycle. This is intentional for v0.5.0 simplicity.
- **Sequential steps only**: Steps run one after another. Parallel step execution is not yet supported.

## API Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /api/v1/workflows | POST | Optional | Create workflow definition |
| /api/v1/workflows | GET | Optional | List workflows |
| /api/v1/workflows/{id}/trigger | POST | Optional | Trigger workflow manually |
| /api/v1/webhook/workflow/{workflow_id} | POST | None (HMAC) | Trigger via webhook |
| /api/v1/repurpose/batch | POST | Optional | Batch repurpose |
| /api/v1/jobs/{id} | GET | None | Unified job status |
