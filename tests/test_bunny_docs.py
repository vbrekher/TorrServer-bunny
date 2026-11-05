"""Documentation smoke checks; no Bunny API credentials or network calls required."""
import pathlib
import os
import subprocess
import tempfile
import ast
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

    def test_installer_and_cli_build_version_are_in_sync(self):
        cli = (ROOT / "bunny/cli.py").read_text(encoding="utf-8")
        installer = (ROOT / "install-bunny.sh").read_text(encoding="utf-8")
        match = re.search(r"^CLI_BUILD = '([^']+)'$", cli, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertIn(match.group(1), installer)
        self.assertIn("def activity_status(", cli)
        self.assertIn("def activity_snapshot(", cli)
        self.assertIn("def activity_status(", installer)
        self.assertIn("def activity_snapshot(", installer)

    def test_installer_embedded_python_compiles(self):
        """A shell syntax check cannot detect broken Python in a here-document."""
        installer = (ROOT / "install-bunny.sh").read_text(encoding="utf-8")
        match = re.search(
            r"(?m)^python3 - \"\$TMP\" <<'PY'\n(.*?)\nPY$",
            installer, re.DOTALL,
        )
        self.assertIsNotNone(match, "Installer's Python verification block is missing")
        ast.parse(match.group(1), filename="installer-embedded-validator")
        self.assertIn("required=(", match.group(1))
        self.assertIn("def activity_probe(", match.group(1))

    def test_installer_without_github_api_and_safe_403_fallback(self):
        """Exercise the actual POSIX installer offline, with fake git and curl."""
        installer = ROOT / "install-bunny.sh"
        cli = ROOT / "bunny/cli.py"
        sha = "a" * 40
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp) / "home"
            home.mkdir()
            bin_dir = pathlib.Path(tmp) / "fake-bin"
            bin_dir.mkdir()
            git = bin_dir / "git"
            git.write_text(
                '#!/bin/sh\n'
                'if [ "$TS_TEST_GIT_MODE" = "fail" ]; then exit 128; fi\n'
                'printf "%s\\trefs/heads/master\\n" "$TS_TEST_SHA"\n',
                encoding="utf-8",
            )
            git.chmod(0o755)
            curl = bin_dir / "curl"
            curl.write_text(
                '#!/bin/sh\n'
                'url=""\noutput=""\n'
                'while [ "$#" -gt 0 ]; do\n'
                '  if [ "$1" = "-o" ]; then shift; output="$1"; '
                'else case "$1" in https://*) url="$1";; esac; fi\n'
                '  shift\n'
                'done\n'
                'printf "%s" "$url" > "$TS_TEST_URL_LOG"\n'
                'case "$url" in *api.github.com*) exit 99;; esac\n'
                'if [ "$TS_TEST_FAIL_CURL" = "1" ]; then\n'
                '  echo "curl: (22) The requested URL returned error: 403" >&2\n'
                '  exit 22\n'
                'fi\n'
                'cp "$TS_TEST_CLI_SOURCE" "$output"\n',
                encoding="utf-8",
            )
            curl.chmod(0o755)
            url_log = pathlib.Path(tmp) / "requested-url"
            env = {**os.environ, "HOME": str(home),
                   "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
                   "TS_TEST_SHA": sha, "TS_TEST_CLI_SOURCE": str(cli),
                   "TS_TEST_URL_LOG": str(url_log)}
            def run(*, git_mode="ok", fail_curl=False):
                return subprocess.run(
                    ["sh", str(installer), "--help"],
                    env={**env, "TS_TEST_GIT_MODE": git_mode,
                         "TS_TEST_FAIL_CURL": "1" if fail_curl else "0"},
                    text=True, capture_output=True, timeout=30,
                )

            result = run()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(f"/{sha}/bunny/cli.py", url_log.read_text())
            self.assertNotIn("api.github.com", result.stdout + result.stderr)
            installed = home / ".local/share/torrserver-bunny/cli.py"
            self.assertTrue(installed.is_file())
            self.assertIn("activity_probe", installed.read_text())

            # Git transport failure (possibly HTTP 403) -> raw master fallback.
            result = run(git_mode="fail")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("/master/bunny/cli.py?cache_bust=", url_log.read_text())
            self.assertIn("Git revision lookup unavailable", result.stdout)
            self.assertNotIn("JSONDecodeError", result.stderr)

            # Raw 403 must preserve the user's prior installation.
            before = installed.read_bytes()
            result = run(git_mode="fail", fail_curl=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Existing local installation left unchanged", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertEqual(before, installed.read_bytes())

    def test_landing_page_retains_first_time_safety_and_truth(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in (
            "torrserver-bunny start", "torrserver-bunny stop",
            "torrserver-bunny status", "status --show-credentials",
            "CREATE", "Anycast", ":32000", "Real-world idle auto-stop verified on 4 Nov 2026", "YOUR_USERNAME/TorrServer-bunny",
            "torrserver-bunny activity", "gh workflow enable idle-watchdog.yml",
            "50 GB", "$0.58", "$2.68", "YouROK",
            "bunny-cli-tests.yml",
        ):
            self.assertIn(phrase, text)

    def test_simple_60_minute_guide_is_complete_in_all_locales(self):
        pages = {
            "ru": ("## 6. Автоотключение через 60 минут — простая инструкция",
                   "Включить один раз", "Как пользоваться каждый день", "ENABLE",
                   "Secrets installed", "Tracked media bytes", "inactive"),
            "en": ("## 6. Auto-stop after 60 idle minutes — easy guide",
                   "Set up once", "Everyday use", "ENABLE", "Secrets installed",
                   "Tracked media bytes", "inactive"),
            "nl": ("## 6. Automatisch stoppen na 60 minuten — eenvoudige uitleg",
                   "Eenmalig instellen", "Dagelijks gebruik", "ENABLE",
                   "Secrets installed", "Tracked media bytes", "inactive"),
        }
        for lang, checks in pages.items():
            text = (ROOT / f"docs/README.{lang}.md").read_text(encoding="utf-8")
            with self.subTest(lang=lang):
                for phrase in checks:
                    self.assertIn(phrase, text)
                self.assertIn('YOUR_USERNAME/TorrServer-bunny', text)
                self.assertIn('gh workflow run idle-watchdog.yml', text)
                self.assertIn('gh run list --workflow idle-watchdog.yml', text)
                self.assertIn('~/.local/bin/torrserver-bunny activity', text)
                self.assertIn('~/.local/bin/torrserver-bunny stop', text)
                self.assertIn('gh auth status', text)
                self.assertNotIn('REPO="vbrekher/TorrServer-bunny"', text)

        landing = (ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in ("Автоотключение за 4 шага", "4 steps to auto-stop",
                       "Automatisch stoppen in 4 stappen",
                       "docs/README.ru.md#6-", "docs/README.en.md#6-",
                       "docs/README.nl.md#6-", "GitHub checks approximately every"):
            self.assertIn(phrase, landing)

    def test_live_idle_stop_status_and_citation_are_consistent(self):
        base = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Scheduled 60-minute shutdown on live Bunny | ✅ Verified:", base)
        self.assertIn("41920393921", base)
        for page in (ROOT / "docs/README.ru.md", ROOT / "docs/README.en.md",
                     ROOT / "docs/README.nl.md", ROOT / "bunny/README.md"):
            content = page.read_text(encoding="utf-8")
            with self.subTest(page=page.name):
                self.assertIn("41920393921", content)
                self.assertIn("ALREADY_INACTIVE", content)
                self.assertIn("State: inactive", content)

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
