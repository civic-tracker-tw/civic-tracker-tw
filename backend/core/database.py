"""
CivicTracker TW - Persistent SQLite Database Engine
Normalized relational schema with WAL journal mode, foreign keys,
and 100% parameterized SQL query protection against SQL injection.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from backend.data.seed_data import get_seed_database
from backend.models.domain import (
    Bill,
    CitizenPetition,
    ExamReportCard,
    ExecutionMilestone,
    InterpellationSpeech,
    LegislativeSession,
    PolicyPromise,
    Politician,
    RoleType,
    Term,
    VoteRecord,
    SubordinateOfficial,
    CouncilInterpellation,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "civic_tracker.db"


class DatabaseEngine:
    """Production SQLite database engine for CivicTracker TW."""

    def __init__(self, db_path: Union[str, Path] = DEFAULT_DB_PATH, auto_seed: bool = True):
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        self._init_pragmas_and_tables()

        if auto_seed and self._is_empty():
            self._seed_from_repository()

    def _get_cursor(self) -> sqlite3.Cursor:
        return self._conn.cursor()

    def _init_pragmas_and_tables(self) -> None:
        """Enforces WAL journal mode, foreign key constraints, and creates normalized schema."""
        cursor = self._conn.cursor()
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA foreign_keys = ON;")

        # 1. Politicians & Terms
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS politicians (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                party TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS terms (
                id TEXT PRIMARY KEY,
                politician_id TEXT NOT NULL,
                role_type TEXT NOT NULL,
                constituency TEXT,
                start_date TEXT,
                end_date TEXT,
                title TEXT,
                FOREIGN KEY (politician_id) REFERENCES politicians(id) ON DELETE CASCADE
            );
        """)

        # 2. Sessions, Speeches, Bills & Votes (Phase 1)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                term_number INTEGER,
                session_number INTEGER,
                date TEXT,
                meeting_type TEXT,
                title TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS speeches (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                speaker_term_id TEXT NOT NULL,
                target_official_id TEXT NOT NULL,
                start_time_sec REAL NOT NULL,
                end_time_sec REAL NOT NULL,
                transcript_raw TEXT NOT NULL,
                ai_summary TEXT NOT NULL,
                topic_tags_json TEXT,
                audit_metadata_json TEXT,
                ivod_clip_id TEXT,
                video_stream_url TEXT,
                billy3321_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL,
                FOREIGN KEY (speaker_term_id) REFERENCES terms(id) ON DELETE CASCADE
            );
        """)

        # Handle migration safely if speeches table existed without video columns
        cursor.execute("PRAGMA table_info(speeches);")
        columns = [row["name"] for row in cursor.fetchall()]
        if "ivod_clip_id" not in columns:
            cursor.execute("ALTER TABLE speeches ADD COLUMN ivod_clip_id TEXT;")
        if "video_stream_url" not in columns:
            cursor.execute("ALTER TABLE speeches ADD COLUMN video_stream_url TEXT;")
        if "billy3321_url" not in columns:
            cursor.execute("ALTER TABLE speeches ADD COLUMN billy3321_url TEXT;")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                session_id TEXT,
                proposer_term_ids_json TEXT,
                description TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id TEXT PRIMARY KEY,
                bill_id TEXT NOT NULL,
                politician_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                source_url TEXT NOT NULL,
                audit_metadata_json TEXT,
                FOREIGN KEY (bill_id) REFERENCES bills(id) ON DELETE CASCADE,
                FOREIGN KEY (politician_id) REFERENCES politicians(id) ON DELETE CASCADE
            );
        """)

        # 3. Policy Promises & Execution Milestones (Phase 2)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promises (
                id TEXT PRIMARY KEY,
                politician_id TEXT NOT NULL,
                term_id TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                source_url TEXT NOT NULL,
                target_completion_date TEXT,
                audit_metadata_json TEXT,
                FOREIGN KEY (politician_id) REFERENCES politicians(id) ON DELETE CASCADE,
                FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                id TEXT PRIMARY KEY,
                promise_id TEXT NOT NULL,
                milestone_date TEXT NOT NULL,
                evidence_summary TEXT NOT NULL,
                source_url TEXT NOT NULL,
                budget_spent REAL,
                audit_metadata_json TEXT,
                FOREIGN KEY (promise_id) REFERENCES promises(id) ON DELETE CASCADE
            );
        """)

        # 4. Phase 3 & Extensibility: Midterm/Final Exam Report Cards & Citizen Petitions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exam_report_cards (
                id TEXT PRIMARY KEY,
                politician_id TEXT NOT NULL,
                term_id TEXT NOT NULL,
                exam_stage TEXT NOT NULL,
                attendance_rate REAL NOT NULL,
                objective_score REAL NOT NULL,
                argon_summary_comment TEXT NOT NULL,
                citizen_rating_avg REAL NOT NULL,
                citizen_reviews_count INTEGER NOT NULL,
                audit_metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (politician_id) REFERENCES politicians(id) ON DELETE CASCADE,
                FOREIGN KEY (term_id) REFERENCES terms(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citizen_petitions (
                id TEXT PRIMARY KEY,
                politician_id TEXT NOT NULL,
                target_promise_id TEXT,
                category TEXT NOT NULL,
                author_name TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                evidence_url TEXT,
                citizen_score INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                audit_metadata_json TEXT,
                FOREIGN KEY (politician_id) REFERENCES politicians(id) ON DELETE CASCADE,
                FOREIGN KEY (target_promise_id) REFERENCES promises(id) ON DELETE SET NULL
            );
        """)

        # 6. Subordinate Officials & Council Interpellations (Phase 2 Council Accountability)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subordinate_officials (
                id TEXT PRIMARY KEY,
                mayor_politician_id TEXT NOT NULL,
                municipality TEXT NOT NULL,
                name TEXT NOT NULL,
                title TEXT NOT NULL,
                level TEXT NOT NULL,
                department TEXT NOT NULL,
                portfolio_tags_json TEXT DEFAULT '[]',
                FOREIGN KEY (mayor_politician_id) REFERENCES politicians(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS council_interpellations (
                id TEXT PRIMARY KEY,
                mayor_politician_id TEXT NOT NULL,
                responder_type TEXT NOT NULL,
                responder_official_id TEXT,
                responder_name TEXT NOT NULL,
                responder_title TEXT NOT NULL,
                department_category TEXT NOT NULL,
                council_name TEXT NOT NULL,
                session_date TEXT NOT NULL,
                councilor_name TEXT NOT NULL,
                interpellation_title TEXT NOT NULL,
                question_summary TEXT NOT NULL,
                official_response TEXT NOT NULL,
                linked_promise_id TEXT,
                gazette_url TEXT NOT NULL,
                vod_url TEXT NOT NULL,
                start_time_sec REAL DEFAULT 0.0,
                end_time_sec REAL DEFAULT 300.0,
                audit_metadata_json TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mayor_politician_id) REFERENCES politicians(id) ON DELETE CASCADE,
                FOREIGN KEY (responder_official_id) REFERENCES subordinate_officials(id) ON DELETE SET NULL,
                FOREIGN KEY (linked_promise_id) REFERENCES promises(id) ON DELETE SET NULL
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_officials_mayor ON subordinate_officials(mayor_politician_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_officials_level ON subordinate_officials(level);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_council_interp_mayor ON council_interpellations(mayor_politician_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_council_interp_resp_type ON council_interpellations(responder_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_council_interp_dept ON council_interpellations(department_category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_council_interp_promise ON council_interpellations(linked_promise_id);")

        # 5. Data Sync Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                items_synced INTEGER NOT NULL,
                details_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Indexes for query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_terms_politician ON terms(politician_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_speeches_speaker ON speeches(speaker_term_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_votes_politician ON votes(politician_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_votes_bill ON votes(bill_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_promises_politician ON promises(politician_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_milestones_promise ON milestones(promise_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exam_politician ON exam_report_cards(politician_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_petitions_politician ON citizen_petitions(politician_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_petitions_status ON citizen_petitions(status);")

        self._conn.commit()

        # Auto-seed officials and council interpellations if table is empty AND politicians exist
        cursor.execute("SELECT COUNT(*) FROM politicians;")
        if cursor.fetchone()[0] > 0:
            cursor.execute("SELECT COUNT(*) FROM subordinate_officials;")
            if cursor.fetchone()[0] == 0:
                seed_db = get_seed_database()
                if hasattr(seed_db, "subordinate_officials"):
                    for off in seed_db.subordinate_officials:
                        self.upsert_subordinate_official(off)
                if hasattr(seed_db, "council_interpellations"):
                    for interp in seed_db.council_interpellations:
                        self.upsert_council_interpellation(interp)

    def _is_empty(self) -> bool:
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM politicians;")
        count = cursor.fetchone()[0]
        return count == 0

    def _seed_from_repository(self) -> None:
        """Seeds initial dataset from seed_data.py into SQLite."""
        seed_db = get_seed_database()

        # Seed Politicians and Terms
        for p in seed_db.politicians.values():
            self.upsert_politician(p)

        # Seed Sessions
        cursor = self._conn.cursor()
        for s in seed_db.sessions.values():
            cursor.execute(
                """
                INSERT OR REPLACE INTO sessions (id, term_number, session_number, date, meeting_type, title)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (s.id, s.term_number, s.session_number, s.date, s.meeting_type, s.title),
            )
        self._conn.commit()

        # Seed Speeches
        for sp in seed_db.speeches:
            self.upsert_speech(sp)

        # Seed Bills
        for b in seed_db.bills.values():
            cursor.execute(
                """
                INSERT OR REPLACE INTO bills (id, title, session_id, proposer_term_ids_json, description)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    b.id,
                    b.title,
                    b.session_id,
                    json.dumps(b.proposer_term_ids, ensure_ascii=False),
                    b.description,
                ),
            )
        self._conn.commit()

        # Seed Votes
        for v in seed_db.votes:
            self.upsert_vote(v)

        # Seed Promises and Milestones
        for pr in seed_db.promises:
            self.upsert_promise(pr)

        # Seed Exam Report Cards
        if hasattr(seed_db, "exam_cards"):
            for card in seed_db.exam_cards:
                self.upsert_exam_card(card)

        # Seed Citizen Petitions
        if hasattr(seed_db, "petitions"):
            for pet in seed_db.petitions:
                self.upsert_petition(pet)

        # Seed Subordinate Officials & Council Interpellations
        if hasattr(seed_db, "subordinate_officials"):
            for off in seed_db.subordinate_officials:
                self.upsert_subordinate_official(off)
        if hasattr(seed_db, "council_interpellations"):
            for interp in seed_db.council_interpellations:
                self.upsert_council_interpellation(interp)

        # Record bootstrap sync log
        self.record_sync_log(
            source="system_bootstrap_seed",
            status="SUCCESS",
            items_synced=len(seed_db.politicians) + len(seed_db.speeches),
            details={"description": "Initial repository seed dataset loaded successfully"},
        )

    # -------------------------------------------------------------------------
    # Mutation APIs (100% Parameterized)
    # -------------------------------------------------------------------------

    def upsert_politician(self, p: Politician) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO politicians (id, name, party)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                party=excluded.party;
            """,
            (p.id, p.name, p.party),
        )
        for t in p.terms:
            cursor.execute(
                """
                INSERT INTO terms (id, politician_id, role_type, constituency, start_date, end_date, title)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    role_type=excluded.role_type,
                    constituency=excluded.constituency,
                    start_date=excluded.start_date,
                    end_date=excluded.end_date,
                    title=excluded.title;
                """,
                (t.id, t.politician_id, t.role_type, t.constituency, t.start_date, t.end_date, t.title),
            )
        self._conn.commit()

    def upsert_speech(self, s: InterpellationSpeech) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO speeches (
                id, session_id, speaker_term_id, target_official_id,
                start_time_sec, end_time_sec, transcript_raw, ai_summary,
                topic_tags_json, audit_metadata_json,
                ivod_clip_id, video_stream_url, billy3321_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                session_id=excluded.session_id,
                speaker_term_id=excluded.speaker_term_id,
                target_official_id=excluded.target_official_id,
                start_time_sec=excluded.start_time_sec,
                end_time_sec=excluded.end_time_sec,
                transcript_raw=excluded.transcript_raw,
                ai_summary=excluded.ai_summary,
                topic_tags_json=excluded.topic_tags_json,
                audit_metadata_json=excluded.audit_metadata_json,
                ivod_clip_id=excluded.ivod_clip_id,
                video_stream_url=excluded.video_stream_url,
                billy3321_url=excluded.billy3321_url;
            """,
            (
                s.id,
                s.session_id,
                s.speaker_term_id,
                s.target_official_id,
                float(s.start_time_sec),
                float(s.end_time_sec),
                s.transcript_raw,
                s.ai_summary,
                json.dumps(s.topic_tags, ensure_ascii=False),
                json.dumps(s.audit_metadata, ensure_ascii=False),
                s.ivod_clip_id,
                s.video_stream_url,
                s.billy3321_url,
            ),
        )
        self._conn.commit()

    def upsert_vote(self, v: VoteRecord) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO votes (id, bill_id, politician_id, decision, source_url, audit_metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                bill_id=excluded.bill_id,
                politician_id=excluded.politician_id,
                decision=excluded.decision,
                source_url=excluded.source_url,
                audit_metadata_json=excluded.audit_metadata_json;
            """,
            (
                v.id,
                v.bill_id,
                v.politician_id,
                v.decision,
                v.source_url,
                json.dumps(v.audit_metadata, ensure_ascii=False),
            ),
        )
        self._conn.commit()

    def upsert_promise(self, pr: PolicyPromise) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO promises (
                id, politician_id, term_id, title, category,
                status, source_url, target_completion_date, audit_metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                category=excluded.category,
                status=excluded.status,
                source_url=excluded.source_url,
                target_completion_date=excluded.target_completion_date,
                audit_metadata_json=excluded.audit_metadata_json;
            """,
            (
                pr.id,
                pr.politician_id,
                pr.term_id,
                pr.title,
                pr.category,
                pr.status,
                pr.source_url,
                pr.target_completion_date,
                json.dumps(pr.audit_metadata, ensure_ascii=False),
            ),
        )
        for m in pr.milestones:
            cursor.execute(
                """
                INSERT INTO milestones (
                    id, promise_id, milestone_date, evidence_summary,
                    source_url, budget_spent, audit_metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    milestone_date=excluded.milestone_date,
                    evidence_summary=excluded.evidence_summary,
                    source_url=excluded.source_url,
                    budget_spent=excluded.budget_spent,
                    audit_metadata_json=excluded.audit_metadata_json;
                """,
                (
                    m.id,
                    m.promise_id,
                    m.milestone_date,
                    m.evidence_summary,
                    m.source_url,
                    m.budget_spent,
                    json.dumps(m.audit_metadata, ensure_ascii=False),
                ),
            )
        self._conn.commit()

    def upsert_exam_card(self, card: ExamReportCard) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO exam_report_cards (
                id, politician_id, term_id, exam_stage,
                attendance_rate, objective_score, argon_summary_comment,
                citizen_rating_avg, citizen_reviews_count, audit_metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                politician_id=excluded.politician_id,
                term_id=excluded.term_id,
                exam_stage=excluded.exam_stage,
                attendance_rate=excluded.attendance_rate,
                objective_score=excluded.objective_score,
                argon_summary_comment=excluded.argon_summary_comment,
                citizen_rating_avg=excluded.citizen_rating_avg,
                citizen_reviews_count=excluded.citizen_reviews_count,
                audit_metadata_json=excluded.audit_metadata_json;
            """,
            (
                card.id,
                card.politician_id,
                card.term_id,
                card.exam_stage,
                float(card.attendance_rate),
                float(card.objective_score),
                card.argon_summary_comment,
                float(card.citizen_rating_avg),
                int(card.citizen_reviews_count),
                json.dumps(card.audit_metadata, ensure_ascii=False),
            ),
        )
        self._conn.commit()

    def upsert_petition(self, p: CitizenPetition) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO citizen_petitions (
                id, politician_id, target_promise_id, category,
                author_name, title, content, evidence_url,
                citizen_score, status, created_at, audit_metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                politician_id=excluded.politician_id,
                target_promise_id=excluded.target_promise_id,
                category=excluded.category,
                author_name=excluded.author_name,
                title=excluded.title,
                content=excluded.content,
                evidence_url=excluded.evidence_url,
                citizen_score=excluded.citizen_score,
                status=excluded.status,
                created_at=excluded.created_at,
                audit_metadata_json=excluded.audit_metadata_json;
            """,
            (
                p.id,
                p.politician_id,
                p.target_promise_id,
                p.category,
                p.author_name,
                p.title,
                p.content,
                p.evidence_url,
                int(p.citizen_score),
                p.status,
                p.created_at,
                json.dumps(p.audit_metadata, ensure_ascii=False),
            ),
        )
        self._conn.commit()

    def record_sync_log(self, source: str, status: str, items_synced: int, details: Dict[str, Any]) -> int:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO sync_logs (source, status, items_synced, details_json)
            VALUES (?, ?, ?, ?);
            """,
            (source, status, items_synced, json.dumps(details, ensure_ascii=False)),
        )
        self._conn.commit()
        return cursor.lastrowid

    # -------------------------------------------------------------------------
    # Query APIs (100% Parameterized)
    # -------------------------------------------------------------------------

    def get_politicians(self) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT id, name, party FROM politicians ORDER BY id ASC;")
        pols_rows = cursor.fetchall()
        result = []

        for p_row in pols_rows:
            p_id = p_row["id"]
            cursor.execute(
                "SELECT id, role_type, constituency, start_date, end_date, title FROM terms WHERE politician_id = ? ORDER BY start_date ASC;",
                (p_id,),
            )
            terms = [dict(t) for t in cursor.fetchall()]

            leg_terms = [t["id"] for t in terms if t["role_type"] == RoleType.LEGISLATOR.value]
            exec_terms = [t["id"] for t in terms if t["role_type"] == RoleType.EXECUTIVE.value]

            if leg_terms:
                placeholders = ",".join("?" for _ in leg_terms)
                cursor.execute(
                    f"SELECT COUNT(*) FROM speeches WHERE speaker_term_id IN ({placeholders});",
                    leg_terms,
                )
                speeches_count = cursor.fetchone()[0]
            else:
                speeches_count = 0

            cursor.execute("SELECT COUNT(*) FROM votes WHERE politician_id = ?;", (p_id,))
            votes_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM promises WHERE politician_id = ?;", (p_id,))
            promises_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM promises WHERE politician_id = ? AND status = 'FULFILLED';", (p_id,))
            fulfilled_count = cursor.fetchone()[0]

            result.append({
                "id": p_id,
                "name": p_row["name"],
                "party": p_row["party"],
                "terms": terms,
                "stats": {
                    "speeches_count": speeches_count,
                    "votes_count": votes_count,
                    "promises_count": promises_count,
                    "fulfilled_count": fulfilled_count,
                    "is_cross_phase": len(leg_terms) > 0 and len(exec_terms) > 0,
                },
            })
        return result

    def get_politician(self, pol_id: str) -> Optional[Dict[str, Any]]:
        pols = self.get_politicians()
        for p in pols:
            if p["id"] == pol_id:
                return p
        return None

    def get_speeches(
        self,
        q: Optional[str] = None,
        tag: Optional[str] = None,
        politician_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        query_sql = """
            SELECT sp.*,
                   p.name AS speaker_name,
                   p.party AS speaker_party,
                   t.title AS speaker_title,
                   sess.title AS session_title,
                   sess.date AS session_date
            FROM speeches sp
            JOIN terms t ON sp.speaker_term_id = t.id
            JOIN politicians p ON t.politician_id = p.id
            LEFT JOIN sessions sess ON sp.session_id = sess.id
            WHERE 1=1
        """
        params: List[Any] = []

        if politician_id:
            query_sql += " AND p.id = ?"
            params.append(politician_id)

        if tag:
            query_sql += " AND sp.topic_tags_json LIKE ?"
            params.append(f"%{tag}%")

        if q:
            query_sql += " AND (sp.transcript_raw LIKE ? OR sp.ai_summary LIKE ? OR sp.topic_tags_json LIKE ?)"
            pattern = f"%{q}%"
            params.extend([pattern, pattern, pattern])

        query_sql += " ORDER BY sp.start_time_sec ASC;"
        cursor.execute(query_sql, params)
        rows = cursor.fetchall()

        results = []
        for r in rows:
            tags = json.loads(r["topic_tags_json"]) if r["topic_tags_json"] else []
            audit = json.loads(r["audit_metadata_json"]) if r["audit_metadata_json"] else {}
            session_data = {
                "id": r["session_id"],
                "title": r["session_title"],
                "date": r["session_date"],
            } if r["session_id"] else None

            results.append({
                "id": r["id"],
                "session_id": r["session_id"],
                "speaker_term_id": r["speaker_term_id"],
                "target_official_id": r["target_official_id"],
                "start_time_sec": r["start_time_sec"],
                "end_time_sec": r["end_time_sec"],
                "transcript_raw": r["transcript_raw"],
                "ai_summary": r["ai_summary"],
                "topic_tags": tags,
                "audit_metadata": audit,
                "ivod_clip_id": r["ivod_clip_id"] if "ivod_clip_id" in r.keys() else None,
                "video_stream_url": r["video_stream_url"] if "video_stream_url" in r.keys() else None,
                "billy3321_url": r["billy3321_url"] if "billy3321_url" in r.keys() else None,
                "speaker_name": r["speaker_name"],
                "speaker_party": r["speaker_party"],
                "speaker_title": r["speaker_title"],
                "session": session_data,
            })
        return results

    def get_votes(
        self,
        politician_id: Optional[str] = None,
        bill_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        sql = """
            SELECT v.*,
                   p.name AS politician_name,
                   p.party AS politician_party,
                   b.title AS bill_title,
                   b.description AS bill_description,
                   b.proposer_term_ids_json AS bill_proposers
            FROM votes v
            JOIN politicians p ON v.politician_id = p.id
            JOIN bills b ON v.bill_id = b.id
            WHERE 1=1
        """
        params: List[Any] = []

        if politician_id:
            sql += " AND v.politician_id = ?"
            params.append(politician_id)

        if bill_id:
            sql += " AND v.bill_id = ?"
            params.append(bill_id)

        sql += " ORDER BY v.id ASC;"
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for r in rows:
            audit = json.loads(r["audit_metadata_json"]) if r["audit_metadata_json"] else {}
            proposers = json.loads(r["bill_proposers"]) if r["bill_proposers"] else []
            bill_obj = {
                "id": r["bill_id"],
                "title": r["bill_title"],
                "description": r["bill_description"],
                "proposer_term_ids": proposers,
            }

            results.append({
                "id": r["id"],
                "bill_id": r["bill_id"],
                "politician_id": r["politician_id"],
                "decision": r["decision"],
                "source_url": r["source_url"],
                "audit_metadata": audit,
                "politician_name": r["politician_name"],
                "politician_party": r["politician_party"],
                "bill": bill_obj,
            })
        return results

    def get_promises(
        self,
        politician_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        sql = """
            SELECT pr.*,
                   p.name AS politician_name,
                   p.party AS politician_party
            FROM promises pr
            JOIN politicians p ON pr.politician_id = p.id
            WHERE 1=1
        """
        params: List[Any] = []

        if politician_id:
            sql += " AND pr.politician_id = ?"
            params.append(politician_id)

        if status:
            sql += " AND pr.status = ?"
            params.append(status)

        sql += " ORDER BY pr.id ASC;"
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for r in rows:
            pr_id = r["id"]
            audit = json.loads(r["audit_metadata_json"]) if r["audit_metadata_json"] else {}

            cursor.execute(
                "SELECT * FROM milestones WHERE promise_id = ? ORDER BY milestone_date ASC;",
                (pr_id,),
            )
            milestones = []
            for mr in cursor.fetchall():
                m_audit = json.loads(mr["audit_metadata_json"]) if mr["audit_metadata_json"] else {}
                milestones.append({
                    "id": mr["id"],
                    "promise_id": mr["promise_id"],
                    "milestone_date": mr["milestone_date"],
                    "evidence_summary": mr["evidence_summary"],
                    "source_url": mr["source_url"],
                    "budget_spent": mr["budget_spent"],
                    "audit_metadata": m_audit,
                })

            results.append({
                "id": pr_id,
                "politician_id": r["politician_id"],
                "term_id": r["term_id"],
                "title": r["title"],
                "category": r["category"],
                "status": r["status"],
                "source_url": r["source_url"],
                "target_completion_date": r["target_completion_date"],
                "audit_metadata": audit,
                "politician_name": r["politician_name"],
                "politician_party": r["politician_party"],
                "milestones": milestones,
            })
        return results

    def get_exam_cards(
        self,
        politician_id: Optional[str] = None,
        exam_stage: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        sql = """
            SELECT ec.*,
                   p.name AS politician_name,
                   p.party AS politician_party,
                   t.title AS term_title
            FROM exam_report_cards ec
            JOIN politicians p ON ec.politician_id = p.id
            JOIN terms t ON ec.term_id = t.id
            WHERE 1=1
        """
        params: List[Any] = []
        if politician_id:
            sql += " AND ec.politician_id = ?"
            params.append(politician_id)
        if exam_stage:
            sql += " AND ec.exam_stage = ?"
            params.append(exam_stage)
        sql += " ORDER BY ec.created_at DESC;"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        results = []
        for r in rows:
            audit = json.loads(r["audit_metadata_json"]) if r["audit_metadata_json"] else {}
            results.append({
                "id": r["id"],
                "politician_id": r["politician_id"],
                "politician_name": r["politician_name"],
                "politician_party": r["politician_party"],
                "term_id": r["term_id"],
                "term_title": r["term_title"],
                "exam_stage": r["exam_stage"],
                "attendance_rate": r["attendance_rate"],
                "objective_score": r["objective_score"],
                "argon_summary_comment": r["argon_summary_comment"],
                "citizen_rating_avg": r["citizen_rating_avg"],
                "citizen_reviews_count": r["citizen_reviews_count"],
                "audit_metadata": audit,
                "created_at": r["created_at"],
            })
        return results

    def get_petitions(
        self,
        politician_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        sql = """
            SELECT cp.*,
                   p.name AS politician_name,
                   p.party AS politician_party,
                   pr.title AS promise_title
            FROM citizen_petitions cp
            JOIN politicians p ON cp.politician_id = p.id
            LEFT JOIN promises pr ON cp.target_promise_id = pr.id
            WHERE 1=1
        """
        params: List[Any] = []
        if politician_id:
            sql += " AND cp.politician_id = ?"
            params.append(politician_id)
        if status:
            sql += " AND cp.status = ?"
            params.append(status)
        sql += " ORDER BY cp.created_at DESC;"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        results = []
        for r in rows:
            audit = json.loads(r["audit_metadata_json"]) if r["audit_metadata_json"] else {}
            results.append({
                "id": r["id"],
                "politician_id": r["politician_id"],
                "politician_name": r["politician_name"],
                "politician_party": r["politician_party"],
                "target_promise_id": r["target_promise_id"],
                "promise_title": r["promise_title"],
                "category": r["category"],
                "author_name": r["author_name"],
                "title": r["title"],
                "content": r["content"],
                "evidence_url": r["evidence_url"],
                "citizen_score": r["citizen_score"],
                "status": r["status"],
                "created_at": r["created_at"],
                "audit_metadata": audit,
            })
        return results

    def upsert_subordinate_official(self, off: SubordinateOfficial) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO subordinate_officials (
                id, mayor_politician_id, municipality, name, title, level, department, portfolio_tags_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                mayor_politician_id=excluded.mayor_politician_id,
                municipality=excluded.municipality,
                name=excluded.name,
                title=excluded.title,
                level=excluded.level,
                department=excluded.department,
                portfolio_tags_json=excluded.portfolio_tags_json;
            """,
            (
                off.id,
                off.mayor_politician_id,
                off.municipality,
                off.name,
                off.title,
                off.level,
                off.department,
                json.dumps(off.portfolio_tags, ensure_ascii=False),
            ),
        )
        self._conn.commit()

    def upsert_council_interpellation(self, ci: CouncilInterpellation) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            INSERT INTO council_interpellations (
                id, mayor_politician_id, responder_type, responder_official_id,
                responder_name, responder_title, department_category, council_name,
                session_date, councilor_name, interpellation_title, question_summary,
                official_response, linked_promise_id, gazette_url, vod_url,
                start_time_sec, end_time_sec, audit_metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                mayor_politician_id=excluded.mayor_politician_id,
                responder_type=excluded.responder_type,
                responder_official_id=excluded.responder_official_id,
                responder_name=excluded.responder_name,
                responder_title=excluded.responder_title,
                department_category=excluded.department_category,
                council_name=excluded.council_name,
                session_date=excluded.session_date,
                councilor_name=excluded.councilor_name,
                interpellation_title=excluded.interpellation_title,
                question_summary=excluded.question_summary,
                official_response=excluded.official_response,
                linked_promise_id=excluded.linked_promise_id,
                gazette_url=excluded.gazette_url,
                vod_url=excluded.vod_url,
                start_time_sec=excluded.start_time_sec,
                end_time_sec=excluded.end_time_sec,
                audit_metadata_json=excluded.audit_metadata_json;
            """,
            (
                ci.id,
                ci.mayor_politician_id,
                ci.responder_type,
                ci.responder_official_id,
                ci.responder_name,
                ci.responder_title,
                ci.department_category,
                ci.council_name,
                ci.session_date,
                ci.councilor_name,
                ci.interpellation_title,
                ci.question_summary,
                ci.official_response,
                ci.linked_promise_id,
                ci.gazette_url,
                ci.vod_url,
                float(ci.start_time_sec),
                float(ci.end_time_sec),
                json.dumps(ci.audit_metadata, ensure_ascii=False),
            ),
        )
        self._conn.commit()

    def _match_mayor_ids(self, query_id: str) -> List[str]:
        aliases = {
            "pol-001": ["pol-001"],
            "pol-002": ["pol-002", "pol-004"],
            "pol-003": ["pol-003", "pol-005"],
            "pol-004": ["pol-004", "pol-006", "pol-002"],
            "pol-005": ["pol-005", "pol-007"],
            "pol-006": ["pol-006", "pol-002"],
            "蔣萬安": ["pol-001"],
            "侯友宜": ["pol-002"],
            "張善政": ["pol-003"],
            "盧秀燕": ["pol-004"],
            "黃偉哲": ["pol-005"],
            "陳其邁": ["pol-006"],
        }
        return aliases.get(query_id, [query_id])

    def list_subordinate_officials(
        self,
        mayor_id: Optional[str] = None,
        level: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        sql = """
            SELECT o.*, p.name as mayor_name, p.party as mayor_party
            FROM subordinate_officials o
            LEFT JOIN politicians p ON o.mayor_politician_id = p.id
            WHERE 1=1
        """
        params = []
        if mayor_id:
            target_ids = self._match_mayor_ids(mayor_id)
            placeholders = ",".join(["?"] * len(target_ids))
            sql += f" AND (o.mayor_politician_id IN ({placeholders}) OR o.municipality LIKE ? OR p.name LIKE ?)"
            params.extend(target_ids)
            params.append(f"%{mayor_id}%")
            params.append(f"%{mayor_id}%")
        if level:
            sql += " AND o.level = ?"
            params.append(level)
        sql += " ORDER BY o.id ASC;"
        cursor.execute(sql, tuple(params))
        results = []
        for r in cursor.fetchall():
            tags = []
            if r["portfolio_tags_json"]:
                try:
                    tags = json.loads(r["portfolio_tags_json"])
                except Exception:
                    tags = []
            results.append({
                "id": r["id"],
                "mayor_id": r["mayor_politician_id"],
                "mayor_politician_id": r["mayor_politician_id"],
                "mayor_name": r["mayor_name"] or "",
                "mayor_party": r["mayor_party"] or "",
                "municipality": r["municipality"],
                "name": r["name"],
                "title": r["title"],
                "level": r["level"],
                "role_level": r["level"],
                "department": r["department"],
                "portfolio_tags": tags,
                "start_date": "2022-12-25",
                "responsibilities": ", ".join(tags) if tags else r["department"],
            })
        return results

    def list_council_interpellations(
        self,
        mayor_id: Optional[str] = None,
        department: Optional[str] = None,
        responder_type: Optional[str] = None,
        promise_id: Optional[str] = None,
        q: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        sql = """
            SELECT ci.*, p.name as mayor_name, p.party as mayor_party, pr.title as promise_title
            FROM council_interpellations ci
            LEFT JOIN politicians p ON ci.mayor_politician_id = p.id
            LEFT JOIN promises pr ON ci.linked_promise_id = pr.id
            WHERE 1=1
        """
        params = []
        if mayor_id:
            target_ids = self._match_mayor_ids(mayor_id)
            placeholders = ",".join(["?"] * len(target_ids))
            sql += f" AND (ci.mayor_politician_id IN ({placeholders}) OR p.name LIKE ?)"
            params.extend(target_ids)
            params.append(f"%{mayor_id}%")
        if department:
            sql += " AND ci.department_category = ?"
            params.append(department)
        if responder_type:
            sql += " AND ci.responder_type = ?"
            params.append(responder_type)
        if promise_id:
            norm_ids = [promise_id, promise_id.replace("prom-", "promise-"), promise_id.replace("promise-", "prom-")]
            placeholders = ",".join(["?"] * len(norm_ids))
            sql += f" AND ci.linked_promise_id IN ({placeholders})"
            params.extend(norm_ids)
        if q:
            sql += " AND (ci.interpellation_title LIKE ? OR ci.question_summary LIKE ? OR ci.official_response LIKE ? OR ci.responder_name LIKE ? OR ci.councilor_name LIKE ?)"
            like_q = f"%{q}%"
            params.extend([like_q, like_q, like_q, like_q, like_q])
        sql += " ORDER BY ci.session_date DESC, ci.id ASC;"
        cursor.execute(sql, tuple(params))
        results = []
        for r in cursor.fetchall():
            audit = {}
            if r["audit_metadata_json"]:
                try:
                    audit = json.loads(r["audit_metadata_json"])
                except Exception:
                    audit = {}
            results.append({
                "id": r["id"],
                "mayor_id": r["mayor_politician_id"],
                "mayor_politician_id": r["mayor_politician_id"],
                "mayor_name": r["mayor_name"] or "",
                "mayor_party": r["mayor_party"] or "",
                "responder_type": r["responder_type"],
                "responder_official_id": r["responder_official_id"],
                "responder_name": r["responder_name"],
                "responder_title": r["responder_title"],
                "department_category": r["department_category"],
                "department": r["department_category"],
                "council_name": r["council_name"],
                "session_date": r["session_date"],
                "sitting_date": r["session_date"],
                "councilor_name": r["councilor_name"],
                "interpellation_member": r["councilor_name"],
                "interpellation_title": r["interpellation_title"],
                "subject": r["interpellation_title"],
                "interpellation_type": "市政總質詢" if "總質詢" in r["department_category"] or "總質詢" in r["interpellation_title"] else "部門質詢",
                "question_summary": r["question_summary"],
                "official_response": r["official_response"],
                "response_summary": r["official_response"],
                "linked_promise_id": r["linked_promise_id"],
                "promise_title": r["promise_title"] or "",
                "gazette_url": r["gazette_url"],
                "official_gazette_url": r["gazette_url"],
                "vod_url": r["vod_url"],
                "council_vod_url": r["vod_url"],
                "start_time_sec": float(r["start_time_sec"] or 0.0),
                "end_time_sec": float(r["end_time_sec"] or 300.0),
                "audit_metadata": audit,
            })
        return results

    def get_overview_stats(self) -> Dict[str, Any]:
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM politicians;")
        total_pols = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM speeches;")
        total_speeches = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bills;")
        total_bills = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM votes;")
        total_votes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM promises;")
        total_promises = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM promises WHERE status = 'FULFILLED';")
        fulfilled_promises = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM exam_report_cards;")
        total_exam_cards = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM citizen_petitions;")
        total_petitions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM subordinate_officials;")
        total_sub_officials = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM council_interpellations;")
        total_council_interp = cursor.fetchone()[0]

        pols = self.get_politicians()
        cross_count = sum(1 for p in pols if p["stats"]["is_cross_phase"])

        return {
            "total_politicians": total_pols,
            "cross_phase_politicians": cross_count,
            "total_speeches": total_speeches,
            "total_bills": total_bills,
            "total_votes": total_votes,
            "total_promises": total_promises,
            "fulfilled_promises": fulfilled_promises,
            "total_exam_cards": total_exam_cards,
            "total_petitions": total_petitions,
            "subordinate_officials_count": total_sub_officials,
            "council_interpellations_count": total_council_interp,
        }

    get_stats = get_overview_stats

    def get_sync_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT * FROM sync_logs ORDER BY id DESC LIMIT ?;",
            (limit,),
        )
        logs = []
        for r in cursor.fetchall():
            logs.append({
                "id": r["id"],
                "source": r["source"],
                "status": r["status"],
                "items_synced": r["items_synced"],
                "details": json.loads(r["details_json"]) if r["details_json"] else {},
                "created_at": r["created_at"],
            })
        return logs

    def get_security_metadata(self) -> Dict[str, Any]:
        cursor = self._conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        cursor.execute("PRAGMA foreign_keys;")
        foreign_keys = cursor.fetchone()[0]
        return {
            "engine": "sqlite3",
            "journal_mode": journal_mode.upper(),
            "foreign_keys_enabled": bool(foreign_keys),
            "parameterized_queries": True,
            "database_path": self.db_path,
        }

    def close(self):
        self._conn.close()


# Global Singleton instance
_GLOBAL_ENGINE: Optional[DatabaseEngine] = None


def get_database_engine(db_path: Union[str, Path] = DEFAULT_DB_PATH, auto_seed: bool = True) -> DatabaseEngine:
    global _GLOBAL_ENGINE
    if _GLOBAL_ENGINE is None:
        _GLOBAL_ENGINE = DatabaseEngine(db_path=db_path, auto_seed=auto_seed)
    return _GLOBAL_ENGINE
