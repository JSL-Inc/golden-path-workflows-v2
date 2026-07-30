# Golden Path Workflows v2

Central reusable GitHub Actions workflows for the golden-path proof of concept.
Application repositories keep only small event callers and their application
scripts; orchestration and gates live here.

## Reusable workflows

| File | Responsibility |
|---|---|
| `branch-validation.yml` | COUNTRY branch-name policy |
| `pr-flow.yml` | Allowed branch promotion paths |
| `code-coverage.yml` | Unit tests, JUnit, Cobertura, 80% coverage, and code quality |
| `new-deploy.yml` | Build once, deploy, test, DAST policy, gates, optional ePreProd, and production verification |
| `feature-tagging.yml` | Create the `f###` traceability tag after a feature merge |
| `pr-semver-check.yml` | Require exactly one `major`, `minor`, or `patch` label |
| `release.yml` | Create the SemVer tag and GitHub Release from the verified production artifact |
| `owasp-zap-scan.yml` | Run a manually targeted OWASP ZAP scan |

The POC callers reference `@main`. A production rollout should publish an
immutable tag such as `v2.0.0` and update callers to that tag.

See [docs/usage.md](docs/usage.md).
