from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = ROOT / "data" / "processed"
KEYWORD_DIR = DATA_PROCESSED / "model_keywords"
LATEST_KEYWORDS_PATH = KEYWORD_DIR / "keywords_latest.jsonl"
# 前端在 pipeline 的上一级（leaderboard/），随主仓库 GitHub Pages 一起部署
SITE_DIR = ROOT.parent
SITE_DATA_DIR = SITE_DIR / "data"
SITE_KEYWORDS_PATH = ROOT / "config" / "site_keywords.yaml"


def normalize_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").strip().lower()).strip()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").strip().lower()).strip("-")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_keyword_rows() -> dict[str, dict[str, Any]]:
    keywords_by_id: dict[str, dict[str, Any]] = {}
    if LATEST_KEYWORDS_PATH.exists():
        for row in load_jsonl(LATEST_KEYWORDS_PATH):
            keywords_by_id[row["arxiv_id"]] = {
                "keywords": row.get("keywords", []),
                "theme": row.get("theme", ""),
            }
        return keywords_by_id
    for path in sorted(KEYWORD_DIR.glob("full_batch_*.jsonl")):
        with path.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                keywords_by_id[row["arxiv_id"]] = {
                    "keywords": row.get("keywords", []),
                    "theme": row.get("theme", ""),
                }
    return keywords_by_id


def load_alias_map() -> dict[str, str]:
    alias_map: dict[str, str] = {}
    if not SITE_KEYWORDS_PATH.exists():
        return alias_map

    data = yaml.safe_load(SITE_KEYWORDS_PATH.read_text(encoding="utf-8")) or {}
    for entry in data.get("keywords", []):
        label = entry["label"].strip()
        alias_map[normalize_key(label)] = label
        for alias in entry.get("aliases", []):
            alias_map[normalize_key(alias)] = label
    return alias_map


def canonicalize_keywords(raw_keywords: list[str], alias_map: dict[str, str]) -> list[str]:
    canonical: list[str] = []
    seen: set[str] = set()
    for keyword in raw_keywords:
        label = alias_map.get(normalize_key(keyword), keyword)
        if label not in seen:
            seen.add(label)
            canonical.append(label)
    return canonical


def build_site_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    papers = load_jsonl(DATA_PROCESSED / "papers.jsonl")
    keyword_rows = load_keyword_rows()
    alias_map = load_alias_map()
    tag_counts: Counter[str] = Counter()

    site_rows: list[dict[str, Any]] = []
    for paper in papers:
        keyword_payload = keyword_rows.get(paper["arxiv_id"], {})
        keywords = canonicalize_keywords(keyword_payload.get("keywords", []), alias_map)
        tag_counts.update(keywords)
        site_rows.append(
            {
                "arxiv_id": paper["arxiv_id"],
                "title": paper["title"],
                "published_date": paper.get("published_date", ""),
                "cited_by_count": paper.get("cited_by_count") or 0,
                "total_score": round(float(paper.get("total_score", 0.0)), 6),
                "hot_score": round(float(paper.get("hot_score", 0.0)), 6),
                "total_rank": int(paper.get("total_rank") or 0),
                "hot_rank": int(paper.get("hot_rank") or 0),
                "theme": keyword_payload.get("theme", ""),
                "keywords": keywords,
                "abs_url": paper.get("abs_url", ""),
                "pdf_url": paper.get("pdf_url", ""),
            }
        )

    site_rows.sort(key=lambda row: row["total_rank"] or 10**9)

    tag_rows = [
        {"label": label, "slug": slugify(label), "count": count}
        for label, count in tag_counts.most_common()
    ]

    # Make query-time normalization robust even for keywords that are already canonical.
    alias_lookup = {normalize_key(tag["label"]): tag["label"] for tag in tag_rows}
    for raw, canonical in alias_map.items():
        alias_lookup[raw] = canonical

    return site_rows, tag_rows, alias_lookup


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main() -> int:
    SITE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    papers, tags, alias_lookup = build_site_rows()
    stats = {
        "paper_count": len(papers),
        "tag_count": len(tags),
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "sorts": [
            {"id": "total_score", "label": "Overall Score"},
            {"id": "hot_score", "label": "Hot Score"},
            {"id": "published_date", "label": "Newest"},
        ],
    }

    write_json(SITE_DATA_DIR / "papers.min.json", papers)
    write_json(SITE_DATA_DIR / "tags.json", tags)
    write_json(SITE_DATA_DIR / "aliases.json", alias_lookup)
    write_json(SITE_DATA_DIR / "stats.json", stats)
    (SITE_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print(
        json.dumps(
            {
                "papers": len(papers),
                "tags": len(tags),
                "outputs": [
                    str(SITE_DATA_DIR / "papers.min.json"),
                    str(SITE_DATA_DIR / "tags.json"),
                    str(SITE_DATA_DIR / "aliases.json"),
                    str(SITE_DATA_DIR / "stats.json"),
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
