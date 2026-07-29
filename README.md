# Golden Path Workflows v2

This repository is the Golden Path control plane.

| Location | Responsibility |
|---|---|
| `.github/workflows/provision-golden-path-repository.yml` | Create and configure application repositories |
| `.github/workflows/apply-golden-path-governance.yml` | Reconcile organization properties and rulesets |
| `governance/org-rulesets/` | Reviewable organization policy |
| `governance/code-security/` | CodeQL, dependency, and secret-protection baseline |
| `governance/repository-rulesets/` | Optional stricter repository overlay example |

The application template intentionally uses local, readable YAML workflows.
New applications do not call the reusable workflows that remain in this
repository from earlier POC experiments.

See [governance/README.md](governance/README.md) for rollout and
[golden-path-template-v2](https://github.com/JSL-Inc/golden-path-template-v2)
for the application-facing pipeline.
