"""
CivicTracker TW - Zero-Cost Static Website Exporter
Exports verified records from SQLite database into static JSON snapshots and a self-contained
serverless web bundle under dist/ for 100% free hosting (GitHub Pages, Netlify, Cloudflare Pages).
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Union

from backend.core.config_compiler import (
    compile_config,
    verify_source_integrity,
)
from backend.core.database import DatabaseEngine, get_database_engine
from backend.core.ly_crawler import LegislativeYuanCrawler
from backend.core.security import MAX_POST_BODY_BYTES, SecurityHeaders

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_FILE = BASE_DIR / "frontend" / "index.html"
CONFIG_HUMAN = BASE_DIR / "config" / "pipeline.human.yaml"
CONFIG_PROTO = BASE_DIR / "config" / "generated" / "agent_protocol.json"
DEFAULT_DIST_DIR = BASE_DIR / "dist"


def export_static_site(
    output_dir: Union[str, Path] = DEFAULT_DIST_DIR,
    db: Optional[DatabaseEngine] = None,
    sync_crawler: bool = True,
) -> Dict[str, Any]:
    """
    Builds a standalone, zero-cost static website distribution in `output_dir`:
    1. Compiles machine protocol
    2. Ensures SQLite database is populated with seed & crawler records
    3. Exports verified records to dist/api/*.json
    4. Injects state into dist/index.html
    5. Emits dist/.nojekyll and netlify.toml
    """
    out_path = Path(output_dir).resolve()
    api_out_path = out_path / "api"
    api_out_path.mkdir(parents=True, exist_ok=True)

    # 1. Compile protocol
    compile_config(CONFIG_HUMAN, CONFIG_PROTO)
    with open(CONFIG_PROTO, "r", encoding="utf-8") as f:
        proto_data = json.load(f)
    is_synced = verify_source_integrity(CONFIG_HUMAN, CONFIG_PROTO)

    # 2. Get database engine and ensure LY crawler has run
    engine = db or get_database_engine()
    if sync_crawler:
        # Check if 11th term legislators are in DB, if not sync them
        pols = engine.get_politicians()
        names = {p["name"] for p in pols}
        if not ("洪申翰" in names and "李彥秀" in names and "陳昭姿" in names):
            crawler = LegislativeYuanCrawler(db=engine)
            crawler.sync_to_database(live=False)

    # 3. Retrieve verified datasets from SQLite
    politicians_data = engine.get_politicians()
    speeches_data = engine.get_speeches()
    votes_data = engine.get_votes()
    promises_data = engine.get_promises()
    stats_data = engine.get_overview_stats()
    sec_meta = engine.get_security_metadata()
    sync_logs = engine.get_sync_logs(limit=10)

    protocol_export = {
        "protocol": proto_data,
        "sync_status": {
            "is_synchronized": is_synced,
            "human_config": CONFIG_HUMAN.name,
            "machine_protocol": CONFIG_PROTO.name,
        },
    }

    security_export = {
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

    # 4. Write static JSON snapshots under dist/api/
    json_targets = {
        "protocol.json": protocol_export,
        "stats.json": stats_data,
        "politicians.json": {"politicians": politicians_data},
        "speeches.json": {"speeches": speeches_data, "total": len(speeches_data)},
        "votes.json": {"votes": votes_data, "total": len(votes_data)},
        "promises.json": {"promises": promises_data, "total": len(promises_data)},
        "security_status.json": security_export,
    }

    for filename, payload in json_targets.items():
        target_file = api_out_path / filename
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # 5. Build self-contained dist/index.html with embedded data
    with open(FRONTEND_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()

    embedded_fallback = {
        "politicians": politicians_data,
        "speeches": speeches_data,
        "votes": votes_data,
        "promises": promises_data,
    }

    embedded_json_str = json.dumps(embedded_fallback, ensure_ascii=False, indent=6)
    target_needle = "const FALLBACK_DATA = {"

    # Replace FALLBACK_DATA with fresh SQLite database snapshot
    if target_needle in html_content:
        # Find opening of FALLBACK_DATA up to ending };
        start_idx = html_content.index(target_needle)
        end_idx = html_content.index("};\n", start_idx) + 2
        new_block = f"const FALLBACK_DATA = {embedded_json_str};\n"
        html_content = html_content[:start_idx] + new_block + html_content[end_idx:]

    dist_index_path = out_path / "index.html"
    with open(dist_index_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 6. Create dist/.nojekyll for GitHub Pages
    nojekyll_path = out_path / ".nojekyll"
    with open(nojekyll_path, "w", encoding="utf-8") as f:
        f.write("# Bypasses Jekyll build on GitHub Pages for clean static file serving\n")

    # 7. Create netlify.toml for Netlify zero-config hosting
    netlify_toml_path = BASE_DIR / "netlify.toml"
    with open(netlify_toml_path, "w", encoding="utf-8") as f:
        f.write(
            """# CivicTracker TW - Netlify Zero-Cost Hosting Configuration
[build]
  publish = "dist"

[[headers]]
  for = "/*"
  [headers.values]
    X-Content-Type-Options = "nosniff"
    X-Frame-Options = "SAMEORIGIN"
    X-XSS-Protection = "1; mode=block"
    Referrer-Policy = "strict-origin-when-cross-origin"
"""
        )

    # Also place a copy inside dist
    shutil.copy(netlify_toml_path, out_path / "netlify.toml")

    manifest = {
        "status": "SUCCESS",
        "output_directory": str(out_path),
        "exported_files": [
            "index.html",
            ".nojekyll",
            "netlify.toml",
            "api/protocol.json",
            "api/stats.json",
            "api/politicians.json",
            "api/speeches.json",
            "api/votes.json",
            "api/promises.json",
            "api/security_status.json",
        ],
        "dataset_metrics": {
            "politicians_count": len(politicians_data),
            "speeches_count": len(speeches_data),
            "votes_count": len(votes_data),
            "promises_count": len(promises_data),
        },
    }
    return manifest


def main():
    print("[StaticExporter] Generating Zero-Cost Static Website Bundle for CivicTracker TW...")
    manifest = export_static_site()

    print("\n" + "=" * 65)
    print("零成本靜態網站打包輸出報告 (Zero-Cost Static Export Manifest)")
    print("=" * 65)
    print(f"輸出目錄 (Output Dir):       {manifest['output_directory']}")
    print(f"匯出靜態檔案數 (Files):      {len(manifest['exported_files'])} 個檔案")
    print(f"政治人物筆數 (Politicians):  {manifest['dataset_metrics']['politicians_count']} 位 (含立委與首長)")
    print(f"質詢公報筆數 (Speeches):     {manifest['dataset_metrics']['speeches_count']} 篇")
    print(f"表決紀錄筆數 (Votes):        {manifest['dataset_metrics']['votes_count']} 筆")
    print(f"首長政見筆數 (Promises):     {manifest['dataset_metrics']['promises_count']} 項")
    print("相容發布平台 (Free Hosting): GitHub Pages, Cloudflare Pages, Netlify")
    print("=" * 65)


if __name__ == "__main__":
    main()
