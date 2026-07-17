"""Bootstrap keyword extraction via library-constrained phrase matching.

正式流程的关键词抽取应该用 LLM（见 extract_model_keywords.py 与
config/keyword_extraction_policy.md）。这个脚本是无 API key 时的自举方案：
用 config/site_keywords.yaml 的 alias 表在 title+abstract 上做词边界匹配，
产出 data/processed/model_keywords/keywords_latest.jsonl，让前端筛选立即可用。

用法：
    python scripts/bootstrap_keywords.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAPERS_PATH = ROOT / "data" / "processed" / "papers.jsonl"
SITE_KEYWORDS_PATH = ROOT / "config" / "site_keywords.yaml"
OUTPUT_DIR = ROOT / "data" / "processed" / "model_keywords"
OUTPUT_PATH = OUTPUT_DIR / "keywords_latest.jsonl"

# 标签优先级：模型家族 > 任务/本体 > 学习范式 > 其余。数值越小越优先。
LABEL_PRIORITY = {
    "World-Action Model": 0,
    "World Model": 1,
    "VLA": 1,
    "Diffusion Policy": 2,
    "Flow Matching": 2,
    "Foundation Model": 3,
    "Latent Action": 3,
    "VLM": 4,
    "Humanoid": 5,
    "Loco-Manipulation": 5,
    "Whole-Body Control": 5,
    "Motion Tracking": 5,
    "Dexterous Hand": 5,
    "Dexterous Manipulation": 5,
    "In-Hand Manipulation": 5,
    "Bimanual Manipulation": 5,
    "Grasping": 6,
    "Legged Locomotion": 6,
    "Teleoperation": 6,
    "Tactile": 6,
    "Imitation Learning": 7,
    "Reinforcement Learning": 7,
    "Test-Time": 7,
    "Sim-to-Real": 8,
    "Cross-Embodiment": 8,
    "Egocentric Video": 8,
    "Human Data": 8,
    "Video Generation": 8,
    "3D Perception": 9,
    "Gaussian Splatting": 9,
    "Action Chunking": 9,
    "Planning": 10,
    "MPC": 10,
    "Reasoning": 10,
    "Pretraining": 10,
    "Post-Training": 10,
    "Skill Learning": 10,
    "Synthetic Data": 11,
    "Simulation": 11,
    "Real-Time Control": 11,
    "Hardware": 11,
    "Manipulation": 12,  # 太泛，垫底
    "Dataset": 13,
    "Benchmark": 13,
    "Survey": 13,
}
DEFAULT_PRIORITY = 12
MAX_KEYWORDS = 6

# 这些泛化标签只有在标题命中时才保留（policy：不给仅评估用途的 artifact 打标签）
TITLE_ONLY_LABELS = {"Dataset", "Benchmark", "Survey", "Simulation", "Manipulation"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def build_matchers() -> list[tuple[str, re.Pattern[str]]]:
    data = yaml.safe_load(SITE_KEYWORDS_PATH.read_text(encoding="utf-8"))
    matchers: list[tuple[str, re.Pattern[str]]] = []
    for entry in data.get("keywords", []):
        label = entry["label"].strip()
        phrases = {label.lower(), *(alias.lower() for alias in entry.get("aliases", []))}
        parts = []
        for phrase in sorted(phrases, key=len, reverse=True):
            escaped = re.escape(phrase).replace(r"\ ", r"[\s-]+").replace(r"\-", r"[\s-]*")
            parts.append(escaped)
        pattern = re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(parts) + r")(?![A-Za-z0-9])", re.IGNORECASE)
        matchers.append((label, pattern))
    return matchers


def infer_theme(title: str, abstract: str) -> str:
    t = title.lower()
    if re.search(r"\bsurvey\b|\breview\b|\btaxonomy\b", t):
        return "survey / review"
    if re.search(r"\bbenchmark\b", t):
        return "benchmark"
    if re.search(r"\bdataset\b|\bdata collection\b", t):
        return "dataset"
    if re.search(r"test[\s-]?time", t):
        return "inference / test-time method"
    return "model architecture"


def extract(paper: dict[str, Any], matchers: list[tuple[str, re.Pattern[str]]]) -> dict[str, Any]:
    title = paper.get("title", "") or ""
    abstract = paper.get("summary", "") or paper.get("abstract", "") or ""
    hits: list[tuple[int, int, str]] = []  # (title_miss, priority, label)
    for label, pattern in matchers:
        in_title = bool(pattern.search(title))
        in_abstract = bool(pattern.search(abstract))
        if not in_title and not in_abstract:
            continue
        if label in TITLE_ONLY_LABELS and not in_title:
            continue
        priority = LABEL_PRIORITY.get(label, DEFAULT_PRIORITY)
        hits.append((0 if in_title else 1, priority, label))
    hits.sort()
    keywords = [label for _, _, label in hits[:MAX_KEYWORDS]]
    return {
        "arxiv_id": paper["arxiv_id"],
        "title": title,
        "theme": infer_theme(title, abstract),
        "keywords": keywords,
        "source": "bootstrap-phrase-match",
    }


def main() -> int:
    papers = load_jsonl(PAPERS_PATH)
    matchers = build_matchers()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 已有的非 bootstrap 行（LLM/人工精修）原样保留，只补/刷 bootstrap 行
    preserved: dict[str, dict[str, Any]] = {}
    if OUTPUT_PATH.exists():
        for row in load_jsonl(OUTPUT_PATH):
            if row.get("source") != "bootstrap-phrase-match" and row.get("arxiv_id"):
                preserved[row["arxiv_id"]] = row

    tagged = 0
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for paper in papers:
            row = preserved.get(paper["arxiv_id"]) or extract(paper, matchers)
            if row.get("keywords"):
                tagged += 1
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {"papers": len(papers), "tagged": tagged, "preserved": len(preserved), "output": str(OUTPUT_PATH)},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
