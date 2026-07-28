# Simplified Golden Path architecture

The design separates GitHub-native policy from pipeline execution.

## GitHub-native controls

Organization security configuration enables CodeQL default setup, GitHub Code
Quality, secret scanning, push protection, the dependency graph, and Dependabot.
Organization rulesets enforce code-scanning, quality, and coverage results.

## Centrally managed automation

- `required-pr.yml` is selected as an organization ruleset workflow. It performs
  branch policy, CI, dependency review, stage validation, and promotion-evidence
  checks as one stable required check.
- `reusable-delivery.yml` builds once, deploys the immutable artifact according
  to branch naming, records feature tags, and completes production releases.
  The production run also republishes the promoted Cobertura evidence against
  `main`, establishing the native coverage baseline without rebuilding.
  POC releases use `v0.0.<delivery-run-number>` so versioning requires no
  release label, PR lookup, or version file.
- `reusable-dast.yml` provides optional non-production DAST.

## Repository contract

Applications provide five scripts:

- `.github/golden-path/ci.sh`
- `.github/golden-path/stage-validate.sh`
- `.github/golden-path/deploy.sh`
- `.github/golden-path/smoke-test.sh`
- `.github/golden-path/production-verify.sh`

The central workflows own orchestration and policy. Application teams own only
the stack-specific commands inside these adapters.
