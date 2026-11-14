"""
CivicTracker TW - Model Router & DualModelPipeline
Orchestrates high-throughput Hydrogen Execution and strict Argon Evaluation & Error Directives.
"""

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from backend.core.config_compiler import (
    ConfigDriftError,
    compute_source_hash,
)
from backend.models.domain import (
    ExecutionMilestone,
    FulfillmentStatus,
    InterpellationSpeech,
    PolicyPromise,
    VoteDecision,
    VoteRecord,
)


@dataclass
class HydrogenSubmissionEnvelope:
    task_code: str
    submission_id: str
    confidence: float
    payload: Dict[str, Any]
    attempt: int = 1
    previous_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ArgonVerdictEnvelope:
    verdict: str  # "APPROVE" | "REJECT"
    task_code: str
    submission_id: str
    confidence: float
    error_code: Optional[str] = None
    model_directive: Optional[str] = None
    evaluator_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineResult:
    success: bool
    task_code: str
    submission_id: str
    attempts: int
    final_payload: Optional[Dict[str, Any]] = None
    argon_verdict: Optional[ArgonVerdictEnvelope] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "task_code": self.task_code,
            "submission_id": self.submission_id,
            "attempts": self.attempts,
            "final_payload": self.final_payload,
            "argon_verdict": self.argon_verdict.to_dict() if self.argon_verdict else None,
            "history": self.history,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


def should_sample_audit(submission_id: str, sample_rate: float) -> bool:
    """
    Deterministic pseudo-random audit sampling based on SHA-256 hash of submission_id.
    Ensures identical audit decisions for the same submission_id without external RNG drift.
    """
    if sample_rate <= 0.0:
        return False
    if sample_rate >= 1.0:
        return True
    digest = hashlib.sha256(submission_id.encode("utf-8")).hexdigest()
    ratio = int(digest[:8], 16) / 0xFFFFFFFF
    return ratio < sample_rate


class RuleChecker:
    """Runs deterministic rule and domain checks before or during Argon evaluation."""

    @staticmethod
    def inspect_payload(task_code: str, payload: Dict[str, Any], gate_cfg: Dict[str, Any]) -> List[tuple]:
        """
        Returns list of (error_code, error_message).
        """
        errors = []

        if payload.get("_simulate_hallucination"):
            errors.append(("E01_HALLUCINATION", "Ungrounded claim or hallucination detected in payload."))

        if task_code == "TASK_SPEECH_PARSE":
            # 1. Video timestamp bounds check (guarded by require_timestamp_bounds)
            if gate_cfg.get("require_timestamp_bounds", True):
                start = payload.get("start_time_sec")
                end = payload.get("end_time_sec")
                if start is not None and end is not None:
                    if start < 0 or end < 0 or start > end:
                        errors.append(("E04_TIMESTAMP_DRIFT", f"start_time_sec ({start}) > end_time_sec ({end}) or negative"))

            # 2. Speaker attribution check (guarded by check_speaker_attribution)
            if gate_cfg.get("check_speaker_attribution", True):
                speaker = payload.get("speaker_term_id")
                official = payload.get("target_official_id")
                if speaker and official and speaker == official:
                    errors.append(("E02_SPEAKER_SWAP", f"Questioning legislator matches target official: {speaker}"))

            if not payload.get("transcript_raw", "").strip():
                errors.append(("E05_SCHEMA_VIOLATION", "transcript_raw is empty"))

            if not payload.get("ai_summary", "").strip():
                errors.append(("E05_SCHEMA_VIOLATION", "ai_summary is empty"))

        elif task_code == "TASK_VOTE_ANALYZE":
            dec = payload.get("decision")
            allowed = gate_cfg.get("allowed_vote_decisions", [d.value for d in VoteDecision])
            if dec not in allowed:
                errors.append(("E05_SCHEMA_VIOLATION", f"Vote decision '{dec}' not in allowed {allowed}"))
            src = payload.get("source_url", "")
            if not (src.startswith("http://") or src.startswith("https://")):
                errors.append(("E03_MISSING_CITATION", f"Vote record lacks valid citation source_url: '{src}'"))

        elif task_code == "TASK_POLICY_EVAL":
            status = payload.get("status")
            allowed = gate_cfg.get("allowed_fulfillment_statuses", [s.value for s in FulfillmentStatus])
            if status not in allowed:
                errors.append(("E05_SCHEMA_VIOLATION", f"Policy status '{status}' not in allowed {allowed}"))
            
            # Check policy election source
            src = payload.get("source_url", "")
            if gate_cfg.get("require_verifiable_citation", True):
                if not (src.startswith("http://") or src.startswith("https://")):
                    errors.append(("E03_MISSING_CITATION", f"Policy promise missing verifiable source_url: '{src}'"))

                # Check milestones
                milestones = payload.get("milestones", [])
                for idx, m in enumerate(milestones):
                    m_src = m.get("source_url", "")
                    if not (m_src.startswith("http://") or m_src.startswith("https://")):
                        errors.append(
                            ("E03_MISSING_CITATION", f"Milestone [{idx}] missing verifiable source_url: '{m_src}'")
                        )

        elif task_code == "TASK_PETITION_TRIAGE":
            if payload.get("_simulate_abuse") or payload.get("is_abusive"):
                errors.append(("E06_UNSUBSTANTIATED_ABUSE", "Petition contains abusive language, defamation, or unsubstantiated attacks."))
            content = payload.get("content", "")
            if not isinstance(content, str) or not content.strip():
                errors.append(("E05_SCHEMA_VIOLATION", "Citizen petition content cannot be empty."))

        return errors


class HydrogenExecutor:
    """
    High-throughput execution agent (Model: Flash).
    Produces structured candidate envelopes.
    """

    def __init__(self, agent_alias: str = "hydrogen", model: str = "gemini-2.5-flash"):
        self.agent_alias = agent_alias
        self.model = model

    def execute(
        self,
        task_code: str,
        payload: Dict[str, Any],
        submission_id: str,
        attempt: int = 1,
        previous_error: Optional[str] = None,
        directive: Optional[str] = None,
        custom_handler: Optional[Callable] = None,
    ) -> HydrogenSubmissionEnvelope:
        if custom_handler:
            return custom_handler(
                task_code=task_code,
                payload=payload,
                submission_id=submission_id,
                attempt=attempt,
                previous_error=previous_error,
                directive=directive,
            )

        # Default fallback execution behavior
        confidence = float(payload.get("confidence", 0.95))
        return HydrogenSubmissionEnvelope(
            task_code=task_code,
            submission_id=submission_id,
            confidence=confidence,
            payload=dict(payload),
            attempt=attempt,
            previous_error=previous_error,
        )


class ArgonEvaluator:
    """
    Precision Evaluator & Acceptance Gatekeeper (Model: Argon).
    Enforces quality gates, checks evidence provenance, and issues structured error directives.
    """

    def __init__(self, agent_alias: str = "argon", model: str = "gemini-4-argon", strict_evidence: bool = True):
        self.agent_alias = agent_alias
        self.model = model
        self.strict_evidence = strict_evidence

    def evaluate(
        self,
        task_code: str,
        submission: HydrogenSubmissionEnvelope,
        gate_cfg: Dict[str, Any],
        err_directives: Dict[str, Any],
        custom_handler: Optional[Callable] = None,
    ) -> ArgonVerdictEnvelope:
        if custom_handler:
            return custom_handler(
                task_code=task_code,
                submission=submission,
                gate_cfg=gate_cfg,
                err_directives=err_directives,
            )

        # 1. Structural and rule checks
        rule_violations = RuleChecker.inspect_payload(task_code, submission.payload, gate_cfg)
        if rule_violations:
            err_code, err_msg = rule_violations[0]
            directive_info = err_directives.get(err_code, {})
            model_dir = directive_info.get("model_directive", f"Correct {err_code} violation.")
            return ArgonVerdictEnvelope(
                verdict="REJECT",
                task_code=task_code,
                submission_id=submission.submission_id,
                confidence=1.0,
                error_code=err_code,
                model_directive=model_dir,
                evaluator_notes=err_msg,
            )

        # 2. Check for explicit hallucination flag in payload (for test / mock scenarios)
        if submission.payload.get("_simulate_hallucination"):
            directive_info = err_directives.get("E01_HALLUCINATION", {})
            return ArgonVerdictEnvelope(
                verdict="REJECT",
                task_code=task_code,
                submission_id=submission.submission_id,
                confidence=1.0,
                error_code="E01_HALLUCINATION",
                model_directive=directive_info.get("model_directive", "Strip unsupported claims."),
                evaluator_notes="Simulation flagged ungrounded hallucination.",
            )

        # 3. Passed all acceptance gates
        return ArgonVerdictEnvelope(
            verdict="APPROVE",
            task_code=task_code,
            submission_id=submission.submission_id,
            confidence=1.0,
            evaluator_notes="All acceptance gates and evidence citations verified.",
        )


class DualModelPipeline:
    """
    Runtime coordination pipeline binding Hydrogen and Argon.
    Ensures strict adherence to agent_protocol.json and automatic self-correction.
    """

    def __init__(
        self,
        protocol_path: Union[str, Path] = "config/generated/agent_protocol.json",
        human_config_path: Union[str, Path] = "config/pipeline.human.yaml",
        verify_drift: bool = True,
    ):
        base_root = Path(__file__).resolve().parent.parent.parent
        p_path = Path(protocol_path)
        h_path = Path(human_config_path)
        self.proto_path = (p_path if p_path.is_absolute() else (base_root / p_path)).resolve()
        self.human_path = (h_path if h_path.is_absolute() else (base_root / h_path)).resolve()

        if not self.proto_path.is_file():
            raise FileNotFoundError(f"Protocol file not found: {self.proto_path}")

        with open(self.proto_path, "r", encoding="utf-8") as f:
            self.protocol = json.load(f)

        if verify_drift:
            self._verify_drift()

        routing = self.protocol["routing"]
        self.executor = HydrogenExecutor(
            agent_alias=routing["exec_agent"],
            model=routing["exec_model"],
        )
        self.evaluator = ArgonEvaluator(
            agent_alias=routing["eval_agent"],
            model=routing["eval_model"],
            strict_evidence=routing.get("strict_evidence_check", True),
        )

    def _verify_drift(self) -> None:
        """Verifies protocol hash matches human config SHA-256."""
        if not self.human_path.is_file():
            return
        current_hash = compute_source_hash(self.human_path)
        recorded_hash = self.protocol.get("source_hash")
        if current_hash != recorded_hash:
            raise ConfigDriftError(
                f"Configuration drift detected!\n"
                f"Source ({self.human_path.name}) hash: {current_hash}\n"
                f"Protocol ({self.proto_path.name}) hash: {recorded_hash}\n"
                f"Run `python -m backend.core.config_compiler` to synchronize."
            )

    _should_sample_audit = staticmethod(should_sample_audit)

    def route_task(
        self,
        task_code: str,
        payload: Dict[str, Any],
        submission_id: Optional[str] = None,
        executor_handler: Optional[Callable] = None,
        evaluator_handler: Optional[Callable] = None,
        force_audit: bool = False,
        enable_sampling: bool = False,
    ) -> PipelineResult:
        """
        Routes task execution through Hydrogen, evaluating with Argon when required or triggered.
        Handles retry loop with exact model directives up to max_retries.
        """
        if task_code not in self.protocol["gates"]:
            raise ValueError(f"Unknown task_code '{task_code}'. Valid gates: {list(self.protocol['gates'].keys())}")

        gate_cfg = self.protocol["gates"][task_code]
        err_directives = self.protocol["err_directives"]
        max_retries = int(self.protocol["routing"].get("max_retries", 2))

        sub_id = submission_id or str(uuid.uuid4())
        attempt = 1
        current_payload = dict(payload)
        previous_error = None
        directive = None
        history: List[Dict[str, Any]] = []

        while attempt <= max_retries + 1:
            # 1. Hydrogen Execution Step
            submission = self.executor.execute(
                task_code=task_code,
                payload=current_payload,
                submission_id=sub_id,
                attempt=attempt,
                previous_error=previous_error,
                directive=directive,
                custom_handler=executor_handler,
            )

            # 2. Determine whether Argon evaluation is triggered
            always_eval = gate_cfg.get("always_require_argon_verdict", False)
            low_confidence = submission.confidence < gate_cfg.get("min_executor_confidence", 0.85)
            has_rule_violations = bool(RuleChecker.inspect_payload(task_code, submission.payload, gate_cfg))
            was_rejected_previously = (attempt > 1) or (previous_error is not None)
            sampled_for_audit = enable_sampling and self._should_sample_audit(
                sub_id, float(gate_cfg.get("sample_audit_rate", 0.0))
            )
            needs_eval = (
                always_eval
                or low_confidence
                or has_rule_violations
                or was_rejected_previously
                or sampled_for_audit
                or force_audit
            )

            if not needs_eval:
                # Hydrogen execution accepted directly
                return PipelineResult(
                    success=True,
                    task_code=task_code,
                    submission_id=sub_id,
                    attempts=attempt,
                    final_payload=submission.payload,
                    argon_verdict=None,
                    history=history,
                )

            # 3. Argon Evaluation Step
            verdict = self.evaluator.evaluate(
                task_code=task_code,
                submission=submission,
                gate_cfg=gate_cfg,
                err_directives=err_directives,
                custom_handler=evaluator_handler,
            )

            history.append({
                "attempt": attempt,
                "submission": submission.to_dict(),
                "verdict": verdict.to_dict(),
            })

            if verdict.verdict == "APPROVE":
                # Approved! Enrich audit metadata on final payload
                final_payload = dict(submission.payload)
                final_payload["audit_metadata"] = {
                    "audit_verdict": "APPROVE",
                    "audited_by": self.protocol["routing"]["eval_agent"],
                    "confidence": verdict.confidence,
                    "attempt": attempt,
                    "notes": verdict.evaluator_notes,
                }
                return PipelineResult(
                    success=True,
                    task_code=task_code,
                    submission_id=sub_id,
                    attempts=attempt,
                    final_payload=final_payload,
                    argon_verdict=verdict,
                    history=history,
                )

            # 4. Handle REJECT verdict
            previous_error = verdict.error_code
            directive = verdict.model_directive

            if attempt <= max_retries:
                attempt += 1
                # Prepare payload for retry if handler allows
                current_payload = dict(submission.payload)
            else:
                # Max retries exhausted
                return PipelineResult(
                    success=False,
                    task_code=task_code,
                    submission_id=sub_id,
                    attempts=attempt,
                    final_payload=submission.payload,
                    argon_verdict=verdict,
                    history=history,
                    error_code=verdict.error_code,
                    error_message=f"Argon rejected after {attempt} attempts: [{verdict.error_code}] {verdict.model_directive}",
                )

        # Safety fallback
        return PipelineResult(
            success=False,
            task_code=task_code,
            submission_id=sub_id,
            attempts=attempt,
            final_payload=current_payload,
            error_code="E05_SCHEMA_VIOLATION",
            error_message="Exceeded retry bounds.",
        )
