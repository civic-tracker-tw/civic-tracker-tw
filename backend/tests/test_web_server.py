"""
CivicTracker TW - Web Server Integration & API Handler Unit Tests
Tests the zero-dependency HTTP server request handling, REST API endpoints,
CORS headers, static HTML serving, and interactive simulation without external sockets.
"""

import io
import json
import unittest
from http import HTTPStatus

from backend.web_server import CivicTrackerApiHandler


class MockHttpHandler(CivicTrackerApiHandler):
    """
    Subclasses CivicTrackerApiHandler to test HTTP handlers deterministically in-memory,
    avoiding network socket permission constraints inside sandbox environments.
    """

    def __init__(self, method: str = "GET", path: str = "/", body: dict = None):
        self.command = method
        self.path = path
        self.request_version = "HTTP/1.1"
        self.headers = {}
        if body is not None:
            raw_body = json.dumps(body).encode("utf-8")
            self.headers["Content-Length"] = str(len(raw_body))
            self.headers["Content-Type"] = "application/json"
            self.rfile = io.BytesIO(raw_body)
        else:
            self.rfile = io.BytesIO()
        self.wfile = io.BytesIO()
        self.response_status = None
        self.response_headers = {}

    def send_response(self, code, message=None):
        self.response_status = code

    def send_header(self, keyword, value):
        self.response_headers[keyword.lower()] = value

    def end_headers(self):
        pass

    def get_json_response(self):
        content = self.wfile.getvalue().decode("utf-8")
        return json.loads(content) if content else {}

    def get_text_response(self):
        return self.wfile.getvalue().decode("utf-8")


class TestWebServerHandlers(unittest.TestCase):
    """Verifies all REST API routes, parameter filters, and simulation endpoints."""

    def test_serve_frontend_index(self):
        handler = MockHttpHandler("GET", "/")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        self.assertIn("text/html", handler.response_headers.get("content-type", ""))
        html = handler.get_text_response()
        self.assertIn("CivicTracker TW", html)
        self.assertIn("Dual-Model Protocol", html)

    def test_options_cors_headers(self):
        handler = MockHttpHandler("OPTIONS", "/api/protocol")
        handler.do_OPTIONS()
        self.assertEqual(handler.response_status, HTTPStatus.NO_CONTENT)
        self.assertEqual(handler.response_headers.get("access-control-allow-origin"), "*")
        self.assertIn("POST", handler.response_headers.get("access-control-allow-methods", ""))

    def test_get_protocol(self):
        handler = MockHttpHandler("GET", "/api/protocol")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()
        self.assertIn("protocol", res)
        self.assertIn("sync_status", res)
        self.assertEqual(res["protocol"]["protocol_version"], "1.0.0")
        self.assertTrue(res["sync_status"]["is_synchronized"])
        self.assertIn("TASK_SPEECH_PARSE", res["protocol"]["gates"])

    def test_get_stats(self):
        handler = MockHttpHandler("GET", "/api/stats")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()
        self.assertGreaterEqual(res["total_politicians"], 3)
        self.assertGreaterEqual(res["cross_phase_politicians"], 1)
        self.assertGreaterEqual(res["total_speeches"], 3)

    def test_get_politicians(self):
        handler = MockHttpHandler("GET", "/api/politicians")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()
        pols = res["politicians"]
        self.assertGreaterEqual(len(pols), 3)

        # Cross-role verification (Legislator -> Mayor)
        target = next((p for p in pols if p["name"] in ("蔣萬安", "林宏遠")), None)
        self.assertIsNotNone(target)
        self.assertTrue(target["stats"]["is_cross_phase"])
        self.assertEqual(len(target["terms"]), 2)

    def test_get_speeches_with_query_and_tag(self):
        # 1. All speeches
        handler = MockHttpHandler("GET", "/api/speeches")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()
        self.assertGreaterEqual(res["total"], 3)

        # 2. Filter by tag
        handler_tag = MockHttpHandler("GET", "/api/speeches?tag=行人路權")
        handler_tag.do_GET()
        self.assertEqual(handler_tag.response_status, HTTPStatus.OK)
        res_tag = handler_tag.get_json_response()
        self.assertEqual(res_tag["total"], 1)
        self.assertIn("行人路權", res_tag["speeches"][0]["topic_tags"])

        # 3. Filter by text search
        handler_q = MockHttpHandler("GET", "/api/speeches?q=打詐專法")
        handler_q.do_GET()
        self.assertEqual(handler_q.response_status, HTTPStatus.OK)
        res_q = handler_q.get_json_response()
        self.assertEqual(res_q["total"], 1)
        self.assertIn(res_q["speeches"][0]["speaker_name"], ("陳其邁", "張靜雅"))

    def test_get_exam_cards(self):
        handler = MockHttpHandler("GET", "/api/exam-cards")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()
        self.assertIn("exam_cards", res)
        self.assertGreaterEqual(res["total"], 1)
        self.assertIn("attendance_rate", res["exam_cards"][0])

    def test_get_petitions(self):
        handler = MockHttpHandler("GET", "/api/petitions")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()
        self.assertIn("petitions", res)
        self.assertGreaterEqual(res["total"], 1)
        self.assertEqual(res["petitions"][0]["status"], "APPROVED")

    def test_get_votes(self):
        handler = MockHttpHandler("GET", "/api/votes")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()
        self.assertEqual(res["total"], 5)
        self.assertIsNotNone(res["votes"][0]["bill"])
        self.assertIsNotNone(res["votes"][0]["politician_name"])

    def test_get_promises_with_status_filter(self):
        # All promises
        handler = MockHttpHandler("GET", "/api/promises")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()
        self.assertEqual(res["total"], 5)

        # Filter FULFILLED
        handler_f = MockHttpHandler("GET", "/api/promises?status=FULFILLED")
        handler_f.do_GET()
        self.assertEqual(handler_f.response_status, HTTPStatus.OK)
        res_f = handler_f.get_json_response()
        self.assertEqual(res_f["total"], 2)
        for pr in res_f["promises"]:
            self.assertEqual(pr["status"], "FULFILLED")

    def test_pipeline_simulate_speaker_swap_correction(self):
        payload = {
            "task_code": "TASK_SPEECH_PARSE",
            "simulate_error": "E02_SPEAKER_SWAP",
        }
        handler = MockHttpHandler("POST", "/api/pipeline/simulate", body=payload)
        handler.do_POST()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()

        meta = res["meta"]
        self.assertEqual(meta["attempts_count"], 2)
        self.assertEqual(meta["final_verdict"], "APPROVE")
        self.assertTrue(meta["error_resolved"])

        # Check step-by-step history trace
        history = res["simulation_result"]["history"]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["verdict"]["error_code"], "E02_SPEAKER_SWAP")
        self.assertEqual(history[1]["verdict"]["verdict"], "APPROVE")

    def test_pipeline_simulate_timestamp_drift_correction(self):
        payload = {
            "task_code": "TASK_SPEECH_PARSE",
            "simulate_error": "E04_TIMESTAMP_DRIFT",
        }
        handler = MockHttpHandler("POST", "/api/pipeline/simulate", body=payload)
        handler.do_POST()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()

        meta = res["meta"]
        self.assertEqual(meta["attempts_count"], 2)
        self.assertTrue(meta["error_resolved"])
        history = res["simulation_result"]["history"]
        self.assertEqual(history[0]["verdict"]["error_code"], "E04_TIMESTAMP_DRIFT")

    def test_pipeline_simulate_missing_citation_correction(self):
        payload = {
            "task_code": "TASK_POLICY_EVAL",
            "simulate_error": "E03_MISSING_CITATION",
        }
        handler = MockHttpHandler("POST", "/api/pipeline/simulate", body=payload)
        handler.do_POST()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()

        meta = res["meta"]
        self.assertEqual(meta["attempts_count"], 2)
        self.assertTrue(meta["error_resolved"])
        history = res["simulation_result"]["history"]
        self.assertEqual(history[0]["verdict"]["error_code"], "E03_MISSING_CITATION")
        self.assertEqual(history[1]["verdict"]["verdict"], "APPROVE")

    def test_not_found_endpoint(self):
        handler = MockHttpHandler("GET", "/api/unknown_route")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.NOT_FOUND)
        res = handler.get_json_response()
        self.assertIn("error", res)

    def test_security_status_endpoint(self):
        handler = MockHttpHandler("GET", "/api/security/status")
        handler.do_GET()
        self.assertEqual(handler.response_status, HTTPStatus.OK)
        res = handler.get_json_response()
        self.assertTrue(res["security_protections"]["sqlite_wal_journal_mode"])
        self.assertTrue(res["security_protections"]["parameterized_queries"])
        self.assertTrue(res["security_protections"]["owasp_headers_enforced"])
        self.assertIn("latest_sync_logs", res)

    def test_sync_ly_endpoint_with_auth(self):
        # 1. Unauthorized attempt (no token)
        bad_handler = MockHttpHandler("POST", "/api/sync/ly", body={"live": False})
        bad_handler.do_POST()
        self.assertEqual(bad_handler.response_status, HTTPStatus.UNAUTHORIZED)

        # 2. Authorized attempt (with valid admin token)
        good_handler = MockHttpHandler("POST", "/api/sync/ly", body={"live": False})
        good_handler.headers["Authorization"] = "Bearer dev-admin-token-change-me"
        good_handler.do_POST()
        self.assertEqual(good_handler.response_status, HTTPStatus.OK)
        res = good_handler.get_json_response()
        self.assertEqual(res["status"], "SUCCESS")
        self.assertGreaterEqual(res["legislators_synced"], 3)


if __name__ == "__main__":
    unittest.main()
