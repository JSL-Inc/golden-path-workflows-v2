# Golden Path Workflows v2

Central reusable GitHub Actions workflows for the golden-path proof of concept.
Application repositories keep only small event callers and their application
scripts; orchestration and gates live here.

## Reusable workflows

| File | Responsibility |
|---|---|
| `reusable-standard-ci.yml` | Build, test, evidence, package publication, or immutable OCI image publication to ACR |
| `reusable-standard-cd.yml` | Wait for exact-SHA CI, promote package/image metadata, deploy to Azure Container Apps or a custom provider, test, gate, and release |
| `branch-validation.yml` | Branch-name policy |
| `pr-flow.yml` | Allowed branch promotion paths |
| `code-coverage.yml` | Legacy POC coverage workflow retained for existing callers |
| `new-deploy.yml` | Legacy combined build/deploy workflow retained for existing callers |
| `feature-tagging.yml` | Create the `f###` traceability tag after a feature merge |
| `pr-semver-check.yml` | Require exactly one `major`, `minor`, or `patch` label |
| `release.yml` | Legacy standalone release workflow retained for existing callers |
| `owasp-zap-scan.yml` | Run a manually targeted OWASP ZAP scan |

The ACA sandbox CI and CD callers reference `@v1.0.4a`. A production rollout
should publish an immutable tag such as `v2.0.0` and update callers to that tag.

See [docs/usage.md](docs/usage.md).

## ACA MVP configuration

Configure values in the application repository, not in this shared workflow
repository. The reusable workflow inputs form the interface; repository
variables store the application's values.

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

CD keeps `deploy_command: bash scripts/aca-deploy.sh`. Each selected GitHub
environment supplies `AZURE_CONTAINER_APP_NAME`, `AZURE_RESOURCE_GROUP`,
`ACA_ENVIRONMENT`, and `ACA_UAMI_RESOURCE_ID`. Optional environment variables
are `ACA_CPU`, `ACA_MEMORY`, `ACA_TARGET_PORT`, and `ACA_STARTUP_COMMAND`
(defaults: `0.5`, `1Gi`, `8080`, and `/cnb/process/web`).

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
`azure/login@v2` requests the temporary token and exchanges it with Azure.
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

`IMAGE_TAG`, digest/reference metadata, and `GITHUB_OUTPUT` are supplied by the
pipeline, not configured as GitHub variables.
