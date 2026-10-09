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

Pull-request CI validates merge eligibility. The Paketo application build command
runs only on publishing push events; the Dockerfile path can build without
publishing. Push CI validates the exact merged commit and, for container
delivery, publishes the image with a commit SHA, run ID, and attempt tag. Standard CD starts
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
Container delivery uses `artifact_type: container` and either a Dockerfile or
`container_build_command`. Standard CI publishes the image to ACR, captures its
digest, and uploads `deployment-metadata.json` inside `application-package`.
Standard CD downloads that descriptor from the successful exact-SHA CI run and
deploys the immutable `registry/repository@sha256:digest` reference.

## ACA MVP configuration

Set application repository variables and pass them through the CI caller:

| Reusable CI input | Application repository variable | Purpose |
| --- | --- | --- |
| `acr_name` | `ACR_NAME` | Existing ACR name without `.azurecr.io` |
| `image_repository` | `ACR_IMAGE_REPOSITORY` | Application repository path, such as `dcoe/gh-poc` |
| `pack_image` | `PACK_IMAGE` | Full approved pack CLI image reference in ACR |
| `paketo_builder_image` | `PAKETO_BUILDER_IMAGE` | Full approved Paketo builder image reference in ACR |
| `paketo_run_image` | `PAKETO_RUN_IMAGE` | Optional full ACR runtime image reference; blank uses the builder default |

```yaml
with:
  artifact_type: container
  acr_name: ${{ vars.ACR_NAME }}
  image_repository: ${{ vars.ACR_IMAGE_REPOSITORY }}
  pack_image: ${{ vars.PACK_IMAGE }}
  paketo_builder_image: ${{ vars.PAKETO_BUILDER_IMAGE }}
  paketo_run_image: ${{ vars.PAKETO_RUN_IMAGE }}
  container_build_command: bash scripts/aca-build.sh
secrets: inherit
```

The shared CI workflow receives image settings through inputs rather than
reading application variables directly. The caller can pass repository
variables or literal image references. The Paketo sample requires pack and
builder images; these inputs default to blank so package and Dockerfile
callers do not need them. All tooling and runtime images must come from ACR.
If the run-image override is blank, the approved builder's default runtime
must reference an image in ACR; otherwise set `PAKETO_RUN_IMAGE`.
No image reference or credential specific to an organization is embedded here.

Set `deployment_provider: azure-container-apps` and
`deploy_command: bash scripts/aca-deploy.sh` in the CD caller. The selected
GitHub environment supplies `AZURE_CONTAINER_APP_NAME`,
`AZURE_RESOURCE_GROUP`, `ACA_ENVIRONMENT`, and `ACA_UAMI_RESOURCE_ID`.
Optional environment variables `ACA_CPU`, `ACA_MEMORY`, `ACA_TARGET_PORT`,
and `ACA_STARTUP_COMMAND` default to `0.5`, `1Gi`, `8080`, and
`/cnb/process/web`. The custom deployment command provider remains available.

Azure login uses a service principal with GitHub OIDC federation, matching
the GitLab federated-token approach. Store these three Actions secrets in the
application repository for CI: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and
`AZURE_SUBSCRIPTION_ID`. Set the same secret names in each deployment
environment (`eint1`–`eint6`, `eqa`, `epreprod`, `prod`) for CD. Use
the ACR subscription ID for CI and the target ACA subscription ID for CD.
Environment secrets override repository secrets; set all three explicitly
for each target to avoid falling back to CI values.

No client secret or `AZURE_CREDENTIALS` JSON is used. Both callers and reusable
workflows grant `id-token: write` and callers use `secrets: inherit`.
The inline Bash login requests a temporary OIDC token from GitHub with
`curl`, extracts it with `jq`, masks it in the Actions log, then runs
`az login --service-principal --federated-token` and
`az account set --subscription`. This branch uses the GitLab-style CLI
approach instead of the `azure/login` action. The token stays in the login
step; do not save it as a secret or artifact. The hosted Ubuntu runner must
provide `curl`, `jq`, and Azure CLI.
The subsequent `az acr login --name "$ACR_NAME"` in CI authenticates Docker
to ACR using that Azure session.

The cloud team must configure the service principal's Azure federated
credentials to trust the application/caller repository, not just this shared
workflow repository. The issuer is `https://token.actions.githubusercontent.com`
and the audience is `api://AzureADTokenExchange`. CI has no GitHub environment,
so its publishing push jobs use branch-based subjects: configure trust for
the permitted feature, release, and hotfix branches, using exact credentials
or an approved flexible credential. CD uses the selected GitHub environment's
subject, including a separate `epreprod` deployment job. Match the actual
OIDC subject format emitted by the repository, including immutable repository
and owner IDs if enabled. Environment deployment rules should restrict which
branches can deploy to each target. This repository change does not create
Azure federated credentials or assign Azure permissions.

CI needs ACR push/pull access; ACA's managed identity needs pull access.
The CD principal needs target app management and permission to assign the
configured user-assigned identity. Never commit identity values or tokens.

## Promotion model

`feature-eint1-6-f###` deploys to its EINT environment. `release-eqa-*` and
`hotfix-eqa-*` stop after EQA. `release-epreprod-*` and
`hotfix-epreprod-*` pass EQA and then promote the same artifact through
ePreProd. A successful merge into `main` promotes that artifact to production,
verifies the same package or image digest, and then creates the release.

## POC pinning

The ACA sandbox CI and CD callers use `@v1.0.5a`.
Before production adoption, tag this repository and pin every caller to an
immutable version or commit SHA.
