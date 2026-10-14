# Florica Ltd static website

A fast, accessible consultancy website generated with Python. The generator has no runtime dependencies and emits plain HTML, CSS, JavaScript, and SVG into `dist/`.

The production deployment is a GitHub project site at
<https://floricaltd.github.io/floricaltd-static-website/>. Its default base path
is `/floricaltd-static-website/`; override `SITE_BASE_PATH` and `SITE_ORIGIN`
only when deliberately building for a different host.

## Local development

Requires Python 3.11 or newer.

```bash
make check
make serve
```

Open <http://localhost:8000/floricaltd-static-website/>. Edit the content in
`src/florica_site/content.py`, templates in `src/florica_site/templates/`,
and presentation assets in `src/florica_site/static/`.

## Build

```bash
python -m pip install --require-hashes -r requirements-build.txt
python -m pip install --no-build-isolation --no-deps .
florica-build
```

The output is in `dist/`. The build is deterministic and removes stale output
before each run. To build for another path:

```bash
SITE_ORIGIN=https://example.com SITE_BASE_PATH=/site/ florica-build
```

Generate the deterministic site archive, SPDX SBOM, checksums, and local in-toto
provenance statement with:

```bash
make evidence
```

## Deployment

The SHA-pinned GitHub Actions workflow validates every pull request. A push to
protected `main` builds and tests once, publishes that same `dist/` tree as
the Pages artifact, retains release evidence, creates a GitHub artifact
attestation for `site.tar`, and deploys through the protected `github-pages`
environment. Pages must use **GitHub Actions** as its source.

The workflow has no manual or arbitrary-ref deployment trigger. Repository
administrators should require pull requests, one approving review, the build
check, signed commits, and conversation resolution on `main`. The
`github-pages` environment should disallow administrator bypass and accept
deployments only from protected branches. A required environment reviewer must
be a human other than the deployment actor; this cannot be safely automated by
the workflow itself.

## Rollback

Revert the faulty commit through a reviewed, signed pull request to `main`.
The resulting push rebuilds, attests, and deploys the previous content under a
new auditable SHA. If GitHub Pages itself is impaired, disable Pages temporarily
rather than deploying an untested artifact or bypassing protections. Retained
`release-evidence-<SHA>` artifacts and attestations provide the digest and SBOM
needed to compare the rollback build.

## Before launch

- Confirm the public contact email. `hello@floricaltd.com` is currently used.
- Replace the example privacy-policy company details if legal requirements differ.
- Add approved analytics only after a consent and privacy review.
