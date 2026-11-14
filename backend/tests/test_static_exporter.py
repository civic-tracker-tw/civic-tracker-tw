"""
CivicTracker TW - Static Website Exporter Unit Tests
Verifies generation of serverless static bundle under dist/, inclusion of
synced 11th-term legislators, Argon audit metadata, and zero-cost hosting configs.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from backend.core.static_exporter import export_static_site


class TestStaticExporter(unittest.TestCase):
    """Verifies static export pipeline, JSON snapshots, and zero-cost hosting files."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="civic_tracker_dist_test_")
        cls.manifest = export_static_site(output_dir=cls.temp_dir, sync_crawler=True)

    @classmethod
    def tearDownClass(cls):
        if Path(cls.temp_dir).exists():
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_export_manifest_status_and_files(self):
        self.assertEqual(self.manifest["status"], "SUCCESS")
        dist_path = Path(self.temp_dir)

        # Check required root files
        self.assertTrue((dist_path / "index.html").is_file())
        self.assertTrue((dist_path / ".nojekyll").is_file())
        self.assertTrue((dist_path / "netlify.toml").is_file())

        # Check API JSON snapshots
        api_dir = dist_path / "api"
        self.assertTrue(api_dir.is_dir())
        for json_file in (
            "protocol.json",
            "stats.json",
            "politicians.json",
            "speeches.json",
            "votes.json",
            "promises.json",
            "exam_cards.json",
            "petitions.json",
            "council_interpellations.json",
            "security_status.json",
        ):
            file_path = api_dir / json_file
            self.assertTrue(file_path.is_file(), f"Missing exported JSON: {json_file}")
            self.assertGreater(file_path.stat().st_size, 0)

    def test_exported_politicians_contain_synced_legislators(self):
        dist_path = Path(self.temp_dir)
        with open(dist_path / "api" / "politicians.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        pols = data["politicians"]
        self.assertGreaterEqual(len(pols), 6)
        names = {p["name"] for p in pols}

        # Verify newly synced 11th-term legislators
        self.assertIn("洪申翰", names)
        self.assertIn("李彥秀", names)
        self.assertIn("陳昭姿", names)

        # Verify cross-phase politician
        target = next((p for p in pols if p["name"] == "蔣萬安"), None)
        self.assertIsNotNone(target)
        self.assertTrue(target["stats"]["is_cross_phase"])
        self.assertEqual(len(target["terms"]), 2)

    def test_exported_speeches_contain_argon_audit(self):
        dist_path = Path(self.temp_dir)
        with open(dist_path / "api" / "speeches.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        speeches = data["speeches"]
        self.assertGreaterEqual(len(speeches), 6)
        for s in speeches:
            audit = s.get("audit_metadata", {})
            self.assertEqual(audit.get("audit_verdict"), "APPROVE")
            self.assertEqual(audit.get("audited_by"), "argon")
            self.assertGreater(s["end_time_sec"], s["start_time_sec"])

    def test_exported_index_html_has_embedded_data_and_simulation(self):
        dist_path = Path(self.temp_dir)
        with open(dist_path / "index.html", "r", encoding="utf-8") as f:
            html = f.read()

        # Check that index.html contains branding and embedded dataset
        self.assertIn("CivicTracker TW", html)
        self.assertIn("QUANTITATIVE_ONLY", html)
        self.assertIn("ivod-sync-widget", html)
        self.assertIn("洪申翰", html)
        self.assertIn("李彥秀", html)
        self.assertIn("陳昭姿", html)
        self.assertIn("蔣萬安", html)
        self.assertIn("侯友宜", html)
        self.assertIn("盧秀燕", html)
        self.assertIn("sim-run-btn", html)
        self.assertIn("E02_SPEAKER_SWAP", html)

    def test_security_status_export(self):
        dist_path = Path(self.temp_dir)
        with open(dist_path / "api" / "security_status.json", "r", encoding="utf-8") as f:
            sec = json.load(f)

        protections = sec["security_protections"]
        self.assertTrue(protections["sqlite_wal_journal_mode"])
        self.assertTrue(protections["parameterized_queries"])
        self.assertTrue(protections["owasp_headers_enforced"])
        self.assertIn("latest_sync_logs", sec)

    def test_exported_council_interpellations_and_officials(self):
        dist_path = Path(self.temp_dir)
        with open(dist_path / "api" / "council_interpellations.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        officials = data["officials"]
        interpellations = data["interpellations"]
        self.assertGreaterEqual(len(officials), 15)
        self.assertGreaterEqual(len(interpellations), 14)

        with open(dist_path / "index.html", "r", encoding="utf-8") as f:
            html = f.read()

        self.assertIn("subordinate-officials-grid", html)
        self.assertIn("council-vod-widget", html)
        self.assertIn("李四川", html)
        self.assertIn("祝惠美", html)
        self.assertIn("葉昭甫", html)
        self.assertIn("林欽榮", html)


if __name__ == "__main__":
    unittest.main()
