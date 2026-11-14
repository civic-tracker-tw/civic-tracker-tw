"""
CivicTracker TW - Cybersecurity Hardening & LY Crawler Tests
Verifies SQL injection protection, rate limiting, security headers,
input sanitization, timing-safe authentication, and end-to-end crawler sync.
"""

import os
import unittest
from http import HTTPStatus

from backend.core.database import DatabaseEngine
from backend.core.ly_crawler import LegislativeYuanCrawler
from backend.core.security import (
    MAX_POST_BODY_BYTES,
    InputSanitizer,
    RateLimiter,
    SecurityHeaders,
    verify_admin_token,
)
from backend.tests.test_web_server import MockHttpHandler


class TestSecurityHardening(unittest.TestCase):
    """Tests OWASP security features and API protections."""

    def setUp(self):
        self.db = DatabaseEngine(":memory:", auto_seed=True)

    def tearDown(self):
        self.db.close()

    def test_parameterized_sql_injection_immunity(self):
        """Verifies that malicious SQL injection strings in queries are sanitized and safe."""
        # 1. Search injection attempt: ' OR '1'='1
        results = self.db.get_speeches(q="' OR '1'='1")
        self.assertEqual(len(results), 0)

        # 2. DROP TABLE attack injection attempt
        malicious_query = "'; DROP TABLE politicians; --"
        results = self.db.get_speeches(q=malicious_query)
        self.assertEqual(len(results), 0)

        # Verify that the table was NOT dropped and remains intact
        pols = self.db.get_politicians()
        self.assertGreaterEqual(len(pols), 3)

        # 3. Politician ID injection attempt
        pol_injected = self.db.get_politician("pol-001' OR '1'='1")
        self.assertIsNone(pol_injected)

    def test_rate_limiter_threshold_and_sliding_window(self):
        """Tests that exceeding request rate limits returns allowed=False and retry-after."""
        limiter = RateLimiter(max_requests=5, window_seconds=2)
        ip = "192.168.1.100"

        # First 5 requests must succeed
        for i in range(5):
            allowed, remaining, retry_after = limiter.check_rate_limit(ip)
            self.assertTrue(allowed)
            self.assertEqual(remaining, 4 - i)
            self.assertEqual(retry_after, 0)

        # 6th request must be blocked
        allowed, remaining, retry_after = limiter.check_rate_limit(ip)
        self.assertFalse(allowed)
        self.assertEqual(remaining, 0)
        self.assertGreater(retry_after, 0)

        # Different IP should not be blocked
        other_ip = "192.168.1.101"
        allowed_other, _, _ = limiter.check_rate_limit(other_ip)
        self.assertTrue(allowed_other)

    def test_security_headers_present_on_http_response(self):
        """Verifies OWASP security headers (nosniff, SAMEORIGIN, etc.) are present."""
        handler = MockHttpHandler("GET", "/api/protocol")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        headers = handler.response_headers

        self.assertEqual(headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(headers.get("x-frame-options"), "SAMEORIGIN")
        self.assertEqual(headers.get("x-xss-protection"), "1; mode=block")
        self.assertEqual(headers.get("referrer-policy"), "strict-origin-when-cross-origin")
        self.assertIn("geolocation=()", headers.get("permissions-policy", ""))
        self.assertIn("x-ratelimit-remaining", headers)

    def test_input_sanitizer_removes_control_characters_and_truncates(self):
        """Tests control character stripping and length limiting."""
        # Null byte, carriage return, newline, escape
        dirty_input = "Hello\x00World\r\n\x1b[31mTaiwan\x7f"
        clean = InputSanitizer.sanitize_query_string(dirty_input)
        self.assertNotIn("\x00", clean)
        self.assertNotIn("\r", clean)
        self.assertNotIn("\n", clean)
        self.assertNotIn("\x1b", clean)
        self.assertIn("HelloWorld", clean)

        # Length truncation test
        long_str = "A" * 200
        truncated = InputSanitizer.sanitize_query_string(long_str, max_len=50)
        self.assertEqual(len(truncated), 50)

    def test_timing_safe_admin_token_verification(self):
        """Verifies admin token authentication using hmac.compare_digest."""
        # Default token test
        self.assertTrue(verify_admin_token("dev-admin-token-change-me"))
        self.assertFalse(verify_admin_token("wrong-token"))
        self.assertFalse(verify_admin_token(None))
        self.assertFalse(verify_admin_token(""))

        # Custom environment token
        try:
            os.environ["CIVIC_ADMIN_TOKEN"] = "super-secret-production-token-2026"
            self.assertTrue(verify_admin_token("super-secret-production-token-2026"))
            self.assertFalse(verify_admin_token("dev-admin-token-change-me"))
        finally:
            del os.environ["CIVIC_ADMIN_TOKEN"]

    def test_post_payload_size_limit_enforced(self):
        """Verifies HTTP 413 Payload Too Large is returned if POST body exceeds MAX_POST_BODY_BYTES."""
        handler = MockHttpHandler("POST", "/api/pipeline/simulate")
        # Oversized payload (> 64 KB)
        oversized_bytes = MAX_POST_BODY_BYTES + 1024
        handler.headers["Content-Length"] = str(oversized_bytes)
        handler.do_POST()
        self.assertEqual(handler.response_status, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)


class TestLegislativeYuanCrawlerAndSync(unittest.TestCase):
    """Verifies Open Data Crawler ingestion, AI pipeline auditing, and SQLite upsert."""

    def setUp(self):
        self.db = DatabaseEngine(":memory:", auto_seed=True)
        self.crawler = LegislativeYuanCrawler(db=self.db)

    def tearDown(self):
        self.db.close()

    def test_crawler_end_to_end_sync(self):
        """Tests that crawler ingests fixtures, routes speeches through Argon audit, and stores records."""
        report = self.crawler.sync_to_database(live=False)

        self.assertEqual(report["status"], "SUCCESS")
        self.assertEqual(report["legislators_synced"], 3)
        self.assertEqual(report["speeches_synced"], 3)
        self.assertEqual(report["argon_audited_count"], 3)
        self.assertIn("OFFICIAL_FIXTURE", report["data_sources"]["legislators"])

        # Check DB state after sync
        pols = self.db.get_politicians()
        names = {p["name"] for p in pols}
        self.assertIn("洪申翰", names)
        self.assertIn("李彥秀", names)
        self.assertIn("陳昭姿", names)

        # Check speeches query
        speeches = self.db.get_speeches(q="碳費")
        self.assertEqual(len(speeches), 1)
        self.assertEqual(speeches[0]["speaker_name"], "洪申翰")
        self.assertEqual(speeches[0]["audit_metadata"]["audit_verdict"], "APPROVE")

        # Verify sync logs
        logs = self.db.get_sync_logs(limit=5)
        self.assertGreaterEqual(len(logs), 2)  # bootstrap + ly_open_data_sync
        ly_log = logs[0]
        self.assertEqual(ly_log["source"], "ly_open_data_sync")
        self.assertEqual(ly_log["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
