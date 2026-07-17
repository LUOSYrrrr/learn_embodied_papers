from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DATA_PROCESSED = ROOT / "data" / "processed"
INPUT_PATH = DATA_PROCESSED / "papers.jsonl"
KEYWORD_DIR = DATA_PROCESSED / "model_keywords"
OUTPUT_PATH = KEYWORD_DIR / "keywords_latest.jsonl"
POLICY_PATH = CONFIG_DIR / "keyword_extraction_policy.md"
LIBRARY_PATH = CONFIG_DIR / "canonical_keywords_library.yaml"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def read_existing_output(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    for row in load_jsonl(path):
        arxiv_id = row.get("arxiv_id", "")
        if arxiv_id:
            rows[arxiv_id] = row
    return rows


def build_allowed_keywords(library: dict[str, Any]) -> dict[str, set[str]]:
    sections = library["sections"]
    theme_to_sections = library["theme_to_sections"]
    allowed: dict[str, set[str]] = {}
    for theme, section_names in theme_to_sections.items():
        current: set[str] = set()
        for section_name in section_names:
            current.update(sections[section_name])
        allowed[theme] = current
    return allowed


def get_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("missing OPENAI_API_KEY")
    return api_key


def call_openai_chat(model: str, system_prompt: str, user_prompt: str) -> dict[str, Any]:
    payload = {
        "model": model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {get_api_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    return json.loads(content)


def make_prompts(policy_text: str, library_text: str, paper: dict[str, Any]) -> tuple[str, str]:
    system_prompt = (
        "You extract core-contribution keywords for arXiv papers. "
        "You must follow the policy exactly, only use canonical keywords from the library, "
        "and return valid JSON only."
    )
    user_prompt = f"""Follow this keyword extraction policy:

{policy_text}

Canonical keyword library:

{library_text}

Paper:
- arxiv_id: {paper.get("arxiv_id", "")}
- title: {paper.get("title", "")}
- abstract: {paper.get("abstract", "")}

Task:
1. infer exactly one theme
2. extract candidate_concepts from the title and abstract
3. select final keywords from the canonical keyword library only

Return JSON with exactly these fields:
{{
  "arxiv_id": "...",
  "title": "...",
  "theme": "...",
  "candidate_concepts": ["..."],
  "keywords": ["..."]
}}
"""
    return system_prompt, user_prompt


def validate_row(row: dict[str, Any], allowed_keywords: dict[str, set[str]], themes: set[str]) -> list[str]:
    errors: list[str] = []
    arxiv_id = row.get("arxiv_id", "")
    theme = row.get("theme", "")
    keywords = row.get("keywords", [])
    if theme not in themes:
        errors.append(f"{arxiv_id}: invalid theme {theme!r}")
        return errors
    if not isinstance(keywords, list):
        errors.append(f"{arxiv_id}: keywords is not a list")
        return errors
    for keyword in keywords:
        if keyword not in allowed_keywords[theme]:
            errors.append(f"{arxiv_id}: keyword {keyword!r} not allowed for theme {theme!r}")
    return errors


def normalize_output(row: dict[str, Any], paper: dict[str, Any]) -> dict[str, Any]:
    candidate_concepts = row.get("candidate_concepts", [])
    keywords = row.get("keywords", [])
    if not isinstance(candidate_concepts, list):
        candidate_concepts = []
    if not isinstance(keywords, list):
        keywords = []
    return {
        "arxiv_id": paper.get("arxiv_id", ""),
        "title": paper.get("title", ""),
        "theme": row.get("theme", ""),
        "candidate_concepts": list(dict.fromkeys(str(item).strip() for item in candidate_concepts if str(item).strip())),
        "keywords": list(dict.fromkeys(str(item).strip() for item in keywords if str(item).strip())),
    }


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract model keywords from arXiv titles and abstracts into keywords_latest.jsonl.")
    parser.add_argument("--input", default=str(INPUT_PATH))
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--limit", type=int, default=0, help="0 means no limit")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    papers = load_jsonl(input_path)
    if args.limit > 0:
        papers = papers[: args.limit]

    if args.overwrite and output_path.exists():
        output_path.unlink()

    existing = read_existing_output(output_path)
    policy_text = POLICY_PATH.read_text(encoding="utf-8")
    library = load_yaml(LIBRARY_PATH)
    library_text = LIBRARY_PATH.read_text(encoding="utf-8")
    allowed_keywords = build_allowed_keywords(library)
    themes = set(library["themes"])

    completed = 0
    skipped = 0
    failed: list[str] = []

    for paper in papers:
        arxiv_id = paper.get("arxiv_id", "")
        if not arxiv_id:
            continue
        if arxiv_id in existing:
            skipped += 1
            continue

        system_prompt, user_prompt = make_prompts(policy_text, library_text, paper)
        try:
            raw_row = call_openai_chat(args.model, system_prompt, user_prompt)
            row = normalize_output(raw_row, paper)
            errors = validate_row(row, allowed_keywords, themes)
            if errors:
                raise ValueError("; ".join(errors))
            append_jsonl(output_path, row)
            completed += 1
            print(f"[ok] {arxiv_id} theme={row['theme']} keywords={','.join(row['keywords'])}", flush=True)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
            failed.append(f"{arxiv_id}: {exc}")
            print(f"[fail] {arxiv_id}: {exc}", flush=True)
        if args.sleep_seconds > 0:
            time.sleep(args.sleep_seconds)

    summary = {
        "input_papers": len(papers),
        "completed": completed,
        "skipped_existing": skipped,
        "failed": len(failed),
        "output": str(output_path),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if failed:
        failures_path = output_path.parent / "keyword_failures.log"
        failures_path.write_text("\n".join(failed), encoding="utf-8")
        print(f"wrote failures to {failures_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
