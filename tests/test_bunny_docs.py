"""Documentation smoke checks; no Bunny API credentials or network calls required."""
import pathlib
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "README.md",
    ROOT / "docs/README.ru.md",
    ROOT / "docs/README.en.md",
    ROOT / "docs/README.nl.md",
    ROOT / "bunny/README.md",
]


class DocumentationTests(unittest.TestCase):
    def test_all_expected_pages_exist(self):
        for page in DOCS:
            with self.subTest(path=str(page)):
                self.assertTrue(page.is_file())
                self.assertGreater(len(page.read_text(encoding="utf-8")), 1500)

    def test_local_markdown_links_resolve(self):
        pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
        for page in DOCS:
            with self.subTest(page=page):
                for link in pattern.findall(page.read_text(encoding="utf-8")):
                    path = link.split("#", 1)[0]
                    if not path or re.match(r"^[a-zA-Z]+:", path):
                        continue
                    target = (page.parent / path).resolve()
                    self.assertTrue(target.is_file(), f"{page}: broken link {link}")

    def test_github_hero_is_accessible_valid_self_contained_svg(self):
        hero = ROOT / "docs/assets/torrserver-bunny-hero.svg"
        self.assertTrue(hero.is_file())
        root = ET.parse(hero).getroot()
        self.assertTrue(root.tag.endswith("svg"))
        self.assertEqual(root.attrib.get("viewBox"), "0 0 1600 560")
        self.assertTrue(any(el.tag.endswith("title") for el in root.iter()))
        self.assertTrue(any(el.tag.endswith("desc") for el in root.iter()))
        svg = hero.read_text(encoding="utf-8")
        self.assertNotIn("<script", svg.lower())
        self.assertNotIn("http://", svg.replace('http://www.w3.org/2000/svg',''))
        landing = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn('src="docs/assets/torrserver-bunny-hero.svg"', landing)
        for lang in ("ru", "en", "nl"):
            self.assertIn(f"docs/README.{lang}.md", landing)

    def test_landing_page_retains_first_time_safety_and_truth(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in (
            "torrserver-bunny start", "torrserver-bunny stop",
            "torrserver-bunny status", "status --show-credentials",
            "CREATE", "Anycast", ":32000", "Scheduled idle shutdown is still **unverified**", "owner-confirmed",
            "torrserver-bunny activity", "gh workflow enable idle-watchdog.yml",
            "50 GB", "$0.58", "$2.68", "YouROK",
            "bunny-cli-tests.yml",
        ):
            self.assertIn(phrase, text)

    def test_all_three_languages_cover_basic_usage(self):
        for lang in ("ru", "en", "nl"):
            page = ROOT / f"docs/README.{lang}.md"
            text = page.read_text(encoding="utf-8")
            with self.subTest(language=lang):
                for command in (
                    "torrserver-bunny start", "torrserver-bunny stop",
                    "torrserver-bunny status", "status --show-credentials",
                    "enable-github-watchdog", "torrserver-bunny doctor",
                    "torrserver-bunny activity",
                ):
                    self.assertIn(command, text)
                for token in ("50", "0,50" if lang != "en" else "0.50",
                              "0,575" if lang != "en" else "0.575",
                              "2,68" if lang != "en" else "2.68",
                              "32000", "CREATE", "Lampa"):
                    self.assertIn(token, text)
                self.assertIn("https://raw.githubusercontent.com/vbrekher/TorrServer-bunny/master/install-bunny.sh", text)

    def test_never_publishes_owners_real_endpoint_or_credentials(self):
        for page in DOCS:
            text = page.read_text(encoding="utf-8")
            for private_value in (
                "109.224.231.152", "HznUbyXuN3o1dpA",
                "mc-tdaxf7hkne.bunny.run",
            ):
                self.assertNotIn(private_value, text, f"Owner-specific value in {page}")
            self.assertNotIn("Registry already verified: 11126", text)


if __name__ == "__main__":
    unittest.main()
