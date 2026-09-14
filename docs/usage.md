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

Pull-request CI validates merge eligibility and builds container images without
publishing them. Push CI validates the exact merged commit and, for container
delivery, publishes the image to its registry by commit SHA. Standard CD starts
from the same push but cannot retrieve the deployment descriptor or deploy
until the exact-SHA push CI run succeeds.

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
`reports/coverage/cobertura.xml`. Package delivery still expects `dist/**`.
Container delivery expects a Dockerfile and uses `artifact_type: container`.
Standard CI publishes the image to ACR or a custom OCI registry, captures its
digest, and uploads `deployment-metadata.json` inside `application-package`.
Standard CD downloads that descriptor from the successful exact-SHA CI run and
deploys the immutable `registry/repository@sha256:digest` reference.

## Container providers

- `registry_provider: acr` authenticates with Azure OIDC and publishes to
  `<acr_name>.azurecr.io/<image_repository>:<commit-sha>`.
- `registry_provider: custom` accepts `registry_server` and a protected custom
  login command while preserving the OCI build and descriptor contract.
- `deployment_provider: azure-container-apps` updates the Container App named
  by the selected GitHub environment's `AZURE_CONTAINER_APP_NAME` and
  `AZURE_RESOURCE_GROUP` variables.
- `deployment_provider: custom` retains the application-owned deploy command.

Azure-backed callers must grant `id-token: write` and inherit
`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID`. Container
Apps should use managed identity with `AcrPull`; workflow credentials publish
images and update revisions but do not supply registry passwords.

## Promotion model

`feature-eint1-6-f###` deploys to its EINT environment. `release-eqa-*` and
`hotfix-eqa-*` stop after EQA. `release-epreprod-*` and
`hotfix-epreprod-*` pass EQA and then promote the same artifact through
ePreProd. A successful merge into `main` promotes that artifact to production,
verifies the same package or image digest, and then creates the release.

## POC pinning

Callers use `@main` so the demonstration reflects this repository immediately.
Before production adoption, tag this repository and pin every caller to an
immutable version or commit SHA.
