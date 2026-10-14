import hashlib
import json
import os
import shutil
import tempfile
import threading
import unittest
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen

from florica_site import build


BASE_PATH = "/floricaltd-static-website/"
ORIGIN = "https://floricaltd.github.io"


class DocumentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.references = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        for attribute in ("href", "src"):
            if values.get(attribute):
                self.references.append(values[attribute])


def tree_digest(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        digest.update(path.relative_to(directory).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output = Path(self.temp_dir.name) / "dist"
        self.output_patch = patch.object(build, "OUTPUT_DIR", self.output)
        self.environment_patch = patch.dict(
            os.environ,
            {"SITE_BASE_PATH": BASE_PATH, "SITE_ORIGIN": ORIGIN},
        )
        self.output_patch.start()
        self.environment_patch.start()
        build.build()

    def tearDown(self):
        self.environment_patch.stop()
        self.output_patch.stop()
        self.temp_dir.cleanup()

    def test_required_pages_and_assets_exist(self):
        expected = (
            "index.html",
            "about/index.html",
            "privacy/index.html",
            "assets/css/main.css",
            "assets/js/main.js",
            "assets/images/favicon.svg",
            "assets/images/social-card.svg",
            "robots.txt",
            "sitemap.xml",
            ".nojekyll",
        )
        for path in expected:
            self.assertTrue((self.output / path).is_file(), path)

    def test_home_page_contains_core_content_and_valid_schema(self):
        page = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn("AI Opportunity Sprint", page)
        self.assertIn("Intelligent automation", page)
        self.assertIn('id="services"', page)
        self.assertNotIn("$service_cards", page)
        payload = page.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0]
        schema = json.loads(payload)
        self.assertEqual(schema["@type"], "ProfessionalService")
        self.assertEqual(schema["url"], f"{ORIGIN}{BASE_PATH}")

    def test_canonical_sitemap_and_robots_use_project_site_base(self):
        pages = {
            "index.html": f"{ORIGIN}{BASE_PATH}",
            "about/index.html": f"{ORIGIN}{BASE_PATH}about/",
            "privacy/index.html": f"{ORIGIN}{BASE_PATH}privacy/",
        }
        for filename, canonical in pages.items():
            page = (self.output / filename).read_text(encoding="utf-8")
            self.assertIn(f'<link rel="canonical" href="{canonical}">', page)
        sitemap = (self.output / "sitemap.xml").read_text(encoding="utf-8")
        for canonical in pages.values():
            self.assertIn(f"<loc>{canonical}</loc>", sitemap)
        robots = (self.output / "robots.txt").read_text(encoding="utf-8")
        self.assertIn(f"Allow: {BASE_PATH}", robots)
        self.assertIn(f"Sitemap: {ORIGIN}{BASE_PATH}sitemap.xml", robots)

    def test_all_local_links_assets_and_fragments_resolve_under_base(self):
        documents = {}
        for path in self.output.rglob("*.html"):
            parser = DocumentParser()
            parser.feed(path.read_text(encoding="utf-8"))
            documents[path] = parser

        for source, parser in documents.items():
            for reference in parser.references:
                parsed = urlsplit(reference)
                if parsed.scheme in {"mailto", "https", "http"}:
                    continue
                if reference.startswith("#"):
                    target_file = source
                else:
                    self.assertTrue(parsed.path.startswith(BASE_PATH), (source, reference))
                    relative = unquote(parsed.path.removeprefix(BASE_PATH))
                    target_file = self.output / relative
                    if not relative or parsed.path.endswith("/"):
                        target_file /= "index.html"
                    self.assertTrue(target_file.is_file(), (source, reference, target_file))
                if parsed.fragment:
                    target = DocumentParser()
                    target.feed(target_file.read_text(encoding="utf-8"))
                    self.assertIn(parsed.fragment, target.ids, (source, reference))

    def test_build_is_deterministic(self):
        first = tree_digest(self.output)
        build.build()
        self.assertEqual(first, tree_digest(self.output))

    def test_every_published_route_and_asset_returns_http_200(self):
        web_root = Path(self.temp_dir.name) / "www"
        target = web_root / BASE_PATH.strip("/")
        shutil.copytree(self.output, target)
        handler = partial(SimpleHTTPRequestHandler, directory=str(web_root))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            routes = (
                BASE_PATH,
                f"{BASE_PATH}about/",
                f"{BASE_PATH}privacy/",
                f"{BASE_PATH}assets/css/main.css",
                f"{BASE_PATH}assets/js/main.js",
                f"{BASE_PATH}assets/images/favicon.svg",
                f"{BASE_PATH}assets/images/social-card.svg",
                f"{BASE_PATH}robots.txt",
                f"{BASE_PATH}sitemap.xml",
            )
            for route in routes:
                with urlopen(f"{origin}{route}", timeout=3) as response:
                    self.assertEqual(response.status, 200, route)
            with self.assertRaises(HTTPError) as error:
                urlopen(f"{origin}/assets/css/main.css", timeout=3)
            self.assertEqual(error.exception.code, 404)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_configuration_rejects_unsafe_paths_and_origins(self):
        for invalid in ("relative/", "/ok/../bad/", "/bad?query/", "/bad#fragment/"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                build.normalize_base_path(invalid)
        with patch.dict(os.environ, {"SITE_ORIGIN": "http://example.com"}):
            with self.assertRaises(ValueError):
                build.SiteConfig.from_environment()


if __name__ == "__main__":
    unittest.main()
