# Validation Results

Validation date: 2026-08-01

## TDD red phase

The initial workspace acceptance test run produced five expected failures: root workspace missing, project endpoints missing, validation endpoint behavior missing, telemetry endpoint missing, and capability manifest missing.

## Targeted regression

```text
33 passed
```

Covered the new workspace, health/app factory, and repurpose API compatibility.

## New workspace acceptance suite

```text
6 passed
```

Covered semantic/accessibility structure, durable CRUD/archive, field errors, privacy-safe telemetry, truthful capability reporting, and production authentication enforcement.

## Full regression

```text
1198 passed, 2 skipped, 10 xfailed
```

The ten xfailed tests are pre-existing planned-feature markers. The final full suite had zero failures.

## Static quality check for changed/new Python modules

```text
All checks passed!
```

Command scope: project workspace API, UI route, models, SQLite store, offline token fallback, and new acceptance tests. The inherited codebase still contains pre-existing lint/deprecation debt outside this changed-file scope, documented in the implementation report.

# v0.9.0 Continuation Validation

## TDD red phase

Three acceptance tests were added first and failed as expected: generation endpoint missing, variant revision/history missing, and generation controls absent from the workspace.

## New workspace suite

```text
9 passed
```

## Full regression after v0.9.0

```text
1201 passed, 2 skipped, 10 xfailed
```

No test failed. The xfails remain pre-existing planned-feature markers.

## Changed-file static validation

```text
All checks passed!
```
