from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = ROOT / "data" / "processed"
DEFAULT_INPUT = DATA_PROCESSED / "papers.jsonl"
DEFAULT_OUTPUT_DIR = DATA_PROCESSED / "model_keywords"


KEYWORD_RULES: list[tuple[str, list[str]]] = [
    ("VLA", ["vision-language-action", "vision language action", "vla"]),
    ("World Model", ["world model", "world-action model", "world action model"]),
    ("Imitation Learning", ["imitation learning", "behavior cloning", "demonstration learning"]),
    ("Reinforcement Learning", ["reinforcement learning", "rl"]),
    ("Pretraining", ["pretraining", "pre-train", "pre trained", "pretrained"]),
    ("Fine-tuning", ["fine tuning", "fine-tuning", "finetune", "fine tune"]),
    ("Co-training", ["co training", "co-train", "co train"]),
    ("Multimodal", ["multimodal", "multi modal", "multi-modal"]),
    ("Language-conditioned", ["language conditioned", "language conditioning"]),
    ("Action-conditioned", ["action conditioned"]),
    ("Egocentric", ["egocentric"]),
    ("Human Data", ["human data", "human videos"]),
    ("Web Data", ["web data"]),
    ("Simulation", ["simulation", "sim-to-real", "sim to real", "simulator"]),
    ("Benchmark", ["benchmark", "evaluation suite", "testbed"]),
    ("Grasping", ["grasping", "grasp"]),
    ("Dexterous Manipulation", ["dexterous manipulation", "in-hand manipulation"]),
    ("Bimanual Manipulation", ["bimanual manipulation", "two-arm manipulation"]),
    ("Mobile Manipulation", ["mobile manipulation"]),
    ("Deformable Objects", ["deformable object", "deformable objects", "cloth", "cable", "rope"]),
    ("Tactile", ["tactile", "touch", "visuotactile"]),
    ("Hardware", ["hardware", "gripper", "hand", "actuator", "robot body"]),
    ("Humanoid", ["humanoid"]),
    ("Planning", ["planning", "planner", "trajectory"]),
    ("Control", ["control", "servoing", "visuomotor"]),
    ("Policy Learning", ["policy learning", "policy optimization", "policy"]),
    ("Dataset", ["dataset", "data collection", "data collection system"]),
    ("Foundation Model", ["foundation model", "foundation models"]),
    ("Cross-Embodiment", ["cross-embodiment", "multi-embodiment", "cross embodiment"]),
    ("Latent Actions", ["latent action", "latent actions"]),
    ("Diffusion", ["diffusion"]),
    ("Hierarchical", ["hierarchical"]),
    ("Memory", ["memory", "retrieval", "experience replay"]),
    ("Reasoning", ["reasoning", "chain-of-thought", "cot"]),
    ("Generalization", ["generalization", "generalisation", "open-world", "open world"]),
    ("Object Pose", ["object pose", "pose estimation"]),
    ("Navigation", ["navigation"]),
    ("Manipulation", ["manipulation"]),
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def extract_keywords(title: str, abstract: str, limit: int = 8) -> list[str]:
    text = f"{title} {abstract}".lower()
    keywords: list[str] = []
    for label, patterns in KEYWORD_RULES:
        if any(pattern in text for pattern in patterns):
            keywords.append(label)
    if "vla" in text and "VLA" not in keywords:
        keywords.insert(0, "VLA")
    return keywords[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Export simple baseline keywords for all papers.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    papers = load_jsonl(input_path)
    freq: Counter[str] = Counter()

    output_path = output_dir / "paper_keywords.jsonl"
    with output_path.open("w", encoding="utf-8") as handle:
        for paper in papers:
            keywords = extract_keywords(paper.get("title", ""), paper.get("abstract", ""), limit=args.limit)
            freq.update(keywords)
            handle.write(
                json.dumps(
                    {
                        "arxiv_id": paper.get("arxiv_id", ""),
                        "title": paper.get("title", ""),
                        "published_date": paper.get("published_date", ""),
                        "keywords": keywords,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    with (output_dir / "keyword_frequency.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["keyword", "count"])
        for keyword, count in freq.most_common():
            writer.writerow([keyword, count])

    print(json.dumps(
        {
            "papers": len(papers),
            "output": str(output_path),
            "frequency_csv": str(output_dir / "keyword_frequency.csv"),
            "top_keywords": freq.most_common(30),
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
