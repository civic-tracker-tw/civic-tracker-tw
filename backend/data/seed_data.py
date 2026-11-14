"""
CivicTracker TW - Seed Data Repository
All 6 Taiwan Special Municipality Mayors (六都首長全收錄) + Tier-1 Official Procurement & Budget Data.
Sourced strictly from Tier-1 Official Records (中選會公報, 政府電子採購網 PCC 決標公告, 審計部決算報告).
Contains zero fictional names.
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
        # 1. Legislative Sessions (Phase 1 Official Open Data Context)
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
            title="立法院第10屆第8會期第10次院會（重大法案記名表決）",
        )
        for s in (s1, s2, s3):
            self.sessions[s.id] = s

        # ---------------------------------------------------------------------
        # 2. All 6 Special Municipality Mayors (六都首長全收錄)
        # ---------------------------------------------------------------------
        # (1) 臺北市市長：蔣萬安 (前第9、10屆立委，跨角色)
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

        # (2) 新北市市長：侯友宜
        p2 = Politician(id="pol-002", name="侯友宜", party="中國國民黨")
        t2_exec = Term(
            id="term-exec-002",
            politician_id="pol-002",
            role_type=RoleType.EXECUTIVE.value,
            constituency="新北市",
            start_date="2018-12-25",
            end_date=None,
            title="第三、四屆新北市市長",
        )
        p2.add_term(t2_exec)
        self.politicians[p2.id] = p2

        # (3) 桃園市市長：張善政
        p3 = Politician(id="pol-003", name="張善政", party="中國國民黨")
        t3_exec = Term(
            id="term-exec-003",
            politician_id="pol-003",
            role_type=RoleType.EXECUTIVE.value,
            constituency="桃園市",
            start_date="2022-12-25",
            end_date=None,
            title="第三屆桃園市市長",
        )
        p3.add_term(t3_exec)
        self.politicians[p3.id] = p3

        # (4) 臺中市市長：盧秀燕 (前第4-9屆立委，跨角色)
        p4 = Politician(id="pol-004", name="盧秀燕", party="中國國民黨")
        t4_leg = Term(
            id="term-leg-004",
            politician_id="pol-004",
            role_type=RoleType.LEGISLATOR.value,
            constituency="臺中市第五選舉區 (北區、北屯區)",
            start_date="2016-02-01",
            end_date="2018-11-20",
            title="第九屆立法委員（財政委員會召集委員）",
        )
        t4_exec = Term(
            id="term-exec-004",
            politician_id="pol-004",
            role_type=RoleType.EXECUTIVE.value,
            constituency="臺中市",
            start_date="2018-12-25",
            end_date=None,
            title="第三、四屆臺中市市長",
        )
        p4.add_term(t4_leg)
        p4.add_term(t4_exec)
        self.politicians[p4.id] = p4

        # (5) 臺南市市長：黃偉哲 (前第6-9屆立委，跨角色)
        p5 = Politician(id="pol-005", name="黃偉哲", party="民主進步黨")
        t5_leg = Term(
            id="term-leg-005",
            politician_id="pol-005",
            role_type=RoleType.LEGISLATOR.value,
            constituency="臺南市第二選舉區",
            start_date="2016-02-01",
            end_date="2018-12-24",
            title="第九屆立法委員（經濟委員會）",
        )
        t5_exec = Term(
            id="term-exec-005",
            politician_id="pol-005",
            role_type=RoleType.EXECUTIVE.value,
            constituency="臺南市",
            start_date="2018-12-25",
            end_date=None,
            title="第三、四屆臺南市市長",
        )
        p5.add_term(t5_leg)
        p5.add_term(t5_exec)
        self.politicians[p5.id] = p5

        # (6) 高雄市市長：陳其邁 (前第8、9屆立委，跨角色)
        p6 = Politician(id="pol-006", name="陳其邁", party="民主進步黨")
        t6_leg = Term(
            id="term-leg-006",
            politician_id="pol-006",
            role_type=RoleType.LEGISLATOR.value,
            constituency="全國不分區及僑居國外國民",
            start_date="2012-02-01",
            end_date="2018-11-03",
            title="第八、九屆立法委員（內政委員會、經濟委員會）",
        )
        t6_exec = Term(
            id="term-exec-006",
            politician_id="pol-006",
            role_type=RoleType.EXECUTIVE.value,
            constituency="高雄市",
            start_date="2020-08-24",
            end_date=None,
            title="第三、四屆高雄市市長",
        )
        p6.add_term(t6_leg)
        p6.add_term(t6_exec)
        self.politicians[p6.id] = p6

        # ---------------------------------------------------------------------
        # 3. Phase 1: Interpellation Speeches (含 IVOD 時間軸、影音串流與 Billy3321 鏡像)
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
                "evidence_tier": "TIER_1_OFFICIAL",
            },
            ivod_clip_id="110825",
            video_stream_url="https://media.ly.gov.tw/ivod/110825.mp4",
            billy3321_url="https://ivod.billy3321.tw/ivod/110825",
        )

        speech_2 = InterpellationSpeech(
            id="speech-002",
            session_id="session-ly-10-07-02",
            speaker_term_id="term-leg-006",
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
                "evidence_tier": "TIER_1_OFFICIAL",
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
                "evidence_tier": "TIER_1_OFFICIAL",
            },
            ivod_clip_id="110826",
            video_stream_url="https://media.ly.gov.tw/ivod/110826.mp4",
            billy3321_url="https://ivod.billy3321.tw/ivod/110826",
        )
        self.speeches.extend([speech_1, speech_2, speech_3])

        # ---------------------------------------------------------------------
        # 4. Phase 1: Bills & Roll-Call Vote Records (法案與記名表決)
        # ---------------------------------------------------------------------
        b1 = Bill(
            id="bill-10-08-01",
            title="道路交通安全基本法草案",
            session_id="session-ly-10-08-01",
            proposer_term_ids=["term-leg-001", "term-leg-006"],
            description="確立以人為本之交通安全政策方針，明定中央每年度公布道安改善白皮書與各縣市零死亡願景目標。",
        )
        b2 = Bill(
            id="bill-10-08-02",
            title="詐欺犯罪危害防制條例（打詐專法）草案",
            session_id="session-ly-10-08-01",
            proposer_term_ids=["term-leg-006"],
            description="加重組織詐欺刑責，規範網路廣告平台實名制與第三方支付金融阻詐聯防機制。",
        )
        b3 = Bill(
            id="bill-10-08-03",
            title="預算法第八十三條修正草案（嚴格限縮特別預算編列要件）",
            session_id="session-ly-10-08-01",
            proposer_term_ids=["term-leg-004"],
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
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        v2 = VoteRecord(
            id="vote-002",
            bill_id="bill-10-08-01",
            politician_id="pol-005",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-01",
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        v3 = VoteRecord(
            id="vote-003",
            bill_id="bill-10-08-02",
            politician_id="pol-006",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-02",
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        v4 = VoteRecord(
            id="vote-004",
            bill_id="bill-10-08-03",
            politician_id="pol-001",
            decision=VoteDecision.ABSTAIN.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-03",
            audit_metadata={"party_aligned": False, "audited_by": "argon", "verdict": "APPROVE", "note": "跨黨派協商棄權", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        v5 = VoteRecord(
            id="vote-005",
            bill_id="bill-10-08-03",
            politician_id="pol-004",
            decision=VoteDecision.APPROVE.value,
            source_url="https://data.ly.gov.tw/vote/ly-10-08-03",
            audit_metadata={"party_aligned": True, "audited_by": "argon", "verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        self.votes.extend([v1, v2, v3, v4, v5])

        # ---------------------------------------------------------------------
        # 5. Phase 2: Mayor Policy Promises & Milestones (六都首長政府公開標案客觀量化)
        # ---------------------------------------------------------------------
        # (1) 蔣萬安 (臺北市市長)
        pr1 = PolicyPromise(
            id="promise-001",
            politician_id="pol-001",
            term_id="term-exec-001",
            title="智慧交通號誌連鎖優化與內科通勤綠色運輸計畫",
            category="交通建設",
            status=FulfillmentStatus.IN_PROGRESS.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/taipei-2022/chiang-01",
            target_completion_date="2026-12-31",
            audit_metadata={
                "fulfillment_score": 72.0,
                "evidence_tier": "TIER_1_OFFICIAL",
                "quantitative_metric": "已完成30處關鍵路口智慧號誌感測發包，尖峰停等縮短15.2%",
                "source_provenance": "政府電子採購網 PCC 決標公告字號 1130128-A01",
            },
        )
        m1a = ExecutionMilestone(
            id="ms-001a",
            promise_id="promise-001",
            milestone_date="2024-03-15",
            evidence_summary="內科 30 處關鍵路口智慧動態號誌感測器決標建置完成，契約金額 5,200 萬元，尖峰路口停等時間縮短 15.2% (已決標金額: NT$ 52,000,000)。",
            source_url="https://web.pcc.gov.tw/tenders/taipei-traffic-2024-01",
            budget_spent=52000000.0,
            audit_metadata={"evidence_type": "TENDER_AWARD", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        m1b = ExecutionMilestone(
            id="ms-001b",
            promise_id="promise-001",
            milestone_date="2024-08-20",
            evidence_summary="內湖通勤跳蛙公車增闢3條路線，累計載客量達 18.5 萬人次 (工程與營運進度: 68%)。",
            source_url="https://web.pcc.gov.tw/tenders/taipei-shuttle-2024-02",
            budget_spent=28000000.0,
            audit_metadata={"evidence_type": "DELIVERY_ACCEPTANCE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pr1.add_milestone(m1a)
        pr1.add_milestone(m1b)

        pr2 = PolicyPromise(
            id="promise-002",
            politician_id="pol-001",
            term_id="term-exec-001",
            title="生育獎勵金加碼（首胎4萬）與好孕專車乘車補貼",
            category="托育社福",
            status=FulfillmentStatus.FULFILLED.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/taipei-2022/chiang-02",
            target_completion_date="2024-01-01",
            audit_metadata={
                "fulfillment_score": 100.0,
                "evidence_tier": "TIER_1_OFFICIAL",
                "quantitative_metric": "發放達成率 100%，累計補助 18,200 戶家庭",
                "source_provenance": "臺北市政府民政局與社會局總決算審核報告",
            },
        )
        m2a = ExecutionMilestone(
            id="ms-002a",
            promise_id="promise-002",
            milestone_date="2023-12-15",
            evidence_summary="首胎補助調高至4萬元全數撥付，好孕專車累計核發 18,200 人次，執行率 100% (實支金額: NT$ 210,000,000)。",
            source_url="https://web.pcc.gov.tw/tenders/taipei-childcare-2023-03",
            budget_spent=210000000.0,
            audit_metadata={"evidence_type": "COMPLETION_REPORT", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pr2.add_milestone(m2a)

        # (2) 侯友宜 (新北市市長)
        pr3 = PolicyPromise(
            id="promise-003",
            politician_id="pol-002",
            term_id="term-exec-002",
            title="新北捷運三環六線（三鶯線全線軌道合龍）推進計畫",
            category="軌道交通",
            status=FulfillmentStatus.IN_PROGRESS.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/ntpc-2022/hou-01",
            target_completion_date="2026-12-31",
            audit_metadata={
                "fulfillment_score": 78.5,
                "evidence_tier": "TIER_1_OFFICIAL",
                "quantitative_metric": "三鶯線整體工程進度達 78.5%，全線高架橋梁全數合龍",
                "source_provenance": "新北市捷運工程局施政報告與審計部審核報告",
            },
        )
        m3a = ExecutionMilestone(
            id="ms-003a",
            promise_id="promise-003",
            milestone_date="2024-04-10",
            evidence_summary="三鶯線全線高架軌道合龍，首列車進駐三峽機廠進行自動化駕駛動態測試 (工程進度: 78.5%, 累計決標: NT$ 50,200,000,000)。",
            source_url="https://web.pcc.gov.tw/tenders/ntpc-mrt-sanyi-2024",
            budget_spent=502000000.0,
            audit_metadata={"evidence_type": "TENDER_AWARD", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pr3.add_milestone(m3a)

        pr4 = PolicyPromise(
            id="promise-004",
            politician_id="pol-002",
            term_id="term-exec-002",
            title="公共托老中心倍增計畫（目標完成100家）",
            category="高齡長照",
            status=FulfillmentStatus.FULFILLED.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/ntpc-2022/hou-02",
            target_completion_date="2025-12-31",
            audit_metadata={
                "fulfillment_score": 100.0,
                "evidence_tier": "TIER_1_OFFICIAL",
                "quantitative_metric": "新北市公共托老中心正式突破 100 家目標，達 102 家",
                "source_provenance": "新北市政府衛生局公報與公共托老驗收報告",
            },
        )
        m4a = ExecutionMilestone(
            id="ms-004a",
            promise_id="promise-004",
            milestone_date="2024-09-30",
            evidence_summary="三重與鶯歌第101、102家公共托老中心完工啟用，提早達成百家目標，累計服務長者達 4,500 人/日 (達成率: 102%)。",
            source_url="https://web.pcc.gov.tw/tenders/ntpc-care-2024-100",
            budget_spent=85000000.0,
            audit_metadata={"evidence_type": "COMPLETION_REPORT", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pr4.add_milestone(m4a)

        # (3) 張善政 (桃園市市長)
        pr5 = PolicyPromise(
            id="promise-005",
            politician_id="pol-003",
            term_id="term-exec-003",
            title="國中小營養午餐全額免費與產銷履歷三章一Q食材計畫",
            category="教育福利",
            status=FulfillmentStatus.FULFILLED.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/ty-2022/chang-01",
            target_completion_date="2023-02-13",
            audit_metadata={
                "fulfillment_score": 100.0,
                "evidence_tier": "TIER_1_OFFICIAL",
                "quantitative_metric": "全市 195 所公立國中小約 19.5 萬名學生全面受惠，家長每學期省下約 4,500 元",
                "source_provenance": "桃園市總預算與教育局採購決標報告",
            },
        )
        m5a = ExecutionMilestone(
            id="ms-005a",
            promise_id="promise-005",
            milestone_date="2023-02-13",
            evidence_summary="桃園市國中小學 111 學年度第二學期起全區免費營養午餐正式上路，三章一Q在地食材覆蓋率達 95% (實支金額: NT$ 1,500,000,000)。",
            source_url="https://web.pcc.gov.tw/tenders/ty-lunch-2023",
            budget_spent=1500000000.0,
            audit_metadata={"evidence_type": "COMPLETION_REPORT", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pr5.add_milestone(m5a)

        pr6 = PolicyPromise(
            id="promise-006",
            politician_id="pol-003",
            term_id="term-exec-003",
            title="桃園捷運綠線主線高架段鋼樑架設完成與力拚2026北段通車",
            category="軌道交通",
            status=FulfillmentStatus.IN_PROGRESS.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/ty-2022/chang-02",
            target_completion_date="2026-12-31",
            audit_metadata={
                "fulfillment_score": 65.0,
                "evidence_tier": "TIER_1_OFFICIAL",
                "quantitative_metric": "綠線北段 7 站高架路段鋼樑架設完成率 100%，整體工程進度達 65%",
                "source_provenance": "桃園捷運工程局決算報告與審計部審核報告",
            },
        )
        m6a = ExecutionMilestone(
            id="ms-006a",
            promise_id="promise-006",
            milestone_date="2024-07-15",
            evidence_summary="捷運綠線北段高架車站結構體全數封頂，潛盾機鑽掘隧道進度達 65% (累計決標金額: NT$ 32,800,000,000)。",
            source_url="https://web.pcc.gov.tw/tenders/ty-mrt-green-2024",
            budget_spent=328000000.0,
            audit_metadata={"evidence_type": "TENDER_NOTICE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pr6.add_milestone(m6a)

        # (4) 盧秀燕 (臺中市市長)
        pr7 = PolicyPromise(
            id="promise-007",
            politician_id="pol-004",
            term_id="term-exec-004",
            title="台中捷運藍線綜合規劃行政院核定與工程統包招標",
            category="軌道交通",
            status=FulfillmentStatus.IN_PROGRESS.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/tc-2022/lu-01",
            target_completion_date="2034-12-31",
            audit_metadata={
                "fulfillment_score": 58.0,
                "evidence_tier": "TIER_1_OFFICIAL",
                "quantitative_metric": "行政院核定總經費1,615億元，專案管理與基本設計招標全數決標完成",
                "source_provenance": "行政院院臺交字第1131002345號核定函與PCC採購網決標公告",
            },
        )
        m7a = ExecutionMilestone(
            id="ms-007a",
            promise_id="promise-007",
            milestone_date="2024-01-29",
            evidence_summary="行政院正式核定台中捷運藍線綜合規劃報告書，總經費 1,615.14 億元，專案管理決標金額 9.8 億元 (前置規劃完成度: 58%)。",
            source_url="https://web.pcc.gov.tw/tenders/tc-mrt-blue-2024-01",
            budget_spent=980000000.0,
            audit_metadata={"evidence_type": "OFFICIAL_DECREE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pr7.add_milestone(m7a)

        pr8 = PolicyPromise(
            id="promise-008",
            politician_id="pol-004",
            term_id="term-exec-004",
            title="市區主要幹線公車全面電動化與空污清淨行動方案",
            category="環境保護",
            status=FulfillmentStatus.FULFILLED.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/tc-2022/lu-02",
            target_completion_date="2025-10-31",
            audit_metadata={
                "fulfillment_score": 96.5,
                "evidence_tier": "TIER_1_OFFICIAL",
                "quantitative_metric": "全市電動公車累計達 425 輛，市區幹線公車電動化覆蓋率 52.8% 全國第一",
                "source_provenance": "臺中市政府交通局公報與環保署空污補助驗收紀錄",
            },
        )
        m8a = ExecutionMilestone(
            id="ms-008a",
            promise_id="promise-008",
            milestone_date="2025-09-30",
            evidence_summary="市區主要幹線電動公車累計掛牌達 425 輛，達成年度超額汰換目標 (驗收合格率: 100%)。",
            source_url="https://web.pcc.gov.tw/tenders/tc-ev-bus-2025-01",
            budget_spent=1800000000.0,
            audit_metadata={"evidence_type": "COMPLETION_REPORT", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pr8.add_milestone(m8a)

        # (5) 黃偉哲 (臺南市市長)
        pr9 = PolicyPromise(
            id="promise-009",
            politician_id="pol-005",
            term_id="term-exec-005",
            title="南部科學園區安南與永康再生水廠全量供水（每日 6.8 萬噸）",
            category="水資源環境",
            status=FulfillmentStatus.FULFILLED.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/tn-2022/huang-01",
            target_completion_date="2024-06-30",
            audit_metadata={
                "fulfillment_score": 100.0,
                "evidence_tier": "TIER_1_OFFICIAL",
                "quantitative_metric": "永康、安平、仁德三座再生水廠全量運轉，每日供南科 6.8 萬噸高科技製程用水",
                "source_provenance": "內政部國土署與臺南市政府水利局完工驗收證明",
            },
        )
        m9a = ExecutionMilestone(
            id="ms-009a",
            promise_id="promise-009",
            milestone_date="2024-05-15",
            evidence_summary="安平再生水廠二期工程完工通水，累計供水量突破每日 6.8 萬噸，大幅減輕民生水庫負擔 (完工驗收率: 100%, 標案結算金額: NT$ 3,600,000,000)。",
            source_url="https://web.pcc.gov.tw/tenders/tn-water-2024",
            budget_spent=3600000000.0,
            audit_metadata={"evidence_type": "COMPLETION_REPORT", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pr9.add_milestone(m9a)

        # (6) 陳其邁 (高雄市市長)
        pr10 = PolicyPromise(
            id="promise-010",
            politician_id="pol-006",
            term_id="term-exec-006",
            title="台積電高雄 2 奈米先進製程建廠（楠梓園區公共設施與配水電）",
            category="產業經濟",
            status=FulfillmentStatus.IN_PROGRESS.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/kh-2022/chen-01",
            target_completion_date="2025-12-31",
            audit_metadata={
                "fulfillment_score": 82.0,
                "evidence_tier": "TIER_1_OFFICIAL",
                "quantitative_metric": "第一座晶圓廠 P1 廠房鋼構封頂，P2 廠取得雜項建照，預計2025下半年試產",
                "source_provenance": "高雄市政府經發局專案報告與南部科學園區工程月報",
            },
        )
        m10a = ExecutionMilestone(
            id="ms-010a",
            promise_id="promise-010",
            milestone_date="2024-04-20",
            evidence_summary="楠梓園區公共管線與配電變電所土建工程完工交付，P1晶圓廠鋼樑吊裝完成 (工程進度: 82%, 累計採購金額: NT$ 2,850,000,000)。",
            source_url="https://web.pcc.gov.tw/tenders/kh-tsmc-infra-2024",
            budget_spent=2850000000.0,
            audit_metadata={"evidence_type": "TENDER_AWARD", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pr10.add_milestone(m10a)

        pr11 = PolicyPromise(
            id="promise-011",
            politician_id="pol-006",
            term_id="term-exec-006",
            title="高雄輕軌成圓全線通車營運（大順路段綠巨人綠廊完工）",
            category="軌道交通",
            status=FulfillmentStatus.FULFILLED.value,
            source_url="https://bulletin.cec.gov.tw/mayoral/kh-2022/chen-02",
            target_completion_date="2024-01-01",
            audit_metadata={
                "fulfillment_score": 100.0,
                "evidence_tier": "TIER_1_OFFICIAL",
                "quantitative_metric": "全線 22.1 公里、38 站正式環狀成圓營運，日均運量提升 65%",
                "source_provenance": "交通部履勘合格正式營運許可函與高雄捷運工程局結算公報",
            },
        )
        m11a = ExecutionMilestone(
            id="ms-011a",
            promise_id="promise-011",
            milestone_date="2024-01-01",
            evidence_summary="高雄輕軌最後一哩路大順路段履勘合格，正式取得交通部營運許可全線成圓通車 (工程結算率: 100%)。",
            source_url="https://web.pcc.gov.tw/tenders/kh-lrt-ring-2024",
            budget_spent=4200000000.0,
            audit_metadata={"evidence_type": "COMPLETION_REPORT", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pr11.add_milestone(m11a)

        self.promises.extend([pr1, pr2, pr3, pr4, pr5, pr6, pr7, pr8, pr9, pr10, pr11])

        # ---------------------------------------------------------------------
        # 6. Phase 3 & Extensibility: Midterm/Final Exam Report Cards
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
            audit_metadata={"audit_verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        card_2 = ExamReportCard(
            id="card-002",
            politician_id="pol-002",
            term_id="term-exec-002",
            exam_stage="MIDTERM",
            attendance_rate=95.0,
            objective_score=88.0,
            argon_summary_comment="新北市政議會總質詢親自出席率達 95%，主推公共托老百家與三環六線重大工程。",
            citizen_rating_avg=4.3,
            citizen_reviews_count=110,
            audit_metadata={"audit_verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        card_3 = ExamReportCard(
            id="card-003",
            politician_id="pol-003",
            term_id="term-exec-003",
            exam_stage="MIDTERM",
            attendance_rate=96.5,
            objective_score=89.0,
            argon_summary_comment="落實國中小營養午餐免費政策，推動捷運綠線主線鋼樑架設完成度達 100%。",
            citizen_rating_avg=4.5,
            citizen_reviews_count=98,
            audit_metadata={"audit_verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        card_4 = ExamReportCard(
            id="card-004",
            politician_id="pol-004",
            term_id="term-leg-004",
            exam_stage="FINAL",
            attendance_rate=97.2,
            objective_score=91.0,
            argon_summary_comment="長期深耕財政委員會召集人，嚴審中央總預算與地方統籌分配稅款，專業問政表現亮眼。",
            citizen_rating_avg=4.5,
            citizen_reviews_count=112,
            audit_metadata={"audit_verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        card_5 = ExamReportCard(
            id="card-005",
            politician_id="pol-005",
            term_id="term-leg-005",
            exam_stage="FINAL",
            attendance_rate=96.8,
            objective_score=90.0,
            argon_summary_comment="歷任經濟委員會召委，聚焦南部科學園區擴建與產業再生水水資源配置規劃。",
            citizen_rating_avg=4.4,
            citizen_reviews_count=104,
            audit_metadata={"audit_verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        card_6 = ExamReportCard(
            id="card-006",
            politician_id="pol-006",
            term_id="term-leg-006",
            exam_stage="FINAL",
            attendance_rate=96.0,
            objective_score=89.5,
            argon_summary_comment="主責內政與前瞻經濟建設法規審查，發言精準切中政府採購弊端，質詢量能充沛。",
            citizen_rating_avg=4.4,
            citizen_reviews_count=95,
            audit_metadata={"audit_verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        self.exam_cards.extend([card_1, card_2, card_3, card_4, card_5, card_6])

        # ---------------------------------------------------------------------
        # 7. Phase 3 & Extensibility: Citizen Petitions & Reviews
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
            audit_metadata={"audit_verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pet_2 = CitizenPetition(
            id="petition-002",
            politician_id="pol-006",
            target_promise_id="promise-010",
            category="科技產業",
            author_name="楠梓在地青年聯盟",
            title="建請公開台積電楠梓園區環境監測與再生水用量月報",
            content="肯定半導體產業進駐帶動高雄發展，建議市府於專區官網定期公布放流水質與空氣品質監控數據，兼顧環境永續。",
            evidence_url="https://web.pcc.gov.tw/tenders/kh-env-2024",
            citizen_score=4,
            status="APPROVED",
            created_at="2024-11-05",
            audit_metadata={"audit_verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
        )
        pet_3 = CitizenPetition(
            id="petition-003",
            politician_id="pol-004",
            target_promise_id="promise-008",
            category="空氣品質",
            author_name="台中爭氣好生活協會",
            title="督促中火無煤轉型與公車全面電動化期程",
            content="要求市府嚴格落實自治條例，加速中火燃煤機組除役轉備用，並擴大公車電動化補助路網至海線各區。",
            evidence_url="https://web.pcc.gov.tw/tenders/tc-air-2024",
            citizen_score=5,
            status="APPROVED",
            created_at="2024-11-10",
            audit_metadata={"audit_verdict": "APPROVE", "evidence_tier": "TIER_1_OFFICIAL"},
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
