#!/usr/bin/env python3
"""Create deterministic release evidence for the generated static site."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def files_under(directory: Path):
    return sorted(path for path in directory.rglob("*") if path.is_file())


def create_tar(source: Path, destination: Path) -> None:
    with tarfile.open(destination, "w", format=tarfile.PAX_FORMAT) as archive:
        for path in files_under(source):
            relative = path.relative_to(source).as_posix()
            info = archive.gettarinfo(str(path), arcname=relative)
            info.uid = info.gid = 0
            info.uname = info.gname = "root"
            info.mtime = 0
            with path.open("rb") as handle:
                archive.addfile(info, handle)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--source-ref", default="refs/heads/main")
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--output", type=Path, default=Path("release"))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    bundle = args.output / "site.tar"
    create_tar(args.dist, bundle)
    bundle_digest = sha256(bundle)

    file_records = []
    for path in files_under(args.dist):
        relative = path.relative_to(args.dist).as_posix()
        file_records.append(
            {
                "SPDXID": f"SPDXRef-File-{hashlib.sha256(relative.encode()).hexdigest()[:16]}",
                "fileName": f"./{relative}",
                "checksums": [{"algorithm": "SHA256", "checksumValue": sha256(path)}],
            }
        )
    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "floricaltd-static-website",
        "documentNamespace": f"https://github.com/floricaltd/floricaltd-static-website/sbom/{args.source_sha}",
        "creationInfo": {"created": "1970-01-01T00:00:00Z", "creators": ["Tool: create_release_evidence.py"]},
        "packages": [
            {
                "SPDXID": "SPDXRef-Package-Site",
                "name": "floricaltd-static-website",
                "versionInfo": args.source_sha,
                "downloadLocation": f"https://github.com/floricaltd/floricaltd-static-website/tree/{args.source_sha}",
                "filesAnalyzed": True,
                "licenseConcluded": "NOASSERTION",
                "licenseDeclared": "NOASSERTION",
                "copyrightText": "Copyright Florica Ltd",
            }
        ],
        "files": file_records,
        "relationships": [
            {"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES", "relatedSpdxElement": "SPDXRef-Package-Site"},
            *[
                {"spdxElementId": "SPDXRef-Package-Site", "relationshipType": "CONTAINS", "relatedSpdxElement": item["SPDXID"]}
                for item in file_records
            ],
        ],
    }
    (args.output / "sbom.spdx.json").write_text(json.dumps(sbom, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    provenance = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": "site.tar", "digest": {"sha256": bundle_digest}}],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://github.com/floricaltd/floricaltd-static-website/.github/workflows/pages.yml",
                "externalParameters": {"sourceRef": args.source_ref},
                "resolvedDependencies": [
                    {
                        "uri": "git+https://github.com/floricaltd/floricaltd-static-website",
                        "digest": {"gitCommit": args.source_sha},
                    }
                ],
            },
            "runDetails": {"builder": {"id": "https://github.com/actions/runner"}},
        },
    }
    (args.output / "provenance.intoto.json").write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.output / "SHA256SUMS").write_text(
        f"{bundle_digest}  site.tar\n{sha256(args.output / 'sbom.spdx.json')}  sbom.spdx.json\n"
        f"{sha256(args.output / 'provenance.intoto.json')}  provenance.intoto.json\n",
        encoding="utf-8",
    )
    print(f"site.tar sha256:{bundle_digest}")


if __name__ == "__main__":
    main()
