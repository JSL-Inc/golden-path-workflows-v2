# Reusable workflow usage

## Design rules

- Caller repositories own language-specific commands.
- Central workflows own orchestration, evidence validation, gates, summaries, and artifact handling.
- Unit tests execute before the build to satisfy the documented fail-fast standard.
- JUnit XML and Cobertura XML are mandatory for applications subject to the unit-testing standard.
- New applications enforce 80% line coverage. Existing low-coverage applications may temporarily set `enforce_coverage: false` with a documented, expiring exception.
- Artifacts are built once. Deployment workflows download and promote the existing artifact rather than rebuilding.
- Environment secrets remain in GitHub Environments. Reusable workflows cannot receive environment secrets through `workflow_call`; the deployment job targets the requested environment directly.
- Production release creation occurs only after production verification.
- A live release must supply the workflow-run ID containing matching, successful production-verification evidence.

## Required caller permissions

CI callers normally need:

```yaml
permissions:
  contents: read
  pull-requests: write
```

Security callers also need:

```yaml
permissions:
  contents: read
  security-events: write
  pull-requests: read
```

Release callers need:

```yaml
permissions:
  contents: write
```

## Artifact repository adapter

The POC uses GitHub Actions artifacts so it runs without enterprise credentials. For production, replace the artifact upload/download adapter with the approved Artifactory integration while retaining:

1. One version calculation
2. One immutable build
3. QA promotion
4. Production promotion
5. Post-production verification
6. Final tag and GitHub Release
