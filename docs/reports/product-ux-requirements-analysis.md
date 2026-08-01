# RepurposeAI Next-Version Product, UX, and Requirements Analysis

**Source reviewed:** `ZipPrompt.md`, treated as an expanded archive containing the Python application, documentation, examples, tests, configuration, and changelog.  
**Analysis date:** 2026-08-01  
**Product version represented:** Primarily v0.7.0, with documentation and implementation traces from v0.1.0 through v0.7.0.

## Analysis scope and confidence

This report distinguishes three evidence levels:

- **Observed:** Directly represented in source code, routes, models, tests, or documentation.
- **Inferred:** A likely user need or behavior derived from the observed architecture and workflows.
- **Unverified:** A documented claim that conflicts with, or is not fully supported by, the supplied implementation snapshot.

A crucial finding is that the package is **an API-first backend, not a complete end-user application UI**. The only directly available interface is the REST API and generated OpenAPI/Swagger documentation. Therefore, screen-level UX findings below describe the interface that exists today, followed by the product UI that the next version needs.

---

# 1. Product understanding

## 1.1 What the application appears to do

RepurposeAI is an AI-assisted content operations platform intended to turn one source item into multiple platform-specific outputs, then automate, publish, and evaluate those outputs.

Its apparent product loop is:

1. Provide source content.
2. Select one or more target formats.
3. Apply a brand voice and optional instructions.
4. Generate platform-oriented variants through a selectable LLM provider.
5. Optionally process content in batches or workflows.
6. Connect external publishing platforms and publish or dry-run a post.
7. Track jobs and workflow executions.
8. Analyze performance, quality gaps, and trends.
9. Export or schedule reports.

The backend exposes capabilities for:

- 20 content formats.
- OpenAI, Anthropic, and OpenRouter routing.
- Per-user brand voice.
- JWT authentication and API keys.
- Free and Pro subscription concepts.
- Batch repurposing.
- Scheduled, manual, and webhook-triggered workflows.
- LinkedIn, Twitter/X, and Medium publishing.
- Analytics, optimization scoring, validation, trends, and export.

However, much of the current breadth is scaffolded. Analytics frequently returns fixed/sample values; storage is mostly in memory; PDF export is a stub; and several integrations are documented more completely than they are implemented.

## 1.2 Likely users and segments

### Primary segment: individual content operators

**Inferred users:** solo creators, consultants, founders, developer advocates, and small marketing teams.

Their core goal is to convert one substantial content item into several usable channel-specific assets without repeatedly copying, prompting, reformatting, and publishing manually.

### Secondary segment: content and social media teams

**Inferred users:** content marketers, social media managers, editorial teams, and agencies.

They need review, consistency, reuse of presets, approval visibility, scheduling, publishing safety, and performance feedback across multiple items or clients.

### Technical segment: developers and automation specialists

**Observed users:** developers using REST endpoints, API keys, webhooks, n8n, Zapier, Make, batch requests, and workflow definitions.

The current product is strongest for this segment because the actual interface is JSON and API documentation rather than a task-oriented graphical UI.

### Administrative segment

**Inferred users:** account owners and team administrators who would manage subscription, credentials, API keys, platform connections, data retention, and access.

The backend contains fragments of these responsibilities, but no coherent administration experience.

## 1.3 Main workflows and usage scenarios

### Workflow A: single-item repurposing

1. Call the repurpose endpoint.
2. Send title, body, source format, target formats, brand voice, and optional instructions.
3. Optionally select an LLM provider/model through headers.
4. Receive generated output.

**UX interpretation:** this is the primary value-generating action, but the present interaction exposes technical concepts through request bodies and headers. A nontechnical user has no guided source editor, format picker, preview, or revision workspace.

### Workflow B: batch repurposing

1. Build a JSON array of up to 50 jobs.
2. Set concurrency.
3. Submit the batch.
4. Inspect completed and failed counts, outputs, and errors.

**UX interpretation:** useful for repeat work, but users must construct payloads manually. There is no import mapping, preview, per-row validation, recovery flow, or retry-only-failed action exposed as a user journey.

### Workflow C: asynchronous processing

1. Submit a webhook repurpose job.
2. Receive a job ID.
3. Poll a status endpoint or depend on callback behavior.
4. Retrieve output when complete.

**UX interpretation:** the status model is appropriate for long-running work, but polling is implementation burden transferred to the user. Documentation also contains version-dependent contradictions about whether callback processing is live.

### Workflow D: workflow automation

1. Define a workflow as JSON.
2. Select manual, schedule, or webhook trigger.
3. Add sequential repurpose, webhook, or wait steps.
4. Configure retries.
5. Trigger or wait for scheduler execution.
6. query a job/execution endpoint.

**UX interpretation:** the engine supports useful automation primitives, but authoring requires schema expertise. There is no visual builder, readable schedule control, run preview, variable mapping, test execution, or recovery action.

### Workflow E: platform connection and publishing

1. Start OAuth or enter a Medium token.
2. Store credentials.
3. Build a publish request.
4. Optionally use dry-run.
5. Submit the job.
6. Poll status.

**UX interpretation:** dry-run is a meaningful safety mechanism. The major gap is that platform connection, credential health, content preview, channel constraints, and publishing status are not combined into one trustworthy flow.

### Workflow F: analytics and validation

1. Query posts or metrics.
2. calculate an optimization score.
3. compare AI drafts with published versions.
4. query time-series trends or top content.
5. export or schedule CSV/PDF reports.

**UX interpretation:** this could close the learning loop, but the supplied implementation is mostly sample/static data and has no dashboard UI. Scores also lack sufficient interpretation and action guidance.

### Workflow G: account and developer setup

1. Register and log in.
2. Manage brand voice.
3. Create and revoke API keys.
4. Check subscription status.
5. configure external credentials.

**UX interpretation:** related settings are fragmented across several endpoints. Credential handling, authentication requirements, and tenancy rules are inconsistent across modules.

---

# 2. UI/UX analysis

## 2.1 Strengths

1. **The core product loop is coherent.** Repurpose, publish, and learn from results form a credible end-to-end content-operations proposition.
2. **Multi-format output matches actual content habits.** Users commonly adapt one source into several channel variants.
3. **Brand voice can be saved per user.** This reduces repeated instructions and supports consistency.
4. **Dry-run publishing lowers anxiety.** It creates a safe checkpoint before an irreversible external action.
5. **Unified job status is directionally good.** Asynchronous work benefits from a common status vocabulary.
6. **Batch error isolation is valuable.** One invalid item does not have to invalidate the full batch.
7. **Integration documentation is unusually extensive.** Examples for Python, n8n, Zapier, and Make support technical adoption.
8. **Format metadata includes audience, structure, tone, and limits.** These attributes can support a strong format-selection and preview UI.
9. **Validation concepts can support learning.** Draft/published comparison, readability, tone, and faithfulness can help users refine templates and voice.

## 2.2 Weaknesses

### No end-user interface

The largest usability gap is not a weak screen but the absence of screens. The application cannot presently deliver a low-friction workflow to the primary nontechnical segments. Swagger is an API exploration tool, not a content workspace.

### Feature breadth exceeds workflow coherence

Repurpose, batch, workflows, publish, analytics, exports, subscriptions, API keys, and settings exist as separate API areas. There is no shared object model visible to users such as:

- content item,
- campaign,
- generated variant,
- approval state,
- scheduled/published post,
- performance result.

Without this continuity, users must mentally connect IDs and payloads across endpoints.

### Technical controls appear in the primary path

Provider/model selection through HTTP headers, raw format IDs, cron expressions, callback URLs, scopes, concurrency, and JSON step configuration create high cognitive load. These belong in advanced controls or developer settings, not the default creation flow.

### Weak outcome visibility

Generation returns content, but the product lacks a visible lifecycle from source to draft to approved to scheduled to published to measured. Users cannot quickly answer:

- What needs my attention?
- What is ready to publish?
- What failed?
- What changed after editing?
- Which content performed best?
- Which recommendation should I act on next?

### Limited error recovery

The APIs expose errors, but a good product workflow also needs user actions: retry, edit and retry, reconnect, duplicate, skip, restore, or rerun failed steps. Those recovery paths are not part of the current interaction design.

## 2.3 Confusing elements and inconsistencies

1. **Implementation and documentation disagree.** Changelog entries imply some webhook gaps were resolved, while other documentation still says jobs remain pending and callbacks are future work.
2. **Test totals conflict.** The supplied materials reference 805, 1,204, 1,215, 1,670, and other counts. This weakens confidence in release readiness.
3. **Version metadata conflicts.** The app constant is 0.7.0 while `pyproject.toml` still identifies 0.1.0.
4. **Analytics is called a dashboard without a dashboard UI.** API modules and sample responses should not be presented to end users as a functioning dashboard.
5. **Analytics endpoints are unauthenticated while user-specific features are authenticated.** This undermines expectations of privacy and tenant isolation.
6. **“Completed” export status may not mean a downloadable artifact.** PDF export returns a path stub, which can create false success.
7. **Optimization score language overstates certainty.** A deterministic formula based on a few rates is not necessarily “algorithm readiness” without calibration or provenance.
8. **Provider fallback to string concatenation is dangerous.** A user asking for AI repurposing may receive low-value concatenated output without a clear degraded-mode warning.
9. **Publishing credential routes appear unauthenticated in documentation.** Credential access must be tenant-bound and protected.
10. **Scheduling is UTC/cron-centric.** Users think in local time, weekdays, and “next run,” not raw cron expressions.

## 2.4 Friction points

### High-frequency friction

- Re-entering source content, target formats, voice, and instructions.
- Copying results between API output and editing/publishing tools.
- Manually tracking job and workflow IDs.
- Polling for completion.
- Reconstructing context after a failure or restart.
- Reconnecting platform credentials after in-memory loss.
- Rebuilding commonly used workflow payloads.
- Converting local publishing time into UTC/cron.

### High-risk friction

- Publishing without a channel-accurate preview.
- Partial Twitter/X thread publication with no visible recovery plan.
- Unclear credential health or token expiration.
- Static/mock analytics presented as real insight.
- Open or inconsistently authenticated endpoints.
- Data loss on service restart.

### Cognitive load

- Twenty formats are presented as IDs rather than user-goal groupings.
- Brand voice, custom instructions, provider, model, strategy, target format, and publish settings compete for attention.
- Workflow JSON requires users to understand schemas, retries, webhooks, step IDs, and execution semantics.
- Analytics uses technical metrics without benchmarks, explanation, or recommended actions.

## 2.5 Navigation and information architecture observations

A task-based product shell should replace the route-based mental model. Recommended top-level navigation:

1. **Home**: work requiring attention, recent jobs, failures, upcoming publications, usage.
2. **Create**: source content, format selection, generation, revision, approval.
3. **Content**: reusable library of sources, variants, status, tags, campaigns.
4. **Calendar**: scheduled and published content across platforms.
5. **Automations**: workflow templates, builder, run history, errors.
6. **Analytics**: performance, comparisons, recommendations, validation learning.
7. **Connections**: platform and provider connection health.
8. **Settings**: brand voice, team, API keys, billing, data controls.

This structure follows user goals instead of the backend package layout.

---

# 3. User behavior analysis

## 3.1 Likely user habits

### Reuse rather than configure from scratch

Users are likely to repeat a few stable combinations, for example:

- blog to LinkedIn post plus Twitter thread,
- podcast transcript to show notes plus newsletter,
- product release to changelog plus social posts,
- long-form article to Medium plus carousel.

They will expect presets, favorites, recent choices, duplication, and “run again with new source.”

### Review before publish

Even when automation is desired, users will usually scan hooks, claims, links, formatting, and tone before publication. They need a human-in-the-loop review step and clear separation between generated, approved, scheduled, and published states.

### Edit outputs unevenly

Users are likely to refine only selected variants. A good workspace must preserve individual edits and allow regeneration of one section or one format without overwriting accepted work.

### Work in bursts

Content teams often generate several items at once, then review and schedule later. Batch imports, queues, bulk status changes, and cross-item filtering are more useful than a single synchronous form alone.

### Learn from prior performance

Once publishing is connected, users will expect successful hooks, formats, posting times, and voice patterns to influence future recommendations. The current analytics architecture suggests this loop but does not operationalize it.

## 3.2 Repeated actions

- Paste or import source content.
- Choose the same 2 to 5 output formats.
- Apply the same brand voice.
- Add recurring custom instructions.
- Scan, edit, copy, regenerate, or approve outputs.
- Validate channel limits and links.
- schedule or publish.
- Check job status and failures.
- Reuse successful workflows.
- Export reports for stakeholders.

These repeated actions should drive defaults, automation, shortcuts, and saved templates.

## 3.3 Likely pain points

1. **No workspace for editing multiple variants side by side.**
2. **No durable content history.** In-memory state threatens trust and repeat use.
3. **No clear publish readiness signal.** Users cannot see whether each variant meets channel requirements.
4. **No approval controls.** Teams cannot safely automate external publishing.
5. **No visible cost/time estimate.** Choosing many formats or premium models has unclear impact.
6. **No reliable distinction between real and mock analytics.** This can lead to incorrect decisions.
7. **No reusable templates or campaign grouping.** Repeated work remains repetitive.
8. **No notification model.** Users must poll or manually check jobs.
9. **No user-friendly schedule builder.** Cron and UTC create avoidable mistakes.
10. **No guided recovery for credentials or partial publish failures.**

## 3.4 Usage bottlenecks

- **Onboarding bottleneck:** users must understand API concepts before experiencing value.
- **Creation bottleneck:** raw requests replace guided input and preview.
- **Review bottleneck:** generated variants have no structured editor or comparison state.
- **Publishing bottleneck:** connection management is separated from content readiness.
- **Automation bottleneck:** JSON workflow authoring excludes nontechnical operators.
- **Learning bottleneck:** analytics data is not reliably real, contextual, or actionable.
- **Trust bottleneck:** ephemeral storage, unauthenticated routes, mock results, and conflicting documentation.

## 3.5 Expected but missing interactions

- Save draft automatically.
- Import from URL, file, transcript, RSS, or pasted text.
- Select recommended formats based on source and goal.
- Preview output in platform-like frames.
- Edit and regenerate only selected text.
- Undo, compare versions, and restore.
- Approve/reject each variant.
- Duplicate a prior job or workflow.
- Retry only failed batch items or workflow steps.
- See local-time schedules and next-run previews.
- Receive in-app/email/webhook completion and failure notifications.
- See connected/disconnected/expiring credential states.
- Browse content and job history with filters.
- Download a real export.
- Understand why a score changed and what to do next.

---

# 4. What should be improved

## 4.1 Critical improvements

1. **Create a focused end-user web application around the core create-review-publish loop.**
2. **Implement durable tenant-scoped persistence** for users, content, variants, jobs, workflows, credentials, schedules, and analytics.
3. **Close security and tenant-isolation gaps** across analytics, workflows, jobs, publishing, exports, and credentials.
4. **Replace static/stub responses with explicit real, empty, unavailable, or demo states.** Never present mock data as live data.
5. **Build a content workspace** with saved sources, generated variants, editing, versioning, autosave, and status.
6. **Provide reliable asynchronous execution** with completion events, retry controls, idempotency, and consistent status semantics.
7. **Create a safe publishing workflow** with connection health, channel validation, previews, approval, scheduling, and partial-failure recovery.
8. **Unify object identity and history** so users do not manually transfer IDs between endpoints.
9. **Make degraded LLM behavior explicit.** Generation must fail clearly or show a warning, not silently return concatenated content.
10. **Establish trustworthy release governance** by reconciling version numbers, tests, implementation status, and user-facing claims.

## 4.2 Medium-priority improvements

1. Saved recipes and recent selections.
2. Visual workflow builder with templates.
3. Batch CSV import and per-row repair.
4. Local-time schedule editor and calendar.
5. Actionable analytics with comparison periods and metric definitions.
6. Brand voice setup using examples, not only preset labels.
7. Notifications and attention inbox.
8. Usage, token/cost, and plan-limit visibility.
9. Search, filtering, tags, campaigns, and bulk actions.
10. Real CSV/PDF exports with secure download and delivery.

## 4.3 Nice-to-have improvements

1. Keyboard shortcuts and command palette.
2. Side-by-side multi-platform preview.
3. Template marketplace or shared team recipes.
4. Experiment comparison for hooks or variants.
5. Calendar drag-and-drop rescheduling.
6. Mobile-friendly approval experience.
7. Saved stakeholder report layouts.
8. Additional publishing adapters only after the current three are reliable.

---

# 5. Requirements

## 5.1 Business requirements

### BR-001: Deliver a complete value loop

- **Type:** Business
- **Description:** The product shall support a continuous source → generate → review → approve → schedule/publish → measure workflow without requiring users to manually reconstruct state across API endpoints.
- **User value:** Users complete their real task in one product rather than combining API calls, spreadsheets, and external editors.
- **Priority:** Must have
- **Rationale:** The backend has broad capabilities but no coherent end-user journey.
- **Acceptance criteria:**
  - A user can start from a saved source and reach an approved or scheduled variant through linked UI states.
  - Every generated variant retains references to its source, job, format, owner, and publish record.
  - The product shows the current lifecycle state and next available action.

### BR-002: Establish production trust

- **Type:** Business
- **Description:** User-facing claims shall reflect implemented and operational capabilities. Mock, demo, unavailable, and live data shall be clearly distinguished.
- **User value:** Users can trust results, status, exports, and analytics.
- **Priority:** Must have
- **Rationale:** Static analytics, PDF stubs, conflicting documentation, and inconsistent test/version claims undermine adoption.
- **Acceptance criteria:**
  - Production endpoints do not return sample business data unless the workspace is explicitly in demo mode.
  - Stub features are hidden or labeled unavailable.
  - Release metadata has one consistent version and capabilities manifest.
  - Release checks fail when documentation claims an unavailable capability.

### BR-003: Support repeatable content operations

- **Type:** Business
- **Description:** The product shall reduce repeated configuration through saved recipes, defaults, duplication, and reusable workflows.
- **User value:** Frequent tasks require fewer decisions and less setup.
- **Priority:** Should have
- **Rationale:** Likely users repeat the same source-to-channel combinations and brand instructions.
- **Acceptance criteria:**
  - Users can save a generation recipe and rerun it with new source content.
  - Recent and favorite formats are available within one selection action.
  - Duplicating a prior job preserves settings but not publication state.

### BR-004: Enable measurable adoption and efficiency

- **Type:** Business
- **Description:** The product shall capture funnel and task-efficiency telemetry while protecting content privacy.
- **User value:** Product improvements can target real abandonment and friction.
- **Priority:** Should have
- **Rationale:** The current extensive functional tests do not reveal whether users succeed.
- **Acceptance criteria:**
  - Track onboarding completion, first generation, approval, connection, schedule/publish, and repeat use.
  - Track median time from source creation to approved variant and failed-job recovery rate.
  - Do not include source or generated content bodies in analytics events by default.

## 5.2 User requirements

### UR-001: Guided first-value onboarding

- **Type:** User
- **Description:** A new user shall be able to generate a useful first variant without knowing APIs, providers, format IDs, or model names.
- **User value:** Faster time to value and lower setup anxiety.
- **Priority:** Must have
- **Rationale:** The current interface assumes developer knowledge.
- **Acceptance criteria:**
  - A guided flow requests source, goal, target channels, and voice in plain language.
  - Provider/model settings default automatically and remain in an advanced section.
  - A first usable variant can be generated without creating an API key or platform connection.

### UR-002: Persistent content workspace

- **Type:** User
- **Description:** Users shall be able to save, reopen, search, and continue source items and generated variants.
- **User value:** Work survives sessions and can be revised later.
- **Priority:** Must have
- **Rationale:** In-memory state is incompatible with repeated professional use.
- **Acceptance criteria:**
  - Drafts autosave and survive restart and logout.
  - Users can search by title and filter by status, format, platform, date, and tag.
  - Opening an item restores source, variants, edits, status, and activity history.

### UR-003: Review and selective regeneration

- **Type:** User
- **Description:** Users shall be able to edit, compare, approve, and selectively regenerate one variant or selected text without replacing accepted work.
- **User value:** Faster refinement and lower risk of losing good edits.
- **Priority:** Must have
- **Rationale:** Users rarely accept every generated output unchanged.
- **Acceptance criteria:**
  - Each variant has independent draft, approved, and rejected states.
  - Regeneration offers replace, create new version, or cancel.
  - Users can compare current and previous versions and restore a prior version.
  - Manual edits are never overwritten without an explicit choice.

### UR-004: Clear progress and attention management

- **Type:** User
- **Description:** Users shall see active, completed, blocked, and failed work in one place with clear next actions.
- **User value:** No manual polling or lost jobs.
- **Priority:** Must have
- **Rationale:** The current system exposes IDs and status endpoints rather than an attention-oriented experience.
- **Acceptance criteria:**
  - Home shows active jobs, approvals needed, failures, and upcoming scheduled posts.
  - Status includes submitted, processing, review needed, approved, scheduled, published, partial, and failed where applicable.
  - Failure cards provide edit, retry, reconnect, or view details actions.

### UR-005: Safe publishing control

- **Type:** User
- **Description:** Users shall review channel-valid previews and explicitly approve content before live publication unless a workflow has clearly configured auto-publish permission.
- **User value:** Prevents accidental or malformed external posts.
- **Priority:** Must have
- **Rationale:** Publishing is irreversible and current dry-run behavior is API-only.
- **Acceptance criteria:**
  - A platform preview shows truncation, threading, title, links, media, and visibility.
  - Validation blocks invalid required fields and warns on soft constraints.
  - Live publish requires a review confirmation or an auditable automation rule.
  - Dry-run results are visible and distinguishable from published status.

### UR-006: Reusable brand voice

- **Type:** User
- **Description:** Users shall define brand voice using descriptive controls and sample content, preview its effect, and apply it consistently.
- **User value:** Less repeated prompting and more consistent outputs.
- **Priority:** Should have
- **Rationale:** Current presets and free-text instructions are useful but underspecified.
- **Acceptance criteria:**
  - Voice setup accepts traits, do/don’t rules, preferred terms, banned terms, and examples.
  - Users can test the voice against sample text before saving.
  - The applied voice and overrides are visible on each generation.

## 5.3 Functional requirements

### FR-001: Durable tenant-scoped domain model

- **Type:** Functional
- **Description:** Persist users, workspaces, content sources, variants, versions, jobs, workflows, executions, credentials, schedules, publications, metrics, exports, and audit events with tenant ownership.
- **User value:** Reliable history, continuity, and privacy.
- **Priority:** Must have
- **Rationale:** Most current stores are process memory.
- **Acceptance criteria:**
  - Restarting any service does not lose committed user data or execution state.
  - All read/write queries are tenant-scoped.
  - Automated tests verify cross-tenant access is denied for every domain object.
  - Schema migrations are executable and reversible according to policy.

### FR-002: Secure authorization coverage

- **Type:** Functional
- **Description:** Require authenticated, authorized access for analytics, jobs, workflows, exports, publishing credentials, subscriptions, and content unless an endpoint is explicitly public.
- **User value:** Protection from unauthorized access and modification.
- **Priority:** Must have
- **Rationale:** Authentication is inconsistent and analytics is documented as open.
- **Acceptance criteria:**
  - Anonymous requests to protected routes return 401.
  - Authenticated cross-tenant requests return 404 or 403 according to policy.
  - API keys enforce documented scopes.
  - Credential responses never reveal stored secrets.

### FR-003: Content project and variant management

- **Type:** Functional
- **Description:** Provide CRUD and version APIs for source projects and format-specific variants.
- **User value:** Supports the workspace, editing, and complete traceability.
- **Priority:** Must have
- **Rationale:** Existing generation responses are not modeled as durable user work.
- **Acceptance criteria:**
  - Create a project from pasted text and associate one or more variants.
  - Save manual edits as versions with author and timestamp.
  - Delete/archive and restore according to retention policy.
  - Return lifecycle and publication status for each variant.

### FR-004: Reliable asynchronous job processing

- **Type:** Functional
- **Description:** Run generation, batch, workflow, publish, metric collection, and export jobs through a durable worker system with idempotency and recovery.
- **User value:** Jobs finish reliably without polling fragile process memory.
- **Priority:** Must have
- **Rationale:** Background behavior and callback support are inconsistent in current materials.
- **Acceptance criteria:**
  - Accepted jobs persist before a 202 response.
  - Workers resume or safely retry interrupted jobs after restart.
  - Idempotency keys return the original job for semantically identical retries in the configured window.
  - Status transitions are validated and timestamped.
  - Completion can be delivered by UI event, webhook, or notification.

### FR-005: Actionable failure recovery

- **Type:** Functional
- **Description:** Record machine-readable error codes, user-readable explanations, retryability, and recovery actions for every job and step.
- **User value:** Users can fix problems without reconstructing requests.
- **Priority:** Must have
- **Rationale:** Current errors are often endpoint details rather than workflow recovery.
- **Acceptance criteria:**
  - Failed batch items can be filtered and resubmitted without successful items.
  - Failed workflow steps can be retried from the failed step when safe.
  - Partial thread publication records published and unpublished segments.
  - Provider and platform errors are sanitized and mapped to recommended actions.

### FR-006: Generation recipes and defaults

- **Type:** Functional
- **Description:** Allow users to save target formats, voice, instructions, provider policy, and output settings as reusable recipes.
- **User value:** Reduces repeated configuration.
- **Priority:** Should have
- **Rationale:** Repetition is the dominant likely habit.
- **Acceptance criteria:**
  - Create, rename, duplicate, archive, and share recipes within a workspace.
  - Apply a recipe to a new source in one action.
  - Recipe changes do not retroactively alter historical outputs.

### FR-007: Platform connection lifecycle

- **Type:** Functional
- **Description:** Manage platform credentials as tenant-scoped encrypted connections with health, scopes, expiry, refresh, reconnection, and revocation states.
- **User value:** Predictable and secure publishing.
- **Priority:** Must have
- **Rationale:** Current credentials are in memory and may be exposed through weakly protected routes.
- **Acceptance criteria:**
  - Secrets are encrypted at rest and redacted from logs and API responses.
  - Connection status shows connected, action required, expired, or revoked.
  - OAuth state and PKCE are validated and single-use.
  - Users can test and revoke a connection.
  - Refresh failures create an actionable reconnect notification.

### FR-008: Channel validation and preview

- **Type:** Functional
- **Description:** Validate each variant against current channel capabilities and render a channel-oriented preview before scheduling or publishing.
- **User value:** Prevents malformed content and reduces external corrections.
- **Priority:** Must have
- **Rationale:** Format metadata exists but is not operationalized in the workflow.
- **Acceptance criteria:**
  - Validate required fields, length, thread segmentation, link/media support, and publish status.
  - Preview uses the final payload, not a separate approximation.
  - Hard errors block publish; warnings require acknowledgement or editing.
  - Validation rules are versioned by platform adapter.

### FR-009: Scheduling with local-time semantics

- **Type:** Functional
- **Description:** Users shall schedule by timezone-aware date/time or human-readable recurrence without writing cron.
- **User value:** Fewer schedule mistakes and clearer automation.
- **Priority:** Must have
- **Rationale:** Current scheduling is UTC and cron-centric, with weak last-run behavior.
- **Acceptance criteria:**
  - Users select a named timezone.
  - The UI displays the next five runs before saving.
  - Daylight-saving changes follow the selected timezone policy.
  - Each schedule stores last run, next run, and last outcome.
  - Duplicate firing is prevented.

### FR-010: Visual workflow authoring and test runs

- **Type:** Functional
- **Description:** Provide a visual builder for supported triggers and steps with schema-based forms, variable mapping, validation, test execution, and run history.
- **User value:** Nontechnical users can automate repeat workflows safely.
- **Priority:** Should have
- **Rationale:** JSON workflow definitions are powerful but inaccessible.
- **Acceptance criteria:**
  - Add, reorder, configure, duplicate, and delete steps without JSON editing.
  - Validate missing inputs and incompatible mappings before activation.
  - Run a test with sample data without enabling the schedule.
  - Show step inputs, outputs, attempts, duration, and errors in run history.

### FR-011: Real analytics ingestion and provenance

- **Type:** Functional
- **Description:** Collect real platform metrics through adapters, normalize them, retain raw provenance, and visibly mark incomplete or unavailable data.
- **User value:** Decisions are based on trustworthy performance data.
- **Priority:** Must have
- **Rationale:** Current analytics uses mock/sample data and no-op persistence.
- **Acceptance criteria:**
  - Sample values are never returned in a non-demo tenant.
  - Each normalized metric identifies platform, source timestamp, collection time, and mapping version.
  - Missing metrics display unavailable rather than zero unless zero is confirmed.
  - Collection errors and stale data are visible.

### FR-012: Explainable recommendations

- **Type:** Functional
- **Description:** Optimization and validation results shall include calculation basis, confidence/limitations, comparison context, and recommended actions.
- **User value:** Users know what a score means and how to improve.
- **Priority:** Should have
- **Rationale:** A single 0–100 score can create false certainty.
- **Acceptance criteria:**
  - Show signal contributions and formula/version.
  - Distinguish heuristic, observed, and LLM-judged results.
  - Provide no recommendation when supporting data is insufficient.
  - Users can navigate from a recommendation to the affected variant.

### FR-013: Real export generation and delivery

- **Type:** Functional
- **Description:** Generate downloadable CSV and PDF artifacts from real tenant data and support scheduled delivery.
- **User value:** Stakeholders receive usable reports.
- **Priority:** Should have
- **Rationale:** PDF export is currently a path stub and export completion is misleading.
- **Acceptance criteria:**
  - Completed exports have an authenticated, expiring download URL.
  - PDF files open successfully and contain the requested date range and metrics.
  - Empty reports state that no data matched.
  - Recurring exports record recipient, timezone, last delivery, next delivery, and failure.

### FR-014: Usage and cost visibility

- **Type:** Functional
- **Description:** Show plan limits, used and remaining repurposes, estimated generation cost/credits, and provider fallback outcomes.
- **User value:** Users can make informed workload and plan choices.
- **Priority:** Should have
- **Rationale:** Free/Pro concepts and multiple models exist, but the cost impact is opaque.
- **Acceptance criteria:**
  - Usage updates atomically with successful billable operations.
  - Before a large batch, show estimated consumption and warn if limits may be exceeded.
  - Generation records the actual provider/model and fallback path.
  - Quota errors explain when usage resets and how to proceed.

### FR-015: Notifications and subscriptions

- **Type:** Functional
- **Description:** Support configurable in-app, email, and webhook notifications for completion, failure, approval needed, credential expiry, and scheduled publish outcomes.
- **User value:** Users do not need to poll repeatedly.
- **Priority:** Should have
- **Rationale:** Asynchronous operations are central to the product.
- **Acceptance criteria:**
  - Users can configure event/channel preferences.
  - Notifications link to the affected item or recovery action.
  - Duplicate events are suppressed.
  - Delivery attempts and failures are auditable.

### FR-016: Accurate degraded-mode behavior

- **Type:** Functional
- **Description:** If no valid LLM provider is available, the product shall not silently represent string concatenation or placeholder output as AI-generated content.
- **User value:** Prevents misleading and low-quality output.
- **Priority:** Must have
- **Rationale:** The documented fallback can violate user expectations.
- **Acceptance criteria:**
  - Default behavior returns a clear provider-configuration error.
  - If a non-AI fallback is enabled for testing, it is labeled in result metadata and UI.
  - Degraded output cannot be auto-published without explicit acknowledgement.

## 5.4 Non-functional requirements

### NFR-001: Reliability and recovery

- **Type:** Non-functional
- **Description:** User data and accepted jobs shall survive process and host restarts.
- **User value:** Professional users can trust the system with ongoing work.
- **Priority:** Must have
- **Rationale:** Current in-memory stores lose critical state.
- **Acceptance criteria:**
  - No committed content, credential metadata, schedule, or job is lost during a controlled restart.
  - Recovery tests cover worker interruption and duplicate delivery.
  - Recovery point and recovery time objectives are documented and monitored.

### NFR-002: Security and privacy

- **Type:** Non-functional
- **Description:** Apply least privilege, encryption, secret redaction, auditability, secure webhook validation, and tenant isolation.
- **User value:** Protects content, identity, credentials, and reputation.
- **Priority:** Must have
- **Rationale:** The product handles unpublished content and external publishing rights.
- **Acceptance criteria:**
  - TLS in transit and managed encryption at rest.
  - Secrets never appear in logs, telemetry, or list responses.
  - SSRF validation occurs after DNS resolution and before each redirect/request.
  - Security tests cover token replay, OAuth state, HMAC, authorization, and webhook replay.

### NFR-003: Performance responsiveness

- **Type:** Non-functional
- **Description:** Interactive pages and actions shall remain responsive while long-running tasks execute asynchronously.
- **User value:** The product feels fast even when generation takes time.
- **Priority:** Must have
- **Rationale:** LLM, export, workflow, and publish operations may take seconds or minutes.
- **Acceptance criteria:**
  - Standard authenticated page API reads meet a defined p95 target under expected load.
  - Job submission responds quickly with durable status.
  - UI provides progress or stage feedback within one second after submission.
  - Large lists use pagination or cursor loading.

### NFR-004: Accessibility

- **Type:** Non-functional
- **Description:** The web application shall meet WCAG 2.2 AA for core workflows.
- **User value:** More users can create, review, and approve content effectively.
- **Priority:** Must have
- **Rationale:** A new UI should not reproduce the exclusion of an API-only experience.
- **Acceptance criteria:**
  - Keyboard-only completion of onboarding, generation, review, scheduling, and publishing.
  - Visible focus, semantic labels, error association, sufficient contrast, and non-color status cues.
  - Automated accessibility checks plus manual screen-reader testing for core flows.

### NFR-005: Observability

- **Type:** Non-functional
- **Description:** Provide structured logs, traces, metrics, and correlation IDs across API, worker, provider, platform, and webhook operations.
- **User value:** Faster support and more accurate status explanations.
- **Priority:** Must have
- **Rationale:** Distributed async work is difficult to diagnose with opaque errors.
- **Acceptance criteria:**
  - Every job has a correlation ID visible to support but not exposing secrets.
  - Monitor queue delay, execution duration, retries, provider failures, publish failures, and stale jobs.
  - User-visible status is derived from the same durable event history used by operations.

### NFR-006: Compatibility and adapter isolation

- **Type:** Non-functional
- **Description:** Platform and LLM integrations shall be versioned adapters with contract tests.
- **User value:** External API changes cause fewer regressions.
- **Priority:** Should have
- **Rationale:** The product depends on several changing external APIs.
- **Acceptance criteria:**
  - Each adapter declares supported capabilities and API version.
  - Contract tests validate payload mapping and error normalization.
  - Unsupported capabilities are hidden or disabled in the UI.

### NFR-007: Internationalization readiness

- **Type:** Non-functional
- **Description:** Store content as Unicode, preserve language metadata, and separate localized UI text from code.
- **User value:** Supports creators who publish in multiple languages.
- **Priority:** Could have
- **Rationale:** Content repurposing naturally serves multilingual use, even though it is not currently explicit.
- **Acceptance criteria:**
  - Source and outputs preserve Unicode without corruption.
  - Each project can record source and target language.
  - Date/time and number display respects locale and timezone.

## 5.5 UX/UI requirements

### UX-001: Goal-first create flow

- **Type:** UX/UI
- **Description:** The Create experience shall organize choices around user goals and channels rather than enum IDs and backend parameters.
- **User value:** Faster, clearer generation setup.
- **Priority:** Must have
- **Rationale:** Twenty ungrouped formats create choice overload.
- **Acceptance criteria:**
  - Group formats into Social, Long-form, Email, Video/Audio, Sales, and Product categories.
  - Show format purpose, typical output, channel, and saved/recent state.
  - Recommend a small set while allowing full browsing.
  - Advanced provider controls are collapsed by default.

### UX-002: Multi-variant workspace

- **Type:** UX/UI
- **Description:** Display source and generated variants in a persistent workspace optimized for scanning, editing, and status changes.
- **User value:** Less copying and context switching.
- **Priority:** Must have
- **Rationale:** The primary task involves comparing multiple outputs from one source.
- **Acceptance criteria:**
  - Users can switch variants without losing cursor or edits.
  - Autosave status is visible.
  - Each variant shows format, version, approval, validation, and publication state.
  - Copy and export actions confirm success non-disruptively.

### UX-003: Progressive disclosure

- **Type:** UX/UI
- **Description:** Keep provider, model, routing strategy, concurrency, webhook, retry, and raw payload controls out of the default nontechnical path.
- **User value:** Reduced cognitive load without limiting experts.
- **Priority:** Must have
- **Rationale:** Current API concepts overwhelm ordinary content work.
- **Acceptance criteria:**
  - Default flow exposes only decisions required for a useful result.
  - Advanced settings explain consequences and have safe defaults.
  - Developer mode can reveal technical configuration and payload previews.

### UX-004: System status and feedback

- **Type:** UX/UI
- **Description:** Every asynchronous and external action shall provide immediate acknowledgement, ongoing state, expected next step, and completion/failure feedback.
- **User value:** Confidence and reduced repeated clicks.
- **Priority:** Must have
- **Rationale:** Current users must poll endpoints manually.
- **Acceptance criteria:**
  - Submission immediately creates a visible job card.
  - Long tasks show stages rather than indeterminate waiting when stages are known.
  - Duplicate submission controls are disabled or idempotent.
  - Success messages identify what happened and where to find the result.

### UX-005: User-centered errors

- **Type:** UX/UI
- **Description:** Error messages shall explain the problem, preserve user input, and offer the most relevant recovery action.
- **User value:** Faster self-service recovery.
- **Priority:** Must have
- **Rationale:** Raw API errors are insufficient for operational workflows.
- **Acceptance criteria:**
  - Validation errors are displayed next to the affected field and summarized.
  - No source content or manual edits are lost on error.
  - Credential errors offer Reconnect; provider errors offer Retry or Change provider; content errors offer Edit.
  - Technical details are available in an expandable section.

### UX-006: Local-time schedule UI

- **Type:** UX/UI
- **Description:** Schedule controls shall use calendar/time inputs, recurrence language, timezone, and next-run preview.
- **User value:** Eliminates cron translation and timing ambiguity.
- **Priority:** Must have
- **Rationale:** UTC cron is a major preventable source of mistakes.
- **Acceptance criteria:**
  - Default timezone is obtained from user settings, not silently assumed.
  - UI renders “Every weekday at 09:00” and the next run dates.
  - DST impact is explained only when relevant.

### UX-007: Analytics for decisions, not inspection

- **Type:** UX/UI
- **Description:** Analytics views shall pair metrics with definitions, comparison, data freshness, and recommended action.
- **User value:** Users can act instead of merely viewing numbers.
- **Priority:** Should have
- **Rationale:** Current endpoints provide values without a usable interpretation layer.
- **Acceptance criteria:**
  - Every chart states date range, timezone, platforms, and last updated time.
  - Empty, stale, partial, and error states are distinct.
  - Recommendations link to supporting posts and relevant creation settings.
  - Users can compare periods and platforms without constructing queries.

### UX-008: Connected-account control center

- **Type:** UX/UI
- **Description:** Connections shall be managed in one page with capability, scope, health, ownership, and recovery information.
- **User value:** Clear confidence before scheduling or publishing.
- **Priority:** Must have
- **Rationale:** Credentials are currently separate API operations with limited visible state.
- **Acceptance criteria:**
  - Each connection shows account identity, supported actions, status, last successful use, and expiry when known.
  - Connecting and reconnecting returns users to the task they were performing.
  - Revocation requires confirmation and explains scheduled-content impact.

## 5.6 Data and integration requirements

### DI-001: Canonical content lineage

- **Type:** Data/Integration
- **Description:** Maintain lineage between source, generation request, variant versions, approvals, publish payloads, platform post IDs, and collected metrics.
- **User value:** Enables traceability, comparison, and credible analytics.
- **Priority:** Must have
- **Rationale:** Current modules are not joined into a user-visible lifecycle.
- **Acceptance criteria:**
  - A published post resolves back to the exact approved variant version.
  - Metrics attach to the correct platform publication.
  - Deleting a source follows a documented cascade/retention policy.

### DI-002: Platform capability registry

- **Type:** Data/Integration
- **Description:** Maintain a versioned registry of channel limits, supported media, authentication scopes, publish modes, and metric availability.
- **User value:** UI and validation stay aligned with actual adapters.
- **Priority:** Must have
- **Rationale:** Format flags exist, but they are too coarse for safe publishing.
- **Acceptance criteria:**
  - Create and publish UI reads capabilities from the registry.
  - Adapter tests ensure advertised capability is implemented.
  - Capability changes are deployable without editing multiple unrelated modules.

### DI-003: Webhook delivery contract

- **Type:** Data/Integration
- **Description:** Deliver signed, replay-protected webhooks with documented event types, stable IDs, retry policy, and delivery log.
- **User value:** Reliable integration without polling.
- **Priority:** Must have
- **Rationale:** Webhook callback, HMAC, and idempotency are inconsistently documented.
- **Acceptance criteria:**
  - Events include event ID, type, version, timestamp, tenant, resource ID, and payload.
  - HMAC is computed over the exact transmitted body.
  - Delivery retries use backoff and expose attempts/status.
  - Consumer retries and duplicate events are safe through event IDs.

### DI-004: Import sources

- **Type:** Data/Integration
- **Description:** Support source creation from pasted text first, then file, URL, RSS, and transcript imports with provenance and user review.
- **User value:** Reduces manual copying at the start of every workflow.
- **Priority:** Should have
- **Rationale:** Source acquisition is a repeated step and common automation entry point.
- **Acceptance criteria:**
  - Imported text is previewed before generation.
  - Source URL/file metadata and import timestamp are retained.
  - Extraction failures do not create empty generation jobs.
  - Users can edit imported text before use.

---

# 5.7 MoSCoW priority summary

## Must have

- BR-001, BR-002
- UR-001 through UR-005
- FR-001 through FR-005, FR-007 through FR-009, FR-011, FR-016
- NFR-001 through NFR-005
- UX-001 through UX-006, UX-008
- DI-001 through DI-003

## Should have

- BR-003, BR-004
- UR-006
- FR-006, FR-010, FR-012 through FR-015
- NFR-006
- UX-007
- DI-004

## Could have

- NFR-007
- Keyboard shortcuts and command palette
- Mobile approval optimization
- Experiment comparison for alternate hooks
- Shared stakeholder report layouts

## Won’t have for now

- Broad expansion to many additional publishing platforms before LinkedIn, Twitter/X, and Medium are reliable.
- A general-purpose no-code automation platform beyond the content-specific step set.
- Fully autonomous publication by default.
- Claims of predictive “algorithm readiness” unless calibrated against sufficient platform data.
- A marketplace before core recipes, teams, and governance are proven.

---

# 6. New opportunities

## 6.1 Saved content recipes

**Opportunity:** One-click reusable combinations of formats, voice, instructions, and publish destinations.

**Why users may want it:** Their content process is repetitive, while the current request model requires the same settings on every run.

**Evidence/reasoning:** The product already models formats, voice, custom instructions, workflows, and batch jobs. Recipes are a natural user-facing abstraction over existing capabilities and directly reduce frequent friction.

## 6.2 Performance-informed recommendations

**Opportunity:** Recommend formats, hooks, structure, or publishing time based on a user’s own connected performance history.

**Why users may want it:** Generation alone saves time, but learning what works increases outcome value.

**Evidence/reasoning:** Analytics, validation, published content, and platform metrics are already conceptualized. Once real data lineage exists, recommendations become a supported extension rather than a random AI feature.

**Constraint:** Recommendations must disclose data sufficiency and remain advisory.

## 6.3 Approval inbox and lightweight team collaboration

**Opportunity:** Central queue for variants requiring review, with comments, assigned reviewer, and approve/reject actions.

**Why users may want it:** Agencies and teams cannot safely combine automation with live publishing without human governance.

**Evidence/reasoning:** Current workflows and publishing can automate actions, but there is no approval state. This is a direct gap in a high-risk workflow.

## 6.4 Content calendar

**Opportunity:** Calendar of draft, approved, scheduled, published, partial, and failed content across connected platforms.

**Why users may want it:** Scheduling and multi-platform publishing create an inevitable need to see timing, collisions, and gaps.

**Evidence/reasoning:** The backend already has schedules, jobs, and publishing. Calendar is the user-centered visualization of those existing objects.

## 6.5 Batch import with repair loop

**Opportunity:** Import CSV or structured rows, map columns, preview validation, process, and retry only failed items.

**Why users may want it:** The current batch endpoint suits burst work but requires hand-authored JSON and offers limited recovery.

**Evidence/reasoning:** Batch processing is implemented as a core capability; the missing layer is a usable operational workflow.

## 6.6 Voice learning from accepted edits

**Opportunity:** Suggest updates to brand voice rules based on repeated differences between generated and accepted/published text.

**Why users may want it:** Users repeatedly make similar corrections and expect the system to improve.

**Evidence/reasoning:** Validation already compares draft and published text, and the product stores brand voice. With explicit consent and explainable suggestions, these can form a personalized learning loop.

**Constraint:** Changes should be proposed, previewed, and approved rather than silently modifying voice.

## 6.7 Operational quality scorecard

**Opportunity:** A workspace-level scorecard for failed jobs, stale connections, unreviewed drafts, overdue approvals, and data freshness.

**Why users may want it:** Daily users need to know what requires action more than they need another feature menu.

**Evidence/reasoning:** The system already has many asynchronous and external dependencies. Consolidating operational status addresses a likely daily bottleneck.

---

# 7. Final recommendation

## 7.1 What should be built first

The next version should not begin by adding more formats, providers, platforms, or analytics modules. It should convert the existing backend breadth into one dependable user journey.

### Release 1: trustworthy creation workspace

Build:

1. Durable tenant-scoped persistence.
2. Consistent authentication and authorization.
3. Goal-first onboarding and Create flow.
4. Persistent source and multi-variant editor.
5. Versioning, autosave, approval status, and selective regeneration.
6. Durable async jobs with clear status and recovery.
7. Explicit provider errors and no silent pseudo-AI fallback.

**Why first:** This is the highest-frequency workflow and the shortest path to repeatable user value. It also resolves the most serious trust and data-loss problems.

### Release 2: safe publish operations

Build:

1. Encrypted tenant-scoped connections.
2. Connection health and reconnection.
3. Channel validation and final-payload previews.
4. Local-time scheduling and content calendar.
5. Approval gates and partial-publication recovery.
6. Completion/failure notifications.

**Why second:** Publishing is a strong differentiator, but it should follow a reliable review workspace. Automating an immature flow increases reputational risk.

### Release 3: operational automation

Build:

1. Saved recipes.
2. Visual workflow builder.
3. Test runs and step-level run history.
4. Batch import, per-item validation, and retry-failed.
5. Signed webhooks and delivery logs.

**Why third:** These capabilities amplify repeat usage after the core object model and execution reliability are stable.

### Release 4: credible learning loop

Build:

1. Real metric adapters and provenance.
2. Honest empty/stale/partial states.
3. Explainable validation and optimization insights.
4. Performance-informed recommendations.
5. Real exports and scheduled report delivery.

**Why fourth:** Analytics should only be productized after data is real, linked to exact publications, and interpretable.

## 7.2 Immediate UI and workflow priorities

1. Replace Swagger as the primary user experience with Home, Create, Content, and Connections.
2. Make “Create from source” the primary call to action.
3. Group formats by user goal and remember favorites/recent selections.
4. Create a multi-variant editing workspace with autosave and version comparison.
5. Add an attention inbox for failures, approvals, expiring connections, and upcoming posts.
6. Move model, provider, routing, concurrency, cron, and webhook details into advanced/developer controls.
7. Show local time and next-run preview everywhere scheduling appears.
8. Never show mock data or stub completion as real success.

## 7.3 Requirements most likely to improve adoption and efficiency

The highest-impact set is:

- **BR-001:** complete value loop.
- **BR-002:** production trust.
- **UR-001:** guided first value.
- **UR-002:** persistent content workspace.
- **UR-003:** selective review and regeneration.
- **UR-004:** progress and attention management.
- **UR-005:** safe publishing control.
- **FR-001:** durable tenant-scoped model.
- **FR-004:** reliable async jobs.
- **FR-007:** secure connection lifecycle.
- **FR-008:** channel validation and preview.
- **FR-009:** local-time scheduling.
- **FR-011:** real analytics provenance.
- **UX-001 through UX-006:** clear, low-friction daily workflows.

## Closing assessment

RepurposeAI has substantial backend ambition and a credible product thesis, but the present package is closer to a broad developer-facing prototype than a finished user-centered application. The most important next-version decision is to stop expanding horizontally and instead make the most frequent journey durable, understandable, reviewable, and safe.

If the product can let a user reliably go from one saved source to several reviewed, channel-valid, scheduled outputs in a few minutes, while preserving history and clearly handling failures, it will have a stronger foundation for automation and analytics than additional scaffolded capabilities would provide.
