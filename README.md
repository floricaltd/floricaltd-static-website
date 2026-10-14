# Florica Ltd static website

A fast, accessible consultancy website generated with Python. The generator has no runtime dependencies and emits plain HTML, CSS, JavaScript, and SVG into `dist/`.

## Local development

Requires Python 3.11 or newer.

```bash
make check
make serve
```

Open <http://localhost:8000>. Edit the content in `src/florica_site/content.py`, templates in `src/florica_site/templates/`, and presentation assets in `src/florica_site/static/`.

## Build

```bash
python -m pip install -e .
florica-build
```

The output is in `dist/`. The build is deterministic and removes stale output before each run.

## Deployment

The included GitHub Actions workflow validates the project and publishes `dist/` to GitHub Pages on pushes to `main`. In the repository settings, set **Pages → Source** to **GitHub Actions**.

## Before launch

- Confirm the canonical domain in `src/florica_site/content.py`.
- Confirm the public contact email. `hello@floricaltd.com` is currently used.
- Replace the example privacy-policy company details if legal requirements differ.
- Add approved analytics only after a consent and privacy review.
