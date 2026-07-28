# Golden Path Workflows v2 — simplified version 2

Central GitHub Actions implementation for the GitLab-to-GitHub Golden Path POC.

This branch intentionally reduces the runtime surface to:

- one organization-required pull-request workflow
- one reusable branch-delivery workflow
- one optional reusable DAST workflow
- two shared composite actions for CI and stage validation

For this POC, production releases need no label or version file. A successful
production promotion automatically creates `v0.0.<delivery-run-number>`.

GitHub-native rulesets enforce CodeQL code scanning, Code Quality, and the 80%
coverage threshold. Secret scanning, push protection, Dependabot, and security
feature enablement belong to organization settings rather than custom workflow
checks.

See:

- [Architecture](docs/architecture.md)
- [Onboarding](docs/onboarding.md)
- [Demo](docs/demo.md)

During branch testing, callers use `@simplified-version-2`. Promote central
references to an immutable release tag before production adoption.
