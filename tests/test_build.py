import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from florica_site import build


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output = Path(self.temp_dir.name) / "dist"
        self.patcher = patch.object(build, "OUTPUT_DIR", self.output)
        self.patcher.start()
        build.build()

    def tearDown(self):
        self.patcher.stop()
        self.temp_dir.cleanup()

    def test_required_pages_and_assets_exist(self):
        expected = (
            "index.html", "about/index.html", "privacy/index.html",
            "assets/css/main.css", "assets/js/main.js", "robots.txt", "sitemap.xml",
        )
        for path in expected:
            self.assertTrue((self.output / path).is_file(), path)

    def test_home_page_contains_core_content(self):
        page = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn("AI Opportunity Sprint", page)
        self.assertIn("Intelligent automation", page)
        self.assertIn('id="services"', page)
        self.assertNotIn("$service_cards", page)

    def test_structured_data_is_valid_json(self):
        page = (self.output / "index.html").read_text(encoding="utf-8")
        payload = page.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0]
        schema = json.loads(payload)
        self.assertEqual(schema["@type"], "ProfessionalService")

    def test_internal_absolute_links_resolve(self):
        page = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/about/"', page)
        self.assertTrue((self.output / "about/index.html").exists())


if __name__ == "__main__":
    unittest.main()
