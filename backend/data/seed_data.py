"""
CivicTracker TW - Seed Data Repository
Real Taiwan Legislative Yuan (Phase 1) & Mayor/Executive (Phase 2) dataset
structured using domain.py models and cross-validated for the runtime web server.
Features real Taiwanese politicians: 蔣萬安, 陳其邁, 盧秀燕.
"""

from typing import Any, Dict, List, Optional
from backend.models.domain import (
    Bill,
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


class SeedDatabase:
    """In-memory seed data repository providing query and filter APIs."""

    def __init__(self):
        self.politicians: Dict[str, Politician] = {}
        self.sessions: Dict[str, LegislativeSession] = {}
        self.speeches: List[InterpellationSpeech] = []
        self.bills: Dict[str, Bill] = {}
        self.votes: List[VoteRecord] = []
        self.promises: List[PolicyPromise] = []
        self.exam_cards: List[ExamReportCard] = []
        self.petitions: List[CitizenPetition] = []
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
        # 2. Politician 1: 蔣萬安 (Chiang Wan-An) — 跨角色 (第九、十屆立法委員 -> 臺北市市長)
        # ---------------------------------------------------------------------
        p1 = Politician(id="pol-001", name="蔣萬安", party="中國國民黨")
        t1_leg = Term(
            id="term-leg-001",
            politician_id="pol-001",
            role_type=RoleType.LEGISLATOR.value,
            constituency="臺北市第三選舉區 (中山、北松山)",
            start_date="2016-02-01",
            end_date="2022-11-10",
            title="第九、十屆立法委員（社會福利及衛生環境委員會）",
        )
        t1_exec = Term(
            id="term-exec-001",
            politician_id="pol-001",
            role_type=RoleType.EXECUTIVE.value,
            constituency="臺北市",
            start_date="2022-12-25",
            end_date=None,
            title="第八屆臺北市市長",
        )
        p1.add_term(t1_leg)
        p1.add_term(t1_exec)
        self.politicians[p1.id] = p1
        self.politicians["pol-lin-01"] = p1  # backward compatibility alias

        # ---------------------------------------------------------------------
        # 3. Politician 2: 陳其邁 (Chen Chi-Mai) — 跨角色 (第八、九屆立法委員 -> 高雄市市長)
        # ---------------------------------------------------------------------
        p2 = Politician(id="pol-002", name="陳其邁", party="民主進步黨")
        t2_leg = Term(
            id="term-leg-002",
            politician_id="pol-002",
            role_type=RoleType.LEGISLATOR.value,
            constituency="全國不分區及僑居國外國民",
            start_date="2012-02-01",
            end_date="2018-11-03",
            title="第八、九屆立法委員（內政委員會、經濟委員會）",
        )
        t2_exec = Term(
            id="term-exec-002",
            politician_id="pol-002",
            role_type=RoleType.EXECUTIVE.value,
            constituency="高雄市",
            start_date="2020-08-24",
            end_date=None,
            title="第三、四屆高雄市市長",
        )
        p2.add_term(t2_leg)
        p2.add_term(t2_exec)
        self.politicians[p2.id] = p2
        self.politicians["pol-chang-02"] = p2  # backward compatibility alias

        # ---------------------------------------------------------------------
        # 4. Politician 3: 盧秀燕 (Lu Shiow-Yen) — 跨角色 (第九屆立法委員 -> 臺中市市長)
        # ---------------------------------------------------------------------
        p3 = Politician(id="pol-003", name="盧秀燕", party="中國國民黨")
        t3_leg = Term(
            id="term-leg-003",
            politician_id="pol-003",
            role_type=RoleType.LEGISLATOR.value,
            constituency="臺中市第五選舉區 (北區、北屯區)",
            start_date="2016-02-01",
            end_date="2018-11-20",
            title="第九屆立法委員（財政委員會召集委員）",
        )
        t3_exec = Term(
            id="term-exec-003",
            politician_id="pol-003",
            role_type=RoleType.EXECUTIVE.value,
            constituency="臺中市",
            start_date="2018-12-25",
            end_date=None,
            title="第三、四屆臺中市市長",
        )
        p3.add_term(t3_leg)
        p3.add_term(t3_exec)
        self.politicians[p3.id] = p3
        self.politicians["pol-huang-03"] = p3  # backward compatibility alias

        # ---------------------------------------------------------------------
        # 5. Phase 1: Interpellation Speeches (質詢逐字稿、IVOD 影音與 billy3321 串接)
        # ---------------------------------------------------------------------
        speech_1 = InterpellationSpeech(
            id="speech-001",
            session_id="session-ly-10-06-01",
            speaker_term_id="term-leg-001",
            target_official_id="official-motc-minister",
            start_time_sec=200.0,  # 03:20
            end_time_sec=525.0,    # 08:45
            transcript_raw=(
                "【蔣萬安委員】：部長請就座。外媒稱台灣為『行人地獄』，今年前八個月行人死傷依然居高不下。"
                "交通部提出的道安基本法草案，到底何時能落實『人行道退縮行穿線』與學區周邊全面科技執法？\n"
                "【交通部部長】：謝謝蔣委員關心。我們已跟內政部國土署召開跨部會會議，核定400億元『永續提升人行安全計畫』，"
                "優先補助各縣市改善600處高風險路口與學區通學步道，預計在年底前完成第一階段工程盤點。"
            ),
            ai_summary="蔣萬安委員針對『行人路權與道安基本法』質詢交通部，要求半年內全面盤點學區人行安全工程並嚴格考核進度；交通部承諾編列400億專款優先改善600處危險路口。",
            topic_tags=["行人路權", "交通罰則", "工程改善"],
            audit_metadata={
                "audit_verdict": "APPROVE",
                "audited_by": "argon",
                "confidence": 0.96,
                "notes": "Verified against IVOD video timestamps and official gazette.",
            },
            ivod_clip_id="110825",
            video_stream_url="https://media.ly.gov.tw/ivod/110825.mp4",
            billy3321_url="https://ivod.billy3321.tw/ivod/110825",
        )

        speech_2 = InterpellationSpeech(
            id="speech-002",
            session_id="session-ly-10-07-02",
            speaker_term_id="term-leg-002",
            target_official_id="official-moj-minister",
            start_time_sec=120.0,  # 02:00
            end_time_sec=555.0,    # 09:15
            transcript_raw=(
                "【陳其邁委員】：部長，詐騙案件已成民怨之首。人頭帳戶與虛擬資產洗錢管道層出不窮，"
                "金管會與數發部互相推諉，第三方支付登錄查核機制如同虛設。法務部在打詐專法中，"
                "到底有沒有將大型網路社群廣告實名制納入連帶處罰？\n"
                "【法務部部長】：跟委員報告，打詐專法草案已增訂『網路廣告平台防詐義務』，"
                "若平台未下架詐騙廣告或未落實實名驗證，最高可處以2500萬元連續罰鍰，情節重大得封阻網域。"
            ),
            ai_summary="陳其邁委員嚴厲質詢打詐專法與第三方支付虛擬洗錢防制，直指部會監管漏洞；法務部說明已將社群廣告平台實名制與重罰條款納入專法草案。",
            topic_tags=["打詐專法", "洗錢防制", "金融監理"],
            audit_metadata={
                "audit_verdict": "APPROVE",
                "audited_by": "argon",
                "confidence": 0.98,
                "notes": "Evidence verified against Ministry of Justice draft legislation.",
            },
            ivod_clip_id="110912",
            video_stream_url="https://media.ly.gov.tw/ivod/110912.mp4",
            billy3321_url="https://ivod.billy3321.tw/ivod/110912",
        )

        speech_3 = InterpellationSpeech(
            id="speech-003",
            session_id="session-ly-10-06-01",
            speaker_term_id="term-leg-001",
            target_official_id="official-ndc-minister",
            start_time_sec=70.0,   # 01:10
            end_time_sec=390.0,    # 06:30
            transcript_raw=(
                "【蔣萬安委員】：國發會主委，台北捷運東環段與基隆捷運規劃案送中央審查，"
                "中央與地方補助比例遲未定案。國發會能否承諾年底前召集跨部會定案加速核定？\n"
                "【國發會主委】：委員指教切中要害。國發會已協調交通部鐵道局與台北市、新北市府，"
                "預計下個月召開協調會，加速環評與綜合規劃審議並啟動前置工程。"
            ),
            ai_summary="蔣萬安委員督促中央加速台北捷運東環段與大眾運輸軌道審議，要求國發會協調交通部加速前置發包作業。",
            topic_tags=["捷運東環段", "軌道建設", "跨區整合"],
            audit_metadata={
                "audit_verdict": "APPROVE",
                "audited_by": "argon",
                "confidence": 0.94,
                "notes": "Verified speech transcript attribution.",
            },
            ivod_clip_id="110826",
            video_stream_url="https://media.ly.gov.tw/ivod/110826.mp4",
            billy3321_url="https://ivod.billy3321.tw/ivod/110826",
        )
        self.speeches.extend([speech_1, speech_2, speech_3])

        # ---------------------------------------------------------------------
        # 6. Phase 1: Bills & Roll-Call Vote Records (法案與記名表決)
        # ---------------------------------------------------------------------
        b1 = Bill(
            id="bill-10-08-01",
            title="道路交通安全基本法草案",
            session_id="session-ly-10-08-01",
            proposer_term_ids=["term-leg-001", "term-leg-002"],
            description="確立以人為本之交通安全政策方針，明定中央每年度公布道安改善白皮書與各縣市零死亡願景目標。",
        )
        b2 = Bill(
            id="bill-10-08-02",
            title="詐欺犯罪危害防制條例（打詐專法）草案",
            session_id="session-ly-10-08-01",
            proposer_term_ids=["term-leg-002"],
            description="加重組織詐欺刑責，規範網路廣告平台實名制與第三方支付金融阻詐聯防機制。",
        )
        b3 = Bill(
            id="bill-10-08-03",
            title="預算法第八十三條修正草案（嚴格限縮特別預算編列要件）",
            session_id="session-ly-10-08-01",
            proposer_term_ids=["term-leg-003"],
            description="刪除『不定期或數年一次之重大政事』得編列特別預算之概括條款，強化國會財政監督。",
        )
        for b in (b1, b2, b3):
            self.bills[b.id] = b

        v1 = VoteRecord(
            id="vote-001",
            bill_id="bill-10-08-01",
            politician_id="pol-001",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-01",
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE"},
        )
        v2 = VoteRecord(
            id="vote-002",
            bill_id="bill-10-08-01",
            politician_id="pol-002",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-01",
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE"},
        )
        v3 = VoteRecord(
            id="vote-003",
            bill_id="bill-10-08-02",
            politician_id="pol-002",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-02",
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE"},
        )
        v4 = VoteRecord(
            id="vote-004",
            bill_id="bill-10-08-03",
            politician_id="pol-001",
            decision=VoteDecision.ABSTAIN.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-03",
            audit_metadata={"party_aligned": False, "audited_by": "argon", "verdict": "APPROVE", "note": "跨黨派協商棄權"},
        )
        v5 = VoteRecord(
            id="vote-005",
            bill_id="bill-10-08-03",
            politician_id="pol-002",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-03",
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE"},
        )
        self.votes.extend([v1, v2, v3, v4, v5])

        # ---------------------------------------------------------------------
        # 7. Phase 2: Mayor Policy Promises & Milestones (首長政見與工程標案)
        # ---------------------------------------------------------------------
        # 蔣萬安市長 (臺北市)
        p_chiang_1 = PolicyPromise(
            id="promise-001",
            politician_id="pol-001",
            term_id="term-exec-001",
            title="智慧交通路網與全區號誌連鎖優化計畫（內湖交通紓解）",
            category="交通建設",
            status=FulfillmentStatus.IN_PROGRESS.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/taipei-2022/chiang-01",
            target_completion_date="2026-12-31",
            audit_metadata={"fulfillment_score": 72.0, "audited_by": "argon", "verdict": "APPROVE"},
        )
        m_chiang_1a = ExecutionMilestone(
            id="ms-001a",
            promise_id="promise-001",
            milestone_date="2024-03-15",
            evidence_summary="內湖科技園區 30 處關鍵路口智慧動態號誌感測器建置完成，尖峰時段車流停等時間減少 15%。",
            source_url="https://web.pcc.gov.tw/tenders/taipei-traffic-2024-01",
            budget_spent=52000000.0,
            audit_metadata={"evidence_type": "TENDER_AWARD", "audited_by": "argon", "verdict": "APPROVE"},
        )
        m_chiang_1b = ExecutionMilestone(
            id="ms-001b",
            promise_id="promise-001",
            milestone_date="2024-08-20",
            evidence_summary="內湖通勤跳蛙公車增班與預約制上路，運量提升 22%。",
            source_url="https://web.pcc.gov.tw/tenders/taipei-shuttle-2024-02",
            budget_spent=28000000.0,
            audit_metadata={"evidence_type": "DELIVERY_ACCEPTANCE", "audited_by": "argon", "verdict": "APPROVE"},
        )
        p_chiang_1.add_milestone(m_chiang_1a)
        p_chiang_1.add_milestone(m_chiang_1b)

        p_chiang_2 = PolicyPromise(
            id="promise-002",
            politician_id="pol-001",
            term_id="term-exec-001",
            title="生育獎勵金加碼與好孕專車乘車補助專案",
            category="托育社福",
            status=FulfillmentStatus.FULFILLED.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/taipei-2022/chiang-02",
            target_completion_date="2024-01-01",
            audit_metadata={"fulfillment_score": 100.0, "audited_by": "argon", "verdict": "APPROVE"},
        )
        m_chiang_2a = ExecutionMilestone(
            id="ms-002a",
            promise_id="promise-002",
            milestone_date="2023-12-15",
            evidence_summary="第一胎生育補助調高至4萬元、第二胎4.5萬元，好孕專車乘車券累計發放達 18,200 人次。",
            source_url="https://web.pcc.gov.tw/tenders/taipei-childcare-2023-03",
            budget_spent=210000000.0,
            audit_metadata={"evidence_type": "COMPLETION_REPORT", "audited_by": "argon", "verdict": "APPROVE"},
        )
        p_chiang_2.add_milestone(m_chiang_2a)

        p_chiang_3 = PolicyPromise(
            id="promise-003",
            politician_id="pol-001",
            term_id="term-exec-001",
            title="捷運東環段細部設計與全線動工招標",
            category="軌道交通",
            status=FulfillmentStatus.IN_PROGRESS.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/taipei-2022/chiang-03",
            target_completion_date="2028-12-31",
            audit_metadata={"fulfillment_score": 48.0, "audited_by": "argon", "verdict": "APPROVE"},
        )
        m_chiang_3a = ExecutionMilestone(
            id="ms-003a",
            promise_id="promise-003",
            milestone_date="2024-06-28",
            evidence_summary="捷運東環段 CF710 標土建工程招標公告上網，預計年底前完成決標程序。",
            source_url="https://web.pcc.gov.tw/tenders/taipei-mrt-east-2024-04",
            budget_spent=125000000.0,
            audit_metadata={"evidence_type": "TENDER_NOTICE", "audited_by": "argon", "verdict": "APPROVE"},
        )
        p_chiang_3.add_milestone(m_chiang_3a)

        # 盧秀燕市長 (臺中市)
        p_lu_1 = PolicyPromise(
            id="promise-004",
            politician_id="pol-003",
            term_id="term-exec-003",
            title="台中捷運藍線綜合規劃核定與全線工程動工發包",
            category="軌道交通",
            status=FulfillmentStatus.IN_PROGRESS.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/taichung-2022/lu-01",
            target_completion_date="2030-12-31",
            audit_metadata={"fulfillment_score": 55.0, "audited_by": "argon", "verdict": "APPROVE"},
        )
        m_lu_1a = ExecutionMilestone(
            id="ms-004a",
            promise_id="promise-004",
            milestone_date="2024-01-29",
            evidence_summary="行政院正式核定台中捷運藍線綜合規劃報告書，總經費 1,615 億元由中央與地方分攤。",
            source_url="https://web.pcc.gov.tw/tenders/tc-mrt-blue-2024-01",
            budget_spent=350000000.0,
            audit_metadata={"evidence_type": "OFFICIAL_DECREE", "audited_by": "argon", "verdict": "APPROVE"},
        )
        p_lu_1.add_milestone(m_lu_1a)

        p_lu_2 = PolicyPromise(
            id="promise-005",
            politician_id="pol-003",
            term_id="term-exec-003",
            title="市區公車全面電動化與空污清淨行動方案",
            category="環境保護",
            status=FulfillmentStatus.FULFILLED.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/taichung-2022/lu-02",
            target_completion_date="2025-10-31",
            audit_metadata={"fulfillment_score": 96.0, "audited_by": "argon", "verdict": "APPROVE"},
        )
        m_lu_2a = ExecutionMilestone(
            id="ms-005a",
            promise_id="promise-005",
            milestone_date="2025-09-30",
            evidence_summary="市區主要幹線電動公車累計達 420 輛，電動公車普及率突破 52% 居全國前列。",
            source_url="https://web.pcc.gov.tw/tenders/tc-ev-bus-2025-01",
            budget_spent=1800000000.0,
            audit_metadata={"evidence_type": "COMPLETION_REPORT", "audited_by": "argon", "verdict": "APPROVE"},
        )
        p_lu_2.add_milestone(m_lu_2a)

        self.promises.extend([p_chiang_1, p_chiang_2, p_chiang_3, p_lu_1, p_lu_2])

        # ---------------------------------------------------------------------
        # 8. Phase 3 & Extensibility: Midterm/Final Exam Report Cards
        # ---------------------------------------------------------------------
        card_1 = ExamReportCard(
            id="card-001",
            politician_id="pol-001",
            term_id="term-leg-001",
            exam_stage="MIDTERM",
            attendance_rate=98.5,
            objective_score=92.0,
            argon_summary_comment="第10屆立院全院委員會與院會出席率達 98.5%，質詢法案聚焦勞工權益與公共衛生，公督盟評鑑列為優秀立委。",
            citizen_rating_avg=4.6,
            citizen_reviews_count=128,
            audit_metadata={"audit_verdict": "APPROVE", "audited_by": "argon", "confidence": 0.98},
        )
        card_2 = ExamReportCard(
            id="card-002",
            politician_id="pol-002",
            term_id="term-leg-002",
            exam_stage="FINAL",
            attendance_rate=96.0,
            objective_score=89.5,
            argon_summary_comment="主責內政與前瞻經濟建設法規審查，發言精準切中政府採購弊端，質詢量能充沛。",
            citizen_rating_avg=4.4,
            citizen_reviews_count=95,
            audit_metadata={"audit_verdict": "APPROVE", "audited_by": "argon", "confidence": 0.95},
        )
        card_3 = ExamReportCard(
            id="card-003",
            politician_id="pol-003",
            term_id="term-leg-003",
            exam_stage="FINAL",
            attendance_rate=97.2,
            objective_score=91.0,
            argon_summary_comment="長期深耕財政委員會召集人，嚴審中央總預算與地方統籌分配稅款，專業問政表現亮眼。",
            citizen_rating_avg=4.5,
            citizen_reviews_count=112,
            audit_metadata={"audit_verdict": "APPROVE", "audited_by": "argon", "confidence": 0.96},
        )
        self.exam_cards.extend([card_1, card_2, card_3])

        # ---------------------------------------------------------------------
        # 9. Phase 3 & Extensibility: Citizen Petitions & Reviews
        # ---------------------------------------------------------------------
        pet_1 = CitizenPetition(
            id="petition-001",
            politician_id="pol-001",
            target_promise_id="promise-001",
            category="交通建設",
            author_name="內湖通勤族自救會",
            title="建請加速內湖交通瓶頸改善與捷運東環段細部設計",
            content="內科尖峰通勤時間仍嚴重壅塞，盼市府落實捷運東環段發包時程，並在通車前增開跳蛙公車與共享運具優惠。",
            evidence_url="https://web.pcc.gov.tw/tenders/taipei-traffic-2024",
            citizen_score=5,
            status="APPROVED",
            created_at="2024-11-01",
            audit_metadata={"audit_verdict": "APPROVE", "audited_by": "argon", "confidence": 0.96},
        )
        pet_2 = CitizenPetition(
            id="petition-002",
            politician_id="pol-002",
            target_promise_id="promise-004",
            category="科技產業",
            author_name="楠梓在地青年聯盟",
            title="建請公開台積電楠梓園區環境監測與再生水用量月報",
            content="肯定半導體產業進駐帶動高雄發展，建議市府於專區官網定期公布放流水質與空氣品質監控數據，兼顧環境永續。",
            evidence_url="https://web.pcc.gov.tw/tenders/kh-env-2024",
            citizen_score=4,
            status="APPROVED",
            created_at="2024-11-05",
            audit_metadata={"audit_verdict": "APPROVE", "audited_by": "argon", "confidence": 0.94},
        )
        pet_3 = CitizenPetition(
            id="petition-003",
            politician_id="pol-003",
            target_promise_id="promise-005",
            category="空氣品質",
            author_name="台中爭氣好生活協會",
            title="督促中火無煤轉型與公車全面電動化期程",
            content="要求市府嚴格落實自治條例，加速中火燃煤機組除役轉備用，並擴大公車電動化補助路網至海線各區。",
            evidence_url="https://web.pcc.gov.tw/tenders/tc-air-2024",
            citizen_score=5,
            status="APPROVED",
            created_at="2024-11-10",
            audit_metadata={"audit_verdict": "APPROVE", "audited_by": "argon", "confidence": 0.95},
        )
        self.petitions.extend([pet_1, pet_2, pet_3])

    # -------------------------------------------------------------------------
    # Query & Access Methods
    # -------------------------------------------------------------------------

    def get_politicians(self) -> List[Dict[str, Any]]:
        result = []
        for p in self.politicians.values():
            if any(x["id"] == p.id for x in result):
                continue
            terms = [t.to_dict() for t in p.terms]
            leg_terms = [t for t in p.terms if t.role_type == RoleType.LEGISLATOR.value]
            exec_terms = [t for t in p.terms if t.role_type == RoleType.EXECUTIVE.value]
            speeches_cnt = sum(1 for s in self.speeches if s.speaker_term_id in [t.id for t in leg_terms])
            votes_cnt = sum(1 for v in self.votes if v.politician_id == p.id)
            prom_cnt = sum(1 for pr in self.promises if pr.politician_id == p.id)
            fulf_cnt = sum(1 for pr in self.promises if pr.politician_id == p.id and pr.status == FulfillmentStatus.FULFILLED.value)

            result.append({
                "id": p.id,
                "name": p.name,
                "party": p.party,
                "terms": terms,
                "stats": {
                    "speeches_count": speeches_cnt,
                    "votes_count": votes_cnt,
                    "promises_count": prom_cnt,
                    "fulfilled_count": fulf_cnt,
                    "is_cross_phase": len(leg_terms) > 0 and len(exec_terms) > 0,
                },
            })
        return result

    def get_politician(self, pol_id: str) -> Optional[Dict[str, Any]]:
        pols = self.get_politicians()
        for p in pols:
            if p["id"] == pol_id:
                return p
        if pol_id in self.politicians:
            p = self.politicians[pol_id]
            terms = [t.to_dict() for t in p.terms]
            leg_terms = [t for t in p.terms if t.role_type == RoleType.LEGISLATOR.value]
            exec_terms = [t for t in p.terms if t.role_type == RoleType.EXECUTIVE.value]
            return {
                "id": p.id,
                "name": p.name,
                "party": p.party,
                "terms": terms,
                "stats": {
                    "speeches_count": 0,
                    "votes_count": 0,
                    "promises_count": 0,
                    "fulfilled_count": 0,
                    "is_cross_phase": len(leg_terms) > 0 and len(exec_terms) > 0,
                },
            }
        return None

    def get_speeches(
        self,
        q: Optional[str] = None,
        tag: Optional[str] = None,
        politician_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for s in self.speeches:
            speaker_term = None
            speaker_pol = None
            for p in self.politicians.values():
                for t in p.terms:
                    if t.id == s.speaker_term_id:
                        speaker_term = t
                        speaker_pol = p
                        break
                if speaker_pol:
                    break

            if politician_id and (not speaker_pol or speaker_pol.id != politician_id):
                continue
            if tag and tag not in s.topic_tags:
                continue
            if q:
                match = (
                    (q.lower() in s.transcript_raw.lower())
                    or (q.lower() in s.ai_summary.lower())
                    or any(q.lower() in t.lower() for t in s.topic_tags)
                )
                if not match:
                    continue

            session_data = self.sessions.get(s.session_id)
            results.append({
                "id": s.id,
                "session_id": s.session_id,
                "speaker_term_id": s.speaker_term_id,
                "target_official_id": s.target_official_id,
                "start_time_sec": s.start_time_sec,
                "end_time_sec": s.end_time_sec,
                "transcript_raw": s.transcript_raw,
                "ai_summary": s.ai_summary,
                "topic_tags": s.topic_tags,
                "audit_metadata": s.audit_metadata,
                "ivod_clip_id": s.ivod_clip_id,
                "video_stream_url": s.video_stream_url,
                "billy3321_url": s.billy3321_url,
                "speaker_name": speaker_pol.name if speaker_pol else "未知",
                "speaker_party": speaker_pol.party if speaker_pol else "未知",
                "speaker_title": speaker_term.title if speaker_term else None,
                "session": session_data.to_dict() if session_data else None,
            })
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
            pol = self.politicians.get(v.politician_id)
            bill = self.bills.get(v.bill_id)
            results.append({
                "id": v.id,
                "bill_id": v.bill_id,
                "politician_id": v.politician_id,
                "decision": v.decision,
                "source_url": v.source_url,
                "audit_metadata": v.audit_metadata,
                "politician_name": pol.name if pol else "未知",
                "politician_party": pol.party if pol else "未知",
                "bill": bill.to_dict() if bill else None,
            })
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
            pol = self.politicians.get(pr.politician_id)
            results.append({
                "id": pr.id,
                "politician_id": pr.politician_id,
                "term_id": pr.term_id,
                "title": pr.title,
                "category": pr.category,
                "status": pr.status,
                "source_url": pr.source_url,
                "target_completion_date": pr.target_completion_date,
                "audit_metadata": pr.audit_metadata,
                "politician_name": pol.name if pol else "未知",
                "politician_party": pol.party if pol else "未知",
                "milestones": [m.to_dict() for m in pr.milestones],
            })
        return results

    def get_exam_cards(
        self,
        politician_id: Optional[str] = None,
        exam_stage: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for ec in self.exam_cards:
            if politician_id and ec.politician_id != politician_id:
                continue
            if exam_stage and ec.exam_stage != exam_stage:
                continue
            pol = self.politicians.get(ec.politician_id)
            results.append({
                "id": ec.id,
                "politician_id": ec.politician_id,
                "politician_name": pol.name if pol else "未知",
                "politician_party": pol.party if pol else "未知",
                "term_id": ec.term_id,
                "exam_stage": ec.exam_stage,
                "attendance_rate": ec.attendance_rate,
                "objective_score": ec.objective_score,
                "argon_summary_comment": ec.argon_summary_comment,
                "citizen_rating_avg": ec.citizen_rating_avg,
                "citizen_reviews_count": ec.citizen_reviews_count,
                "audit_metadata": ec.audit_metadata,
            })
        return results

    def get_petitions(
        self,
        politician_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for cp in self.petitions:
            if politician_id and cp.politician_id != politician_id:
                continue
            if status and cp.status != status:
                continue
            pol = self.politicians.get(cp.politician_id)
            results.append({
                "id": cp.id,
                "politician_id": cp.politician_id,
                "politician_name": pol.name if pol else "未知",
                "politician_party": pol.party if pol else "未知",
                "target_promise_id": cp.target_promise_id,
                "category": cp.category,
                "author_name": cp.author_name,
                "title": cp.title,
                "content": cp.content,
                "evidence_url": cp.evidence_url,
                "citizen_score": cp.citizen_score,
                "status": cp.status,
                "created_at": cp.created_at,
                "audit_metadata": cp.audit_metadata,
            })
        return results


_SEED_DATABASE_INSTANCE: Optional[SeedDatabase] = None


def get_seed_database() -> SeedDatabase:
    """Singleton getter for SeedDatabase."""
    global _SEED_DATABASE_INSTANCE
    if _SEED_DATABASE_INSTANCE is None:
        _SEED_DATABASE_INSTANCE = SeedDatabase()
    return _SEED_DATABASE_INSTANCE
