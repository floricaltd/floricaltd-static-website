"""Dependency-free static site generator for Florica Ltd."""

from __future__ import annotations

import html
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

from .content import NAVIGATION, PRINCIPLES, PRODUCTS, SERVICES, SITE

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PACKAGE_DIR / "templates"
STATIC_DIR = PACKAGE_DIR / "static"
OUTPUT_DIR = Path.cwd() / "dist"
DEFAULT_BASE_PATH = "/floricaltd-static-website/"


@dataclass(frozen=True)
class SiteConfig:
    origin: str
    base_path: str

    @classmethod
    def from_environment(cls) -> "SiteConfig":
        origin = os.environ.get("SITE_ORIGIN", SITE["origin"]).rstrip("/")
        parsed = urlsplit(origin)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path or parsed.query or parsed.fragment:
            raise ValueError("SITE_ORIGIN must be an HTTPS origin without a path, query, or fragment")
        return cls(origin=origin, base_path=normalize_base_path(os.environ.get("SITE_BASE_PATH", DEFAULT_BASE_PATH)))

    def path(self, route: str = "/") -> str:
        parsed = urlsplit(route)
        if parsed.scheme or parsed.netloc or parsed.query or not parsed.path.startswith("/"):
            raise ValueError(f"route must be a root-relative path without a query: {route!r}")
        relative = parsed.path.lstrip("/")
        value = f"{self.base_path}{relative}"
        if parsed.fragment:
            value = f"{value}#{parsed.fragment}"
        return value

    def absolute_url(self, route: str = "/") -> str:
        return f"{self.origin}{self.path(route)}"


def normalize_base_path(value: str) -> str:
    if not value.startswith("/") or "?" in value or "#" in value or ".." in value.split("/"):
        raise ValueError("SITE_BASE_PATH must be an absolute URL path without queries, fragments, or '..'")
    segments = [segment for segment in value.split("/") if segment]
    return "/" + "/".join(segments) + "/" if segments else "/"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def navigation(config: SiteConfig) -> str:
    return "\n".join(
        f'<a href="{esc(config.path(url))}">{esc(label)}</a>' for label, url in NAVIGATION
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


def render_page(
    config: SiteConfig,
    template_name: str,
    output: str,
    *,
    title: str,
    description: str,
    **context: str,
) -> None:
    template = Template((TEMPLATE_DIR / template_name).read_text(encoding="utf-8"))
    route = "/" if output == "index.html" else "/" + output.removesuffix("index.html")
    canonical = config.absolute_url(route)
    schema = {
        "@context": "https://schema.org",
        "@type": "ProfessionalService",
        "name": SITE["name"],
        "url": config.absolute_url(),
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
        "navigation": navigation(config),
        "year": SITE["copyright_year"],
        "home_url": esc(config.path()),
        "services_url": esc(config.path("/#services")),
        "products_url": esc(config.path("/#products")),
        "about_url": esc(config.path("/about/")),
        "privacy_url": esc(config.path("/privacy/")),
        "css_url": esc(config.path("/assets/css/main.css")),
        "js_url": esc(config.path("/assets/js/main.js")),
        "favicon_url": esc(config.path("/assets/images/favicon.svg")),
        "social_image_url": esc(config.absolute_url("/assets/images/social-card.svg")),
        "schema": json.dumps(schema, separators=(",", ":")),
        **context,
    }
    rendered = template.safe_substitute(values)
    destination = OUTPUT_DIR / output
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8")


def build() -> Path:
    config = SiteConfig.from_environment()
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    shutil.copytree(STATIC_DIR, OUTPUT_DIR / "assets")

    render_page(
        config,
        "index.html",
        "index.html",
        title="Florica Ltd — AI & technology, made useful",
        description=SITE["description"],
        service_cards=service_cards(),
        product_cards=product_cards(),
        principles=principles(),
    )
    render_page(
        config,
        "about.html",
        "about/index.html",
        title="About — Florica Ltd",
        description="Meet the practical, senior-led consultancy behind Florica Ltd.",
    )
    render_page(
        config,
        "privacy.html",
        "privacy/index.html",
        title="Privacy — Florica Ltd",
        description="How Florica Ltd handles information you share with us.",
    )
    (OUTPUT_DIR / ".nojekyll").touch()
    (OUTPUT_DIR / "robots.txt").write_text(
        f"User-agent: *\nAllow: {config.base_path}\nSitemap: {config.absolute_url('/sitemap.xml')}\n",
        encoding="utf-8",
    )
    urls = ("/", "/about/", "/privacy/")
    sitemap = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + (
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(f"  <url><loc>{config.absolute_url(path)}</loc></url>" for path in urls)
        + "\n</urlset>\n"
    )
    (OUTPUT_DIR / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    return OUTPUT_DIR


def main() -> None:
    destination = build()
    print(f"Built Florica Ltd website at {destination}")


if __name__ == "__main__":
    main()
