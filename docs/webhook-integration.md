# Webhook Integration Guide

Asynchronous content repurposing via webhooks. Submit content, get a `job_id`
back immediately, and receive the repurposed result at your callback URL when
processing completes.

> **Current status**: The enqueue and status-polling endpoints are live.
> Callback delivery and HMAC signing are scaffolded but pending the background
> worker implementation (see [Limitations](#limitations)).

---

## How It Works

```
┌──────────┐     POST /api/v1/webhook/repurpose      ┌──────────────┐
│  CLIENT  │  ───────────────────────────────────────  │  REPURPOSE   │
│          │      202 { job_id, status_url }            │     AI       │
│  (n8n /  │  ◀───────────────────────────────────────  │              │
│  Zapier  │                                            │              │
│  / Code) │     GET /api/v1/webhook/repurpose/status/{job_id} (poll loop)│              │
│          │  ────────────────────────────────────────  │              │
│          │      200 { status, result, ... }            │              │
│          │  ◀───────────────────────────────────────  │              │
│          │                                            │              │
│          │     POST callback_url (when done)           │              │
│          │  ◀───────────────────────────────────────  │  (future)    │
└──────────┘                                            └──────────────┘
```

Two endpoints, one workflow:

| Step | Endpoint | Description |
|------|----------|-------------|
| 1. Submit | `POST /api/v1/webhook/repurpose` | Enqueue content for async repurposing |
| 2. Poll | `GET /api/v1/webhook/repurpose/status/{job_id}` | Check progress until `completed`/`failed` |
| 3. (future) Callback | `POST` to your `callback_url` | Server pushes result when done |

### Job Lifecycle

```
pending ──► processing ──► completed
                  │
                  └──► failed
```

When the job reaches `completed`, the `result` field contains the repurposed
content map (`{format: text, ...}`).

---

## API Reference

### POST /api/v1/webhook/repurpose

**Request**

```json
{
  "content": {
    "title": "AI in Healthcare",
    "body": "AI is transforming diagnostics...",
    "source_format": "blog_post",
    "tags": ["ai", "healthcare"]
  },
  "target_formats": ["twitter_thread", "linkedin_post"],
  "callback_url": "https://your-service.com/webhook-receiver",
  "brand_voice": "professional",
  "custom_instructions": "Focus on actionable insights"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | object | yes | — | `{title, body, source_format, tags}` |
| `content.title` | string | yes | — | Content headline |
| `content.body` | string | yes | — | Main body text (max 100 KB) |
| `content.source_format` | string | yes | — | Format of source content |
| `content.tags` | string[] | no | `[]` | Tags for categorization |
| `target_formats` | string[] | yes | — | 1+ desired output formats |
| `callback_url` | string | yes | — | HTTPS callback destination |
| `brand_voice` | enum | no | `professional` | Tone preset |
| `custom_instructions` | string | no | null | Free-form processing hints |

**Header parameters**

| Header | Type | Description |
|--------|------|-------------|
| `Idempotency-Key` | string | UUID/string to prevent duplicate submissions |
| `Content-Type` | string | Must be `application/json` |

**Response** — 202 Accepted

```json
{
  "job_id": "b191d726-d45e-4690-a940-68e9270d59b6",
  "status_url": "/api/v1/webhook/repurpose/status/b191d726-d45e-4690-a940-68e9270d59b6"
}
```

### GET /api/v1/webhook/repurpose/status/{job_id}

**Response** — 200 OK

```json
{
  "job_id": "b191d726-d45e-4690-a940-68e9270d59b6",
  "status": "pending",
  "created_at": "2026-07-24T12:51:28.885531",
  "completed_at": null,
  "result": null,
  "error": null
}
```

**Error response** — 404 Not Found

```json
{
  "detail": "Job not found"
}
```

### Error Reference

| HTTP Status | Meaning | Common Causes |
|-------------|---------|---------------|
| `202` | Accepted | Job enqueued successfully |
| `200` | OK | Status retrieved |
| `404` | Not Found | Unknown `job_id` |
| `413` | Payload Too Large | Content body > 100 KB |
| `422` | Unprocessable Entity | Missing fields, invalid format/voice, blocked callback URL |

---

## Integration Examples

### Python (httpx)

```python
import httpx
import time
import uuid

BASE_URL = "https://repurposeai-production-d688.up.railway.app"


def submit_job() -> tuple[str, str]:
    """Submit content for async repurposing. Returns (job_id, status_url)."""
    payload = {
        "content": {
            "title": "AI in Healthcare",
            "body": "AI is transforming diagnostics across every major field.",
            "source_format": "blog_post",
            "tags": ["ai", "healthcare"],
        },
        "target_formats": ["twitter_thread", "linkedin_post"],
        "callback_url": "https://example.com/webhook-receiver",
        "brand_voice": "professional",
    }
    headers = {
        "Content-Type": "application/json",
        "Idempotency-Key": str(uuid.uuid4()),
    }
    resp = httpx.post(
        f"{BASE_URL}/api/v1/webhook/repurpose",
        json=payload,
        headers=headers,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["job_id"], data["status_url"]


def poll_status(job_id: str, timeout: int = 300, interval: int = 5) -> dict:
    """Poll job status until completed/failed or timeout."""
    start = time.monotonic()
    while True:
        resp = httpx.get(
            f"{BASE_URL}/api/v1/webhook/repurpose/status/{job_id}"
        )
        resp.raise_for_status()
        data = resp.json()
        if data["status"] in ("completed", "failed"):
            return data
        if time.monotonic() - start > timeout:
            raise TimeoutError(f"Job {job_id} did not finish within {timeout}s")
        time.sleep(interval)


# Example usage
job_id, status_url = submit_job()
print(f"Submitted job: {job_id}")
print(f"Status URL: {status_url}")

result = poll_status(job_id)
print(f"Final status: {result['status']}")
if result["status"] == "completed":
    print(f"Output: {result['result']}")
else:
    print(f"Error: {result['error']}")
```

### n8n Workflow

Create a workflow with these nodes:

**1. Manual Trigger** (or schedule/HTTP webhook trigger)

**2. HTTP Request node** — POST the repurpose job

- Method: `POST`
- URL: `https://repurposeai-production-d688.up.railway.app/api/v1/webhook/repurpose`
- Authentication: None (add API key header if configured)
- Headers:
  ```
  Content-Type: application/json
  Idempotency-Key: {{ $json.idempotencyKey || $json.id }}
  ```
- Body (JSON):
  ```json
  {
    "content": {
      "title": "{{ $json.contentTitle }}",
      "body": "{{ $json.contentBody }}",
      "source_format": "{{ $json.sourceFormat || 'blog_post' }}",
      "tags": {{ $json.tags || '[]' }}
    },
    "target_formats": {{ $json.targetFormats || '["twitter_thread"]' }},
    "callback_url": "{{ $json.callbackUrl || $env.WEBHOOK_RECEIVER_URL }}",
    "brand_voice": "{{ $json.brandVoice || 'professional' }}"
  }
  ```

**3. Wait node** — 5 seconds delay (optional, for polling rate limiting)

**4. HTTP Request node** — Poll status (loop back to this node via a "Loop Over Items" or "Split In Batches" pattern)

- Method: `GET`
- URL: `https://repurposeai-production-d688.up.railway.app/api/v1/webhook/repurpose/status/{{ $json.job_id }}`
- Send response as body: Yes

**5. IF node** — check status

- Condition: `{{ $json.status === 'completed' }}`
- If true: Output the result
- If false: Loop back to step 3 (Wait + poll again)

**6. (Optional) Callback receiver** — Create a separate n8n webhook workflow:

- Trigger: `Webhook` node listening at `/repurpose-callback`
- Expects POST with body `{job_id, status, result, ...}`
- Store result, send notification, etc.

**n8n JSON export snippet:**

```json
{
  "name": "RepurposeAI — Async Content",
  "nodes": [
    {
      "parameters": {},
      "name": "Manual Trigger",
      "type": "n8n-nodes-base.manualTrigger"
    },
    {
      "parameters": {
        "url": "https://repurposeai-production-d688.up.railway.app/api/v1/webhook/repurpose",
        "options": {},
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {"name": "content", "value": "={{ $json.content }}"},
            {"name": "target_formats", "value": "={{ $json.targetFormats }}"},
            {"name": "callback_url", "value": "={{ $json.callbackUrl }}"},
            {"name": "brand_voice", "value": "={{ $json.brandVoice || 'professional' }}"}
          ]
        }
      },
      "name": "Submit Repurpose Job",
      "type": "n8n-nodes-base.httpRequest"
    }
  ]
}
```

### Zapier Integration

Use the **Webhooks by Zapier** app:

**Trigger**: Any (Schedule, Form submission, RSS, etc.)

**Action 1 — Webhook POST (Submit Job)**

- App: `Webhooks by Zapier`
- Event: `POST`
- URL: `https://repurposeai-production-d688.up.railway.app/api/v1/webhook/repurpose`
- Headers:
  ```
  Content-Type: application/json
  ```
- Data:
  ```json
  {
    "content": {
      "title": "{{content_title}}",
      "body": "{{content_body}}",
      "source_format": "blog_post",
      "tags": []
    },
    "target_formats": ["twitter_thread", "linkedin_post"],
    "callback_url": "https://your-public-endpoint.com/repurpose-callback",
    "brand_voice": "professional"
  }
  ```

**Action 2 — Webhook GET (Poll Status)**

- App: `Webhooks by Zapier`
- Event: `GET`
- URL: `https://repurposeai-production-d688.up.railway.app/api/v1/webhook/repurpose/status/{{1.job_id}}`

Use **Delay by Zapier** (60 seconds) then loop back to Action 2, or use the
**Filter by Zapier** after Action 2 to check `status` and only proceed when
`completed` or `failed`.

> **Tip**: For Zapier, the simplest approach is to rely on the callback pattern
> — set up a Zap that receives the callback POST and processes the result, then
> have your enqueue action fire as a separate Zap.

### Make (formerly Integromat)

**Scenario structure:**

```
Trigger (Webhook / Schedule)
    │
    ▼
HTTP Module (POST — Submit Job)
    │
    ▼
Repeater (loop: wait 5s → GET status → check)
    │
    ▼
Router → [completed: Output result]
         → [failed: Error handling]
         → [pending/processing: Loop back]
```

**HTTP Module 1 — Submit Job:**

- URL: `https://repurposeai-production-d688.up.railway.app/api/v1/webhook/repurpose`
- Method: `POST`
- Headers:
  ```
  Content-Type: application/json
  ```
- Body type: `Raw` / `JSON`
- Body:
  ```json
  {
    "content": {
      "title": "AI in Healthcare",
      "body": "AI is transforming diagnostics.",
      "source_format": "blog_post",
      "tags": ["ai"]
    },
    "target_formats": ["twitter_thread"],
    "callback_url": "https://your-service.com/callback",
    "brand_voice": "professional"
  }
  ```

**HTTP Module 2 — Poll Status (inside a Repeater/Iterator):**

- URL: `https://repurposeai-production-d688.up.railway.app/api/v1/webhook/repurpose/status/{{1.job_id}}`
- Method: `GET`
- Store `status` in a variable.

**Filter:** Only continue when `status == "completed"` or `status == "failed"`.
Set the Repeater to a max of 60 iterations (5 min at 5s intervals).

---

## SSRF Protection

The webhook endpoint enforces strict callback URL validation:

| Check | Behaviour |
|-------|-----------|
| Scheme must be `https://` | `http://` URLs are rejected with 422 |
| No private IPs | `127.0.0.1`, `192.168.x.x`, `10.x.x.x` are blocked |
| No metadata endpoints | `169.254.169.254`, `metadata.google.internal` blocked |
| No dangerous schemes | `file://`, `ftp://`, `gopher://` blocked |
| DNS resolution | Host is resolved and checked before accepting |

All checks return **422 Unprocessable Entity** with a descriptive message.

---

## Idempotency

Pass an `Idempotency-Key` header to prevent duplicate submissions if the
request is retried (e.g., due to network failure). The same key within a
time window returns the existing `job_id` instead of creating a new job.

> **Note**: Idempotency deduplication is scaffolded at the model level
> (`idempotency_key` field on `WebhookRepurposeRequest`) but not yet
> implemented in the handler. It will return 202 and create a new job
> regardless for now.

---

## Limitations

| Area | Status | Detail |
|------|--------|--------|
| Background processing | Not yet implemented | Jobs stay `pending`; no worker processes them yet |
| Callback delivery | Scaffolded | `POST` to callback_url when job completes (future) |
| HMAC signing | Scaffolded | `X-Signature-256` header on callbacks (future) |
| Idempotency | Scaffolded | Deduplication via `Idempotency-Key` (future) |
| Rate limiting | Not yet implemented | No per-user or per-IP limits currently |
| Retry on callback failure | Design phase | 3 retries with exponential backoff (future) |

---

## Testing

```python
import httpx

BASE = "https://repurposeai-production-d688.up.railway.app"


def test_connection():
    """Verify the API is reachable."""
    resp = httpx.get(f"{BASE}/health")
    assert resp.status_code == 200
    print("API is healthy:", resp.json())


def test_submit_and_poll():
    """Submit a webhook job and verify status polling works."""
    # Submit
    payload = {
        "content": {
            "title": "Test",
            "body": "Test content body for quick verification.",
            "source_format": "blog_post",
        },
        "target_formats": ["twitter_thread"],
        "callback_url": "https://example.com/verify",
        "brand_voice": "professional",
    }
    resp = httpx.post(f"{BASE}/api/v1/webhook/repurpose", json=payload)
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # Poll
    resp = httpx.get(f"{BASE}/api/v1/webhook/repurpose/status/{job_id}")
    assert resp.status_code == 200
    status = resp.json()
    assert status["status"] == "pending"
    assert status["job_id"] == job_id
    print(f"Job {job_id} is {status['status']}")


def test_ssrf_blocked():
    """Verify SSRF protection blocks non-HTTPS callbacks."""
    payload = {
        "content": {
            "title": "T",
            "body": "B",
            "source_format": "blog_post",
        },
        "target_formats": ["twitter_thread"],
        "callback_url": "http://localhost:8000/evil",
    }
    resp = httpx.post(f"{BASE}/api/v1/webhook/repurpose", json=payload)
    assert resp.status_code == 422
    print(f"SSRF blocked correctly: {resp.json()['detail']}")


if __name__ == "__main__":
    test_connection()
    test_submit_and_poll()
    test_ssrf_blocked()
    print("All integration smoke tests passed.")
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-07-24 | Initial webhook endpoints (`POST /api/v1/webhook/repurpose`, `GET /api/v1/webhook/repurpose/status/{job_id}`) added |
