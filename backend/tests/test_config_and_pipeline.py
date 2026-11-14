"""
CivicTracker TW - Unit Tests
Tests configuration compiler, hash integrity / drift detection, domain models,
and the DualModelPipeline (Hydrogen Executor <-> Argon Evaluator) retry loops.
"""

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

from backend.core.config_compiler import (
    ConfigDriftError,
    ConfigValidationError,
    compile_config,
    compile_protocol,
    compute_source_hash,
    validate_human_config,
)
from backend.core.model_router import (
    ArgonVerdictEnvelope,
    DualModelPipeline,
    HydrogenSubmissionEnvelope,
    PipelineResult,
)
from backend.core.yaml_parser import load_yaml
from backend.models.domain import (
    CitizenPetition,
    ExamReportCard,
    ExecutionMilestone,
    FulfillmentStatus,
    InterpellationSpeech,
    LegislativeSession,
    PolicyPromise,
    Politician,
    RoleType,
    Term,
    VoteDecision,
    VoteRecord,
)


class TestConfigCompilerAndDrift(unittest.TestCase):
    """Verifies YAML parsing, schema validation, protocol compilation, and drift detection."""

    def setUp(self):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.human_yaml_path = self.base_dir / "config" / "pipeline.human.yaml"
        self.generated_json_path = self.base_dir / "config" / "generated" / "agent_protocol.json"

    def test_compile_production_config(self):
        result = compile_config(self.human_yaml_path, self.generated_json_path)
        self.assertEqual(result["protocol_version"], "1.0.0")
        self.assertEqual(result["project_name"], "CivicTracker-TW")
        self.assertTrue(result["source_hash"].startswith("sha256:"))
        self.assertIn("TASK_SPEECH_PARSE", result["gates"])
        self.assertIn("TASK_VOTE_ANALYZE", result["gates"])
        self.assertIn("TASK_POLICY_EVAL", result["gates"])
        self.assertIn("TASK_PETITION_TRIAGE", result["gates"])
        self.assertIn("E01_HALLUCINATION", result["err_directives"])
        self.assertIn("E02_SPEAKER_SWAP", result["err_directives"])
        self.assertIn("E03_MISSING_CITATION", result["err_directives"])
        self.assertIn("E04_TIMESTAMP_DRIFT", result["err_directives"])
        self.assertIn("E05_SCHEMA_VIOLATION", result["err_directives"])
        self.assertIn("E06_UNSUBSTANTIATED_ABUSE", result["err_directives"])
        self.assertIn("feature_flags", result)
        self.assertTrue(result["feature_flags"]["enable_ivod_video_embed"])
        self.assertIn("external_endpoints", result)
        self.assertIn("v2.ly.govapi.tw", result["external_endpoints"]["ly_govapi_v2_url"])
        self.assertIn("HydrogenSubmissionEnvelope", result["wire_schemas"])
        self.assertIn("ArgonVerdictEnvelope", result["wire_schemas"])

    def test_drift_detection_raises_error(self):
        # 1. Pipeline should load fine with matching config
        pipeline = DualModelPipeline(
            protocol_path=self.generated_json_path,
            human_config_path=self.human_yaml_path,
            verify_drift=True,
        )
        self.assertIsNotNone(pipeline)

        # 2. Simulate drift: modified human config
        with tempfile.NamedTemporaryFile("w+", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write("version: '1.0.1'\nproject_name: 'DriftedProject'\n")
            drifted_yaml_path = f.name

        try:
            with self.assertRaises(ConfigDriftError):
                DualModelPipeline(
                    protocol_path=self.generated_json_path,
                    human_config_path=drifted_yaml_path,
                    verify_drift=True,
                )
        finally:
            if os.path.exists(drifted_yaml_path):
                os.remove(drifted_yaml_path)

    def test_config_validation_failures(self):
        raw_cfg = load_yaml(str(self.human_yaml_path))

        # Missing required section
        bad_cfg = copy.deepcopy(raw_cfg)
        del bad_cfg["models"]
        with self.assertRaises(ConfigValidationError):
            validate_human_config(bad_cfg)

        # Invalid confidence bounds (> 1.0)
        bad_cfg = copy.deepcopy(raw_cfg)
        bad_cfg["quality_gates"]["interpellation_transcript"]["min_executor_confidence"] = 1.5
        with self.assertRaises(ConfigValidationError):
            validate_human_config(bad_cfg)

        # Invalid error severity
        bad_cfg = copy.deepcopy(raw_cfg)
        bad_cfg["error_catalog"][0]["severity"] = "UNKNOWN_SEVERITY"
        with self.assertRaises(ConfigValidationError):
            validate_human_config(bad_cfg)

        # Duplicate error code
        bad_cfg = copy.deepcopy(raw_cfg)
        bad_cfg["error_catalog"].append(copy.deepcopy(bad_cfg["error_catalog"][0]))
        with self.assertRaises(ConfigValidationError):
            validate_human_config(bad_cfg)


class TestDomainModels(unittest.TestCase):
    """Verifies domain models representing Phase 1 and Phase 2."""

    def test_politician_cross_phase_terms(self):
        # Politician starts as Legislator (Phase 1), then becomes Mayor/Executive (Phase 2)
        pol = Politician(id="pol-001", name="陳大文", party="無黨籍")
        term1 = Term(
            id="term-leg-10",
            politician_id="pol-001",
            role_type=RoleType.LEGISLATOR.value,
            constituency="台北市第一選區",
            start_date="2020-02-01",
            end_date="2024-01-31",
            title="立法委員",
        )
        term2 = Term(
            id="term-exec-08",
            politician_id="pol-001",
            role_type=RoleType.EXECUTIVE.value,
            constituency="台北市",
            start_date="2024-12-25",
            end_date=None,
            title="台北市市長",
        )
        pol.add_term(term1)
        pol.add_term(term2)

        self.assertEqual(len(term1.validate()), 0)
        self.assertEqual(len(term2.validate()), 0)
        self.assertTrue(pol.is_legislator())
        self.assertTrue(pol.is_executive())
        self.assertEqual(len(pol.get_terms_by_role(RoleType.LEGISLATOR)), 1)
        self.assertEqual(len(pol.get_terms_by_role(RoleType.EXECUTIVE)), 1)

    def test_interpellation_speech_validation(self):
        # Valid speech
        speech = InterpellationSpeech(
            id="speech-001",
            session_id="session-10-01",
            speaker_term_id="term-leg-10",
            target_official_id="term-exec-gov-01",
            start_time_sec=100.0,
            end_time_sec=450.0,
            transcript_raw="質詢內容...",
            ai_summary="摘要內容...",
            topic_tags=["交通改革", "行人安全"],
        )
        self.assertEqual(speech.validate(), [])

        # Inverted timestamps -> E04_TIMESTAMP_DRIFT
        bad_timestamps = copy.deepcopy(speech)
        bad_timestamps.start_time_sec = 500.0
        bad_timestamps.end_time_sec = 300.0
        errs = bad_timestamps.validate()
        self.assertTrue(any(code == "E04_TIMESTAMP_DRIFT" for code, _ in errs))

        # Speaker swap (legislator identical to target official) -> E02_SPEAKER_SWAP
        swapped_speaker = copy.deepcopy(speech)
        swapped_speaker.target_official_id = swapped_speaker.speaker_term_id
        errs = swapped_speaker.validate()
        self.assertTrue(any(code == "E02_SPEAKER_SWAP" for code, _ in errs))

    def test_vote_record_validation(self):
        vote = VoteRecord(
            id="vote-001",
            bill_id="bill-ly-1234",
            politician_id="pol-001",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/1234",
        )
        self.assertEqual(vote.validate(), [])

        # Invalid decision -> E05_SCHEMA_VIOLATION
        bad_vote = copy.deepcopy(vote)
        bad_vote.decision = "NOT_A_DECISION"
        errs = bad_vote.validate()
        self.assertTrue(any(code == "E05_SCHEMA_VIOLATION" for code, _ in errs))

        # Missing URL -> E03_MISSING_CITATION
        no_url = copy.deepcopy(vote)
        no_url.source_url = "invalid-url"
        errs = no_url.validate()
        self.assertTrue(any(code == "E03_MISSING_CITATION" for code, _ in errs))

    def test_policy_promise_and_milestones_validation(self):
        promise = PolicyPromise(
            id="promise-tp-01",
            politician_id="pol-001",
            term_id="term-exec-08",
            title="興建公共自行車專用道 50 公里",
            category="交通建設",
            status=FulfillmentStatus.IN_PROGRESS.value,
            source_url="https://bulletin.cec.gov.tw/promise/01",
        )
        milestone = ExecutionMilestone(
            id="ms-01",
            promise_id="promise-tp-01",
            milestone_date="2025-06-30",
            evidence_summary="第一期路網發包完成，預算支應 3000 萬元",
            source_url="https://web.pcc.gov.tw/tender/ms-01",
            budget_spent=30000000.0,
        )
        promise.add_milestone(milestone)
        self.assertEqual(promise.validate(), [])

        # Milestone missing citation URL -> E03_MISSING_CITATION
        bad_milestone = copy.deepcopy(milestone)
        bad_milestone.source_url = ""
        bad_promise = copy.deepcopy(promise)
        bad_promise.milestones = [bad_milestone]
        errs = bad_promise.validate()
        self.assertTrue(any(code == "E03_MISSING_CITATION" for code, _ in errs))

    def test_exam_report_card_validation(self):
        card = ExamReportCard(
            id="card-001",
            politician_id="pol-001",
            term_id="term-001",
            exam_stage="MIDTERM",
            attendance_rate=98.5,
            objective_score=92.0,
            argon_summary_comment="問政質詢專業，委員會全勤",
            citizen_rating_avg=4.6,
            citizen_reviews_count=128,
        )
        self.assertEqual(card.validate(), [])

        # Invalid stage -> E05_SCHEMA_VIOLATION
        bad_card = copy.deepcopy(card)
        bad_card.exam_stage = "INVALID_STAGE"
        errs = bad_card.validate()
        self.assertTrue(any(code == "E05_SCHEMA_VIOLATION" for code, _ in errs))

    def test_citizen_petition_validation(self):
        pet = CitizenPetition(
            id="petition-001",
            politician_id="pol-001",
            category="交通建設",
            author_name="內湖通勤族",
            title="建請加速內湖捷運東環段",
            content="內科交通急需改善，盼加速捷運施工進度",
            citizen_score=5,
            status="APPROVED",
            created_at="2024-11-01",
        )
        self.assertEqual(pet.validate(), [])

        # Bad score (> 5) -> E05_SCHEMA_VIOLATION
        bad_pet = copy.deepcopy(pet)
        bad_pet.citizen_score = 10
        errs = bad_pet.validate()
        self.assertTrue(any(code == "E05_SCHEMA_VIOLATION" for code, _ in errs))


class TestPhase1SpeechParsePipeline(unittest.TestCase):
    """
    Tests Phase 1 Speech Parsing task where Hydrogen initially makes an attribution or timestamp
    error, Argon catches it with E02/E04 and directive, and Hydrogen self-corrects on retry.
    """

    def setUp(self):
        self.pipeline = DualModelPipeline()

    def test_speaker_swap_correction_on_retry(self):
        """Hydrogen produces speaker swap error on attempt 1; fixes on attempt 2 after Argon directive."""
        task_code = "TASK_SPEECH_PARSE"
        initial_payload = {
            "session_id": "session-10-02",
            "speaker_term_id": "pol-target-minister",  # Incorrectly swapped!
            "target_official_id": "pol-target-minister",  # Same as speaker!
            "start_time_sec": 120.0,
            "end_time_sec": 300.0,
            "transcript_raw": "委員質詢有關社宅進度，部長答覆已發包三千戶。",
            "ai_summary": "社宅發包進度質詢與答覆",
            "confidence": 0.88,
        }

        def mock_hydrogen_executor(task_code, payload, submission_id, attempt, previous_error, directive):
            curr_payload = dict(payload)
            if attempt == 1:
                # First attempt has speaker swap bug
                curr_payload["speaker_term_id"] = "pol-target-minister"
                curr_payload["target_official_id"] = "pol-target-minister"
            else:
                # Hydrogen received directive from Argon! Self-corrects:
                self.assertEqual(previous_error, "E02_SPEAKER_SWAP")
                self.assertIn("Re-attribute speaker turns", directive)
                curr_payload["speaker_term_id"] = "pol-leg-chen"
                curr_payload["target_official_id"] = "pol-target-minister"

            return HydrogenSubmissionEnvelope(
                task_code=task_code,
                submission_id=submission_id,
                confidence=0.92,
                payload=curr_payload,
                attempt=attempt,
                previous_error=previous_error,
            )

        res: PipelineResult = self.pipeline.route_task(
            task_code=task_code,
            payload=initial_payload,
            executor_handler=mock_hydrogen_executor,
        )

        self.assertTrue(res.success)
        self.assertEqual(res.attempts, 2)
        self.assertEqual(len(res.history), 2)
        self.assertEqual(res.history[0]["verdict"]["verdict"], "REJECT")
        self.assertEqual(res.history[0]["verdict"]["error_code"], "E02_SPEAKER_SWAP")
        self.assertEqual(res.history[1]["verdict"]["verdict"], "APPROVE")
        self.assertEqual(res.final_payload["speaker_term_id"], "pol-leg-chen")
        self.assertEqual(res.final_payload["audit_metadata"]["audit_verdict"], "APPROVE")

    def test_timestamp_drift_correction_on_retry(self):
        """Hydrogen produces inverted timestamps on attempt 1; fixes on attempt 2."""
        task_code = "TASK_SPEECH_PARSE"
        initial_payload = {
            "session_id": "session-10-02",
            "speaker_term_id": "pol-leg-chen",
            "target_official_id": "pol-target-minister",
            "start_time_sec": 450.0,  # Inverted!
            "end_time_sec": 120.0,
            "transcript_raw": "交通部長答詢...",
            "ai_summary": "交通議題",
            "confidence": 0.90,
        }

        def mock_hydrogen_executor(task_code, payload, submission_id, attempt, previous_error, directive):
            curr_payload = dict(payload)
            if attempt == 1:
                curr_payload["start_time_sec"] = 450.0
                curr_payload["end_time_sec"] = 120.0
            else:
                self.assertEqual(previous_error, "E04_TIMESTAMP_DRIFT")
                self.assertIn("Recalculate timestamps", directive)
                curr_payload["start_time_sec"] = 120.0
                curr_payload["end_time_sec"] = 450.0

            return HydrogenSubmissionEnvelope(
                task_code=task_code,
                submission_id=submission_id,
                confidence=0.95,
                payload=curr_payload,
                attempt=attempt,
                previous_error=previous_error,
            )

        res: PipelineResult = self.pipeline.route_task(
            task_code=task_code,
            payload=initial_payload,
            executor_handler=mock_hydrogen_executor,
        )

        self.assertTrue(res.success)
        self.assertEqual(res.attempts, 2)
        self.assertEqual(res.history[0]["verdict"]["error_code"], "E04_TIMESTAMP_DRIFT")
        self.assertEqual(res.final_payload["start_time_sec"], 120.0)
        self.assertEqual(res.final_payload["end_time_sec"], 450.0)


class TestPhase2PolicyEvalPipeline(unittest.TestCase):
    """
    Tests Phase 2 Policy Promise Evaluation where TASK_POLICY_EVAL forces Argon verdict
    and enforces strict citation provenance (E03_MISSING_CITATION).
    """

    def setUp(self):
        self.pipeline = DualModelPipeline()

    def test_missing_citation_rejection_and_approval(self):
        task_code = "TASK_POLICY_EVAL"
        initial_payload = {
            "promise_id": "promise-exec-99",
            "title": "四年興辦公托中心 100 處",
            "status": "IN_PROGRESS",
            "source_url": "https://bulletin.cec.gov.tw/mayoral/promise-99",
            "milestones": [
                {
                    "id": "ms-99-1",
                    "milestone_date": "2025-03-01",
                    "evidence_summary": "第一批 20 處公托完工啟用",
                    "source_url": "",  # Missing citation!
                }
            ],
            "confidence": 0.98,  # Even with high confidence, always_require_argon_verdict forces Argon review!
        }

        def mock_hydrogen_executor(task_code, payload, submission_id, attempt, previous_error, directive):
            curr_payload = copy.deepcopy(payload)
            if attempt == 1:
                curr_payload["milestones"][0]["source_url"] = ""
            else:
                self.assertEqual(previous_error, "E03_MISSING_CITATION")
                self.assertIn("Attach exact provenance", directive)
                curr_payload["milestones"][0]["source_url"] = "https://web.pcc.gov.tw/tenders/tender-99-1"

            return HydrogenSubmissionEnvelope(
                task_code=task_code,
                submission_id=submission_id,
                confidence=0.98,
                payload=curr_payload,
                attempt=attempt,
                previous_error=previous_error,
            )

        res: PipelineResult = self.pipeline.route_task(
            task_code=task_code,
            payload=initial_payload,
            executor_handler=mock_hydrogen_executor,
        )

        self.assertTrue(res.success)
        self.assertEqual(res.attempts, 2)
        self.assertEqual(res.history[0]["verdict"]["error_code"], "E03_MISSING_CITATION")
        self.assertEqual(res.history[1]["verdict"]["verdict"], "APPROVE")
        self.assertEqual(
            res.final_payload["milestones"][0]["source_url"],
            "https://web.pcc.gov.tw/tenders/tender-99-1",
        )
        self.assertEqual(res.final_payload["audit_metadata"]["audited_by"], "argon")

    def test_low_confidence_triggers_argon(self):
        """When Hydrogen confidence < min_executor_confidence (0.85), Argon evaluation is automatically triggered."""
        task_code = "TASK_SPEECH_PARSE"
        payload = {
            "session_id": "session-10-03",
            "speaker_term_id": "pol-leg-wang",
            "target_official_id": "pol-minister-lin",
            "start_time_sec": 10.0,
            "end_time_sec": 50.0,
            "transcript_raw": "簡短詢答內容",
            "ai_summary": "簡短摘要",
            "confidence": 0.70,  # Below min_executor_confidence (0.85)
        }

        # Handler produces low confidence submission with no errors
        res = self.pipeline.route_task(task_code, payload)
        self.assertTrue(res.success)
        # Even though rules passed, Argon was triggered because confidence (0.70) < 0.85
        self.assertIsNotNone(res.argon_verdict)
        self.assertEqual(res.argon_verdict.verdict, "APPROVE")

    def test_max_retries_exhaustion(self):
        """If Hydrogen repeatedly fails and cannot correct itself within max_retries, pipeline fails."""
        task_code = "TASK_SPEECH_PARSE"
        payload = {
            "session_id": "session-bad",
            "speaker_term_id": "pol-same",
            "target_official_id": "pol-same",  # Always broken
            "start_time_sec": 0.0,
            "end_time_sec": 10.0,
            "transcript_raw": "raw",
            "ai_summary": "summary",
            "confidence": 0.90,
        }

        res = self.pipeline.route_task(task_code, payload)
        self.assertFalse(res.success)
        # 1 initial attempt + 2 retries = 3 attempts total
        self.assertEqual(res.attempts, 3)
        self.assertEqual(res.error_code, "E02_SPEAKER_SWAP")
        self.assertIn("Argon rejected after 3 attempts", res.error_message)

    def test_vote_decision_schema_violation_retry(self):
        """Vote task with invalid decision is caught by E05_SCHEMA_VIOLATION, fixed on retry."""
        task_code = "TASK_VOTE_ANALYZE"
        initial_payload = {
            "bill_id": "bill-001",
            "politician_id": "pol-001",
            "decision": "UNCONFIRMED",  # Invalid enum!
            "source_url": "https://data.ly.gov.tw/vote/001",
            "confidence": 0.95,
        }

        def mock_executor(task_code, payload, submission_id, attempt, previous_error, directive):
            p = dict(payload)
            if attempt == 1:
                p["decision"] = "UNCONFIRMED"
            else:
                self.assertEqual(previous_error, "E05_SCHEMA_VIOLATION")
                self.assertIn("Conform strictly to schema", directive)
                p["decision"] = "APPROVE"
            return HydrogenSubmissionEnvelope(
                task_code=task_code,
                submission_id=submission_id,
                confidence=0.95,
                payload=p,
                attempt=attempt,
                previous_error=previous_error,
            )

        res = self.pipeline.route_task(task_code, initial_payload, executor_handler=mock_executor)
        self.assertTrue(res.success)
        self.assertEqual(res.attempts, 2)
        self.assertEqual(res.final_payload["decision"], "APPROVE")

    def test_hallucination_directive_handling(self):
        """Argon flags hallucination with E01_HALLUCINATION, Hydrogen strips unsupported claims on retry."""
        task_code = "TASK_SPEECH_PARSE"
        initial_payload = {
            "session_id": "session-10-09",
            "speaker_term_id": "pol-leg-01",
            "target_official_id": "pol-exec-02",
            "start_time_sec": 10.0,
            "end_time_sec": 40.0,
            "transcript_raw": "質詢內容...",
            "ai_summary": "官員承諾下個月補助每人十萬元（未在逐字稿中出現的幻覺內容）",
            "confidence": 0.92,
            "_simulate_hallucination": True,
        }

        def mock_executor(task_code, payload, submission_id, attempt, previous_error, directive):
            p = dict(payload)
            if attempt == 1:
                p["_simulate_hallucination"] = True
            else:
                self.assertEqual(previous_error, "E01_HALLUCINATION")
                self.assertIn("Strip unsupported claims", directive)
                p["_simulate_hallucination"] = False
                p["ai_summary"] = "官員說明預算研議程序。"
            return HydrogenSubmissionEnvelope(
                task_code=task_code,
                submission_id=submission_id,
                confidence=0.95,
                payload=p,
                attempt=attempt,
                previous_error=previous_error,
            )

        res = self.pipeline.route_task(task_code, initial_payload, executor_handler=mock_executor)
        self.assertTrue(res.success)
        self.assertEqual(res.attempts, 2)
        self.assertEqual(res.history[0]["verdict"]["error_code"], "E01_HALLUCINATION")
        self.assertEqual(res.history[1]["verdict"]["verdict"], "APPROVE")
        self.assertFalse(res.final_payload.get("_simulate_hallucination", False))

    def test_deterministic_sample_audit_rate(self):
        """Verifies deterministic SHA-256 sample audit triggers and honors enable_sampling."""
        # 1. Helper function boundaries
        self.assertFalse(self.pipeline._should_sample_audit("any-id", 0.0))
        self.assertTrue(self.pipeline._should_sample_audit("any-id", 1.0))
        self.assertTrue(self.pipeline._should_sample_audit("test-sub-10", 0.20))
        self.assertFalse(self.pipeline._should_sample_audit("test-sub-0", 0.20))

        # 2. High-confidence valid payload (normally would NOT trigger Argon)
        task_code = "TASK_SPEECH_PARSE"  # sample_audit_rate = 0.20
        payload = {
            "session_id": "session-audit-1",
            "speaker_term_id": "pol-leg-01",
            "target_official_id": "pol-minister-02",
            "start_time_sec": 10.0,
            "end_time_sec": 30.0,
            "transcript_raw": "逐字稿內容",
            "ai_summary": "質詢摘要",
            "confidence": 0.99,  # High confidence
        }

        # Case A: enable_sampling=True with sampled ID -> Argon evaluation triggered
        res_sampled = self.pipeline.route_task(
            task_code,
            payload,
            submission_id="test-sub-10",
            enable_sampling=True,
        )
        self.assertTrue(res_sampled.success)
        self.assertIsNotNone(res_sampled.argon_verdict)
        self.assertEqual(res_sampled.argon_verdict.verdict, "APPROVE")
        self.assertEqual(res_sampled.final_payload["audit_metadata"]["audited_by"], "argon")

        # Case B: enable_sampling=True with unsampled ID -> Argon not triggered
        res_unsampled = self.pipeline.route_task(
            task_code,
            payload,
            submission_id="test-sub-0",
            enable_sampling=True,
        )
        self.assertTrue(res_unsampled.success)
        self.assertIsNone(res_unsampled.argon_verdict)

        # Case C: enable_sampling=False with sampled ID -> Argon not triggered
        res_disabled = self.pipeline.route_task(
            task_code,
            payload,
            submission_id="test-sub-10",
            enable_sampling=False,
        )
        self.assertTrue(res_disabled.success)
        self.assertIsNone(res_disabled.argon_verdict)


if __name__ == "__main__":
    unittest.main()
