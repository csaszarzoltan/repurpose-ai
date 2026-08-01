# RepurposeAI Next-Version Product, UX, and Software Requirements Report

**Source reviewed:** `ZipPrompt.md`, treated as an expanded ZIP archive containing the Python application, documentation, examples, tests, configuration, changelog, and prior analysis materials.  
**Analysis date:** 2026-08-01  
**Current represented version:** v1.1.0  
**Method:** Evidence-led product and UX review. Statements are labeled **Observed**, **Inferred**, or **Unverified/Conflicting** where appropriate.

## Executive summary

RepurposeAI is evolving from an API-first content repurposing backend into a lightweight browser workspace. Version 1.1.0 now supports durable, owner-scoped projects, versioned generated variants, approval and copy actions, visible LLM fallback modes, and reusable recipes. These additions address the most frequent creation loop better than earlier versions.

The application still has a split product reality. The **project-generation-review** journey is increasingly coherent and durable, while publishing, workflows, jobs, credentials, analytics, and exports remain fragmented, often API-only, and in several cases scaffolded or stored in memory. The highest-value next step is therefore not more formats or providers. It is to connect the current workspace to a trustworthy **create → review → approve → schedule/publish → measure** lifecycle with durable state, user-centered recovery, secure connection management, and honest capability reporting.

The recommended next release should prioritize: a unified content workspace, autosave and selective regeneration, an attention-oriented home view, durable job execution, safe platform preview and approval, secure persistent connections, local-time scheduling, and removal or explicit labeling of mock/stub analytics.

---

## 1. Product understanding

### What the application appears to do

**Observed:** RepurposeAI is a Python 3.11+ FastAPI application for turning a source item into platform-specific content. It supports 20 formats, OpenRouter/OpenAI/Anthropic routing, brand-voice guidance, projects, generated variants, recipes, batch processing, workflow automation, publishing to LinkedIn, Twitter/X and Medium, authentication, API keys, subscriptions, analytics, validation, trends, and export APIs.

**Observed:** Version 1.1.0 includes a responsive workspace at `/`. A user can create and resume projects, choose output formats, generate drafts, inspect variants, save revisions non-destructively, approve content, copy results, archive projects, and save or apply owner-scoped recipes. Project and variant data use SQLite in WAL mode; production workspace access is JWT protected.

**Observed:** Generation exposes three modes:

- `llm`: a configured provider generated the result without warnings.
- `template_fallback`: no provider was configured.
- `llm_fallback`: a provider was configured but generation degraded to fallback output.

This is an important trust feature because degraded output is not silently represented as normal AI output.

**Observed:** Other major domains remain less mature. Workflow and execution state, publishing credentials, some job state, subscriptions, and analytics repositories are described as in-memory in accompanying materials. Analytics includes mock/sample data and no-op or scaffolded persistence. PDF export returns a path stub rather than a verified report. Documentation contains contradictory statements about webhook workers, callback delivery, HMAC, idempotency, and scheduler behavior.

### Likely users

1. **Individual creators and consultants**  
   **Inferred:** They want to turn one article, transcript, release, or idea into a small, repeated set of channel-ready outputs while preserving their voice.

2. **Content marketers and social media operators**  
   **Inferred:** They work in batches, review unevenly, schedule content, reuse recipes, monitor failures, and need a clear queue of what requires attention.

3. **Small teams and agencies**  
   **Inferred:** They need client/workspace separation, approval states, reviewer accountability, shared recipes, secure platform connections, and traceable publication history.

4. **Developers and automation specialists**  
   **Observed:** They use REST endpoints, API keys, webhooks, workflows, n8n/Zapier/Make patterns, batch requests, and provider controls. The API remains strongest for this segment.

5. **Workspace owners or administrators**  
   **Inferred:** They manage connections, credentials, API keys, usage, billing, data retention, team access, and operational health.

### Main workflows and usage scenarios

#### A. Create and save a content project

1. Enter title and source body.
2. Choose target formats.
3. Set brand voice and optional guidance.
4. Save the project.
5. Reopen it from recent projects or search.

**Current quality:** This is the most productized flow. It is durable, accessible, and supports explicit empty/loading/success/error states.

#### B. Generate, review, revise, and approve variants

1. Generate one version per selected format.
2. View current variants or history.
3. Edit a variant.
4. Save a revision as a new version.
5. Approve and copy the selected output.

**Current quality:** Directionally strong. Non-destructive revisions and visible fallback modes reduce trust risks. The experience still needs autosave, compare/restore, selective regeneration, publish readiness, and stronger multi-variant navigation.

#### C. Reuse a recipe

1. Save formats, brand voice, and guidance as a recipe.
2. Apply it to the current form or create a project from it.
3. Edit the recipe without changing historical projects.

**Current quality:** High-value and aligned with repeated user behavior. Missing capabilities include favorites/defaults, duplication, sharing, recipe performance history, and clearer distinction between applying a recipe and modifying it.

#### D. Batch repurpose

1. Build a JSON array of up to 50 jobs.
2. Set concurrency.
3. Submit the jobs.
4. Inspect result and error arrays.

**Current quality:** Useful backend capability, but not a user workflow. There is no CSV import, field mapping, row preview, per-row repair, progress UI, or retry-only-failed action.

#### E. Workflow automation

1. Define manual, schedule, or webhook trigger configuration.
2. Add sequential `repurpose`, `webhook`, or `wait` steps.
3. Configure retry behavior.
4. Trigger or wait for execution.
5. Inspect job/execution status.

**Current quality:** Suitable for technical users. Raw JSON, cron, step IDs, payload mapping, and retry semantics create excessive cognitive load for content operators. Durability and documentation consistency are not yet sufficient for production reliance.

#### F. Connect a platform and publish

1. Begin OAuth or enter a Medium token.
2. Store credentials.
3. Build a platform-specific request.
4. Optionally dry-run.
5. Publish and poll job status.

**Current quality:** Dry-run and retry concepts are valuable. However, credential storage, tenant authorization, token health, platform previews, approval, and partial-failure recovery are not presented as one safe end-user flow.

#### G. Analyze and export

1. Query posts or summaries.
2. Calculate an optimization score.
3. Compare generated and published text.
4. View trends and top content.
5. Export or schedule reports.

**Current quality:** Conceptually valuable but not trustworthy as a user-facing product because several services return samples, stubs, or in-memory results and there is no complete analytics UI.

---

## 2. UI/UX analysis

### Strengths

- **A real workspace now exists.** The product no longer relies only on Swagger for its primary creation journey.
- **The core workspace is task-oriented.** Projects, variants, recipes, and review actions reflect how users actually repeat content work.
- **Non-destructive versioning is a strong trust pattern.** Saving a revision creates history rather than overwriting prior work.
- **Fallback disclosure is unusually honest.** `template_fallback` and `llm_fallback` reduce the risk of users mistaking degraded output for normal generation.
- **Recipes reduce repeated setup.** They directly address stable user habits around formats, voice, and guidance.
- **Accessibility foundations are present.** Semantic regions, labels, skip navigation, keyboard focus, reduced-motion support, ARIA live feedback, and non-color status cues are represented in tests and implementation notes.
- **Archive is safer than destructive deletion.** It protects against accidental loss.
- **Client/server validation preserves unsaved input.** This supports recovery rather than punishment.
- **Privacy-safe telemetry is intentionally constrained.** Content, titles, prompts, credentials, and secrets are rejected.
- **Dry-run publishing is a good safety primitive.** It can become a valuable user-facing preflight step.

### Weaknesses

#### The product shell is incomplete

The root workspace covers the create/review area, while publishing, analytics, workflows, account settings, connections, jobs, and billing remain separate API domains. Users do not have a single navigation model or lifecycle view.

#### The lifecycle is not continuous

The workspace does not yet make the following relationship obvious:

`source → generated variant → reviewed version → approval → publish payload → platform post → metrics`

Users must mentally connect identifiers across services. This increases error risk and weakens the sense that the product remembers their work.

#### Variant review is functional but not yet efficient

Likely gaps include autosave, side-by-side source reference, format switching that preserves cursor state, version comparison, restore, selective regeneration, publish-readiness checks, and a clear summary of which outputs are approved.

#### Technical concepts remain too visible outside the workspace

Provider headers, model names, routing strategy, raw format IDs, cron expressions, callback URLs, HMAC, concurrency, step IDs, and JSON payloads are appropriate for developer mode, not for ordinary content creation.

#### Outcome visibility is weak

Users need quick answers to:

- What is waiting for me?
- What failed?
- Which output is approved?
- What is scheduled next?
- Which connection needs attention?
- Which publication was partial?
- Is the displayed metric live, stale, or demo data?

The current API status endpoints do not create this attention-oriented experience.

### Confusing elements

- **Conflicting documentation:** webhook guides say processing/callbacks are pending, while later changelog entries describe job processing and retries as implemented.
- **Mixed persistence:** projects/variants/recipes are durable, but workflows, credentials, jobs, and analytics are often in memory. Users cannot easily predict what survives restart.
- **“Analytics Dashboard” naming:** the supplied product primarily contains analytics APIs and sample/scaffold services rather than a finished dashboard.
- **False completion risk:** a PDF export may report completion while only returning a stub file path.
- **Score semantics:** “algorithm readiness” suggests predictive certainty that the deterministic formula and limited signals do not substantiate.
- **Authentication inconsistency:** analytics, jobs, workflow, and credential routes are documented with inconsistent or absent access control.
- **Degraded generation remains usable:** visible labeling is good, but fallback content should not flow into auto-publish without explicit acknowledgement.
- **Test/version history is noisy:** multiple historical test counts and capability claims make it harder to know the exact release truth.

### Friction points

#### High-frequency friction

- Reopening and understanding the current project state.
- Switching among multiple variants while maintaining context.
- Re-entering or rediscovering preferred configuration when a recipe is not yet saved.
- Copying approved outputs into external publishing tools.
- Polling job status and tracking IDs.
- Rebuilding batch and workflow payloads.
- Translating human schedules into UTC cron.
- Reconnecting platform credentials after restart.

#### High-risk friction

- Publishing without a final-payload, platform-like preview.
- A thread failing after some posts have already been published.
- Expired credentials being discovered only during publication.
- Mock analytics looking operational.
- Fallback content being treated as high-quality generated content.
- Unauthorized access to analytics, jobs, credentials, or workflow state.

### Navigation and workflow recommendation

Recommended top-level navigation:

- **Home:** approvals needed, active jobs, failures, upcoming publications, connection alerts.
- **Create:** source, goal, format selection, generation.
- **Content:** projects, variants, status, tags, campaigns, archive.
- **Calendar:** scheduled, published, partial, and failed posts.
- **Automations:** recipes, workflows, batch imports, run history.
- **Analytics:** real metrics, comparisons, validation and recommendations.
- **Connections:** platforms and LLM/provider health.
- **Settings:** brand voice, team, API keys, usage, billing, privacy.

This structure follows user goals instead of backend route groupings.

---

## 3. User behavior analysis

### Likely user habits

1. **Repeat a small set of transformations.** Most users will favor two to five formats rather than browse all 20 on every run.
2. **Create in bursts and review later.** Users often generate multiple items, then return for editing, approval, and scheduling.
3. **Review before publishing.** Hooks, claims, names, links, tone, media, and length require human verification.
4. **Edit variants unevenly.** A LinkedIn post may be refined heavily while a show-notes variant is accepted quickly.
5. **Reuse successful patterns.** Users expect recent selections, favorite recipes, duplication, and “run again with new source.”
6. **Monitor exceptions, not every success.** Experienced users want a queue of failures, expired credentials, and approvals rather than constant polling.
7. **Learn from outcomes.** Once publishing and metrics are connected, users expect successful formats and edits to influence later recommendations.

### Repeated actions

- Paste or import source content.
- Select the same formats.
- Apply a familiar voice and instructions.
- Generate, scan, edit, copy, approve, or regenerate.
- Validate channel constraints.
- Schedule or publish.
- Check failures and retry.
- Duplicate prior work.
- Report performance to stakeholders.

### Likely pain points

- No consolidated home/attention view.
- No autosave assurance during editing.
- No selective text regeneration or version comparison.
- No obvious publish-readiness signal per variant.
- No safe team approval workflow.
- No persistent connection-health model.
- No local-time scheduling UI.
- No retry-only-failed experience for batch/workflow work.
- No real analytics provenance or freshness display.
- No import flow for URL, file, RSS, or transcript.
- No visible cost, quota, or expected processing impact before large jobs.

### Usage bottlenecks

- **Onboarding:** configuration and provider concepts can precede first value.
- **Review:** multiple formats need a stronger editor and comparison model.
- **Publishing:** content readiness and connection readiness are separated.
- **Automation:** JSON authoring limits adoption to technical users.
- **Recovery:** errors lack a consistent next-best action.
- **Learning:** analytics is not yet real, linked, explainable, or actionable.
- **Trust:** inconsistent persistence and documentation make operational behavior unpredictable.

### Expected but missing interactions

- Autosave with visible “Saved” state.
- Compare and restore versions.
- Regenerate a selection, section, or single format only.
- Favorite/pin recipes and formats.
- Duplicate project with fresh publication state.
- Import from file, URL, RSS, or transcript.
- Final-payload platform preview.
- Approve, reject, comment, and assign reviewer.
- Retry the failed item or failed step only.
- Connection expiry warnings and one-click reconnect.
- Human-readable schedules with next-run preview.
- In-app/email/webhook notifications.
- Real downloadable exports.
- Metric definitions, provenance, freshness, and recommended action.

---

## 4. What should be improved

### Critical improvements

1. **Unify the content lifecycle.** Link project, variant version, approval, publication, and metrics as one traceable object graph.
2. **Add an attention-oriented Home.** Show active work, approvals, failures, upcoming posts, and connection problems.
3. **Complete the review workspace.** Add autosave, compare/restore, selective regeneration, publish readiness, and efficient variant switching.
4. **Make jobs durable.** Generation, batch, workflow, export, publish, and metric collection must survive restart and support idempotent recovery.
5. **Secure every tenant-owned domain.** Analytics, jobs, workflows, exports, credentials, subscriptions, and content must have consistent authentication and authorization.
6. **Create a safe publish flow.** Persistent encrypted connections, platform validation, final-payload previews, approval, local-time scheduling, and partial-failure recovery are essential.
7. **Remove false product claims.** Mock/sample analytics and PDF stubs must be disabled, clearly labeled, or isolated in demo mode.
8. **Standardize status and errors.** Each failed state needs a user-readable reason, retryability, and direct recovery action.
9. **Prevent unsafe degraded automation.** Fallback output must require explicit review before scheduling or auto-publishing.
10. **Reconcile documentation and capability metadata.** Release claims should be generated or validated against operational capabilities.

### Medium-priority improvements

- Visual workflow builder and test runs.
- Batch CSV import, mapping, preview, and repair.
- Calendar and human-readable recurrence.
- Shared/team recipes and lightweight approvals.
- Notifications and activity history.
- Brand voice builder with examples, preferred/banned terms, and preview.
- Usage, quota, provider, and cost visibility.
- Search, tags, campaigns, filters, and bulk actions.
- Real analytics ingestion and explainable recommendations.
- Real CSV/PDF export and scheduled delivery.

### Nice-to-have improvements

- Keyboard shortcuts and command palette.
- Mobile-first approval view.
- A/B hook or variant experiments.
- Drag-and-drop calendar rescheduling.
- Shared report layouts.
- Additional publishing platforms only after current adapters are trustworthy.

---

## 5. Requirements

### BR-001: Complete content value loop

- **Type:** Business
- **Description:** The product shall support a continuous source → generate → review → approve → schedule/publish → measure lifecycle without manual transfer of IDs or payloads.
- **User value:** Users complete their actual job in one product.
- **Priority:** Must have
- **Rationale:** The creation workspace is coherent, but downstream capabilities remain fragmented.
- **Acceptance criteria:**
  - Every variant references its project, source version, generation job, approval state, publication record, and metrics where applicable.
  - The UI shows current lifecycle state and the next valid action.
  - A user can move from saved source to scheduled/published content without using Swagger or copying JSON.

### BR-002: Truthful production capability

- **Type:** Business
- **Description:** User-facing claims and statuses shall distinguish live, unavailable, degraded, demo, stale, and scaffolded capabilities.
- **User value:** Users can trust outcomes and make informed decisions.
- **Priority:** Must have
- **Rationale:** Analytics samples, PDF stubs, and conflicting documentation create false confidence.
- **Acceptance criteria:**
  - Non-demo tenants never receive sample business data.
  - Stub features are hidden or labeled unavailable.
  - `/health` exposes a versioned capability manifest.
  - Release validation fails when documentation claims an unavailable feature.

### BR-003: Reduce repeated configuration

- **Type:** Business
- **Description:** The product shall minimize repeated choices through recipes, recent selections, favorites, defaults, and duplication.
- **User value:** Frequent work becomes faster and more consistent.
- **Priority:** Should have
- **Rationale:** v1.1.0 recipes validate that repeated configuration is a core behavior.
- **Acceptance criteria:**
  - Users can pin a default recipe and favorite formats.
  - “Create similar” preserves settings but clears publication state.
  - Recipe edits never alter historical projects.

### UR-001: Guided first value

- **Type:** User
- **Description:** A new user shall generate a useful first variant without understanding providers, model names, API keys, format IDs, or routing strategies.
- **User value:** Lower cognitive load and faster activation.
- **Priority:** Must have
- **Rationale:** Technical configuration should not precede product value.
- **Acceptance criteria:**
  - The default flow asks for source, goal, desired channels, and voice in plain language.
  - Model/provider settings are automatic and placed under Advanced.
  - A first draft can be created without platform connection or API-key creation.

### UR-002: Persistent, searchable workspace

- **Type:** User
- **Description:** Users shall save, reopen, search, filter, and continue projects and variants across sessions.
- **User value:** Work is never lost and remains easy to find.
- **Priority:** Must have
- **Rationale:** Current project persistence is strong but navigation and lifecycle filtering are incomplete.
- **Acceptance criteria:**
  - Source and edits autosave and survive restart/logout.
  - Search covers title and tags without exposing content to telemetry.
  - Filters include status, format, platform, date, recipe, and archive.
  - Opening a project restores source, current variant, edits, history, and status.

### UR-003: Efficient review and selective regeneration

- **Type:** User
- **Description:** Users shall edit, compare, restore, approve, reject, and selectively regenerate without losing accepted work.
- **User value:** Faster refinement and lower overwrite risk.
- **Priority:** Must have
- **Rationale:** Users rarely accept all variants unchanged.
- **Acceptance criteria:**
  - Each variant has independent lifecycle status.
  - Users can compare any two versions and restore a prior version.
  - Regeneration supports current format, selected text, or full project.
  - Manual edits are never overwritten without an explicit choice.

### UR-004: Attention and progress management

- **Type:** User
- **Description:** Users shall see active, completed, blocked, partial, and failed work in one place with clear next actions.
- **User value:** Eliminates manual polling and lost jobs.
- **Priority:** Must have
- **Rationale:** Asynchronous operations are central to the product.
- **Acceptance criteria:**
  - Home displays processing jobs, approvals needed, failures, upcoming posts, and connection alerts.
  - Each failure offers a relevant action such as Edit, Retry, Reconnect, or View details.
  - Duplicate submissions are prevented or idempotent.

### UR-005: Safe publishing control

- **Type:** User
- **Description:** Users shall preview and approve channel-valid content before live publication unless an explicit, auditable auto-publish rule exists.
- **User value:** Prevents reputational and formatting mistakes.
- **Priority:** Must have
- **Rationale:** Publishing is externally visible and sometimes irreversible.
- **Acceptance criteria:**
  - Preview shows the exact final payload, including thread segmentation, title, links, media, visibility, and truncation.
  - Hard validation errors block publish; warnings require acknowledgement.
  - Dry-run, scheduled, published, partial, and failed states are visually distinct.
  - Auto-publish rules record who enabled them and what conditions apply.

### UR-006: Reusable brand voice

- **Type:** User
- **Description:** Users shall define voice using traits, examples, preferred terms, banned terms, and do/don’t rules, then preview its effect.
- **User value:** More consistent output with less repetitive prompting.
- **Priority:** Should have
- **Rationale:** Current presets and instructions are useful but underspecified.
- **Acceptance criteria:**
  - Voice setup accepts structured rules and examples.
  - Users can test voice on sample text before saving.
  - Each generation records the applied voice and overrides.

### FR-001: Canonical durable domain model

- **Type:** Functional
- **Description:** Persist tenant-scoped projects, sources, variants, versions, approvals, jobs, workflows, executions, connections, schedules, publications, metrics, exports, recipes, and audit events.
- **User value:** Reliable history and continuity across the full lifecycle.
- **Priority:** Must have
- **Rationale:** Persistence is currently uneven across domains.
- **Acceptance criteria:**
  - Restarting services does not lose committed data or accepted jobs.
  - Every query is tenant scoped.
  - Cross-tenant access tests cover every domain object.
  - Schema migrations are versioned and tested.

### FR-002: Consistent authorization

- **Type:** Functional
- **Description:** Require authenticated and authorized access for all tenant-owned resources, with explicit public exceptions only.
- **User value:** Protects content, credentials, metrics, and external publishing authority.
- **Priority:** Must have
- **Rationale:** Current documentation shows inconsistent protection.
- **Acceptance criteria:**
  - Anonymous access to protected endpoints returns 401.
  - Cross-tenant access returns 403 or 404 according to policy.
  - API-key scopes are enforced per operation.
  - Secret values are never returned by list/read endpoints.

### FR-003: Durable job execution and idempotency

- **Type:** Functional
- **Description:** Run generation, batch, workflow, publish, export, webhook, and metric collection through a durable worker model.
- **User value:** Jobs finish reliably and can recover after interruption.
- **Priority:** Must have
- **Rationale:** Polling and in-memory job state are fragile.
- **Acceptance criteria:**
  - Jobs are persisted before a 202 response.
  - Interrupted work resumes or safely retries after restart.
  - Idempotency returns the original job for duplicate semantic requests within policy.
  - Every state transition is validated, timestamped, and auditable.

### FR-004: Actionable error recovery

- **Type:** Functional
- **Description:** Every failed job or step shall include a stable error code, sanitized explanation, retryability, and recovery actions.
- **User value:** Users can recover without reconstructing requests.
- **Priority:** Must have
- **Rationale:** API error text alone is insufficient for daily operations.
- **Acceptance criteria:**
  - Failed batch items can be retried without successful items.
  - Safe workflows can resume from the failed step.
  - Partial thread publication records completed and remaining segments.
  - Provider/platform errors map to clear user actions.

### FR-005: Secure connection lifecycle

- **Type:** Functional
- **Description:** Platform credentials shall be tenant scoped, encrypted, persistent, health checked, refreshable, revocable, and never exposed.
- **User value:** Reliable and safe publishing.
- **Priority:** Must have
- **Rationale:** In-memory credentials and unclear protection undermine production use.
- **Acceptance criteria:**
  - Secrets are encrypted at rest and redacted in logs and responses.
  - Status includes Connected, Action required, Expired, and Revoked.
  - OAuth state/PKCE are validated and single-use.
  - Refresh failures create a reconnect task and notification.

### FR-006: Platform validation and preview

- **Type:** Functional
- **Description:** Validate variants against versioned platform capabilities and preview the final publish payload.
- **User value:** Reduces malformed or surprising posts.
- **Priority:** Must have
- **Rationale:** Existing format metadata is not enough for safe publication.
- **Acceptance criteria:**
  - Rules cover required fields, length, threads, links, media, visibility, and publish status.
  - Preview uses the exact outgoing payload.
  - Capability rules are adapter-versioned and contract tested.

### FR-007: Local-time scheduling

- **Type:** Functional
- **Description:** Users shall schedule by named timezone, date/time, or human-readable recurrence without writing cron.
- **User value:** Fewer timing mistakes.
- **Priority:** Must have
- **Rationale:** Users think in local dates and weekdays, not UTC cron.
- **Acceptance criteria:**
  - The UI displays the next five runs before saving.
  - DST follows the selected timezone policy.
  - Schedule records last run, next run, and last result.
  - Duplicate firing is prevented.

### FR-008: Controlled degraded generation

- **Type:** Functional
- **Description:** Fallback output shall be clearly identified and prevented from unattended publication by default.
- **User value:** Users do not unknowingly publish low-confidence output.
- **Priority:** Must have
- **Rationale:** v1.1.0 labels fallback correctly, but automation policy must enforce the warning.
- **Acceptance criteria:**
  - Fallback mode is stored on every variant version.
  - Fallback output requires explicit review before schedule/publish.
  - The UI explains why fallback occurred and offers retry/change-provider actions.

### FR-009: Visual workflow authoring

- **Type:** Functional
- **Description:** Provide schema-driven forms for triggers and steps, variable mapping, validation, test runs, and step-level history.
- **User value:** Nontechnical operators can automate repeated work.
- **Priority:** Should have
- **Rationale:** Raw JSON and cron are adoption barriers.
- **Acceptance criteria:**
  - Users can add, reorder, duplicate, configure, and remove steps without JSON.
  - Missing inputs and incompatible mappings block activation.
  - Test runs do not activate schedules or publish live content.
  - Run history shows inputs, outputs, attempts, duration, and errors with secrets redacted.

### FR-010: Batch import and repair

- **Type:** Functional
- **Description:** Support CSV/structured import with mapping, validation preview, per-row status, and retry-only-failed.
- **User value:** Makes burst work practical.
- **Priority:** Should have
- **Rationale:** The batch API exists, but users cannot operate it efficiently.
- **Acceptance criteria:**
  - Users map source columns before submission.
  - Invalid rows can be corrected without re-uploading valid rows.
  - Progress and per-row results are visible.
  - Retrying failed rows does not duplicate successful outputs.

### FR-011: Real analytics with provenance

- **Type:** Functional
- **Description:** Collect real platform metrics, preserve raw provenance, and distinguish missing, zero, stale, partial, and unavailable values.
- **User value:** Decisions are based on trustworthy data.
- **Priority:** Must have
- **Rationale:** Current analytics contains mock/sample/scaffold behavior.
- **Acceptance criteria:**
  - Non-demo tenants never receive sample points.
  - Each metric records source, platform timestamp, collection time, and mapping version.
  - Missing values are not converted to zero.
  - Data freshness and collection errors are visible.

### FR-012: Explainable recommendations

- **Type:** Functional
- **Description:** Scores and recommendations shall show contributing signals, method/version, limitations, comparison context, and actionable next step.
- **User value:** Users understand what to change and why.
- **Priority:** Should have
- **Rationale:** A single “algorithm readiness” score overstates certainty.
- **Acceptance criteria:**
  - Heuristic, observed, and LLM-judged results are labeled separately.
  - Recommendations are withheld when data is insufficient.
  - Users can navigate from a recommendation to the affected variant.
  - Formula and adapter versions are retained for reproducibility.

### FR-013: Real export and scheduled delivery

- **Type:** Functional
- **Description:** Generate valid CSV/PDF artifacts from tenant data and securely deliver or download them.
- **User value:** Stakeholders receive usable reports.
- **Priority:** Should have
- **Rationale:** PDF behavior is currently a stub.
- **Acceptance criteria:**
  - Completed export includes an authenticated expiring URL.
  - PDF opens successfully and contains requested filters/date range.
  - Empty exports state that no data matched.
  - Scheduled delivery records recipient, timezone, attempts, last/next delivery.

### FR-014: Notifications

- **Type:** Functional
- **Description:** Provide configurable in-app, email, and webhook notifications for completion, failure, approval, credential expiry, and publishing outcomes.
- **User value:** Users do not need to poll.
- **Priority:** Should have
- **Rationale:** The product is highly asynchronous.
- **Acceptance criteria:**
  - Preferences are configurable by event and channel.
  - Notifications deep-link to the affected object and action.
  - Duplicate notifications are suppressed.
  - Delivery attempts are auditable.

### FR-015: Usage and cost visibility

- **Type:** Functional
- **Description:** Show plan limits, remaining usage, actual provider/model, fallback path, and estimated batch impact.
- **User value:** Users can plan work and understand consumption.
- **Priority:** Should have
- **Rationale:** Free/Pro tiers and multiple providers exist, but their practical impact is opaque.
- **Acceptance criteria:**
  - Usage is updated atomically for billable success.
  - Large jobs show estimated consumption before submission.
  - Quota errors show reset time and recovery options.
  - Generation records actual provider/model and fallback chain.

### NFR-001: Reliability and recovery

- **Type:** Non-functional
- **Description:** Committed user data and accepted work shall survive process, worker, and host restarts.
- **User value:** Professional trust.
- **Priority:** Must have
- **Rationale:** Several current stores are in memory.
- **Acceptance criteria:**
  - Controlled restart tests show no committed data loss.
  - Worker interruption and duplicate-delivery scenarios are tested.
  - Recovery objectives are documented and monitored.

### NFR-002: Security and privacy

- **Type:** Non-functional
- **Description:** Apply least privilege, encryption, secure OAuth/webhooks, tenant isolation, secret redaction, and auditability.
- **User value:** Protects unpublished content and publishing authority.
- **Priority:** Must have
- **Rationale:** The application handles sensitive drafts and external account access.
- **Acceptance criteria:**
  - Secrets never enter telemetry, logs, URLs, or list responses.
  - Webhooks are signed, replay protected, and use stable event IDs.
  - SSRF checks cover DNS resolution and redirects.
  - Security tests cover authorization, HMAC, OAuth state, PKCE, refresh, and replay.

### NFR-003: Responsive performance

- **Type:** Non-functional
- **Description:** Interactive pages shall remain responsive while long operations run asynchronously.
- **User value:** The product feels fast even when generation is slow.
- **Priority:** Must have
- **Rationale:** LLM, publish, and export work can take seconds or minutes.
- **Acceptance criteria:**
  - Job submission quickly returns a durable ID.
  - UI acknowledgement appears within one second.
  - Lists use bounded pagination/cursors.
  - Page/API p95 targets are defined for expected load.

### NFR-004: Accessibility

- **Type:** Non-functional
- **Description:** Core web flows shall meet WCAG 2.2 AA.
- **User value:** Inclusive creation, review, scheduling, and approval.
- **Priority:** Must have
- **Rationale:** Existing semantic foundations should be preserved as scope grows.
- **Acceptance criteria:**
  - Keyboard-only completion of core flows.
  - Visible focus, labels, error association, sufficient contrast, and non-color status cues.
  - Automated checks plus manual screen-reader testing before release.

### NFR-005: Observability

- **Type:** Non-functional
- **Description:** Provide structured logs, traces, metrics, durable events, and correlation IDs across API, workers, LLMs, platforms, exports, and webhooks.
- **User value:** Faster diagnosis and accurate status.
- **Priority:** Must have
- **Rationale:** Distributed asynchronous work is otherwise opaque.
- **Acceptance criteria:**
  - Every job has a correlation ID and auditable event history.
  - Monitor queue delay, stale jobs, retries, provider failures, publish failures, and connection health.
  - User-visible status derives from the same durable event record used by support.

### UX-001: Goal-first create flow

- **Type:** UX/UI
- **Description:** Organize creation around goals and channels, not enums and backend parameters.
- **User value:** Faster selection and less choice overload.
- **Priority:** Must have
- **Rationale:** Twenty formats are difficult to scan as a flat technical list.
- **Acceptance criteria:**
  - Group formats into Social, Long-form, Email, Video/Audio, Sales, and Product.
  - Show purpose, expected output, audience, and favorite/recent status.
  - Recommend a small set without hiding the full catalog.
  - Advanced provider controls are collapsed by default.

### UX-002: Multi-variant review workspace

- **Type:** UX/UI
- **Description:** Display source and variants in a workspace optimized for scanning, editing, comparison, and status changes.
- **User value:** Less copying and context switching.
- **Priority:** Must have
- **Rationale:** Comparing several outputs is the core daily task.
- **Acceptance criteria:**
  - Switching variants preserves edits and cursor position.
  - Autosave state is visible.
  - Each variant shows format, version, approval, validation, generation mode, and publication state.
  - Copy/export feedback is non-disruptive and accessible.

### UX-003: Progressive disclosure

- **Type:** UX/UI
- **Description:** Hide provider, model, routing, concurrency, retry, webhook, cron, and raw payload controls from the default path.
- **User value:** Reduced cognitive load without removing expert capability.
- **Priority:** Must have
- **Rationale:** The API exposes implementation details ordinary users do not need.
- **Acceptance criteria:**
  - The default path shows only required decisions.
  - Advanced settings explain consequences and use safe defaults.
  - Developer mode can expose payload and technical controls.

### UX-004: Clear status and feedback

- **Type:** UX/UI
- **Description:** Every asynchronous or external action shall provide immediate acknowledgement, stage/status, next step, and terminal feedback.
- **User value:** Confidence and fewer repeated clicks.
- **Priority:** Must have
- **Rationale:** Manual polling is a major source of friction.
- **Acceptance criteria:**
  - Submission creates a visible job card immediately.
  - Known stages are shown instead of generic waiting.
  - Success messages say what happened and where the result is.
  - Status remains available after navigation or restart.

### UX-005: Recovery-centered errors

- **Type:** UX/UI
- **Description:** Errors shall preserve work, explain the cause in plain language, and present the best recovery action.
- **User value:** Faster self-service recovery.
- **Priority:** Must have
- **Rationale:** Raw errors do not support end-to-end tasks.
- **Acceptance criteria:**
  - Field errors appear beside fields and in a summary.
  - Source and manual edits are never lost.
  - Reconnect, Retry, Edit, Change provider, and View details are context sensitive.
  - Technical details are optional and sanitized.

### UX-006: Connected-account control center

- **Type:** UX/UI
- **Description:** Manage all publishing connections in one place with identity, capabilities, scopes, health, expiry, and recovery.
- **User value:** Confidence before scheduling or publishing.
- **Priority:** Must have
- **Rationale:** Current credentials are separate API operations.
- **Acceptance criteria:**
  - Each connection shows account identity, supported actions, status, last success, and expiry when known.
  - Connect/reconnect returns the user to their interrupted task.
  - Revocation explains impact on schedules.

### DI-001: Canonical content lineage

- **Type:** Data/Integration
- **Description:** Maintain lineage from source and recipe through generation, approved version, publish payload, platform ID, and metrics.
- **User value:** Traceability and credible analytics.
- **Priority:** Must have
- **Rationale:** Existing modules are insufficiently joined.
- **Acceptance criteria:**
  - A platform post resolves to the exact approved variant version.
  - Metrics attach to the correct platform publication.
  - Deletion/archive follows a documented retention and cascade policy.

### DI-002: Platform capability registry

- **Type:** Data/Integration
- **Description:** Maintain a versioned registry of limits, media support, auth scopes, publish modes, and metric availability.
- **User value:** UI and validation remain aligned with real adapters.
- **Priority:** Must have
- **Rationale:** Current format metadata is too coarse for publication safety.
- **Acceptance criteria:**
  - Create, preview, publish, and analytics read the same registry.
  - Contract tests prove every advertised capability.
  - Unsupported controls are hidden or disabled.

### DI-003: Webhook delivery contract

- **Type:** Data/Integration
- **Description:** Deliver signed, replay-protected, versioned events with stable IDs, retries, and delivery logs.
- **User value:** Reliable integration without polling.
- **Priority:** Must have
- **Rationale:** Webhook behavior is inconsistently documented.
- **Acceptance criteria:**
  - Event includes ID, type, version, timestamp, tenant, and resource ID.
  - HMAC covers the exact transmitted body.
  - Attempts, response summaries, and next retry are visible.
  - Consumers can safely deduplicate events.

### DI-004: Source import

- **Type:** Data/Integration
- **Description:** Support pasted text first, then file, URL, RSS, and transcript import with provenance and review.
- **User value:** Reduces the first repeated manual step.
- **Priority:** Should have
- **Rationale:** Source acquisition is a logical entry point and common automation need.
- **Acceptance criteria:**
  - Extracted text is previewed and editable before generation.
  - Source metadata and import time are retained.
  - Extraction failure cannot create an empty generation job.

### MoSCoW summary

#### Must have

BR-001, BR-002; UR-001 through UR-005; FR-001 through FR-008, FR-011; NFR-001 through NFR-005; UX-001 through UX-006; DI-001 through DI-003.

#### Should have

BR-003; UR-006; FR-009, FR-010, FR-012 through FR-015; DI-004.

#### Could have

- Keyboard shortcuts and command palette.
- Mobile-first approval experience.
- Controlled A/B variant experiments.
- Shared report layouts.
- Internationalization and multilingual project metadata.

#### Won’t have for now

- Broad expansion to more publishing platforms before current adapters are reliable.
- A general-purpose no-code platform beyond content-specific automation.
- Autonomous publication by default.
- Predictive “algorithm readiness” claims without calibrated evidence.
- A recipe/template marketplace before team governance and core workflows are proven.

---

## 6. New opportunities

### 6.1 Approval inbox and lightweight collaboration

**Opportunity:** A queue of variants awaiting review, with assignment, comments, approve/reject, and activity history.  
**Why users may want it:** Teams and agencies need human governance before external publication.  
**Evidence/reasoning:** Approval already exists at variant level, publishing is high risk, and the current product lacks an attention-oriented team workflow.

### 6.2 Content calendar

**Opportunity:** A calendar showing draft, approved, scheduled, published, partial, and failed items across platforms.  
**Why users may want it:** Scheduling and multi-platform publication create a need to detect collisions and coverage gaps.  
**Evidence/reasoning:** Schedule, workflow, publish, and project concepts already exist. Calendar is the user-centered representation of those objects.

### 6.3 Performance-informed recipe recommendations

**Opportunity:** Suggest recipes, formats, structures, hooks, or times based on the user’s own verified publication history.  
**Why users may want it:** Time savings are useful, but learning what works increases business value.  
**Evidence/reasoning:** The product already models recipes, publications, validation, and analytics. This becomes justified once real lineage and metrics exist.  
**Constraint:** Recommendations must show data sufficiency and remain advisory.

### 6.4 Voice improvement from accepted edits

**Opportunity:** Detect repeated edits and propose changes to brand-voice rules.  
**Why users may want it:** Users repeatedly correct the same phrases or tone patterns.  
**Evidence/reasoning:** Version history and draft-versus-published validation create a basis for explainable, consent-based suggestions.  
**Constraint:** Never change voice rules silently.

### 6.5 Operational quality scorecard

**Opportunity:** A workspace health view for stale connections, failed jobs, overdue approvals, fallback outputs, stale metrics, and unreviewed scheduled content.  
**Why users may want it:** Daily operators focus on exceptions rather than browsing every module.  
**Evidence/reasoning:** The system has many asynchronous and external dependencies, making operational visibility a likely daily need.

### 6.6 Batch import with repair loop

**Opportunity:** Upload, map, validate, correct, process, and retry only failed rows.  
**Why users may want it:** Content teams often work in bursts.  
**Evidence/reasoning:** A batch endpoint already exists, but the usable workflow layer is missing.

---

## 7. Final recommendation

### What should be built first

#### Release A: Unified creation and attention workspace

Build:

- Home/attention inbox.
- Canonical content lineage.
- Autosave, compare/restore, selective regeneration.
- Better multi-variant navigation and lifecycle status.
- Durable job execution and recovery.
- Consistent authorization across all user-owned objects.
- Enforced review for fallback output.

**Why first:** This strengthens the highest-frequency journey already started in v1.1.0 and closes the most important efficiency and trust gaps.

#### Release B: Safe publish operations

Build:

- Encrypted persistent platform connections.
- Connection health and expiry alerts.
- Platform capability registry.
- Final-payload preview and validation.
- Approval gates.
- Local-time scheduling and calendar.
- Partial-publication recovery and notifications.

**Why second:** Publishing is a major differentiator but also the highest-reputation-risk workflow.

#### Release C: Operational automation

Build:

- Visual workflow builder.
- Test runs and step history.
- Batch import and repair.
- Signed webhook delivery and logs.
- Shared recipes and lightweight team review.

**Why third:** Automation amplifies value only after content objects, jobs, identity, and recovery are reliable.

#### Release D: Credible learning loop

Build:

- Real metrics adapters and provenance.
- Honest stale/partial/empty states.
- Explainable recommendations.
- Real exports and scheduled delivery.
- Performance-informed recipe suggestions.

**Why fourth:** Analytics should be exposed only when the data is real, linked to exact publications, and actionable.

### Immediate UI and workflow priorities

1. Make Home an attention view, not a generic dashboard.
2. Keep Create goal-first and group formats by user intent.
3. Upgrade review with autosave, compare, restore, and selective regeneration.
4. Show generation mode and review requirement on every variant.
5. Add a clear publish-readiness state.
6. Move provider/model/cron/webhook details into Advanced or Developer mode.
7. Make every failure recoverable from its own screen.
8. Never display mock analytics or stub exports as live success.

### Requirements most likely to improve adoption and efficiency

The highest-impact set is: **BR-001, BR-002, UR-001 through UR-005, FR-001 through FR-008, FR-011, UX-001 through UX-006, and DI-001 through DI-003.** Together, these requirements turn the current capable but fragmented application into a dependable daily content workspace.

### Closing assessment

RepurposeAI v1.1.0 has made meaningful progress: the workspace, durable projects and variants, recipes, accessible feedback, and honest LLM fallback reporting are strong foundations. The next product decision should be depth over breadth. The application should stop adding disconnected capabilities and make the core lifecycle continuous, recoverable, secure, and understandable.

The clearest adoption target is simple: a user should be able to take one saved source, generate several variants, confidently revise and approve them, publish or schedule them safely, and later understand their performance without leaving the product or questioning whether the displayed state is real.
