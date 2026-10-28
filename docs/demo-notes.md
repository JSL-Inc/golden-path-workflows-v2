# Quality and artifact integration rehearsal

This branch starts at `v1.0.5a`, commit
`87dbafbe01ca26f1455116365850e3cbe17b7532`. It retains that version's standard
CI and ACA/CD implementation. Nothing on the original branches is replaced.

The personal repository versions inspected do not contain the Artifactory
implementation described in the supplied comparison. The
`artifactory-evidence` action is a new, isolated rehearsal adapter with a
similar package/metadata/upload/retrieval shape, not a verified copy of the
enterprise implementation. It must not be presented as earlier completed work.

`preview` creates a real archive, records the tested commit, and validates its
checksum locally. Its summary explicitly says external Artifactory and
environment deployment were not run. GitHub Actions stores that preview evidence.

`roundtrip` requires a real HTTPS Artifactory URL, generic repository key, and
access token. It uploads the archive and metadata, retrieves both, then checks
identity and checksum. It does not deploy anything, configure server retention,
or guarantee server-side immutability. The token is not written to evidence.
Redirects are refused so credentials cannot follow a different endpoint.

The adapter has local contract tests, including corrupted downloads and identity
mismatches. These tests use an in-memory transport; they do not prove live
Artifactory access. No enterprise endpoint or credential is committed here.

The only change to existing standard CI is a summary correction: package
artifacts can be published on PR events, so the summary must not describe them
as unpublished merely because the event is not a push.

The companion sandbox contains the short presenter guide and two unmerged PRs.
Both stop before environment delivery. Existing rulesets are inspected, not
weakened or replaced for this rehearsal.
