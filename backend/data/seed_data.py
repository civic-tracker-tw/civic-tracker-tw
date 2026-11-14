"""
CivicTracker TW - Seed Data Repository
Realistic Taiwan Legislative Yuan (Phase 1) & Mayor/Executive (Phase 2) dataset
structured using domain.py models and cross-validated for the runtime web server.
"""

from typing import Any, Dict, List, Optional
from backend.models.domain import (
    Bill,
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


class SeedDatabase:
    """In-memory seed data repository providing query and filter APIs."""

    def __init__(self):
        self.politicians: Dict[str, Politician] = {}
        self.sessions: Dict[str, LegislativeSession] = {}
        self.speeches: List[InterpellationSpeech] = []
        self.bills: Dict[str, Bill] = {}
        self.votes: List[VoteRecord] = []
        self.promises: List[PolicyPromise] = []
        self._init_data()

    def _init_data(self):
        # ---------------------------------------------------------------------
        # 1. Legislative Sessions
        # ---------------------------------------------------------------------
        s1 = LegislativeSession(
            id="session-ly-10-06-01",
            term_number=10,
            session_number=6,
            date="2022-10-14",
            meeting_type="COMMITTEE",
            title="立法院第10屆第6會期交通委員會第4次全體委員會議",
        )
        s2 = LegislativeSession(
            id="session-ly-10-07-02",
            term_number=10,
            session_number=7,
            date="2023-04-12",
            meeting_type="COMMITTEE",
            title="立法院第10屆第7會期司法及法制委員會第8次全體委員會議",
        )
        s3 = LegislativeSession(
            id="session-ly-10-08-01",
            term_number=10,
            session_number=8,
            date="2023-11-28",
            meeting_type="PLENARY",
            title="立法院第10屆第8會期第10次院會（法案記名表決）",
        )
        for s in (s1, s2, s3):
            self.sessions[s.id] = s

        # ---------------------------------------------------------------------
        # 2. Politician 1: 林宏遠 (Lin Hung-Yuan) — 跨角色 (立法委員 -> 縣市長)
        # ---------------------------------------------------------------------
        p1 = Politician(id="pol-lin-01", name="林宏遠", party="台灣進步陣線")
        t1_leg = Term(
            id="term-lin-leg-10",
            politician_id="pol-lin-01",
            role_type=RoleType.LEGISLATOR.value,
            constituency="台北市第一選區 (士林、北投)",
            start_date="2020-02-01",
            end_date="2024-01-31",
            title="第十屆立法委員（交通委員會召集委員）",
        )
        t1_exec = Term(
            id="term-lin-exec-11",
            politician_id="pol-lin-01",
            role_type=RoleType.EXECUTIVE.value,
            constituency="新竹市",
            start_date="2024-12-25",
            end_date=None,
            title="第十一屆新竹市市長",
        )
        p1.add_term(t1_leg)
        p1.add_term(t1_exec)
        self.politicians[p1.id] = p1

        # ---------------------------------------------------------------------
        # 3. Politician 2: 張靜雅 (Chang Ching-Ya) — 資深國會立委
        # ---------------------------------------------------------------------
        p2 = Politician(id="pol-chang-02", name="張靜雅", party="民主社會黨")
        t2_leg = Term(
            id="term-chang-leg-10",
            politician_id="pol-chang-02",
            role_type=RoleType.LEGISLATOR.value,
            constituency="全國不分區及僑居國外國民",
            start_date="2020-02-01",
            end_date="2028-01-31",
            title="第十、十一屆立法委員（司法及法制委員會、財政委員會）",
        )
        p2.add_term(t2_leg)
        self.politicians[p2.id] = p2

        # ---------------------------------------------------------------------
        # 4. Politician 3: 黃紹華 (Huang Shao-Hua) — 直轄市市長
        # ---------------------------------------------------------------------
        p3 = Politician(id="pol-huang-03", name="黃紹華", party="繁榮公民黨")
        t3_exec = Term(
            id="term-huang-exec-04",
            politician_id="pol-huang-03",
            role_type=RoleType.EXECUTIVE.value,
            constituency="台中市",
            start_date="2022-12-25",
            end_date=None,
            title="第四屆台中市市長",
        )
        p3.add_term(t3_exec)
        self.politicians[p3.id] = p3

        # ---------------------------------------------------------------------
        # 5. Phase 1: Interpellation Speeches (質詢逐字稿與 IVOD 時間軸)
        # ---------------------------------------------------------------------
        speech_1 = InterpellationSpeech(
            id="speech-001",
            session_id="session-ly-10-06-01",
            speaker_term_id="term-lin-leg-10",
            target_official_id="official-motc-minister",
            start_time_sec=200.0,  # 03:20
            end_time_sec=525.0,    # 08:45
            transcript_raw=(
                "【林宏遠委員】：部長請就座。外媒稱台灣為『行人地獄』，今年前八個月行人死傷依然居高不下。"
                "交通部提出的道安基本法草案，到底何時能落實『人行道退縮行穿線』與學區周邊全面科技執法？\n"
                "【交通部部長】：謝謝林委員關心。我們已跟內政部國土署召開跨部會會議，核定400億元『永續提升人行安全計畫』，"
                "優先補助各縣市改善600處高風險路口與學區通學步道，預計在年底前完成第一階段工程盤點。"
            ),
            ai_summary="林宏遠委員針對『行人路權與道安基本法』質詢交通部，要求半年內全面盤點學區人行安全工程並嚴格考核進度；交通部承諾編列400億專款優先改善600處危險路口。",
            topic_tags=["行人路權", "交通罰則", "工程改善"],
            audit_metadata={
                "audit_verdict": "APPROVE",
                "audited_by": "argon",
                "confidence": 0.96,
                "notes": "Verified against IVOD video timestamps and official gazette.",
            },
        )

        speech_2 = InterpellationSpeech(
            id="speech-002",
            session_id="session-ly-10-07-02",
            speaker_term_id="term-chang-leg-10",
            target_official_id="official-moj-minister",
            start_time_sec=120.0,  # 02:00
            end_time_sec=555.0,    # 09:15
            transcript_raw=(
                "【張靜雅委員】：部長，詐騙案件已成民怨之首。人頭帳戶與虛擬資產洗錢管道層出不窮，"
                "金管會與數發部互相推諉，第三方支付登錄查核機制如同虛設。法務部在打詐專法中，"
                "到底有沒有將大型網路社群廣告實名制納入連帶處罰？\n"
                "【法務部部長】：跟委員報告，打詐專法草案已增訂『網路廣告平台防詐義務』，"
                "若平台未下架詐騙廣告或未落實實名驗證，最高可處以2500萬元連續罰鍰，情節重大得封阻網域。"
            ),
            ai_summary="張靜雅委員嚴厲質詢打詐專法與第三方支付虛擬洗錢防制，直指部會監管漏洞；法務部說明已將社群廣告平台實名制與重罰條款納入專法草案。",
            topic_tags=["打詐專法", "洗錢防制", "金融監理"],
            audit_metadata={
                "audit_verdict": "APPROVE",
                "audited_by": "argon",
                "confidence": 0.98,
                "notes": "Evidence verified against Ministry of Justice draft legislation.",
            },
        )

        speech_3 = InterpellationSpeech(
            id="speech-003",
            session_id="session-ly-10-06-01",
            speaker_term_id="term-lin-leg-10",
            target_official_id="official-ndc-minister",
            start_time_sec=70.0,   # 01:10
            end_time_sec=390.0,    # 06:30
            transcript_raw=(
                "【林宏遠委員】：國發會主委，大新竹地區每日通勤國道一號竹科段嚴重壅塞，"
                "竹科輕軌藍線案送中央審查已超過一年，中央與地方補助比例遲未定案。國發會能否承諾年底前召集跨部會定案？\n"
                "【國發會主委】：委員指教切中要害。國發會已協調交通部鐵道局與新竹縣市政府，"
                "預計下個月召開第一次大新竹軌道建設協調會，加速環評與綜合規劃審議。"
            ),
            ai_summary="林宏遠委員督促中央加速新竹輕軌藍線審議，要求國發會成立跨縣市軌道平台解決竹科交通壅塞瓶頸。",
            topic_tags=["竹科交通", "軌道建設", "跨區整合"],
            audit_metadata={
                "audit_verdict": "APPROVE",
                "audited_by": "argon",
                "confidence": 0.94,
                "notes": "Verified speech transcript attribution.",
            },
        )
        self.speeches.extend([speech_1, speech_2, speech_3])

        # ---------------------------------------------------------------------
        # 6. Phase 1: Bills & Roll-Call Vote Records (法案與記名表決)
        # ---------------------------------------------------------------------
        b1 = Bill(
            id="bill-10-08-01",
            title="道路交通安全基本法草案",
            session_id="session-ly-10-08-01",
            proposer_term_ids=["term-lin-leg-10", "term-chang-leg-10"],
            description="確立以人為本之交通安全政策方針，明定中央每年度公布道安改善白皮書與各縣市零死亡願景目標。",
        )
        b2 = Bill(
            id="bill-10-08-02",
            title="詐欺犯罪危害防制條例（打詐專法）草案",
            session_id="session-ly-10-08-01",
            proposer_term_ids=["term-chang-leg-10"],
            description="加重組織詐欺刑責，規範網路廣告平台實名制與第三方支付金融阻詐聯防機制。",
        )
        b3 = Bill(
            id="bill-10-08-03",
            title="預算法第八十三條修正草案（嚴格限縮特別預算編列要件）",
            session_id="session-ly-10-08-01",
            proposer_term_ids=["term-chang-leg-10"],
            description="刪除『不定期或數年一次之重大政事』得編列特別預算之概括條款，強化國會財政監督。",
        )
        for b in (b1, b2, b3):
            self.bills[b.id] = b

        v1 = VoteRecord(
            id="vote-001",
            bill_id="bill-10-08-01",
            politician_id="pol-lin-01",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-01",
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE"},
        )
        v2 = VoteRecord(
            id="vote-002",
            bill_id="bill-10-08-01",
            politician_id="pol-chang-02",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-01",
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE"},
        )
        v3 = VoteRecord(
            id="vote-003",
            bill_id="bill-10-08-02",
            politician_id="pol-chang-02",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-02",
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE"},
        )
        v4 = VoteRecord(
            id="vote-004",
            bill_id="bill-10-08-03",
            politician_id="pol-lin-01",
            decision=VoteDecision.ABSTAIN.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-03",
            audit_metadata={"party_aligned": False, "audited_by": "argon", "verdict": "APPROVE", "note": "跨黨派協商棄權"},
        )
        v5 = VoteRecord(
            id="vote-005",
            bill_id="bill-10-08-03",
            politician_id="pol-chang-02",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-03",
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE"},
        )
        self.votes.extend([v1, v2, v3, v4, v5])

        # ---------------------------------------------------------------------
        # 7. Phase 2: Mayor Policy Promises & Milestones (首長政見與工程標案)
        # ---------------------------------------------------------------------
        # 林宏遠市長 (新竹市)
        p_lin_1 = PolicyPromise(
            id="promise-lin-01",
            politician_id="pol-lin-01",
            term_id="term-lin-exec-11",
            title="智慧交通路網與全區號誌連鎖優化計畫",
            category="交通建設",
            status=FulfillmentStatus.IN_PROGRESS.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/hsinchu-2024/lin-01",
            target_completion_date="2026-12-31",
            audit_metadata={"fulfillment_score": 68.5, "audited_by": "argon", "verdict": "APPROVE"},
        )
        m_lin_1a = ExecutionMilestone(
            id="ms-lin-1a",
            promise_id="promise-lin-01",
            milestone_date="2025-03-15",
            evidence_summary="慈雲路與光復路 25 處關鍵路口智慧動態號誌感測器發包完成，預估尖峰時段車流停等時間減少 18%。",
            source_url="https://web.pcc.gov.tw/tenders/hsinchu-traffic-2025-01",
            budget_spent=45000000.0,
            audit_metadata={"evidence_type": "TENDER_AWARD", "audited_by": "argon", "verdict": "APPROVE"},
        )
        m_lin_1b = ExecutionMilestone(
            id="ms-lin-1b",
            promise_id="promise-lin-01",
            milestone_date="2025-08-20",
            evidence_summary="竹科通勤專車全電動化第一期（共 15 輛低底盤電動公車）正式上路營運。",
            source_url="https://web.pcc.gov.tw/tenders/hsinchu-shuttle-2025-02",
            budget_spent=32000000.0,
            audit_metadata={"evidence_type": "DELIVERY_ACCEPTANCE", "audited_by": "argon", "verdict": "APPROVE"},
        )
        p_lin_1.add_milestone(m_lin_1a)
        p_lin_1.add_milestone(m_lin_1b)

        p_lin_2 = PolicyPromise(
            id="promise-lin-02",
            politician_id="pol-lin-01",
            term_id="term-lin-exec-11",
            title="0至6歲公立托育設施倍增與第二胎育兒津貼加碼",
            category="托育社福",
            status=FulfillmentStatus.FULFILLED.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/hsinchu-2024/lin-02",
            target_completion_date="2025-09-01",
            audit_metadata={"fulfillment_score": 100.0, "audited_by": "argon", "verdict": "APPROVE"},
        )
        m_lin_2a = ExecutionMilestone(
            id="ms-lin-2a",
            promise_id="promise-lin-02",
            milestone_date="2025-08-10",
            evidence_summary="新設東區與北區 12 處社區公共托育家園驗收完畢，第二胎加碼補助全面撥款發放達 3,850 戶。",
            source_url="https://web.pcc.gov.tw/tenders/hsinchu-childcare-2025-03",
            budget_spent=88000000.0,
            audit_metadata={"evidence_type": "COMPLETION_REPORT", "audited_by": "argon", "verdict": "APPROVE"},
        )
        p_lin_2.add_milestone(m_lin_2a)

        p_lin_3 = PolicyPromise(
            id="promise-lin-03",
            politician_id="pol-lin-01",
            term_id="term-lin-exec-11",
            title="竹科新創產學孵化專區二期擴建案",
            category="產業經濟",
            status=FulfillmentStatus.STALLED.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/hsinchu-2024/lin-03",
            target_completion_date="2027-06-30",
            audit_metadata={"fulfillment_score": 15.0, "audited_by": "argon", "verdict": "APPROVE", "delay_reason": "土地徵收公聽會地主爭議暫緩"},
        )
        m_lin_3a = ExecutionMilestone(
            id="ms-lin-3a",
            promise_id="promise-lin-03",
            milestone_date="2025-05-18",
            evidence_summary="可行性評估案完成，但都市計畫土地變更作業因周邊農地業主陳情，市府議會審查暫予保留。",
            source_url="https://web.pcc.gov.tw/tenders/hsinchu-incubator-2025-04",
            budget_spent=15000000.0,
            audit_metadata={"evidence_type": "AUDIT_WARNING", "audited_by": "argon", "verdict": "APPROVE"},
        )
        p_lin_3.add_milestone(m_lin_3a)

        # 黃紹華市長 (台中市)
        p_huang_1 = PolicyPromise(
            id="promise-huang-01",
            politician_id="pol-huang-03",
            term_id="term-huang-exec-04",
            title="台中捷運藍線綜合規劃核定與全線工程動工發包",
            category="軌道交通",
            status=FulfillmentStatus.IN_PROGRESS.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/taichung-2022/huang-01",
            target_completion_date="2030-12-31",
            audit_metadata={"fulfillment_score": 52.0, "audited_by": "argon", "verdict": "APPROVE"},
        )
        m_huang_1a = ExecutionMilestone(
            id="ms-huang-1a",
            promise_id="promise-huang-01",
            milestone_date="2024-01-29",
            evidence_summary="行政院核定台中捷運藍線綜合規劃報告書，總經費 1,615 億元由中央與地方分攤。",
            source_url="https://web.pcc.gov.tw/tenders/tc-mrt-blue-2024-01",
            budget_spent=350000000.0,
            audit_metadata={"evidence_type": "OFFICIAL_DECREE", "audited_by": "argon", "verdict": "APPROVE"},
        )
        p_huang_1.add_milestone(m_huang_1a)

        p_huang_2 = PolicyPromise(
            id="promise-huang-02",
            politician_id="pol-huang-03",
            term_id="term-huang-exec-04",
            title="市區公車全面電動化與空污清淨行動方案",
            category="環境保護",
            status=FulfillmentStatus.FULFILLED.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/taichung-2022/huang-02",
            target_completion_date="2025-10-31",
            audit_metadata={"fulfillment_score": 96.0, "audited_by": "argon", "verdict": "APPROVE"},
        )
        m_huang_2a = ExecutionMilestone(
            id="ms-huang-2a",
            promise_id="promise-huang-02",
            milestone_date="2025-09-30",
            evidence_summary="市區主要幹線電動公車累計達 420 輛，電動公車普及率突破 52% 居全國前列。",
            source_url="https://web.pcc.gov.tw/tenders/tc-ev-bus-2025-01",
            budget_spent=1800000000.0,
            audit_metadata={"evidence_type": "COMPLETION_REPORT", "audited_by": "argon", "verdict": "APPROVE"},
        )
        p_huang_2.add_milestone(m_huang_2a)

        self.promises.extend([p_lin_1, p_lin_2, p_lin_3, p_huang_1, p_huang_2])

    # -------------------------------------------------------------------------
    # Query & Access Methods
    # -------------------------------------------------------------------------

    def get_politicians(self) -> List[Dict[str, Any]]:
        result = []
        for p in self.politicians.values():
            p_dict = p.to_dict()
            # Calculate activity metrics
            leg_terms = [t["id"] for t in p_dict["terms"] if t["role_type"] == RoleType.LEGISLATOR.value]
            exec_terms = [t["id"] for t in p_dict["terms"] if t["role_type"] == RoleType.EXECUTIVE.value]
            speeches_count = sum(1 for s in self.speeches if s.speaker_term_id in leg_terms)
            votes_count = sum(1 for v in self.votes if v.politician_id == p.id)
            promises_count = sum(1 for pr in self.promises if pr.politician_id == p.id)
            fulfilled_count = sum(
                1 for pr in self.promises if pr.politician_id == p.id and pr.status == FulfillmentStatus.FULFILLED.value
            )
            p_dict["stats"] = {
                "speeches_count": speeches_count,
                "votes_count": votes_count,
                "promises_count": promises_count,
                "fulfilled_count": fulfilled_count,
                "is_cross_phase": len(leg_terms) > 0 and len(exec_terms) > 0,
            }
            result.append(p_dict)
        return result

    def get_politician(self, pol_id: str) -> Optional[Dict[str, Any]]:
        for p in self.get_politicians():
            if p["id"] == pol_id:
                return p
        return None

    def get_speeches(
        self,
        q: Optional[str] = None,
        tag: Optional[str] = None,
        politician_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        target_term_ids = set()
        if politician_id and politician_id in self.politicians:
            target_term_ids = {t.id for t in self.politicians[politician_id].terms}

        for s in self.speeches:
            if target_term_ids and s.speaker_term_id not in target_term_ids:
                continue
            if tag and tag not in s.topic_tags:
                continue
            if q:
                q_lower = q.lower()
                matches_transcript = q_lower in s.transcript_raw.lower()
                matches_summary = q_lower in s.ai_summary.lower()
                matches_tag = any(q_lower in t.lower() for t in s.topic_tags)
                if not (matches_transcript or matches_summary or matches_tag):
                    continue

            # Enrich speaker info
            s_dict = s.to_dict()
            for p in self.politicians.values():
                for t in p.terms:
                    if t.id == s.speaker_term_id:
                        s_dict["speaker_name"] = p.name
                        s_dict["speaker_party"] = p.party
                        s_dict["speaker_title"] = t.title
            s_dict["session"] = self.sessions.get(s.session_id, None).to_dict() if s.session_id in self.sessions else None
            results.append(s_dict)
        return results

    def get_votes(
        self,
        politician_id: Optional[str] = None,
        bill_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for v in self.votes:
            if politician_id and v.politician_id != politician_id:
                continue
            if bill_id and v.bill_id != bill_id:
                continue

            v_dict = v.to_dict()
            bill = self.bills.get(v.bill_id)
            pol = self.politicians.get(v.politician_id)
            v_dict["bill"] = bill.to_dict() if bill else None
            v_dict["politician_name"] = pol.name if pol else None
            v_dict["politician_party"] = pol.party if pol else None
            results.append(v_dict)
        return results

    def get_promises(
        self,
        politician_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for pr in self.promises:
            if politician_id and pr.politician_id != politician_id:
                continue
            if status and pr.status != status:
                continue

            pr_dict = pr.to_dict()
            pol = self.politicians.get(pr.politician_id)
            pr_dict["politician_name"] = pol.name if pol else None
            pr_dict["politician_party"] = pol.party if pol else None
            results.append(pr_dict)
        return results

    def get_overview_stats(self) -> Dict[str, Any]:
        return {
            "total_politicians": len(self.politicians),
            "cross_phase_politicians": sum(1 for p in self.politicians.values() if p.is_legislator() and p.is_executive()),
            "total_speeches": len(self.speeches),
            "total_bills": len(self.bills),
            "total_votes": len(self.votes),
            "total_promises": len(self.promises),
            "fulfilled_promises": sum(1 for pr in self.promises if pr.status == FulfillmentStatus.FULFILLED.value),
        }


# Global singleton instance
_GLOBAL_DB: Optional[SeedDatabase] = None


def get_seed_database() -> SeedDatabase:
    global _GLOBAL_DB
    if _GLOBAL_DB is None:
        _GLOBAL_DB = SeedDatabase()
    return _GLOBAL_DB
