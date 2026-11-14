"""
CivicTracker TW - Domain Models
Unified Phase 1 (Legislative), Phase 2 (Executive) & Extensibility Domain Dataclasses.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse


class DomainValidationError(Exception):
    """Raised when a domain model entity fails business logic validation."""
    pass


class RoleType(str, Enum):
    LEGISLATOR = "LEGISLATOR"
    EXECUTIVE = "EXECUTIVE"


class VoteDecision(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ABSTAIN = "ABSTAIN"
    ABSENT = "ABSENT"


class FulfillmentStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PLANNING = "IN_PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    FULFILLED = "FULFILLED"
    STALLED = "STALLED"
    BROKEN = "BROKEN"


def _is_valid_url(url: Optional[str]) -> bool:
    if not url or not isinstance(url, str):
        return False
    stripped = url.strip()
    if not (stripped.startswith("http://") or stripped.startswith("https://")):
        return False
    try:
        parsed = urlparse(stripped)
        return bool(parsed.scheme and parsed.netloc)
    except Exception:
        return False


# -----------------------------------------------------------------------------
# Base Entities: Politician & Term
# -----------------------------------------------------------------------------

@dataclass
class Term:
    id: str
    politician_id: str
    role_type: str  # RoleType.LEGISLATOR or RoleType.EXECUTIVE
    constituency: str
    start_date: str
    end_date: Optional[str] = None
    title: Optional[str] = None

    def validate(self) -> List[Tuple[str, str]]:
        errors: List[Tuple[str, str]] = []
        if self.role_type not in (RoleType.LEGISLATOR.value, RoleType.EXECUTIVE.value):
            errors.append(("E05_SCHEMA_VIOLATION", f"Invalid role_type: {self.role_type}"))
        if not self.politician_id:
            errors.append(("E05_SCHEMA_VIOLATION", "politician_id is required"))
        if not self.constituency:
            errors.append(("E05_SCHEMA_VIOLATION", "constituency is required"))
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Politician:
    id: str
    name: str
    party: str
    terms: List[Term] = field(default_factory=list)

    def add_term(self, term: Term) -> None:
        self.terms.append(term)

    def is_legislator(self) -> bool:
        return any(t.role_type in (RoleType.LEGISLATOR, RoleType.LEGISLATOR.value) for t in self.terms)

    def is_executive(self) -> bool:
        return any(t.role_type in (RoleType.EXECUTIVE, RoleType.EXECUTIVE.value) for t in self.terms)

    def get_terms_by_role(self, role: Union[RoleType, str]) -> List[Term]:
        target = role.value if isinstance(role, RoleType) else role
        return [t for t in self.terms if t.role_type == target or (isinstance(t.role_type, RoleType) and t.role_type.value == target)]

    @property
    def is_cross_phase(self) -> bool:
        roles = {t.role_type for t in self.terms}
        return RoleType.LEGISLATOR.value in roles and RoleType.EXECUTIVE.value in roles

    def validate(self) -> List[Tuple[str, str]]:
        errors: List[Tuple[str, str]] = []
        if not self.name.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "Politician name cannot be empty"))
        if not self.party.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "Politician party cannot be empty"))
        for term in self.terms:
            errors.extend(term.validate())
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "party": self.party,
            "terms": [t.to_dict() for t in self.terms],
            "stats": {
                "speeches_count": 0,
                "votes_count": 0,
                "promises_count": 0,
                "fulfilled_count": 0,
                "is_cross_phase": self.is_cross_phase,
            },
        }


# -----------------------------------------------------------------------------
# Phase 1: Parliamentary Speeches & Roll-Call Votes
# -----------------------------------------------------------------------------

@dataclass
class LegislativeSession:
    id: str
    term_number: int
    session_number: int
    date: str
    meeting_type: str  # "PLENARY" | "COMMITTEE"
    title: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InterpellationSpeech:
    id: str
    session_id: str
    speaker_term_id: str
    target_official_id: str
    start_time_sec: float
    end_time_sec: float
    transcript_raw: str
    ai_summary: str
    topic_tags: List[str] = field(default_factory=list)
    audit_metadata: Dict[str, Any] = field(default_factory=dict)
    ivod_clip_id: Optional[str] = None
    video_stream_url: Optional[str] = None
    billy3321_url: Optional[str] = None

    def validate(self, protocol: Optional[Dict[str, Any]] = None) -> List[Tuple[str, str]]:
        errors: List[Tuple[str, str]] = []

        # Video timestamp bounds check
        if self.start_time_sec < 0 or self.end_time_sec < 0:
            errors.append(("E04_TIMESTAMP_DRIFT", f"Timestamps cannot be negative: start={self.start_time_sec}, end={self.end_time_sec}"))
        elif self.start_time_sec > self.end_time_sec:
            errors.append(
                ("E04_TIMESTAMP_DRIFT", f"start_time_sec ({self.start_time_sec}) exceeds end_time_sec ({self.end_time_sec})")
            )

        # Speaker attribution check
        if not self.speaker_term_id or not self.target_official_id:
            errors.append(("E05_SCHEMA_VIOLATION", "speaker_term_id and target_official_id are required"))
        elif self.speaker_term_id == self.target_official_id:
            errors.append(
                ("E02_SPEAKER_SWAP", f"Questioning legislator and target official cannot be identical: {self.speaker_term_id}")
            )

        if not self.transcript_raw.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "transcript_raw cannot be empty"))

        if not self.ai_summary.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "ai_summary cannot be empty"))

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Bill:
    id: str
    title: str
    session_id: str
    proposer_term_ids: List[str] = field(default_factory=list)
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VoteRecord:
    id: str
    bill_id: str
    politician_id: str
    decision: str
    source_url: str
    audit_metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self, protocol: Optional[Dict[str, Any]] = None) -> List[Tuple[str, str]]:
        errors: List[Tuple[str, str]] = []

        allowed = {d.value for d in VoteDecision}
        if protocol and "gates" in protocol and "TASK_VOTE_ANALYZE" in protocol["gates"]:
            allowed = set(protocol["gates"]["TASK_VOTE_ANALYZE"].get("allowed_vote_decisions", allowed))

        if self.decision not in allowed:
            errors.append(("E05_SCHEMA_VIOLATION", f"Decision '{self.decision}' not in allowed decisions: {allowed}"))

        if not _is_valid_url(self.source_url):
            errors.append(("E03_MISSING_CITATION", f"Vote record missing valid citation source_url: '{self.source_url}'"))

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# -----------------------------------------------------------------------------
# Phase 2: Mayor/Executive Policy Promises & Execution Milestones
# -----------------------------------------------------------------------------

@dataclass
class ExecutionMilestone:
    id: str
    promise_id: str
    milestone_date: str
    evidence_summary: str
    source_url: str
    budget_spent: Optional[float] = None
    audit_metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[Tuple[str, str]]:
        errors: List[Tuple[str, str]] = []
        if not _is_valid_url(self.source_url):
            errors.append(("E03_MISSING_CITATION", f"Milestone source_url '{self.source_url}' is not a valid URL"))
        if not self.evidence_summary.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "Milestone evidence_summary cannot be empty"))
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyPromise:
    id: str
    politician_id: str
    term_id: str
    title: str
    category: str
    status: str  # FulfillmentStatus
    source_url: str
    target_completion_date: Optional[str] = None
    audit_metadata: Dict[str, Any] = field(default_factory=dict)
    milestones: List[ExecutionMilestone] = field(default_factory=list)

    def add_milestone(self, m: ExecutionMilestone) -> None:
        self.milestones.append(m)

    def validate(self, protocol: Optional[Dict[str, Any]] = None) -> List[Tuple[str, str]]:
        errors: List[Tuple[str, str]] = []

        allowed_statuses = {s.value for s in FulfillmentStatus}
        if protocol and "gates" in protocol and "TASK_POLICY_EVAL" in protocol["gates"]:
            allowed_statuses = set(protocol["gates"]["TASK_POLICY_EVAL"].get("allowed_fulfillment_statuses", allowed_statuses))

        if self.status not in allowed_statuses:
            errors.append(("E05_SCHEMA_VIOLATION", f"Status '{self.status}' is invalid. Allowed: {allowed_statuses}"))

        if not _is_valid_url(self.source_url):
            errors.append(("E03_MISSING_CITATION", f"PolicyPromise source_url '{self.source_url}' is not a valid URL"))

        for m in self.milestones:
            errors.extend(m.validate())

        return errors

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "politician_id": self.politician_id,
            "term_id": self.term_id,
            "title": self.title,
            "category": self.category,
            "status": self.status,
            "source_url": self.source_url,
            "target_completion_date": self.target_completion_date,
            "audit_metadata": self.audit_metadata,
            "milestones": [m.to_dict() for m in self.milestones],
        }


# -----------------------------------------------------------------------------
# Phase 3 & Extensibility: Midterm/Final Exam Report Cards & Citizen Petitions
# -----------------------------------------------------------------------------

@dataclass
class ExamReportCard:
    id: str
    politician_id: str
    term_id: str
    exam_stage: str  # "MIDTERM" | "FINAL"
    attendance_rate: float
    objective_score: float
    argon_summary_comment: str
    citizen_rating_avg: float
    citizen_reviews_count: int
    audit_metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self, protocol: Optional[Dict[str, Any]] = None) -> List[Tuple[str, str]]:
        errors: List[Tuple[str, str]] = []
        if self.exam_stage not in ("MIDTERM", "FINAL"):
            errors.append(("E05_SCHEMA_VIOLATION", f"exam_stage must be 'MIDTERM' or 'FINAL', got: {self.exam_stage}"))
        if not (0.0 <= self.attendance_rate <= 100.0):
            errors.append(("E05_SCHEMA_VIOLATION", f"attendance_rate must be 0-100, got: {self.attendance_rate}"))
        if not (0.0 <= self.objective_score <= 100.0):
            errors.append(("E05_SCHEMA_VIOLATION", f"objective_score must be 0-100, got: {self.objective_score}"))
        if not self.politician_id:
            errors.append(("E05_SCHEMA_VIOLATION", "politician_id cannot be empty"))
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CitizenPetition:
    id: str
    politician_id: str
    category: str
    author_name: str
    title: str
    content: str
    citizen_score: int  # 1 to 5
    status: str  # "PENDING" | "APPROVED" | "QUARANTINED"
    created_at: str
    target_promise_id: Optional[str] = None
    evidence_url: Optional[str] = None
    audit_metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self, protocol: Optional[Dict[str, Any]] = None) -> List[Tuple[str, str]]:
        errors: List[Tuple[str, str]] = []
        if self.status not in ("PENDING", "APPROVED", "QUARANTINED"):
            errors.append(("E05_SCHEMA_VIOLATION", f"status must be PENDING/APPROVED/QUARANTINED, got: {self.status}"))
        if not (1 <= self.citizen_score <= 5):
            errors.append(("E05_SCHEMA_VIOLATION", f"citizen_score must be between 1 and 5, got: {self.citizen_score}"))
        if not self.title.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "title cannot be empty"))
        if not self.content.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "content cannot be empty"))
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# -----------------------------------------------------------------------------
# Phase 2 Council Accountability: Subordinate Officials & Council Interpellations
# -----------------------------------------------------------------------------

@dataclass
class SubordinateOfficial:
    id: str
    mayor_politician_id: str
    municipality: str
    name: str
    title: str
    level: str  # "DEPUTY_MAYOR" | "BUREAU_CHIEF"
    department: str
    portfolio_tags: List[str] = field(default_factory=list)

    def validate(self, protocol: Optional[Dict[str, Any]] = None) -> List[Tuple[str, str]]:
        errors: List[Tuple[str, str]] = []
        if not self.id or not isinstance(self.id, str) or not self.id.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "id cannot be empty"))
        if not self.mayor_politician_id or not isinstance(self.mayor_politician_id, str) or not self.mayor_politician_id.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "mayor_politician_id cannot be empty"))
        if not self.municipality or not isinstance(self.municipality, str) or not self.municipality.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "municipality cannot be empty"))
        if not self.name or not isinstance(self.name, str) or not self.name.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "name cannot be empty"))
        if not self.title or not isinstance(self.title, str) or not self.title.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "title cannot be empty"))
        if self.level not in ("DEPUTY_MAYOR", "BUREAU_CHIEF"):
            errors.append(("E05_SCHEMA_VIOLATION", f"level must be 'DEPUTY_MAYOR' or 'BUREAU_CHIEF', got: {self.level}"))
        if not self.department or not isinstance(self.department, str) or not self.department.strip():
            errors.append(("E05_SCHEMA_VIOLATION", "department cannot be empty"))
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CouncilInterpellation:
    id: str
    mayor_politician_id: str
    responder_type: str  # "MAYOR" | "DEPUTY_MAYOR" | "BUREAU_CHIEF"
    responder_official_id: Optional[str]
    responder_name: str
    responder_title: str
    department_category: str  # "市政總質詢" | "交通與捷運部門" | "工務與都發部門" | "財經與產業部門"
    council_name: str
    session_date: str
    councilor_name: str
    interpellation_title: str
    question_summary: str
    official_response: str
    linked_promise_id: Optional[str] = None
    gazette_url: str = ""
    vod_url: str = ""
    start_time_sec: float = 0.0
    end_time_sec: float = 300.0
    audit_metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self, protocol: Optional[Dict[str, Any]] = None) -> List[Tuple[str, str]]:
        errors: List[Tuple[str, str]] = []
        if self.responder_type not in ("MAYOR", "DEPUTY_MAYOR", "BUREAU_CHIEF"):
            errors.append(("E05_SCHEMA_VIOLATION", f"responder_type must be MAYOR/DEPUTY_MAYOR/BUREAU_CHIEF, got: {self.responder_type}"))
        if self.responder_type != "MAYOR" and not self.responder_official_id:
            errors.append(("E05_SCHEMA_VIOLATION", "responder_official_id required for DEPUTY_MAYOR and BUREAU_CHIEF"))
        if self.start_time_sec < 0 or self.end_time_sec < 0:
            errors.append(("E04_TIMESTAMP_DRIFT", f"Timestamps cannot be negative: start={self.start_time_sec}, end={self.end_time_sec}"))
        elif self.start_time_sec > self.end_time_sec:
            errors.append(("E04_TIMESTAMP_DRIFT", f"start_time_sec ({self.start_time_sec}) exceeds end_time_sec ({self.end_time_sec})"))
        if self.gazette_url and not _is_valid_url(self.gazette_url):
            errors.append(("E03_MISSING_CITATION", f"Invalid gazette_url: {self.gazette_url}"))
        if self.vod_url and not _is_valid_url(self.vod_url):
            errors.append(("E03_MISSING_CITATION", f"Invalid vod_url: {self.vod_url}"))
        if not self.id:
            errors.append(("E05_SCHEMA_VIOLATION", "id cannot be empty"))
        if not self.mayor_politician_id:
            errors.append(("E05_SCHEMA_VIOLATION", "mayor_politician_id cannot be empty"))
        if not self.responder_name:
            errors.append(("E05_SCHEMA_VIOLATION", "responder_name cannot be empty"))
        if not self.interpellation_title:
            errors.append(("E05_SCHEMA_VIOLATION", "interpellation_title cannot be empty"))
        if not self.question_summary:
            errors.append(("E05_SCHEMA_VIOLATION", "question_summary cannot be empty"))
        if not self.official_response:
            errors.append(("E05_SCHEMA_VIOLATION", "official_response cannot be empty"))
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
