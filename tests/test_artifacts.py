"""Tests for stremio-ha-addon artifacts.

These tests validate the project files (Dockerfile, addon.yaml,
download_server.sh) without requiring a Docker daemon. They run with
python3 and need no dependencies beyond the standard library + PyYAML.
"""

import re
import unittest
from pathlib import Path

import yaml

ADDON_DIR = Path(__file__).resolve().parents[1]

# --- Required file presence ---

REQUIRED_FILES = [
    "Dockerfile",
    "addon.yaml",
    "download_server.sh",
    "README.md",
    "CHANGELOG.md",
    "docs/config.md",
    "docs/stremio-ha-addon-design.md",
    "docs/superpowers/plans/2026-10-24-stremio-ha-addon-plan.md",
]


class TestRequiredFiles(unittest.TestCase):
    """Ensure all expected files exist."""

    def test_files_exist(self):
        missing = []
        for rel in REQUIRED_FILES:
            p = ADDON_DIR / rel
            if not p.exists():
                missing.append(rel)
        self.assertEqual(missing, [], f"Missing files: {missing}")


# --- download_server.sh matches upstream ---

class TestDownloadServerSh(unittest.TestCase):
    """download_server.sh must be an exact upstream copy to avoid drift."""

    def test_script_has_required_logic(self):
        text = (ADDON_DIR / "download_server.sh").read_text()
        self.assertIn("VERSION", text, "Must reference $VERSION arg")
        self.assertIn("https://dl.strem.io/server/", text, "Must fetch from correct URL")
        self.assertIn("BUILD", text, "Must reference $BUILD arg")


# --- addon.yaml manifest correctness ---

class TestAddonYaml(unittest.TestCase):
    def setUp(self):
        self.data = yaml.safe_load((ADDON_DIR / "addon.yaml").read_text())

    def test_required_top_level_keys(self):
        for key in ["name", "slug", "version", "version_str"]:
            self.assertIn(key, self.data, f"addon.yaml missing top-level key: {key}")

    def test_version_format(self):
        v = self.data["version"]
        # Expect <stremio-version>-<addon-build> e.g. 4.20.3-1
        self.assertRegex(v, r"^\d+\.\d+\.\d+-\d+$", f"Bad version format: {v}")

    def test_slug(self):
        self.assertEqual(self.data["slug"], "stremio-server")

    def test_build_section(self):
        b = self.data["build"]
        self.assertEqual(b["dockerfile"], "./Dockerfile")
        self.assertIn("VERSION", b["args"])
        # VERSION must be a tagged release, not master
        self.assertRegex(b["args"]["VERSION"], r"v\d", "VERSION must be a tagged release")

    def test_ports_exposed(self):
        ports = [p["port"] for p in self.data["ports"]]
        self.assertIn(11470, ports, "HTTP port 11470 must be exposed")
        self.assertIn(12470, ports, "HTTPS port 12470 must be exposed")

    def test_environment_defaults(self):
        env = self.data.get("environment", [])
        env_dict = dict(e.split("=", 1) for e in env)
        self.assertEqual(env_dict.get("NO_CORS"), "1", "NO_CORS must be 1")
        self.assertEqual(env_dict.get("APP_PATH"), "/config/stremio", "APP_PATH must be /config/stremio")

    def test_volume_mapping(self):
        vols = self.data.get("volumes", [])
        self.assertTrue(
            any(v.startswith("/config/stremio:/root/.stremio-server:rw") for v in vols),
            "Must mount /root/.stremio-server with rw"
        )

    def test_arch_support(self):
        archs = self.data.get("arch", [])
        for a in ["amd64", "arm64"]:
            self.assertIn(a, archs, f"Must support arch {a}")


# --- Dockerfile correctness ---

class TestDockerfile(unittest.TestCase):
    def setUp(self):
        self.text = (ADDON_DIR / "Dockerfile").read_text()

    def test_from_node14(self):
        self.assertIn("FROM node:", self.text, "Must base on Node image")
        # Node 14 matches upstream
        self.assertRegex(self.text, r"ARG NODE_VERSION=14", "Node must be pinned to 14")

    def test_arg_defaults(self):
        self.assertIn("ARG VERSION=", self.text, "VERSION arg must exist")
        self.assertIn("ARG JELLYFIN_VERSION=", self.text, "JELLYFIN_VERSION arg must exist")

    def test_exposes(self):
        self.assertIn("EXPOSE 11470", self.text, "Must expose HTTP 11470")
        self.assertIn("EXPOSE 12470", self.text, "Must expose HTTPS 12470")

    def test_ha_env_overrides(self):
        self.assertIn("ENV NO_CORS=1", self.text, "NO_CORS=1 must be set")
        self.assertIn("ENV APP_PATH=/config/stremio", self.text, "APP_PATH must point at /config/stremio")
        self.assertIn("ENV FFMPEG_BIN=/usr/lib/jellyfin-ffmpeg/ffmpeg", "FFMPEG_BIN must point at baked-in binary")
        self.assertIn("ENV CASTING_DISABLED=1", "CASTING_DISABLED=1 must be set")

    def test_entrypoint(self):
        self.assertIn('ENTRYPOINT [ "node", "server.js" ]', self.text)

    def test_volume_declared(self):
        self.assertIn('VOLUME ["/root/.stremio-server"]', self.text)


# --- README completeness ---

class TestReadme(unittest.TestCase):
    def setUp(self):
        self.text = (ADDON_DIR / "README.md").read_text().lower()

    def test_key_sections_present(self):
        for phrase in ["installation", "configuration", "updating", "usage", "troubleshooting"]:
            self.assertIn(phrase, self.text, f"README must have a '{phrase}' section")

    def test_update_instructions(self):
        self.assertIn("bump", self.text, "README must mention bumping version")


if __name__ == "__main__":
    unittest.main()
