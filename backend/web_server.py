"""
CivicTracker TW - Standard Library HTTP & REST Web Server
Provides zero-dependency API, SQLite persistence, cybersecurity hardening,
and serves the interactive Single-Page Application.
"""

import argparse
import copy
import json
import mimetypes
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from backend.core.config_compiler import (
    compile_config,
    verify_source_integrity,
)
from backend.core.database import get_database_engine
from backend.core.ly_crawler import LegislativeYuanCrawler
from backend.core.model_router import (
    DualModelPipeline,
    HydrogenSubmissionEnvelope,
)
from backend.core.security import (
    MAX_POST_BODY_BYTES,
    InputSanitizer,
    SecurityHeaders,
    get_rate_limiter,
    verify_admin_token,
)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
CONFIG_HUMAN = BASE_DIR / "config" / "pipeline.human.yaml"
CONFIG_PROTO = BASE_DIR / "config" / "generated" / "agent_protocol.json"


class CivicTrackerApiHandler(BaseHTTPRequestHandler):
    """Handles REST API and static asset requests for CivicTracker TW."""

    server_version = "CivicTrackerServer/2.0"

    def _get_client_ip(self) -> str:
        if hasattr(self, "client_address") and self.client_address:
            return self.client_address[0]
        return "127.0.0.1"

    def _send_security_and_cors_headers(self, remaining_limit: Optional[int] = None):
        SecurityHeaders.apply(self)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Admin-Token")
        if remaining_limit is not None:
            self.send_header("X-RateLimit-Remaining", str(remaining_limit))

    def _send_json_response(self, data: Any, status: int = HTTPStatus.OK, remaining_limit: Optional[int] = None):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_security_and_cors_headers(remaining_limit=remaining_limit)
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, message: str, status: int = HTTPStatus.BAD_REQUEST, code: Optional[str] = None):
        payload = {"error": message, "status": status}
        if code:
            payload["code"] = code
        self._send_json_response(payload, status=status)

    def _serve_file(self, file_path: Path):
        if not file_path.is_file():
            self._send_error_json("Resource not found", status=HTTPStatus.NOT_FOUND)
            return

        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "text/html" if file_path.suffix == ".html" else "application/octet-stream"
        if mime_type.startswith("text/"):
            mime_type += "; charset=utf-8"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self._send_security_and_cors_headers()
            self.end_headers()
            self.wfile.write(content)
        except Exception as exc:
            self._send_error_json(f"Error serving file: {exc}", status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_security_and_cors_headers()
        self.end_headers()

    def do_GET(self):
        # 1. Rate Limiting Check
        client_ip = self._get_client_ip()
        allowed, remaining, retry_after = get_rate_limiter().check_rate_limit(client_ip)
        if not allowed:
            self.send_response(HTTPStatus.TOO_MANY_REQUESTS)
            self.send_header("Retry-After", str(retry_after))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_security_and_cors_headers(remaining_limit=0)
            self.end_headers()
            self.wfile.write(b'{"error": "Too Many Requests. Rate limit exceeded.", "status": 429}')
            return

        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # ---------------------------------------------------------------------
        # Static Content Routing
        # ---------------------------------------------------------------------
        if path in ("/", "/index.html"):
            index_path = FRONTEND_DIR / "index.html"
            self._serve_file(index_path)
            return

        if not path.startswith("/api/"):
            rel_file = path.lstrip("/")
            file_candidate = FRONTEND_DIR / rel_file
            if file_candidate.is_file():
                self._serve_file(file_candidate)
                return
            self._serve_file(FRONTEND_DIR / "index.html")
            return

        # ---------------------------------------------------------------------
        # REST API Endpoints (Persistent SQLite Backend)
        # ---------------------------------------------------------------------
        db = get_database_engine()

        if path == "/api/protocol":
            if not CONFIG_PROTO.is_file():
                compile_config(CONFIG_HUMAN, CONFIG_PROTO)
            with open(CONFIG_PROTO, "r", encoding="utf-8") as f:
                proto_data = json.load(f)
            is_synced = verify_source_integrity(CONFIG_HUMAN, CONFIG_PROTO)
            response = {
                "protocol": proto_data,
                "sync_status": {
                    "is_synchronized": is_synced,
                    "human_config": CONFIG_HUMAN.name,
                    "machine_protocol": CONFIG_PROTO.name,
                },
            }
            self._send_json_response(response, remaining_limit=remaining)
            return

        elif path == "/api/stats":
            self._send_json_response(db.get_overview_stats(), remaining_limit=remaining)
            return

        elif path == "/api/security/status":
            sec_meta = db.get_security_metadata()
            sync_logs = db.get_sync_logs(limit=5)
            response = {
                "security_protections": {
                    "sqlite_wal_journal_mode": sec_meta.get("journal_mode") == "WAL",
                    "foreign_keys_enforced": sec_meta.get("foreign_keys_enabled", True),
                    "parameterized_queries": True,
                    "owasp_headers_enforced": True,
                    "rate_limiter_active": True,
                    "rate_limit_policy": "120 requests / 60 seconds per IP",
                    "max_post_body_bytes": MAX_POST_BODY_BYTES,
                    "timing_safe_admin_auth": True,
                },
                "database_metadata": sec_meta,
                "latest_sync_logs": sync_logs,
            }
            self._send_json_response(response, remaining_limit=remaining)
            return

        elif path == "/api/politicians":
            self._send_json_response({"politicians": db.get_politicians()}, remaining_limit=remaining)
            return

        elif path.startswith("/api/politicians/"):
            raw_id = path.replace("/api/politicians/", "").strip()
            pol_id = InputSanitizer.sanitize_query_string(raw_id)
            pol = db.get_politician(pol_id)
            if pol:
                self._send_json_response(pol, remaining_limit=remaining)
            else:
                self._send_error_json(f"Politician '{pol_id}' not found", status=HTTPStatus.NOT_FOUND)
            return

        elif path == "/api/speeches":
            q = InputSanitizer.sanitize_query_string(query.get("q", [None])[0])
            tag = InputSanitizer.sanitize_query_string(query.get("tag", [None])[0])
            pol_id = InputSanitizer.sanitize_query_string(query.get("politician_id", [None])[0])
            speeches = db.get_speeches(q=q or None, tag=tag or None, politician_id=pol_id or None)
            self._send_json_response({"speeches": speeches, "total": len(speeches)}, remaining_limit=remaining)
            return

        elif path == "/api/votes":
            pol_id = InputSanitizer.sanitize_query_string(query.get("politician_id", [None])[0])
            bill_id = InputSanitizer.sanitize_query_string(query.get("bill_id", [None])[0])
            votes = db.get_votes(politician_id=pol_id or None, bill_id=bill_id or None)
            self._send_json_response({"votes": votes, "total": len(votes)}, remaining_limit=remaining)
            return

        elif path == "/api/promises":
            pol_id = InputSanitizer.sanitize_query_string(query.get("politician_id", [None])[0])
            status = InputSanitizer.sanitize_query_string(query.get("status", [None])[0])
            promises = db.get_promises(politician_id=pol_id or None, status=status or None)
            self._send_json_response({"promises": promises, "total": len(promises)}, remaining_limit=remaining)
            return

        elif path == "/api/exam-cards":
            pol_id = InputSanitizer.sanitize_query_string(query.get("politician_id", [None])[0])
            stage = InputSanitizer.sanitize_query_string(query.get("exam_stage", [None])[0])
            cards = db.get_exam_cards(politician_id=pol_id or None, exam_stage=stage or None)
            self._send_json_response({"exam_cards": cards, "total": len(cards)}, remaining_limit=remaining)
            return

        elif path == "/api/petitions":
            pol_id = InputSanitizer.sanitize_query_string(query.get("politician_id", [None])[0])
            status = InputSanitizer.sanitize_query_string(query.get("status", [None])[0])
            petitions = db.get_petitions(politician_id=pol_id or None, status=status or None)
            self._send_json_response({"petitions": petitions, "total": len(petitions)}, remaining_limit=remaining)
            return

        else:
            self._send_error_json(f"API endpoint '{path}' not found", status=HTTPStatus.NOT_FOUND)

    def do_POST(self):
        # 1. Rate Limiting Check
        client_ip = self._get_client_ip()
        allowed, remaining, retry_after = get_rate_limiter().check_rate_limit(client_ip)
        if not allowed:
            self.send_response(HTTPStatus.TOO_MANY_REQUESTS)
            self.send_header("Retry-After", str(retry_after))
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_security_and_cors_headers(remaining_limit=0)
            self.end_headers()
            self.wfile.write(b'{"error": "Too Many Requests. Rate limit exceeded.", "status": 429}')
            return

        parsed = urlparse(self.path)
        path = parsed.path

        # 2. Input Size Limit Check
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > MAX_POST_BODY_BYTES:
            self._send_error_json(
                f"Payload Too Large: Exceeds {MAX_POST_BODY_BYTES} bytes maximum limit.",
                status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            )
            return

        try:
            raw_body = self.rfile.read(content_length).decode("utf-8")
            body = json.loads(raw_body) if raw_body else {}
        except Exception as exc:
            self._send_error_json(f"Invalid JSON request body: {exc}", status=HTTPStatus.BAD_REQUEST)
            return

        db = get_database_engine()

        # Endpoint A: Interactive Simulation
        if path == "/api/pipeline/simulate":
            result = self._handle_pipeline_simulate(body)
            self._send_json_response(result, remaining_limit=remaining)
            return

        # Endpoint B: Legislative Yuan Open Data Synchronization
        elif path == "/api/sync/ly":
            # Timing-attack-safe admin authentication
            auth_header = self.headers.get("Authorization", "")
            token = None
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ", 1)[1].strip()
            elif "X-Admin-Token" in self.headers:
                token = self.headers["X-Admin-Token"].strip()
            elif body and "admin_token" in body:
                token = str(body["admin_token"]).strip()

            if not verify_admin_token(token):
                self._send_error_json(
                    "Unauthorized: Invalid or missing admin authentication token.",
                    status=HTTPStatus.UNAUTHORIZED,
                    code="ERR_AUTH_FAILED",
                )
                return

            is_live = bool(body.get("live", False)) if body else False
            crawler = LegislativeYuanCrawler(db=db)
            sync_report = crawler.sync_to_database(live=is_live)
            self._send_json_response(sync_report, remaining_limit=remaining)
            return

        self._send_error_json(f"Endpoint '{path}' not supported for POST", status=HTTPStatus.NOT_FOUND)

    def _handle_pipeline_simulate(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Runs interactive task through DualModelPipeline and returns full execution trace."""
        task_code = body.get("task_code", "TASK_SPEECH_PARSE")
        simulate_error = body.get("simulate_error", "NONE")
        enable_sampling = bool(body.get("enable_sampling", False))

        pipeline = DualModelPipeline(
            protocol_path=CONFIG_PROTO,
            human_config_path=CONFIG_HUMAN,
            verify_drift=False,
        )

        # Build initial payload according to selected task & simulation error
        if task_code == "TASK_SPEECH_PARSE":
            base_payload = {
                "session_id": "session-sim-101",
                "speaker_term_id": "pol-lin-leg-10",
                "target_official_id": "official-motc-01",
                "start_time_sec": 150.0,
                "end_time_sec": 420.0,
                "transcript_raw": (
                    "【委員】：請交通部針對全國人行步道退縮行穿線全面啟動評估。"
                    "【部長】：我們已會同國土署編列 400 億專款優先改善 600 處路口。"
                ),
                "ai_summary": "委員質詢行人交通工程安全與退縮行穿線進度，交通部說明 400 億專款專用計畫。",
                "confidence": 0.92,
            }

            def hydrogen_mock(task_code, payload, submission_id, attempt, previous_error, directive):
                curr = dict(payload)
                if attempt == 1:
                    if simulate_error == "E02_SPEAKER_SWAP":
                        curr["speaker_term_id"] = "official-motc-01"
                        curr["target_official_id"] = "official-motc-01"
                    elif simulate_error == "E04_TIMESTAMP_DRIFT":
                        curr["start_time_sec"] = 420.0
                        curr["end_time_sec"] = 150.0
                    elif simulate_error == "E01_HALLUCINATION":
                        curr["_simulate_hallucination"] = True
                        curr["ai_summary"] = "交通部當場簽署同意下週全台廢除所有測速照相機。"
                else:
                    if previous_error == "E02_SPEAKER_SWAP":
                        curr["speaker_term_id"] = "pol-lin-leg-10"
                        curr["target_official_id"] = "official-motc-01"
                    elif previous_error == "E04_TIMESTAMP_DRIFT":
                        curr["start_time_sec"] = 150.0
                        curr["end_time_sec"] = 420.0
                    elif previous_error == "E01_HALLUCINATION":
                        curr["_simulate_hallucination"] = False
                        curr["ai_summary"] = "交通部說明 400 億專款專用改善 600 處路口。"

                return HydrogenSubmissionEnvelope(
                    task_code=task_code,
                    submission_id=submission_id,
                    confidence=0.95,
                    payload=curr,
                    attempt=attempt,
                    previous_error=previous_error,
                )

            res = pipeline.route_task(
                task_code=task_code,
                payload=base_payload,
                executor_handler=hydrogen_mock,
                enable_sampling=enable_sampling,
            )

        elif task_code == "TASK_POLICY_EVAL":
            base_payload = {
                "promise_id": "promise-sim-202",
                "title": "智慧節能公車普及與綠色路網計畫",
                "status": "IN_PROGRESS",
                "source_url": "https://bulletin.cec.gov.tw/mayoral/promise-sim-202",
                "milestones": [
                    {
                        "id": "ms-sim-01",
                        "milestone_date": "2025-06-01",
                        "evidence_summary": "第一期 30 輛低底盤電動公車驗收啟用",
                        "source_url": "https://web.pcc.gov.tw/tenders/bus-2025-01",
                    }
                ],
                "confidence": 0.98,
            }

            def hydrogen_policy_mock(task_code, payload, submission_id, attempt, previous_error, directive):
                curr = copy.deepcopy(payload)
                if attempt == 1:
                    if simulate_error == "E03_MISSING_CITATION":
                        curr["milestones"][0]["source_url"] = ""
                else:
                    if previous_error == "E03_MISSING_CITATION":
                        curr["milestones"][0]["source_url"] = "https://web.pcc.gov.tw/tenders/bus-2025-01"

                return HydrogenSubmissionEnvelope(
                    task_code=task_code,
                    submission_id=submission_id,
                    confidence=0.98,
                    payload=curr,
                    attempt=attempt,
                    previous_error=previous_error,
                )

            res = pipeline.route_task(
                task_code=task_code,
                payload=base_payload,
                executor_handler=hydrogen_policy_mock,
                enable_sampling=enable_sampling,
            )

        elif task_code == "TASK_VOTE_ANALYZE":
            base_payload = {
                "bill_id": "bill-sim-303",
                "politician_id": "pol-lin-01",
                "decision": "APPROVE",
                "source_url": "https://data.ly.gov.tw/vote/sim-303",
                "confidence": 0.95,
            }

            def hydrogen_vote_mock(task_code, payload, submission_id, attempt, previous_error, directive):
                curr = dict(payload)
                if attempt == 1 and simulate_error == "E05_SCHEMA_VIOLATION":
                    curr["decision"] = "UNCONFIRMED_VOTE"
                elif attempt > 1:
                    curr["decision"] = "APPROVE"
                return HydrogenSubmissionEnvelope(
                    task_code=task_code,
                    submission_id=submission_id,
                    confidence=0.95,
                    payload=curr,
                    attempt=attempt,
                    previous_error=previous_error,
                )

            res = pipeline.route_task(
                task_code=task_code,
                payload=base_payload,
                executor_handler=hydrogen_vote_mock,
                enable_sampling=enable_sampling,
            )

        else:
            return {"error": f"Unsupported simulation task_code: {task_code}"}

        return {
            "simulation_result": res.to_dict(),
            "meta": {
                "task_code": task_code,
                "simulated_error": simulate_error,
                "attempts_count": res.attempts,
                "final_verdict": res.argon_verdict.verdict if res.argon_verdict else "APPROVED_BY_GATE",
                "error_resolved": (res.attempts > 1 and res.success),
            },
        }


def run_server(port: int = 8080, host: str = "0.0.0.0"):
    """Starts the ThreadingHTTPServer."""
    if not CONFIG_PROTO.is_file():
        compile_config(CONFIG_HUMAN, CONFIG_PROTO)

    # Initialize and verify persistent database
    db = get_database_engine()
    sec_meta = db.get_security_metadata()

    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, CivicTrackerApiHandler)
    print(f"[CivicTracker Web Server] Running on http://{host}:{port}/")
    print(f"[CivicTracker Web Server] Database Engine: SQLite ({sec_meta.get('journal_mode')} Mode, Parameterized SQL Active)")
    print(f"[CivicTracker Web Server] Rate Limiter: Active (120 req / 60s per IP)")
    print(f"[CivicTracker Web Server] OWASP Security Headers: Enforced")
    print(f"[CivicTracker Web Server] Frontend UI: http://localhost:{port}/")
    print(f"[CivicTracker Web Server] API Security Status: http://localhost:{port}/api/security/status")
    print(f"[CivicTracker Web Server] Press Ctrl+C to terminate.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[CivicTracker Web Server] Shutting down gracefully...")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CivicTracker TW Full-Stack Web Server")
    default_port = int(os.environ.get("PORT", "8080"))
    parser.add_argument("--port", type=int, default=default_port, help="Port to listen on (default 8080)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface (default 0.0.0.0)")
    args = parser.parse_args()
    run_server(port=args.port, host=args.host)
