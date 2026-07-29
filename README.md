# Golden Path Workflows v2

This repository is the Golden Path control plane.

- `.github/workflows/provision-golden-path-repository.yml` creates and
  configures application repositories.
- `.github/workflows/apply-golden-path-governance.yml` reconciles organization
  properties and rulesets.
- `governance/` contains the reviewable organization policy specifications.
- The existing reusable workflows remain available for teams that choose that
  model, but the POC template uses understandable local YAML workflows and does
  not depend on callers.

See [governance/README.md](governance/README.md) for the organization rollout.

Central reusable GitHub Actions workflows for the COUNTRY GitLab-to-GitHub proof of concept.

## Workflows

| Workflow | Purpose |
|---|---|
| `reusable-ci.yml` | Dependency restore, unit tests, JUnit XML, Cobertura XML, 80% coverage gate, build, lint, and artifact publishing |
| `reusable-pr-policy.yml` | COUNTRY branch-transition validation and exact semantic-version label validation |
| `reusable-feature-id-tag.yml` | Idempotent Rally feature-ID tagging after a feature branch is merged into a release branch |
| `reusable-security.yml` | Optional CodeQL SAST and opt-in dependency review |
| `reusable-dast.yml` | OWASP ZAP scan against a non-production URL |
| `reusable-deploy.yml` | Promote an existing build artifact into a protected GitHub Environment |
| `reusable-production-verification.yml` | Post-deployment production health verification |
| `reusable-release.yml` | Idempotent semantic-version calculation and verified GitHub Release creation |

Consumers should call the `v2` release branch:

```yaml
uses: JSL-Inc/golden-path-workflows-v2/.github/workflows/reusable-ci.yml@v2
```

The `v2` branch is the POC release channel. A production implementation should use immutable release tags or commit SHAs.

Application callers should use one push-only branch workflow for CI, integration,
regression, and non-production delivery; one PR-only policy workflow; one
merge-only feature-ID tag workflow; and one main-push production-release
workflow. This keeps status checks visible without running the same CI workload
once for `push` and again for `pull_request`.

See [docs/usage.md](docs/usage.md).
