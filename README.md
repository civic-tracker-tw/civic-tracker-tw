# CivicTracker TW — 國會／議會監督與首長政見追蹤平台

本專案旨在建立一個結構化、可溯源的政治人物監督平台：
* **Phase 1（國會／地方議會監督）**：追蹤立法委員與縣市議員之院會／委員會出席率、質詢逐字稿（對齊 IVOD 影音時間軸）、法案提案連署與記名表決紀錄。
* **Phase 2（市長／行政首長政見追蹤）**：結構化拆解競選公報與施政報告承諾，串接預算書、政府採購標案與議會質詢紀錄，追蹤實際執行成果與兌現度。

---

## 核心特色：雙層 Config 與雙模型協作 (Hydrogen × Argon)

本系統在**開發階段（Antigravity 多代理協作）**與**資料管線執行階段（Runtime AI Pipeline）**皆採用雙模型協作模式：

1. **人類維護版設定檔 (Human-Facing Config)**：
   * 路徑：[`config/pipeline.human.yaml`](./config/pipeline.human.yaml)
   * 包含完整的繁體中文商業邏輯註解、模型分工角色、品質門檻（Quality Gates）與資料源定義。**人類開發者只需修改此檔案**。
2. **模型溝通與協定版 (Model-to-Model Protocol Config)**：
   * 路徑：`config/generated/agent_protocol.json`（由編譯器自動生成，請勿手動修改）
   * 去除冗餘註解，將規則轉換為高密度代號、嚴格 Enum 與 JSON Schema，供 **Hydrogen（高速執行者）** 與 **Argon（決策與錯誤評估者）** 之間進行低 Token 消耗、零歧義的任務交接與退件修正。

---

## 目錄結構

```text
civic-tracker/
├── README.md                          # 專案說明文件（人類閱讀）
├── AGENTS.md                          # Antigravity 代理協作協定（模型閱讀）
├── Dockerfile                         # 零依賴容器化部署設定
├── railway.json                       # Railway 雲端一鍵部署組態
├── config/
│   ├── pipeline.human.yaml            # [人類維護] 雙模型分工、品質門檻與資料源設定
│   └── generated/
│       └── agent_protocol.json        # [自動編譯] 供 Hydrogen <-> Argon 溝通之緊湊協定與 Schema
├── data/
│   └── civic_tracker.db               # [SQLite 生產資料庫] WAL 事務模式、外鍵約束與 100% 參數化查詢
├── frontend/
│   └── index.html                     # 現代化響應式單頁應用 (SPA)、AI 雙模型協作室與資安同步面板
└── backend/
    ├── web_server.py                  # 標準庫零依賴 HTTP & REST API 網頁伺服器 (含 OWASP 防護)
    ├── core/
    │   ├── config_compiler.py         # 將 pipeline.human.yaml 驗證並編譯為 agent_protocol.json
    │   ├── database.py                # 生產級 SQLite 資料庫引擎 (WAL 模式、規範化 Schema、防止注入)
    │   ├── ly_crawler.py              # 立法院開放資料 (data.ly.gov.tw) 爬蟲與 DualModelPipeline 審查管線
    │   ├── model_router.py            # Hydrogen 執行 × Argon 錯誤評估與自癒重試調度器
    │   ├── security.py                # OWASP 資安標頭、IP 滑動窗口限流、64KB 封包防護、常數時間鑑權
    │   └── yaml_parser.py             # 純 Python 輕量級 YAML 解析器 (PyYAML 零依賴後備)
    ├── data/
    │   └── seed_data.py               # 台灣立法院與縣市長真實語料資料庫 (跨 Phase 人物、逐字稿、標案)
    ├── models/
    │   └── domain.py                  # 核心領域模型（支援議員監督 Phase 1 與首長政見 Phase 2）
    └── tests/
        ├── test_config_and_pipeline.py # Config 編譯、哈希防漂移與雙模型退件自癒單元測試
        ├── test_security_and_crawler.py # SQL 注入免疫、限流阻擋、資安標頭、時序安全與爬蟲端到端測試
        └── test_web_server.py         # Web Server REST API 與互動模擬沙盒測試
```

## 快速指令

```powershell
# 1. 編譯人類版 YAML 設定檔為模型溝通 JSON 協定
python -m backend.core.config_compiler

# 2. 執行立法院開放資料 (data.ly.gov.tw) 爬蟲與 AI 雙模型審查同步
python -m backend.core.ly_crawler

# 3. 啟動本機全端網頁伺服器（開啟瀏覽器訪問 http://localhost:8080/）
python -m backend.web_server --port 8080

# 4. 執行全套自動化單元、資安與整合測試（36 項測試全部通過）
python -m unittest discover -s backend/tests -v
```
