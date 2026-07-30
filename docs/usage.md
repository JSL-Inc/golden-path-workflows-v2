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
| Branch name, PR flow, and coverage | Pull request |
| Branch delivery | Push to a standard branch |
| Feature tag | Feature pull request merged into a release branch |
| SemVer label | Pull request to `main` |
| Production release | Successful `Branch Delivery Pipeline` run on `main` |
| ZAP scan | Manual POC dispatch |

This separation prevents the same build pipeline from running once for `push`
and again for `pull_request`.

## Application contract

The delivery workflow calls these paths in the application repository:

- `scripts/build.sh`
- `scripts/deploy.sh`
- `scripts/unit-test.sh`
- `scripts/integration-test.sh`
- `scripts/regression-test.sh`
- `scripts/smoke-test.sh`
- `.zap/rules.tsv`

The unit-test script must emit `reports/junit/results.xml` and
`reports/coverage/cobertura.xml`; the build script must create `dist/**`.
Application function code stays in the application repository.

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
