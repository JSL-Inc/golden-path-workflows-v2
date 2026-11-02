# Rally defect management for INT/QA and ePreProd

This branch replaces the former integration checks in INT/QA and ePreProd
with calls to an external defects composite action. It does not implement
integration testing. Regression testing remains a separate job. Deployment,
artifact promotion, and branch selection are unchanged; the route flag and
job references are now consistently named `defect_management`.

## Replace the action reference

In both defect-management jobs in `.github/workflows/reusable-standard-cd.yml`, replace:

```yaml
uses: REPLACE-WITH-OWNER/REPLACE-WITH-REPOSITORY/actions/defects-gate@REPLACE-WITH-REF
```

Use the approved repository, directory containing `action.yml`, and version or
commit SHA. GitHub requires this reference to be literal; it cannot be passed
through a workflow input. The placeholder is intentional and will not resolve
until replaced. No external action implementation or organization-specific
repository link is included in this branch.

Reference links to fill in within your approved internal copy:

- Action documentation: `REPLACE_WITH_ACTION_DOCUMENTATION_LINK`
- Rally project: `REPLACE_WITH_RALLY_PROJECT_LINK`
- Defect policy: `REPLACE_WITH_DEFECT_POLICY_LINK`

## Configure the application caller

Point the application CD caller at this branch and pass its Rally settings:

```yaml
jobs:
  delivery:
    uses: JSL-Inc/golden-path-workflows-v2/.github/workflows/reusable-standard-cd.yml@personal-sp-test-rally-defects
    with:
      # Retain the caller's existing deployment and artifact inputs here.
      rally_url: ${{ vars.RALLY_URL }}
      rally_workspace_id: ${{ vars.RALLY_WORKSPACE_ID }}
      rally_project_id: ${{ vars.RALLY_PROJECT_ID }}
      rally_release_name: ${{ vars.RALLY_RELEASE_NAME }}
      rally_extra_filters: ${{ vars.RALLY_EXTRA_FILTERS }}
      rally_severity_field: Priority
      rally_severity_values: Critical,High
      rally_exclude_states: Closed
      rally_include_child_projects: false
      defects_enforce: true
      defects_runner: ubuntu-latest
    secrets: inherit
```

The caller example shows the new settings; merge them into the existing caller
rather than removing its current inputs. No application repository is modified
by this branch.

Set `RALLY_URL`, `RALLY_WORKSPACE_ID`, and `RALLY_PROJECT_ID` in application
repository variables. Store a read-only ALM WSAPI API key in the application
repository secret `RALLY_API_KEY`. Its account must be able to read the selected
workspace, project, and any child projects included in the query. Never put
the key in YAML or commit a real ID or internal link into this template.

`RALLY_RELEASE_NAME` and `RALLY_EXTRA_FILTERS` are optional. An empty release
queries all releases in the selected scope. Extra filters follow the external
action's format, one condition per line. Match severity values and excluded
states to the actual Rally configuration. Child projects are excluded by
default to avoid unintentionally counting another team's defects.

The action receives the routed label (`eint1` through `eint6`, or `eqa`) for
INT/QA and `epreprod` for ePreProd reporting. That label does not itself filter
Rally records. All stages query
the same configured scope unless the caller supplies different settings in
its respective runs. Add the appropriate application/release/environment
filters when a narrower population is required.

The job reads the supplied workflow inputs and repository-level secret; it
does not bind a GitHub deployment environment or automatically load its
environment-level settings. The runner needs Bash, Python 3, pip, and access
to Rally, the external action repository, and its dependency source. Change
`defects_runner` to an approved runner label when required.

## Results and enforcement

The external action owns the query, threshold evaluation, outputs, and JSON
artifact upload. The calling workflow has no second enforcement or upload
step. The fixed maximum blocking count is zero.

| Scenario | Expected defects-job result | INT/QA/ePreProd behavior |
| --- | --- | --- |
| No blocking defects | Success | Other stage checks must also succeed |
| Blocking defects, `defects_enforce: true` | Failure | Aggregate gate fails |
| Blocking defects, `defects_enforce: false` | Success with a failing policy verdict/warning | Other checks still control the aggregate gate |
| Authentication, query, configuration, or dependency error | Failure | Aggregate gate fails; an error must never mean zero defects |
| Defects job unexpectedly skipped or cancelled | Not success | Aggregate gate fails for an applicable stage |

The jobs are `defect_management` and `preprod_defect_management`. The route
output, job dependencies, and INT/QA/ePreProd gate result references use these
names throughout. Both jobs expose `verdict` and `defect_count` outputs for
reporting. Aggregate gates evaluate the job result so that warning mode is
respected; they do not independently enforce `verdict`.
QA failure continues to block ePreProd deployment and Release Readiness.
ePreProd defects failure fails its aggregate gate and Release Readiness.
The existing INT Gate remains available for the repository's merge policy.
Remove the obsolete `integration_test_command` input from any custom caller.
Application URLs remain in the deployment, regression, smoke, and production
verification paths; they are not inputs to defect management.

## Mock testing

For a mock run, commit sanitized JSON at `demo/rally_two.json` in the application
repository and pass `rally_mock_response: demo/rally_two.json` through the
application CD caller. Both defects jobs then check out that caller repository
before invoking the action. The file must exist on the tested application
commit. The same mock input applies to INT/QA and ePreProd when those stages run.
With the default empty input, no checkout is needed and the action queries live
Rally. Clear the mock input to resume live checks. Mock results only verify
pipeline behavior; they do not provide evidence of a successful live Rally query.

Before enabling the live integration, verify the external action contract:

- It accepts the inputs supplied by the caller and emits `verdict` and
  `defect-count` step outputs.
- It writes its result file and outputs before exiting nonzero on an enforced
  policy failure; the result upload runs after failure unless cancelled.
- It reports infrastructure/query errors distinctly and fails on them even
  when policy enforcement is disabled.
- API requests have bounded timeouts and count every matching result, including
  paginated results.
- It does not require a checkout of the application repository for live reads.

No successful fallback is configured. Until the action references and either
the live configuration or mock data are supplied, this is an integration template rather
than a working live Rally check. Validate clean, blocking, warning-only, and
API-error cases with an approved test project before adopting it.
