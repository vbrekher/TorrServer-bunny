"""Documentation smoke checks; no Bunny API credentials or network calls required."""
import pathlib
import re
import unittest

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

    def test_all_three_languages_cover_basic_usage(self):
        for lang in ("ru", "en", "nl"):
            page = ROOT / f"docs/README.{lang}.md"
            text = page.read_text(encoding="utf-8")
            with self.subTest(language=lang):
                for command in (
                    "torrserver-bunny start", "torrserver-bunny stop",
                    "torrserver-bunny status", "status --show-credentials",
                    "enable-github-watchdog", "torrserver-bunny doctor",
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
