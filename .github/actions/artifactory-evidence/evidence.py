"""Isolated demo adapter. Preview is local evidence, never a successful deployment."""

import hashlib
import json
import os
from pathlib import Path
import re
import tarfile
from urllib import error, parse, request


def digest(data):
    return hashlib.sha256(data).hexdigest()


def segment(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", value):
        raise ValueError("Package coordinates must contain simple path segments")
    return value


def prepare(source, output, application, repository, sha, run_id, attempt):
    application, repository = segment(application), segment(repository)
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("A full tested commit SHA is required")
    if not run_id.isdecimal() or not attempt.isdecimal():
        raise ValueError("Numeric run ID and attempt are required")
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output or source in output.parents:
        raise ValueError("Evidence output must be outside the package source")
    files = sorted(source.rglob("*"))
    if not any(p.is_file() for p in files):
        raise ValueError("Build output is missing or empty")
    if any(p.is_symlink() for p in files):
        raise ValueError("Symlinks are not accepted in this demo package")
    output.mkdir(parents=True, exist_ok=True)
    package = output / "package.tgz"
    with tarfile.open(package, "w:gz") as archive:
        for path in files:
            if path.is_file():
                archive.add(path, arcname=str(path.relative_to(source)), recursive=False)
    metadata = {
        "schemaVersion": 1,
        "applicationId": application,
        "sourceSha": sha,
        "runId": run_id,
        "runAttempt": attempt,
        "packageFile": "package.tgz",
        "packageSha256": digest(package.read_bytes()),
        "coordinates": f"{repository}/{application}/{sha}/{run_id}-{attempt}",
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    verify(metadata, package.read_bytes(), application, sha)
    return metadata


def verify(metadata, package, application, sha):
    if metadata.get("schemaVersion") != 1:
        raise ValueError("Unsupported metadata schema")
    if metadata.get("applicationId") != application or metadata.get("sourceSha") != sha:
        raise ValueError("Artifact identity does not match the expected application/commit")
    if metadata.get("packageFile") != "package.tgz":
        raise ValueError("Unexpected package filename")
    if not package or digest(package) != metadata.get("packageSha256"):
        raise ValueError("Artifact checksum mismatch")


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Artifactory redirects are refused to protect the access token")


def transfer(method, url, token, data=None):
    headers = {"Authorization": f"Bearer {token}"}
    if data is not None:
        headers["Content-Type"] = "application/octet-stream"
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.build_opener(NoRedirect()).open(req, timeout=45) as response:
            return response.read()
    except error.HTTPError as exc:
        # Never print request headers or response bodies that might contain secrets.
        raise RuntimeError(f"Artifactory {method} failed with HTTP {exc.code}") from None
    except error.URLError:
        raise RuntimeError("Artifactory connection failed") from None


def roundtrip(output, metadata, url, token):
    parsed = parse.urlsplit(url)
    if (parsed.scheme != "https" or not parsed.netloc or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("Set a plain HTTPS Artifactory base URL without credentials")
    if not token:
        raise ValueError("A real Artifactory access token is required")
    base = url.rstrip("/") + "/" + "/".join(
        parse.quote(segment(part), safe="") for part in metadata["coordinates"].split("/")
    )
    for filename in ("package.tgz", "metadata.json"):
        transfer("PUT", base + "/" + filename, token, (output / filename).read_bytes())
    received_metadata = json.loads(transfer("GET", base + "/metadata.json", token))
    received_package = transfer("GET", base + "/package.tgz", token)
    if received_metadata != metadata:
        raise ValueError("Retrieved metadata differs from the published record")
    verify(received_metadata, received_package, metadata["applicationId"], metadata["sourceSha"])
    retrieved = output / "retrieved"
    retrieved.mkdir(exist_ok=True)
    (retrieved / "metadata.json").write_text(json.dumps(received_metadata, indent=2) + "\n")
    (retrieved / "package.tgz").write_bytes(received_package)


def main():
    mode = os.environ.get("DEMO_MODE", "preview")
    if mode not in {"preview", "roundtrip"}:
        raise ValueError("Select preview or roundtrip")
    output = Path(os.environ["DEMO_OUTPUT"]).resolve()
    metadata = prepare(
        os.environ["DEMO_SOURCE"], output, os.environ["DEMO_APPLICATION"],
        os.environ["DEMO_REPOSITORY"], os.environ["GITHUB_SHA"],
        os.environ["GITHUB_RUN_ID"], os.environ["GITHUB_RUN_ATTEMPT"],
    )
    external = "Not run — local preview only"
    if mode == "roundtrip":
        roundtrip(output, metadata, os.environ["DEMO_ARTIFACTORY_URL"],
                  os.environ.get("DEMO_ARTIFACTORY_TOKEN", ""))
        external = "Passed — real upload and download; checksum verified"
    lines = [
        "## Artifact integration evidence", "",
        "| Control | Result |", "|---|---|",
        "| Built output packaged | Passed |",
        "| Tested commit recorded | `" + metadata["sourceSha"] + "` |",
        "| Package checksum | Verified locally |",
        "| External Artifactory | " + external + " |",
        "| Environment deployment | Not run |", "",
        "Coordinates: `" + metadata["coordinates"] + "`", "",
        "This helper was added for this rehearsal. Preview does not contact Artifactory.",
        "A checksum identifies bytes; server overwrite/retention policy is a separate control.",
    ]
    report = "\n".join(lines) + "\n"
    (output / "README.md").write_text(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(report)
    print(external)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as exc:
        print(f"::error::{exc}")
        raise SystemExit(1) from None
