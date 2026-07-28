# Application onboarding

1. Create the repository from `golden-path-template-v2`.
2. Replace the commands in the five `.github/golden-path/` adapter scripts.
3. Confirm CI produces:
   - `reports/junit/results.xml`
   - `reports/coverage/cobertura.xml`
   - at least one file under `dist/`
4. Create the GitHub Environments used by the application.
5. Add the repository to the Golden Path organization rulesets.
6. Enable the approved organization security configuration.
7. Run one pull request and one branch delivery before activating enforcement.

The `pull-request.yml` caller is retained for this isolated POC. Once
`required-pr.yml` is enforced as an organization ruleset workflow, remove the
repository caller to prevent the same validation from running twice.
