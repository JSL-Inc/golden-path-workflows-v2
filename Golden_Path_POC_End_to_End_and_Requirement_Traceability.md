# Golden Path POC

## End-to-End Flow, Repository Functions, Requirements Traceability, and Rulesets

**Repositories reviewed**

- [JSL-Inc/golden-path-workflows-v2](https://github.com/JSL-Inc/golden-path-workflows-v2)
- [JSL-Inc/golden-path-sandbox-v2](https://github.com/JSL-Inc/golden-path-sandbox-v2)

**Discovery basis:** current default branch (`main`) as of August 19, 2026.

> **Purpose:** This document explains the current proof of concept (POC), describes how code moves from development to production, maps each requirement to repository files and GitHub controls, and identifies controls that still depend on live repository or organization settings.

> **Evidence boundary:** Committed workflow and ruleset files prove design intent. They do not, by themselves, prove that a ruleset, environment reviewer, CodeQL policy, secret-scanning control, or push-protection setting is enabled in GitHub. Runtime activation must be confirmed in Settings and with test pull requests.

## 1. Executive summary

The POC demonstrates a credible GitHub golden path that translates the source GitLab standards into GitHub-native controls:

- Pull requests and rulesets provide governance.
- Reusable GitHub Actions workflows provide shared pipeline behavior.
- GitHub Environments provide deployment controls and approvals.
- GitHub Actions artifacts support build-once promotion for the POC.
- GitHub tags and Releases provide versioned production evidence.

The core POC path is represented: branch validation, source-to-target flow, unit tests, an 80% coverage threshold, code quality, artifact creation, EINT/EQA/ePreProd/prod routing, test gates, SemVer labels, feature tags, and production releases.

Production readiness still depends on activating and testing the rulesets and environments, replacing placeholder owners, pinning central workflows to immutable versions, and replacing simulated deployment/test adapters with application-specific implementations.

| Area | Current state | Interpretation |
|---|---|---|
| Pipeline mechanics | Implemented | Reusable and local workflow implementations demonstrate the intended POC flow. |
| Repository governance | Configuration-dependent | Ruleset specifications are committed, but live activation must be verified in GitHub Settings. |
| Security controls | Conditional | CodeQL, secret scanning, and push protection depend on live settings and eligibility. DAST includes policy validation and a manually dispatched ZAP scan. |
| Deployment implementation | POC adapter | Scripts validate artifacts and report success; they are not real application deployments. |
| Centralization | Mixed state | The central repository contains reusable workflows, while the sandbox still contains a mixture of thin callers and local workflow logic. |

## 2. Architecture and repository responsibilities

The intended operating model separates organization-owned orchestration from application-owned implementation details.

| Component | Primary owner | Role | Contents and controls |
|---|---|---|---|
| `golden-path-workflows-v2` | Platform / DevSecOps | Reusable policy and delivery orchestration | Branch and PR policy, quality, deployment gates, DAST wrapper, feature tagging, release automation, and usage documentation |
| `golden-path-sandbox-v2` | Application team / POC | Template and working demonstration | Event callers, scripts, sample application, `.zap` policy, governance specifications, and environment/ruleset documentation |
| GitHub repository settings | Repository administrators | Enforcement plane | Rulesets, status checks, environments, reviewers, security settings, and merge strategy |
| GitHub organization settings | Organization administrators | Scale and consistency | Organization rulesets, required workflows where supported, custom-property targeting, shared teams, and shared secrets |

### Recommended target model

Keep orchestration in the central repository and keep only thin event callers plus application adapters in consuming repositories. Pin callers to an immutable release tag such as `@v2.0.0` rather than `@main`.

This gives Platform/DevSecOps centralized control of the golden path while application teams retain responsibility for how their application builds, tests, deploys, and reports evidence.

## 3. End-to-end delivery flow

The delivery router explicitly ignores branch-creation events so a newly created branch does not deploy before a substantive push occurs.

1. A developer works on `develop-<story>`. Pull requests validate the branch name, allowed source-to-target transition, unit tests, code quality, and coverage.
2. The develop branch is merged into `feature-eintN-f###`. The feature-branch push builds once, publishes an application artifact, deploys it to `eint1` through `eint6`, runs integration and regression tests, and evaluates the INT Gate.
3. The feature branch is merged into `release-eqa-<description>` or `release-epreprod-<description>`. A successful merged feature PR creates an immutable `f###` traceability tag on the release merge commit.
4. The release or hotfix branch builds and deploys to EQA. Integration, regression, smoke, and DAST policy checks run, followed by the QA Gate.
5. For an ePreProd branch, the validated EQA artifact continues to ePreProd. Deployment, integration, regression, smoke, and DAST checks run again. Release Readiness requires QA and, when selected, ePreProd.
6. A pull request from release or hotfix to `main` requires exactly one SemVer label: `major`, `minor`, or `patch`. Main promotion reuses the previously validated release-candidate artifact instead of rebuilding it.
7. The main delivery run deploys the promoted artifact to prod, runs smoke testing and production verification, and completes successfully.
8. The Production Release workflow starts from the successful Branch Delivery Pipeline `workflow_run`, calculates the version from the merged PR label, packages the exact artifact, creates the `vX.Y.Z` tag, and publishes a GitHub Release with generated notes and traceability.

### 3.1 Branch and environment routing

| Branch pattern | Purpose | Environment | Resulting pipeline |
|---|---|---|---|
| `develop-<story>` | Development | None | Build and quality only when configured; no deployment |
| `feature-eint[1-6]-f###` | Feature | `eint1`–`eint6` | Build → deploy → integration → regression → INT Gate |
| `release-eqa-*` / `hotfix-eqa-*` | Release candidate | `eqa` | Build → deploy → integration/regression/smoke/DAST → QA Gate → Release Readiness |
| `release-epreprod-*` / `hotfix-epreprod-*` | Release candidate | `eqa`, then `epreprod` | QA Gate → ePreProd deployment/tests/DAST → ePreProd Gate → Release Readiness |
| `main` | Production | `prod` | Promote prior artifact → deploy → smoke → verification → production release |

### 3.2 Build once and promote the same artifact

The application package is built on the non-main branch and uploaded as the `application-package` Actions artifact. After the release or hotfix PR is merged, the main delivery workflow locates the successful release-candidate run and downloads that artifact.

The Production Release workflow then downloads the artifact from the successful main delivery run and attaches a versioned archive to the GitHub Release.

This preserves artifact identity across EQA, optional ePreProd, production, and release publication. It is the POC equivalent of promoting a versioned Artifactory object and avoids rebuilding different bits for production.

## 4. Current repository inventory and functions

### 4.1 Central workflow repository

| Path | Function |
|---|---|
| `.github/workflows/branch-validation.yml` | Reusable branch-name policy for develop, feature/EINT, release, and hotfix names |
| `.github/workflows/pr-flow.yml` | Reusable source-to-target branch promotion policy |
| `.github/workflows/code-coverage.yml` | Reusable Python unit-test, JUnit, Cobertura, Ruff, and 80% coverage check |
| `.github/workflows/new-deploy.yml` | Reusable branch router, build, artifact promotion, deployments, functional tests, and INT/QA/ePreProd/production gates |
| `.github/workflows/feature-tagging.yml` | Creates `f###` traceability tags after successful feature-to-release merges |
| `.github/workflows/pr-semver-check.yml` | Requires exactly one `major`, `minor`, or `patch` label on production-bound PRs |
| `.github/workflows/release.yml` | Calculates SemVer, reuses the validated artifact, and creates the production GitHub Release |
| `.github/workflows/owasp-zap-scan.yml` | Reusable/manual ZAP full-scan wrapper using the consumer repository's `.zap/rules.tsv` |
| `docs/usage.md` | Consumer contract, event model, adoption steps, artifact model, and required adapter scripts |
| `.github/CODEOWNERS` | POC ownership for central workflow changes; replace with approved Platform/AppSec teams |

### 4.2 Sandbox/template repository

| Path | Function |
|---|---|
| `.github/workflows/*.yml` | Event-triggered workflows or callers that expose status checks in the application repository |
| `scripts/build.sh` | Compiles the sample Python application and creates a checksummed artifact |
| `scripts/unit-test.sh` | Runs pytest, emits JUnit and Cobertura XML, and fails below 80% coverage |
| `scripts/deploy.sh` | POC adapter that validates the artifact and reports deployment success for the selected environment |
| `scripts/integration-test.sh` | POC adapter that writes passing integration-test evidence |
| `scripts/regression-test.sh` | POC adapter that writes passing regression-test evidence |
| `scripts/smoke-test.sh` | POC adapter that confirms the promoted artifact exists and reports smoke success |
| `testing/` | Sample application and pytest suite used to demonstrate build, unit-test, coverage, and quality controls |
| `.zap/rules.tsv` | Repository-specific ZAP alert policy |
| `.github/CODEOWNERS` | Currently assigns ownership to the POC owner; replace with Platform, AppSec, and application teams |
| `governance/rulesets/*.json` | Version-controlled intended branch and tag rulesets; specifications rather than proof of activation |
| `governance/settings.md` | Repository settings, environments, labels, checks, and adoption guidance |

> **Current-state consistency issue:** The sandbox `main` branch is not yet a perfectly thin consumer. It contains a mixture of local/full implementations and central callers, including duplicate coverage workflows. Preserve the working demo first; then reduce the template to one caller per control and update live required-check names at the same time.

### 4.3 Intended template file trees

Central repository:

```text
golden-path-workflows-v2/
├── .github/
│   ├── CODEOWNERS
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── dependabot.yml
│   └── workflows/
│       ├── branch-validation.yml
│       ├── pr-flow.yml
│       ├── code-coverage.yml
│       ├── new-deploy.yml
│       ├── feature-tagging.yml
│       ├── pr-semver-check.yml
│       ├── release.yml
│       └── owasp-zap-scan.yml
├── docs/
│   └── usage.md
└── README.md
```

Application template or sandbox:

```text
golden-path-sandbox-v2/
├── .github/
│   ├── CODEOWNERS
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── dependabot.yml
│   └── workflows/                  # thin event callers only
├── .zap/
│   └── rules.tsv                   # AppSec-owned repository policy
├── scripts/                        # application-owned adapters
│   ├── build.sh
│   ├── deploy.sh
│   ├── unit-test.sh
│   ├── integration-test.sh
│   ├── regression-test.sh
│   └── smoke-test.sh
├── testing/                        # sample application and unit tests
├── governance/
│   ├── environments.json
│   ├── labels.json
│   ├── settings.md
│   └── rulesets/
│       ├── feature-prerelease.json
│       ├── release.json
│       ├── main.json
│       └── tags.json
├── docs/
├── requirements.txt
└── README.md
```

## 5. Requirements traceability matrix

| Requirement | Mechanism/evidence | Primary location | Status |
|---|---|---|---|
| Governed source control and review | Pull requests, CODEOWNERS, branch/tag rulesets | Sandbox `.github/` and `governance/rulesets/` | Configuration-dependent |
| Branch naming | `Branch Name` status check validates approved patterns | `branch-validation.yml` | Implemented |
| Allowed branch progression | `Branch Flow` validates source and target | `pr-flow.yml` | Implemented |
| PR validation | Policy, unit, coverage, quality, and security checks | Sandbox callers and central reusables | Implemented |
| Build | Compile, package, checksum, and `application-package` artifact | `new-deploy.yml`, `scripts/build.sh` | Implemented |
| Unit tests | pytest failures block the workflow | `scripts/unit-test.sh` | Implemented |
| JUnit reporting | JUnit XML uploaded as evidence | `reports/junit/results.xml` | Implemented |
| Code coverage | Cobertura XML and `--cov-fail-under=80` | Unit-test script and coverage workflow | Implemented |
| Code quality | Ruff lint and formatting checks | Delivery/coverage workflow | Implemented |
| SAST | Require CodeQL/code-scanning results | GitHub Security settings and ruleset | Configuration-dependent |
| Secret scanning and push protection | GitHub repository security settings | Settings, not workflow source | Configuration-dependent |
| Dependency scanning | Dependabot and optional dependency review | `.github/dependabot.yml` | Conditional |
| Artifact publishing | Actions artifact named `application-package` | `new-deploy.yml` | Implemented for POC |
| INT deployment | Feature route to `eint1`–`eint6` Environment | `new-deploy.yml` | Implemented for POC |
| Integration tests | Environment-specific adapter and evidence | `scripts/integration-test.sh` | Implemented for POC |
| Regression tests | Environment-specific adapter and evidence | `scripts/regression-test.sh` | Implemented for POC |
| Smoke tests | Artifact and environment smoke validation | `scripts/smoke-test.sh` | Implemented for POC |
| INT Gate | Requires EINT deployment, integration, and regression success | `new-deploy.yml` | Implemented |
| EQA deployment and QA Gate | Protected environment plus integration/regression/smoke/DAST | `new-deploy.yml`, `eqa` Environment | Configuration-dependent |
| ePreProd path | Optional EQA-to-ePreProd promotion and gate | `new-deploy.yml`, `epreprod` Environment | Implemented/conditional |
| DAST | Policy validation and manually dispatched full ZAP scan | `.zap/rules.tsv`, `owasp-zap-scan.yml` | POC/conditional |
| Production approval | Protected `prod` Environment reviewers | GitHub Environment settings | Configuration-dependent |
| Production deployment | Promotes the validated artifact to prod | `new-deploy.yml` | Implemented for POC |
| Production verification | Post-deployment verification job | `new-deploy.yml` | Implemented for POC |
| Feature traceability | `f###` tag after successful feature-to-release merge | `feature-tagging.yml` | Implemented |
| Semantic versioning | Exactly one `major`, `minor`, or `patch` PR label | `pr-semver-check.yml` | Implemented |
| Release creation | `workflow_run` creates `vX.Y.Z`, notes, and build asset | `release.yml` | Implemented |
| Monitoring/logging hooks | No real Splunk, Dynatrace, or Azure Monitor integration | Not supplied | Gap |
| Change/CAB evidence | No ServiceNow, Rally, or RSAM integration | Not supplied | Gap |
| Reusable template | Central workflows plus documented consumer contract | Central workflows and `docs/usage.md` | Implemented; cleanup needed |

## 6. Rulesets and enforcement discovery

The sandbox contains four version-controlled ruleset specifications. An `enforcement: active` value in JSON describes the intended imported configuration; it does not prove that GitHub is enforcing the rule.

Confirm each ruleset under **Settings → Rules → Rulesets** and validate it with a pull request before treating the requirement as complete.

### 6.1 Application repository rulesets

| Ruleset | Target branches/tags | Branch/tag rules | Required checks |
|---|---|---|---|
| `golden-path-feature-branches-v2` | `feature-*` | 1 approval; dismiss stale reviews; approval after last push; resolve conversations; squash only; block deletion and force push | `Branch Name`, `Branch Flow`, `Coverage 80%`, `Build and Quality Checks` |
| `golden-path-release-branches-v2` | `release-*` | 2 approvals; dismiss stale reviews; approval after last push; resolve conversations; squash only; block deletion and force push | `Branch Name`, `Branch Flow`, `Coverage 80%`, `INT Gate` |
| `golden-path-main-v2` | `main` | 2 approvals; dismiss stale reviews; approval after last push; resolve conversations; squash only; block deletion and force push | `Branch Name`, `Branch Flow`, `Coverage 80%`, `Release Label`, `Release Readiness` |
| `golden-path-managed-tags-v2` | `v*` and `f*` tags | Block deletion and non-fast-forward updates | None |

### 6.2 Central workflow repository protection

The central workflow repository should use a separate `main` ruleset because a change there can affect every consuming repository.

Recommended central rule:

- **Name:** `central-workflow-main-protection`
- **Target:** `main`
- Require pull requests.
- Require at least one approval.
- Require CODEOWNERS review.
- Require conversation resolution.
- Block deletion and force push.
- Do not require application-specific checks unless this repository has dedicated workflow-contract tests that emit those contexts.

### 6.3 Repository-level versus organization-level controls

| Control plane | Best use | Operational implication |
|---|---|---|
| Repository-level ruleset | POC and repository-specific exceptions | Directly targets sandbox branches and checks that have run in that repository; easiest to test and tune |
| Organization-level ruleset | Scaled golden-path adoption | Applies the same protections to selected repositories, ideally using a custom property such as `golden_path=enabled`; required status checks still must be emitted in each target repository |
| Organization required workflow | Non-optional baseline controls where the GitHub plan supports it | Guarantees a workflow runs across selected repositories; emitted status-check names must remain stable |

Central workflow jobs do execute on behalf of the calling repository, so their status contexts appear on the caller repository's pull request. However, GitHub must have observed the exact context in each target repository before it can be safely required there.

### 6.4 Ruleset activation and test checklist

- Confirm **Enforcement** is **Active**, not **Evaluate** or **Disabled**.
- Confirm include patterns exactly match `feature-*`, `release-*`, `main`, and `v*`/`f*` tags.
- Decide whether `hotfix-*` needs its own protected-branch ruleset or intentionally remains flexible under the emergency process.
- Run every intended required check once in the repository before adding it to a ruleset.
- Copy the exact check context shown on a PR. Reusable workflow and caller prefixes can make the displayed context differ from the YAML job name.
- Verify branch creation is not blocked by a check that only runs after a substantive push.
- Test direct push, force push, deletion, stale review dismissal, last-push approval, unresolved conversations, a missing SemVer label, a failing unit test, and coverage below 80%.
- Verify CodeQL/code scanning, secret scanning, and push protection separately in Security settings.
- Capture screenshots or exported settings after validation. Repository source alone is not sufficient audit evidence of live enforcement.

## 7. Security and quality control notes

### 7.1 Code quality does not duplicate code scanning

Ruff and CodeQL serve different purposes:

- **Ruff** enforces formatting, style, and maintainability conventions.
- **CodeQL** finds security-relevant data flows and vulnerable code patterns.

Requiring code-scanning results does not replace linting or formatting. The POC should retain both, while live CodeQL enforcement is enabled and verified separately.

### 7.2 DAST ownership model

The central workflow should own the scanner implementation, action version, evidence format, and default behavior. The consuming repository should retain `.zap/rules.tsv` because its rules reflect application-specific endpoints and accepted findings.

The `.zap/rules.tsv` file should be CODEOWNED by AppSec. This prevents an application developer from silently weakening DAST by deleting or downgrading every rule while preserving the repository-specific configuration model.

The current sandbox CODEOWNERS assignment is a POC placeholder. Before production, replace it with the approved AppSec team and require code-owner review in the applicable branch ruleset.

### 7.3 Credential ownership

The POC does not embed credentials. In production:

- Prefer OIDC and short-lived identities over stored credentials.
- Scope secrets to the specific GitHub Environment.
- Let the platform team define the approved mechanism.
- Let the application or target-system owner request and approve access.
- Let the credential owner control rotation and permitted use.
- Prevent untrusted pull-request code from accessing production credentials.

## 8. Known gaps, risks, and cleanup before production

| Risk or limitation | Production action |
|---|---|
| Live enforcement is not proven | Validate rulesets and security settings in GitHub and run negative tests |
| Mixed caller/local workflow state | Consolidate only after the demo; update required-check names atomically |
| Duplicate coverage workflows | Select one caller and remove the legacy file after ruleset migration |
| Mutable workflow references | Publish an approved version such as `v2.0.0` and pin callers to it or a commit SHA |
| POC deployment/test adapters | Replace print/pass adapters with real deployment and Robot/API/UI test implementations |
| DAST is partly advisory | Define target URLs, authentication, thresholds, evidence, and blocking policy |
| Actions artifacts are not Artifactory | Define enterprise artifact retention, immutability, access, and repository integration |
| Enterprise integrations are absent | Add ServiceNow/CAB, Rally, RSAM exception, and observability hooks if required |
| Placeholder ownership | Replace the POC user with Platform, AppSec, application, and release teams |
| Hotfix governance is unresolved | Document emergency approval, bypass, and audit expectations |

## 9. Recommended productionization sequence

1. Freeze the demonstrated POC behavior and record the exact passing status-context names.
2. Clean the sandbox into thin callers plus application adapters. Remove duplicate workflows only after updating required checks.
3. Replace POC owners with approved Platform, AppSec, application, and release-management teams.
4. Publish an immutable central workflow release and pin callers to that tag or commit SHA.
5. Create and activate rulesets, labels, and environments through a repeatable bootstrap/API process; verify each with negative tests.
6. Replace POC build, deployment, and test scripts with supported language templates and real environment integrations.
7. Integrate CodeQL, secret scanning, push protection, dependency review, blocking DAST, enterprise artifact storage, approvals, and observability according to application risk tier.
8. Capture workflow artifacts, ruleset exports/screenshots, environment approvals, release evidence, and exception records as the acceptance package.

## 10. Acceptance evidence checklist

- [ ] An invalid branch name fails `Branch Name`.
- [ ] An unsupported source-to-target pair fails `Branch Flow`.
- [ ] A failing unit test or coverage below 80% blocks merge and preserves JUnit/Cobertura evidence.
- [ ] A feature push deploys to the correct EINT environment, and the INT Gate passes only after integration and regression tests.
- [ ] A successful feature-to-release merge creates the expected `f###` tag; closing without merge creates no tag.
- [ ] A `release-eqa-*` branch completes EQA and Release Readiness without ePreProd.
- [ ] A `release-epreprod-*` branch requires both QA and ePreProd gates.
- [ ] A production-bound PR without exactly one SemVer label is blocked.
- [ ] Main reuses the release-candidate artifact, deploys to prod, verifies production, and triggers one Production Release run.
- [ ] The GitHub Release includes a `vX.Y.Z` tag, source/PR/delivery traceability, generated notes, and the versioned build artifact.
- [ ] Direct push, force push, deletion, approval, conversation, CodeQL, secret-scanning, and push-protection tests behave as configured.

## 11. Source links

- [Central workflow repository](https://github.com/JSL-Inc/golden-path-workflows-v2)
- [Sandbox/template repository](https://github.com/JSL-Inc/golden-path-sandbox-v2)
- [Sandbox governance settings](https://github.com/JSL-Inc/golden-path-sandbox-v2/blob/main/governance/settings.md)
- [Feature ruleset specification](https://github.com/JSL-Inc/golden-path-sandbox-v2/blob/main/governance/rulesets/feature-prerelease.json)
- [Release ruleset specification](https://github.com/JSL-Inc/golden-path-sandbox-v2/blob/main/governance/rulesets/release.json)
- [Main ruleset specification](https://github.com/JSL-Inc/golden-path-sandbox-v2/blob/main/governance/rulesets/main.json)
- [Managed-tags ruleset specification](https://github.com/JSL-Inc/golden-path-sandbox-v2/blob/main/governance/rulesets/tags.json)
- [Central consumer contract](https://github.com/JSL-Inc/golden-path-workflows-v2/blob/main/docs/usage.md)

## Conclusion

The repositories are sufficient to demonstrate the golden-path concept and trace the source standards to GitHub controls. The next maturity step is enforcement and operationalization rather than additional workflow complexity: activate and test the rulesets, configure protected environments and security settings, clean the consumer into thin callers, pin the central workflows, and replace simulated adapters with real application integrations.
