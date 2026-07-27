# Golden Path Workflows v2

Central reusable GitHub Actions workflows for the COUNTRY GitLab-to-GitHub proof of concept.

## Workflows

| Workflow | Purpose |
|---|---|
| `reusable-ci.yml` | Dependency restore, unit tests, JUnit XML, Cobertura XML, 80% coverage gate, build, lint, and artifact publishing |
| `reusable-pr-policy.yml` | COUNTRY branch-transition validation and exact semantic-version label validation |
| `reusable-security.yml` | CodeQL SAST and dependency review |
| `reusable-dast.yml` | OWASP ZAP scan against a non-production URL |
| `reusable-deploy.yml` | Promote an existing build artifact into a protected GitHub Environment |
| `reusable-production-verification.yml` | Post-deployment production health verification |
| `reusable-release.yml` | Semantic-version calculation and verified GitHub Release creation |

Consumers should call the `v2` release branch:

```yaml
uses: JSL-Inc/golden-path-workflows-v2/.github/workflows/reusable-ci.yml@v2
```

The `v2` branch is the POC release channel. A production implementation should use immutable release tags or commit SHAs.

See [docs/usage.md](docs/usage.md).
