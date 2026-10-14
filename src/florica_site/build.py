"""Dependency-free static site generator for Florica Ltd."""

from __future__ import annotations

import html
import json
import shutil
from datetime import date
from pathlib import Path
from string import Template

from .content import NAVIGATION, PRINCIPLES, PRODUCTS, SERVICES, SITE

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parents[1]
TEMPLATE_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"
OUTPUT_DIR = PROJECT_DIR / "dist"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def navigation() -> str:
    return "\n".join(
        f'<a href="{esc(url)}">{esc(label)}</a>' for label, url in NAVIGATION
    )


def service_cards() -> str:
    cards = []
    for item in SERVICES:
        tags = "".join(f"<li>{esc(tag)}</li>" for tag in item["tags"])
        cards.append(
            f"""<article class="service-card reveal">
  <span class="service-number">{esc(item['number'])}</span>
  <h3>{esc(item['title'])}</h3>
  <p>{esc(item['text'])}</p>
  <ul class="tag-list" aria-label="Capabilities">{tags}</ul>
</article>"""
        )
    return "\n".join(cards)


def product_cards() -> str:
    cards = []
    for item in PRODUCTS:
        cards.append(
            f"""<article class="product-card reveal">
  <p class="eyebrow">{esc(item['eyebrow'])}</p>
  <h3>{esc(item['title'])}</h3>
  <p>{esc(item['text'])}</p>
  <p class="product-outcome"><span aria-hidden="true">↗</span> {esc(item['outcome'])}</p>
</article>"""
        )
    return "\n".join(cards)


def principles() -> str:
    return "\n".join(
        f"""<li class="principle reveal"><h3>{esc(title)}</h3><p>{esc(text)}</p></li>"""
        for title, text in PRINCIPLES
    )


def render_page(template_name: str, output: str, *, title: str, description: str, **context: str) -> None:
    template = Template((TEMPLATE_DIR / template_name).read_text(encoding="utf-8"))
    canonical = f"{SITE['url']}{'/' if output == 'index.html' else '/' + output.removesuffix('index.html')}"
    schema = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": SITE["name"],
        "url": SITE["url"],
        "email": SITE["email"],
        "description": SITE["description"],
        "areaServed": "Worldwide",
        "knowsAbout": ["Artificial intelligence", "Technology strategy", "Digital product engineering", "Automation"],
    }
    values = {
        "site_name": esc(SITE["name"]),
        "page_title": esc(title),
        "description": esc(description),
        "canonical": esc(canonical),
        "email": esc(SITE["email"]),
        "navigation": navigation(),
        "year": str(date.today().year),
        "schema": json.dumps(schema, separators=(",", ":")),
        **context,
    }
    rendered = template.safe_substitute(values)
    destination = OUTPUT_DIR / output
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8")


def build() -> Path:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(STATIC_DIR, OUTPUT_DIR / "assets")

    render_page(
        "index.html",
        "index.html",
        title="Florica Ltd — AI & technology, made useful",
        description=SITE["description"],
        service_cards=service_cards(),
        product_cards=product_cards(),
        principles=principles(),
    )
    render_page(
        "about.html",
        "about/index.html",
        title="About — Florica Ltd",
        description="Meet the practical, senior-led consultancy behind Florica Ltd.",
    )
    render_page(
        "privacy.html",
        "privacy/index.html",
        title="Privacy — Florica Ltd",
        description="How Florica Ltd handles information you share with us.",
    )
    (OUTPUT_DIR / ".nojekyll").touch()
    (OUTPUT_DIR / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {SITE['url']}/sitemap.xml\n", encoding="utf-8"
    )
    urls = ("/", "/about/", "/privacy/")
    sitemap = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(f"  <url><loc>{SITE['url']}{path}</loc></url>" for path in urls)
        + "\n</urlset>\n"
    )
    (OUTPUT_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    return OUTPUT_DIR


def main() -> None:
    destination = build()
    print(f"Built Florica Ltd website at {destination}")


if __name__ == "__main__":
    main()
