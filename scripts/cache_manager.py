#!/usr/bin/env python3
"""
crawl_cache.db 管理器 — 三层去重的第一层
负责本地 SQLite 缓存，避免对已见过的 URL 反复抓取详情。
"""

import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "crawl_cache.db"


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS crawl_cache (
            url_hash       TEXT PRIMARY KEY,
            url            TEXT NOT NULL,
            source         TEXT NOT NULL,
            title          TEXT,
            company        TEXT,
            first_seen     TEXT NOT NULL,
            last_seen      TEXT NOT NULL,
            detail_fetched INTEGER DEFAULT 0,
            detail_json    TEXT,
            expired        INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON crawl_cache(source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_expired ON crawl_cache(expired)")
    conn.commit()
    return conn


def url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().encode()).hexdigest()


def check_urls(urls: list[dict]) -> dict:
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    new_items, seen_items = [], []
    for item in urls:
        h = url_hash(item["url"])
        row = conn.execute("SELECT * FROM crawl_cache WHERE url_hash = ?", (h,)).fetchone()
        if row:
            conn.execute(
                "UPDATE crawl_cache SET last_seen = ?, title = COALESCE(?, title), "
                "company = COALESCE(?, company) WHERE url_hash = ?",
                (now, item.get("title"), item.get("company"), h),
            )
            seen_items.append(item)
        else:
            conn.execute(
                "INSERT INTO crawl_cache (url_hash, url, source, title, company, first_seen, last_seen) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (h, item["url"], item.get("source", "unknown"), item.get("title"), item.get("company"), now, now),
            )
            new_items.append(item)
    conn.commit()
    conn.close()
    return {"new": new_items, "seen": seen_items, "stats": {"total_checked": len(urls), "new_count": len(new_items), "seen_count": len(seen_items)}}


def mark_detail_fetched(url: str, detail_json: str | None = None):
    conn = get_db()
    conn.execute("UPDATE crawl_cache SET detail_fetched = 1, detail_json = ? WHERE url_hash = ?", (detail_json, url_hash(url)))
    conn.commit()
    conn.close()


def mark_expired(days_threshold: int = 14):
    conn = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_threshold)).isoformat()
    result = conn.execute("UPDATE crawl_cache SET expired = 1 WHERE last_seen < ? AND expired = 0", (cutoff,))
    count = result.rowcount
    conn.commit()
    conn.close()
    return count


def cleanup_old_expired(days_threshold: int = 30):
    conn = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days_threshold)).isoformat()
    result = conn.execute("DELETE FROM crawl_cache WHERE expired = 1 AND last_seen < ?", (cutoff,))
    count = result.rowcount
    conn.commit()
    conn.close()
    return count


def get_stats() -> dict:
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM crawl_cache").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM crawl_cache WHERE expired = 0").fetchone()[0]
    fetched = conn.execute("SELECT COUNT(*) FROM crawl_cache WHERE detail_fetched = 1").fetchone()[0]
    expired = conn.execute("SELECT COUNT(*) FROM crawl_cache WHERE expired = 1").fetchone()[0]
    by_source = {}
    for row in conn.execute("SELECT source, COUNT(*) as cnt FROM crawl_cache GROUP BY source"):
        by_source[row["source"]] = row["cnt"]
    conn.close()
    return {"total": total, "active": active, "detail_fetched": fetched, "expired": expired, "by_source": by_source}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: cache_manager.py <command>\n  check <json_file>\n  stats\n  expire\n  cleanup")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "check":
        data = json.loads(Path(sys.argv[2]).read_text())
        print(json.dumps(check_urls(data), ensure_ascii=False, indent=2))
    elif cmd == "stats":
        print(json.dumps(get_stats(), ensure_ascii=False, indent=2))
    elif cmd == "expire":
        print(f"标记 {mark_expired(int(sys.argv[2]) if len(sys.argv) > 2 else 14)} 条记录为过期")
    elif cmd == "cleanup":
        print(f"清理 {cleanup_old_expired(int(sys.argv[2]) if len(sys.argv) > 2 else 30)} 条过期记录")
