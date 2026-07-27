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
- The automatic release chain validates that production-verification evidence belongs to the deployed main commit before tagging it.
- Production verification does not target the protected environment a second time; the production deployment is the single approval point.
- Re-running release creation is idempotent for a commit that already has its SemVer tag and GitHub Release.

## Recommended caller event model

- A push-only branch caller handles `develop-*`, `feature-*`, `release-*`, and
  `hotfix-*` CI/delivery. Keep integration and regression in that same run.
- A PR-only caller validates branch transitions and release labels.
- A main-push caller resolves the merged release/hotfix PR, promotes its
  previously built artifact, verifies production, and creates the release.
- Optional security runs on PR, schedule, or manual dispatch. Set
  `dependency_review_enabled: true` only after the dependency graph is enabled.

Do not configure the same Standard CI caller for both `push` and
`pull_request`; doing so intentionally creates two workflow runs for one commit.

## Required caller permissions

Branch CI callers normally need:

```yaml
permissions:
  actions: read
  contents: read
  pull-requests: read
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
  actions: read
  contents: write
  id-token: write
  pull-requests: read
```

## Artifact repository adapter

The POC uses GitHub Actions artifacts so it runs without enterprise credentials. For production, replace the artifact upload/download adapter with the approved Artifactory integration while retaining:

1. One version calculation
2. One immutable build
3. QA promotion
4. Production promotion
5. Post-production verification
6. Final tag and GitHub Release
