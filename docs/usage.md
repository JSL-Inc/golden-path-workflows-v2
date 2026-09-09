# Reusable workflow usage

## Repository split

- `golden-path-workflows-v2` owns reusable workflow logic.
- Each application repository owns the triggers in `.github/workflows`, the
  language-specific commands in `scripts`, its tests, and `.zap/rules.tsv`.
- Workflow files must remain directly under `.github/workflows`; GitHub does
  not discover callers in a nested `golden-path` directory.

## Event model

| Caller | Event |
|---|---|
| Branch name and PR flow | Pull request |
| Standard CI | Pull request and push to a standard branch |
| Standard CD | Push to a deployable standard branch; waits for successful push CI on the exact commit SHA |
| Feature tag | Feature pull request merged into a release branch |
| SemVer label | Pull request to `main` |
| Production release | Final job in Standard CD after successful production verification |
| ZAP scan | Manual POC dispatch |

Pull-request CI validates merge eligibility. Push CI validates and packages the
exact merged commit. Standard CD starts from the same push but cannot retrieve
the artifact or deploy until the exact-SHA push CI run succeeds.

## Application contract

The CI workflow calls these paths in the application repository:

- `scripts/build.sh`
- `scripts/unit-test.sh`

The CD workflow calls these paths in the application repository:

- `scripts/deploy.sh`
- `scripts/integration-test.sh`
- `scripts/regression-test.sh`
- `scripts/smoke-test.sh`
- `.zap/rules.tsv`

The unit-test script must emit `reports/junit/results.xml` and
`reports/coverage/cobertura.xml`; the build script must create `dist/**`.
Application function code stays in the application repository. Standard CI
publishes `application-package`; Standard CD downloads that artifact from the
successful CI run for the same commit and republishes it for deployment jobs.

## Promotion model

`feature-eint1-6-f###` deploys to its EINT environment. `release-eqa-*` and
`hotfix-eqa-*` stop after EQA. `release-epreprod-*` and
`hotfix-epreprod-*` pass EQA and then promote the same artifact through
ePreProd. A successful merge into `main` promotes that artifact to production,
verifies it, and then creates the release.

## POC pinning

Callers use `@main` so the demonstration reflects this repository immediately.
Before production adoption, tag this repository and pin every caller to an
immutable version or commit SHA.
