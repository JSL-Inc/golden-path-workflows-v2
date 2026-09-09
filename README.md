# Golden Path Workflows v2

Central reusable GitHub Actions workflows for the golden-path proof of concept.
Application repositories keep only small event callers and their application
scripts; orchestration and gates live here.

## Reusable workflows

| File | Responsibility |
|---|---|
| `reusable-standard-ci.yml` | Build, unit tests, JUnit/Cobertura evidence, code quality, and the deployable artifact |
| `reusable-standard-cd.yml` | Wait for exact-SHA CI success, promote the validated artifact, deploy, test, evaluate gates, and create the production release |
| `branch-validation.yml` | COUNTRY branch-name policy |
| `pr-flow.yml` | Allowed branch promotion paths |
| `code-coverage.yml` | Legacy POC coverage workflow retained for existing callers |
| `new-deploy.yml` | Legacy combined build/deploy workflow retained for existing callers |
| `feature-tagging.yml` | Create the `f###` traceability tag after a feature merge |
| `pr-semver-check.yml` | Require exactly one `major`, `minor`, or `patch` label |
| `release.yml` | Legacy standalone release workflow retained for existing callers |
| `owasp-zap-scan.yml` | Run a manually targeted OWASP ZAP scan |

The POC callers reference `@main`. A production rollout should publish an
immutable tag such as `v2.0.0` and update callers to that tag.

See [docs/usage.md](docs/usage.md).
