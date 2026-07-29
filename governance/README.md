# Golden Path governance

Organization rulesets are the default. They are targeted dynamically with the
custom property `golden_path=enabled`, so a repository joins or leaves the
standard without copying rulesets.

## Organization rulesets

| Ruleset | Target | Required evidence |
|---|---|---|
| Golden Path - Feature Branches | `feature-*` | Branch name, branch flow, quality/coverage, dependency review, CodeQL |
| Golden Path - Release Branches | `release-*` | Common evidence plus `INT Gate` |
| Golden Path - Production Main | default branch | Common evidence plus `Release Readiness` and one SemVer label |

Only the final gate names are required. Conditional child jobs such as
individual deployments are deliberately not required because an unused path
reports as skipped. Requiring those jobs creates noisy pull requests or checks
that remain Expected.

The production ruleset does not require a GitHub deployment to `prod`. The
production deployment happens after merge, so requiring it before merge would
create a circular wait. `Release Readiness` proves the appropriate EQA-only or
EQA-to-ePreProd path before the merge; the protected `prod` environment gates
the post-merge deployment.

## Repository rulesets

No repository ruleset is required for a normal Golden Path repository.
Repository rulesets are reserved for true overlays, such as a critical
application needing an extra approval. The disabled example in
`repository-rulesets/` shows the shape. Do not copy the organization rulesets
into every repository.

## One-time organization setup

1. Store an organization Actions secret named `GOLDEN_PATH_ADMIN_TOKEN` for
   this control repository. For production, use a GitHub App installation token
   rather than a personal token.
2. Run **Apply Golden Path Governance** once. It creates the custom properties,
   reconciles the organization rulesets, and marks the source repository as a
   template.
3. The workflow also creates or updates **Golden Path Security Baseline**.
   Provisioning attaches that configuration only to enrolled repositories.
4. Confirm the required check names in the sandbox before running the workflow.
   The committed POC rulesets use active enforcement.

## Per-repository setup

Run **Provision Golden Path Repository**. The workflow creates or reconciles:

- the repository from `golden-path-template-v2`;
- squash-only merge settings and read-only default workflow permissions;
- `major`, `minor`, `patch`, and supporting maintenance/exception labels;
- `eint1`-`eint6`, `eqa`, `epreprod`, and `prod` environments;
- deployment branch policies for each environment;
- `golden_path` and `release_path` custom properties; and
- the organization code-security configuration.

Supply the numeric shared-stage and production reviewer team IDs to the
provisioning workflow to configure approvals automatically. Leaving an ID
blank creates the environment without an approval rule; the workflow never
guesses governance identities.
