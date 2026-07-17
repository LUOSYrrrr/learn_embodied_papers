from __future__ import annotations

import argparse
import csv
import http.client
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, as_completed, wait
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from threading import Lock
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"
DATA_RAW_ARXIV = ROOT / "data" / "raw" / "arxiv"
DATA_RAW_SCHOLAR = ROOT / "data" / "raw" / "scholar"
DATA_PROCESSED = ROOT / "data" / "processed"
TOPICS_DIR = ROOT / "topics"
GENERATED_INDEX_PATH = TOPICS_DIR / "index.md"
ARXIV_PROGRESS_PATH = DATA_RAW_ARXIV / "_progress.json"
RUN_STATUS_PATH = DATA_PROCESSED / "_runtime_status.json"

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
PRINT_LOCK = Lock()
STATUS_LOCK = Lock()
ARXIV_PROGRESS_LOCK = Lock()
RUN_STATUS: dict[str, Any] = {}


@dataclass
class RunOptions:
    years_back: int | None
    max_results_per_query: int | None
    only_queries: set[str] | None = None


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def log_progress(message: str) -> None:
    timestamp = now_utc().strftime("%H:%M:%S")
    with PRINT_LOCK:
        print(f"[{timestamp}] {message}", flush=True)
    update_run_status(last_log=message, last_log_at=iso(now_utc()))


def update_run_status(**fields: Any) -> None:
    with STATUS_LOCK:
        RUN_STATUS.update(fields)
        RUN_STATUS["pid"] = os.getpid()
        RUN_STATUS["updated_at"] = iso(now_utc())
        if "started_at" not in RUN_STATUS:
            RUN_STATUS["started_at"] = RUN_STATUS["updated_at"]
        with RUN_STATUS_PATH.open("w", encoding="utf-8") as handle:
            json.dump(RUN_STATUS, handle, ensure_ascii=False, indent=2)


def start_run_status(command: str, args: list[str]) -> None:
    update_run_status(
        state="running",
        command=command,
        args=args,
        started_at=iso(now_utc()),
        stage="starting",
        last_log="starting",
        last_log_at=iso(now_utc()),
    )


def finish_run_status(state: str, **fields: Any) -> None:
    update_run_status(state=state, finished_at=iso(now_utc()), **fields)


def ensure_dirs() -> None:
    for path in (DATA_RAW_ARXIV, DATA_RAW_SCHOLAR, DATA_PROCESSED, TOPICS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_title(text: str) -> str:
    lowered = clean_text(text).lower()
    return re.sub(r"[^a-z0-9]+", " ", lowered).strip()


def canonical_arxiv_id(raw_id: str) -> str:
    tail = raw_id.rstrip("/").split("/")[-1]
    return re.sub(r"v\d+$", "", tail)


def parse_arxiv_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.fromisoformat(normalized).astimezone(timezone.utc)


def iso(dt: datetime | None) -> str:
    return dt.isoformat().replace("+00:00", "Z") if dt else ""


def parse_date_start(value: str | date | datetime) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def format_arxiv_bound(dt: datetime, end: bool) -> str:
    return dt.strftime("%Y%m%d2359" if end else "%Y%m%d0000")


def build_arxiv_query(base_query: str, categories: list[str], start_dt: datetime, end_dt: datetime) -> str:
    since = format_arxiv_bound(start_dt, end=False)
    until = format_arxiv_bound(end_dt, end=True)
    if categories:
        category_clause = " OR ".join(f"cat:{cat}" for cat in categories)
        return f"submittedDate:[{since} TO {until}] AND ({category_clause}) AND {base_query}"
    return f"submittedDate:[{since} TO {until}] AND {base_query}"


def fetch_url(url: str, max_attempts: int = 5) -> bytes:
    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(url, headers={"User-Agent": "embodied-intelligence-knowledge-base/0.1"})
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except http.client.IncompleteRead:
            if attempt == max_attempts:
                raise
            time.sleep(min(60.0, 3.0 * attempt))
        except urllib.error.HTTPError as exc:
            status = exc.code
            if status not in {429, 500, 502, 503, 504} or attempt == max_attempts:
                raise
            retry_after = exc.headers.get("Retry-After")
            sleep_seconds = float(retry_after) if retry_after else min(90.0, 5.0 * attempt)
            time.sleep(sleep_seconds)
        except urllib.error.URLError:
            if attempt == max_attempts:
                raise
            time.sleep(min(60.0, 3.0 * attempt))
    return b""


def parse_arxiv_entry(entry: ET.Element) -> dict[str, Any]:
    raw_id = entry.findtext("atom:id", "", ATOM_NS)
    arxiv_id = canonical_arxiv_id(raw_id)
    links = entry.findall("atom:link", ATOM_NS)
    pdf_url = ""
    for link in links:
        if link.attrib.get("title") == "pdf":
            pdf_url = link.attrib.get("href", "")
            break
    if not pdf_url:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    categories = [tag.attrib.get("term", "") for tag in entry.findall("atom:category", ATOM_NS)]
    doi = clean_text(entry.findtext("arxiv:doi", "", ATOM_NS))
    return {
        "arxiv_id": arxiv_id,
        "entry_id": raw_id,
        "title": clean_text(entry.findtext("atom:title", "", ATOM_NS)),
        "abstract": clean_text(entry.findtext("atom:summary", "", ATOM_NS)),
        "authors": [clean_text(author.findtext("atom:name", "", ATOM_NS)) for author in entry.findall("atom:author", ATOM_NS)],
        "categories": sorted({category for category in categories if category}),
        "published_at": entry.findtext("atom:published", "", ATOM_NS),
        "updated_at": entry.findtext("atom:updated", "", ATOM_NS),
        "doi": doi,
        "comment": clean_text(entry.findtext("arxiv:comment", "", ATOM_NS)),
        "journal_ref": clean_text(entry.findtext("arxiv:journal_ref", "", ATOM_NS)),
        "pdf_url": pdf_url,
        "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
    }


def load_arxiv_progress() -> dict[str, Any]:
    if not ARXIV_PROGRESS_PATH.exists():
        return {}
    with ARXIV_PROGRESS_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_arxiv_progress(progress: dict[str, Any]) -> None:
    with ARXIV_PROGRESS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(progress, handle, ensure_ascii=False, indent=2)


def update_arxiv_progress(progress: dict[str, Any], query_id: str, **fields: Any) -> dict[str, Any]:
    with ARXIV_PROGRESS_LOCK:
        current = dict(progress.get(query_id, {}))
        current.update(fields)
        progress[query_id] = current
        save_arxiv_progress(progress)
        return current


def load_query_cache(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("papers", [])


def load_all_arxiv_raw_papers(config: dict[str, Any], only_queries: set[str] | None = None) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for query_cfg in config["queries"]["arxiv"]["queries"]:
        query_id = query_cfg["id"]
        if only_queries and query_id not in only_queries:
            continue
        cache_path = DATA_RAW_ARXIV / f"{query_id}.json"
        papers = load_query_cache(cache_path)
        for paper in papers:
            matched = sorted(set(paper.get("matched_queries", []) + [query_id]))
            paper["matched_queries"] = matched
            current = merged.get(paper["arxiv_id"])
            if current is None:
                merged[paper["arxiv_id"]] = paper
            else:
                merged[paper["arxiv_id"]] = {
                    **current,
                    **paper,
                    "matched_queries": sorted(set(current.get("matched_queries", []) + matched)),
                }
    return sorted(merged.values(), key=lambda item: item["published_at"], reverse=True)


def merge_papers_by_id(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {paper["arxiv_id"]: paper for paper in existing}
    for paper in incoming:
        current = merged.get(paper["arxiv_id"])
        if current is None:
            merged[paper["arxiv_id"]] = paper
            continue
        matched_queries = sorted(set(current.get("matched_queries", []) + paper.get("matched_queries", [])))
        merged[paper["arxiv_id"]] = {**current, **paper, "matched_queries": matched_queries}
    return sorted(merged.values(), key=lambda item: item["published_at"], reverse=True)


def fetch_single_arxiv_query(
    query_cfg: dict[str, Any],
    arxiv_cfg: dict[str, Any],
    years_back: int,
    max_results: int | None,
    progress: dict[str, Any],
) -> dict[str, Any]:
    query_id = query_cfg["id"]
    categories = arxiv_cfg["categories"]
    batch_size = arxiv_cfg["batch_size"]
    base_url = arxiv_cfg["base_url"]
    pause_seconds = float(arxiv_cfg["pause_seconds"])
    sort_by = arxiv_cfg["sort_by"]
    sort_order = arxiv_cfg["sort_order"]

    cache_path = DATA_RAW_ARXIV / f"{query_id}.json"
    existing_entries = load_query_cache(cache_path)
    existing_ids = {paper["arxiv_id"] for paper in existing_entries}
    query_progress = dict(progress.get(query_id, {}))
    start_dt = parse_date_start(query_cfg["start_date"]) if query_cfg.get("start_date") else (now_utc() - timedelta(days=365 * years_back))
    end_dt = parse_arxiv_datetime(query_progress["resume_window_end"]) if query_progress.get("resume_window_end") else now_utc()
    resume_incomplete = bool(query_progress) and not query_progress.get("complete", False)
    incremental_refresh = bool(existing_entries) and query_progress.get("complete", False)
    if resume_incomplete:
        start_index = int(query_progress.get("resume_start", 0) or 0)
    else:
        start_index = 0 if incremental_refresh else len(existing_entries)
    if end_dt < start_dt:
        end_dt = start_dt

    search_query = build_arxiv_query(query_cfg["text"], categories, start_dt, end_dt)
    raw_entries: list[dict[str, Any]] = []
    fetched = 0
    if resume_incomplete:
        page_index = int(query_progress.get("resume_page", 0) or 0)
    else:
        page_index = 0 if incremental_refresh else (start_index // batch_size)
    max_results_text = str(max_results) if max_results is not None else "unlimited"
    mode = "incremental" if incremental_refresh else ("resume" if resume_incomplete else "full")

    log_progress(
        f"[arxiv:{query_id}] start mode={mode} window={start_dt.date()}..{end_dt.date()} "
        f"existing={len(existing_entries)} start_index={start_index} max_results={max_results_text}"
    )
    update_run_status(
        stage="fetch_arxiv",
        arxiv_current_query=query_id,
        arxiv_query_window_start=start_dt.date().isoformat(),
        arxiv_query_window_end=end_dt.date().isoformat(),
        arxiv_query_existing=len(existing_entries),
        arxiv_query_fetched=0,
        arxiv_query_page=0,
    )
    update_arxiv_progress(
        progress,
        query_id,
        start_date=start_dt.date().isoformat(),
        resume_window_end=iso(end_dt),
        resume_start=start_index,
        resume_page=page_index,
        complete=False,
    )

    while True:
        if max_results is not None and fetched >= max_results:
            break
        page_index += 1
        size = batch_size if max_results is None else min(batch_size, max_results - fetched)
        params = urllib.parse.urlencode(
            {
                "search_query": search_query,
                "start": start_index,
                "max_results": size,
                "sortBy": sort_by,
                "sortOrder": sort_order,
            }
        )
        payload = fetch_url(f"{base_url}?{params}")
        root = ET.fromstring(payload)
        entries = [parse_arxiv_entry(entry) for entry in root.findall("atom:entry", ATOM_NS)]
        if not entries:
            log_progress(f"[arxiv:{query_id}] no more entries at page={page_index} fetched={fetched}")
            break

        page_new_entries: list[dict[str, Any]] = []
        for paper in entries:
            paper["matched_queries"] = sorted(set(paper.get("matched_queries", []) + [query_id]))
            if not incremental_refresh or paper["arxiv_id"] not in existing_ids:
                page_new_entries.append(paper)
                existing_ids.add(paper["arxiv_id"])
        raw_entries.extend(page_new_entries)
        fetched += len(page_new_entries)
        start_index += len(entries)
        log_progress(
            f"[arxiv:{query_id}] page={page_index} got={len(entries)} "
            f"new={len(page_new_entries)} run_total={fetched} next_start={start_index} "
            f"stored_total~{len(existing_entries) + len(raw_entries)}"
        )
        update_run_status(
            stage="fetch_arxiv",
            arxiv_current_query=query_id,
            arxiv_query_fetched=fetched,
            arxiv_query_page=page_index,
            arxiv_query_last_page_size=len(entries),
            arxiv_query_stored_estimate=len(existing_entries) + len(raw_entries),
        )
        update_arxiv_progress(
            progress,
            query_id,
            start_date=start_dt.date().isoformat(),
            resume_window_end=iso(end_dt),
            resume_start=start_index,
            resume_page=page_index,
            complete=False,
        )
        if incremental_refresh and not page_new_entries:
            log_progress(f"[arxiv:{query_id}] reached cached frontier at page={page_index}")
            break
        if len(entries) < size:
            log_progress(f"[arxiv:{query_id}] short page -> reached end with run_total={fetched}")
            break
        time.sleep(pause_seconds)

    stored_entries = merge_papers_by_id(existing_entries, raw_entries)
    with cache_path.open("w", encoding="utf-8") as handle:
        json.dump(
            {
                "query": search_query,
                "window_start": iso(start_dt),
                "window_end": iso(end_dt),
                "count": len(stored_entries),
                "last_run_count": len(raw_entries),
                "papers": stored_entries,
            },
            handle,
            ensure_ascii=False,
            indent=2,
        )

    progress_update = update_arxiv_progress(
        progress,
        query_id,
        start_date=start_dt.date().isoformat(),
        resume_window_end="",
        resume_start=0,
        resume_page=0,
        complete=True,
        last_completed_at=iso(now_utc()),
        last_window_end=iso(end_dt),
        last_run_count=len(raw_entries),
    )
    log_progress(f"[arxiv:{query_id}] done stored={len(stored_entries)}")

    return {
        "query_id": query_id,
        "existing_entries": existing_entries,
        "raw_entries": raw_entries,
        "stored_entries": stored_entries,
        "progress_update": progress_update,
    }


def fetch_arxiv(config: dict[str, Any], options: RunOptions) -> list[dict[str, Any]]:
    arxiv_cfg = config["queries"]["arxiv"]
    years_back = options.years_back or arxiv_cfg["years_back"]
    raw_max_results = options.max_results_per_query if options.max_results_per_query is not None else arxiv_cfg["max_results_per_query"]
    max_results = None if not raw_max_results or int(raw_max_results) <= 0 else int(raw_max_results)
    parallel_queries = int(arxiv_cfg.get("parallel_queries", 1) or 1)
    progress = load_arxiv_progress()

    merged: dict[str, dict[str, Any]] = {}
    selected_queries = [
        query_cfg
        for query_cfg in arxiv_cfg["queries"]
        if not options.only_queries or query_cfg["id"] in options.only_queries
    ]
    update_run_status(
        stage="fetch_arxiv",
        arxiv_total_queries=len(selected_queries),
        arxiv_completed_queries=0,
        arxiv_parallel_queries=parallel_queries,
    )

    with ThreadPoolExecutor(max_workers=max(1, parallel_queries)) as executor:
        futures = [
            executor.submit(fetch_single_arxiv_query, query_cfg, arxiv_cfg, years_back, max_results, progress)
            for query_cfg in selected_queries
        ]
        for future in as_completed(futures):
            result = future.result()
            query_id = result["query_id"]
            if result["progress_update"] is not None:
                progress[query_id] = result["progress_update"]
            for paper in result["stored_entries"]:
                current = merged.get(paper["arxiv_id"])
                if current is None:
                    merged[paper["arxiv_id"]] = paper
                else:
                    merged[paper["arxiv_id"]] = {
                        **current,
                        **paper,
                        "matched_queries": sorted(set(current.get("matched_queries", []) + paper.get("matched_queries", []))),
                    }
            completed_queries = sum(1 for value in futures if value.done())
            update_run_status(
                stage="fetch_arxiv",
                arxiv_last_completed_query=query_id,
                arxiv_completed_queries=completed_queries,
                arxiv_merged_papers=len(merged),
            )

    save_arxiv_progress(progress)

    papers = sorted(merged.values(), key=lambda item: item["published_at"], reverse=True)
    return papers


def classify_papers(papers: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    classified: list[dict[str, Any]] = []
    for paper in papers:
        published_at = parse_arxiv_datetime(paper["published_at"])
        age_days = max(0, (now_utc() - published_at).days)
        enriched = dict(paper)
        enriched["age_days"] = age_days
        enriched["published_year"] = published_at.year
        enriched["published_date"] = published_at.date().isoformat()
        classified.append(enriched)

    return classified


def fetch_text_url(url: str, max_attempts: int = 3, timeout: int = 20) -> str:
    for attempt in range(1, max_attempts + 1):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                )
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError:
            if attempt == max_attempts:
                raise
            time.sleep(2.0 * attempt)
        except urllib.error.URLError:
            if attempt == max_attempts:
                raise
            time.sleep(2.0 * attempt)
    return ""


def get_serper_keys() -> list[str]:
    keys: list[str] = []
    for env_name in ("SERPER_API_KEYS", "SERPER_API_KEY"):
        raw = os.getenv(env_name, "").strip()
        if not raw:
            continue
        keys.extend([item.strip() for item in raw.split(",") if item.strip()])
    deduped: list[str] = []
    seen: set[str] = set()
    for key in keys:
        if key not in seen:
            deduped.append(key)
            seen.add(key)
    return deduped


def ordered_serper_keys(seed: str) -> list[str]:
    keys = get_serper_keys()
    if len(keys) <= 1:
        return keys
    offset = sum(ord(ch) for ch in seed) % len(keys)
    return keys[offset:] + keys[:offset]


def fetch_serper_json(query: str, key_seed: str) -> tuple[dict[str, Any], str]:
    keys = ordered_serper_keys(key_seed)
    if not keys:
        raise RuntimeError("missing SERPER_API_KEY or SERPER_API_KEYS")

    last_error: Exception | None = None
    for api_key in keys:
        payload = json.dumps({"q": query}).encode("utf-8")
        request = urllib.request.Request(
            "https://google.serper.dev/scholar",
            data=payload,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8")), api_key
        except http.client.RemoteDisconnected as exc:
            last_error = exc
            continue
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in {401, 403, 429}:
                continue
            raise
        except urllib.error.URLError as exc:
            last_error = exc
            continue
    if last_error is not None:
        raise last_error
    raise RuntimeError("no usable Serper key")


def scholar_search_queries(paper: dict[str, Any]) -> list[str]:
    raw_title = clean_text(paper["title"])
    normalized_title = raw_title.replace("$", "").replace("{", "").replace("}", "").replace("π", "pi")
    compact_title = re.sub(r"[^A-Za-z0-9 .:_-]+", " ", normalized_title)
    author = clean_text(paper.get("authors", [""])[0] if paper.get("authors") else "")
    short_author = clean_text(author.split(",")[0].split(" ")[0] if author else "")
    year = paper.get("published_date", "")[:4]
    arxiv_id = paper["arxiv_id"]
    queries = [
        f'"arXiv:{arxiv_id}"',
        f'"https://arxiv.org/abs/{arxiv_id}"',
        f'"{raw_title}" "arXiv:{arxiv_id}"',
        f'"{normalized_title}" "arXiv:{arxiv_id}"',
        f'"{raw_title}"',
        f'"{normalized_title}"',
        f'"{compact_title}"',
        f'"{normalized_title}" {year}',
        f'"{compact_title}" {year}',
        f'"{normalized_title}" {short_author}',
        f'"{compact_title}" "{arxiv_id}"',
    ]
    seen: set[str] = set()
    ordered: list[str] = []
    for query in queries:
        query = clean_text(query)
        if query and query not in seen:
            ordered.append(query)
            seen.add(query)
    return ordered


def normalize_scholar_text(text: str) -> str:
    text = clean_text(text).lower()
    text = text.replace("π", "pi")
    text = text.replace("$", " ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def scholar_title_similarity(expected_title: str, actual_title: str) -> float:
    return SequenceMatcher(None, normalize_scholar_text(expected_title), normalize_scholar_text(actual_title)).ratio()


def scholar_title_core_similarity(expected_title: str, actual_title: str) -> float:
    expected = normalize_scholar_text(expected_title)
    actual = normalize_scholar_text(actual_title)
    if ":" in expected:
        expected = expected.split(":", 1)[1].strip()
    if ":" in actual:
        actual = actual.split(":", 1)[1].strip()
    return SequenceMatcher(None, expected, actual).ratio()


def scholar_author_overlap(expected_authors: list[str], actual_summary: str) -> int:
    summary = normalize_scholar_text(actual_summary)
    overlap = 0
    for author in expected_authors[:3]:
        tokens = [token for token in normalize_scholar_text(author).split() if len(token) > 2]
        if tokens and any(token in summary for token in tokens):
            overlap += 1
    return overlap


def scholar_candidate_score(paper: dict[str, Any], candidate: dict[str, Any]) -> float:
    title_score = scholar_title_similarity(paper["title"], candidate.get("title", ""))
    core_title_score = scholar_title_core_similarity(paper["title"], candidate.get("title", ""))
    summary = candidate.get("summary", "")
    author_score = scholar_author_overlap(paper.get("authors", []), summary) / max(1, min(3, len(paper.get("authors", []))))
    year_score = 0.0
    summary_years = re.findall(r"(?:19|20)\d{2}", summary)
    if paper.get("published_date", "")[:4] in summary_years:
        year_score = 0.15
    source_score = 0.1 if ("arxiv" in summary.lower() or "preprint" in summary.lower()) else 0.0
    return max(title_score, core_title_score) * 0.7 + author_score * 0.15 + year_score + source_score


def scholar_candidates_from_result(data: dict[str, Any]) -> list[dict[str, Any]]:
    organic = data.get("organic", []) or []
    candidates: list[dict[str, Any]] = []
    for item in organic:
        candidates.append(
            {
                "title": item.get("title", ""),
                "summary": item.get("publicationInfo", ""),
                "result_id": item.get("id", ""),
                "cited_by": item.get("citedBy"),
                "cited_link": item.get("link", ""),
            }
        )
    return candidates


def parse_scholar_citation_count(html_text: str) -> tuple[str, int | None]:
    lowered = html_text.lower()
    if "not a robot" in lowered or "unusual traffic" in lowered or "detected unusual traffic" in lowered:
        return "captcha", None
    patterns = [
        r"Cited by\s*(\d+)",
        r"被引用次数[:：]?\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text, flags=re.IGNORECASE)
        if match:
            return "found", int(match.group(1))
    return "missing", None


def fetch_scholar_citation_for_paper(paper: dict[str, Any]) -> dict[str, Any]:
    cache_path = DATA_RAW_SCHOLAR / f"{paper['arxiv_id']}.json"
    if cache_path.exists():
        with cache_path.open("r", encoding="utf-8") as handle:
            cached = json.load(handle)
        if cached:
            return cached

    result = {
        "arxiv_id": paper["arxiv_id"],
        "title": paper["title"],
        "scholar_cited_by_count": None,
        "scholar_status": "missing",
        "scholar_query": "",
        "scholar_url": "",
        "scholar_candidate_title": "",
        "scholar_candidate_score": None,
        "scholar_title_similarity": None,
    }
    api_keys = get_serper_keys()
    if not api_keys:
        result["scholar_status"] = "missing_api_key"
        with cache_path.open("w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
        return result
    for query in scholar_search_queries(paper):
        try:
            payload, used_key = fetch_serper_json(query, key_seed=f"{paper['arxiv_id']}:{query}")
        except http.client.RemoteDisconnected:
            result["scholar_status"] = "network_error"
            continue
        except urllib.error.HTTPError as exc:
            result["scholar_status"] = f"http_{exc.code}"
            continue
        except urllib.error.URLError:
            result["scholar_status"] = "network_error"
            continue
        except RuntimeError:
            result["scholar_status"] = "missing_api_key"
            continue
        candidates = scholar_candidates_from_result(payload)
        scored = sorted(
            ((scholar_candidate_score(paper, candidate), candidate) for candidate in candidates),
            key=lambda item: item[0],
            reverse=True,
        )
        if not scored:
            result["scholar_status"] = "missing"
            result["scholar_query"] = query
            result["scholar_url"] = ""
            continue
        best_score, best_candidate = scored[0]
        result["scholar_query"] = query
        result["scholar_url"] = best_candidate.get("cited_link", "")
        result["serper_key_suffix"] = used_key[-6:]
        result["scholar_candidate_title"] = best_candidate.get("title", "")
        result["scholar_candidate_score"] = round(best_score, 4)
        title_similarity = scholar_title_similarity(paper["title"], best_candidate.get("title", ""))
        core_title_similarity = scholar_title_core_similarity(paper["title"], best_candidate.get("title", ""))
        result["scholar_title_similarity"] = round(title_similarity, 4)
        summary = best_candidate.get("summary", "")
        exact_spelling = query.startswith('"')
        summary_has_source = ("arxiv" in summary.lower() or "preprint" in summary.lower())
        summary_has_year = paper.get("published_date", "")[:4] in summary
        if not (
            ((max(title_similarity, core_title_similarity) >= 0.94 and summary_has_source and summary_has_year))
            or (max(title_similarity, core_title_similarity) >= 0.92 and best_score >= 0.74)
        ):
            result["scholar_status"] = "low_confidence"
            continue
        result["scholar_cited_by_count"] = best_candidate.get("cited_by")
        result["scholar_status"] = "found" if best_candidate.get("cited_by") is not None else "missing"
        if result["scholar_status"] == "found":
            break
        time.sleep(2.0)

    with cache_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    return result


def scholar_info_from_cache(arxiv_id: str) -> tuple[int | None, str, str, str]:
    cache_path = DATA_RAW_SCHOLAR / f"{arxiv_id}.json"
    if not cache_path.exists():
        return None, "missing", "", ""
    with cache_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not payload:
        return None, "missing", "", ""
    return (
        payload.get("scholar_cited_by_count"),
        payload.get("scholar_status", "missing"),
        payload.get("scholar_query", ""),
        payload.get("scholar_url", ""),
    )


def enrich_single_scholar_paper(paper: dict[str, Any]) -> dict[str, Any]:
    current = dict(paper)
    cited_by_count, scholar_status, scholar_query, scholar_url = scholar_info_from_cache(current["arxiv_id"])
    current["scholar_cited_by_count"] = cited_by_count
    current["scholar_status"] = scholar_status
    current["scholar_query"] = scholar_query
    current["scholar_url"] = scholar_url
    current["cited_by_count"] = cited_by_count
    current["citation_status"] = scholar_status
    return current


def enrich_with_scholar_cache(papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    total = len(papers)
    update_run_status(
        stage="enrich_scholar_cache",
        scholar_cache_total_papers=total,
        scholar_cache_completed_papers=0,
    )
    for index, paper in enumerate(papers, start=1):
        enriched.append(enrich_single_scholar_paper(paper))
        if index == 1 or index % 1000 == 0 or index == total:
            update_run_status(
                stage="enrich_scholar_cache",
                scholar_cache_total_papers=total,
                scholar_cache_completed_papers=index,
                scholar_cache_found=sum(1 for item in enriched if item.get("citation_status") == "found"),
            )
    log_progress(
        f"[scholar-cache] loaded cached citations for {sum(1 for item in enriched if item.get('citation_status') == 'found')}/{total} papers"
    )
    return enriched


def enrich_with_scholar_fetch(papers: list[dict[str, Any]], parallel_requests: int = 12) -> list[dict[str, Any]]:
    total = len(papers)
    enriched: list[dict[str, Any] | None] = [None] * total
    cached_found = 0
    fetch_targets: list[tuple[int, dict[str, Any]]] = []

    update_run_status(
        stage="enrich_scholar_fetch",
        scholar_fetch_total_papers=total,
        scholar_fetch_cached_papers=0,
        scholar_fetch_requested_papers=0,
        scholar_fetch_completed_papers=0,
    )

    for index, paper in enumerate(papers):
        cache_path = DATA_RAW_SCHOLAR / f"{paper['arxiv_id']}.json"
        if cache_path.exists():
            enriched[index] = enrich_single_scholar_paper(paper)
            if enriched[index].get("citation_status") == "found":
                cached_found += 1
        else:
            fetch_targets.append((index, paper))

    log_progress(
        f"[scholar-fetch] cache ready for {total - len(fetch_targets)}/{total} papers; fetching {len(fetch_targets)} missing citations"
    )
    update_run_status(
        stage="enrich_scholar_fetch",
        scholar_fetch_total_papers=total,
        scholar_fetch_cached_papers=total - len(fetch_targets),
        scholar_fetch_requested_papers=len(fetch_targets),
        scholar_fetch_completed_papers=0,
        scholar_fetch_found=cached_found,
    )

    completed = 0
    found = cached_found
    if fetch_targets:
        with ThreadPoolExecutor(max_workers=max(1, parallel_requests)) as executor:
            future_map = {
                executor.submit(fetch_scholar_citation_for_paper, paper): (index, paper)
                for index, paper in fetch_targets
            }
            for future in as_completed(future_map):
                index, paper = future_map[future]
                payload = future.result()
                enriched[index] = enrich_single_scholar_paper(paper)
                completed += 1
                if enriched[index].get("citation_status") == "found":
                    found += 1
                if completed == 1 or completed % 100 == 0 or completed == len(fetch_targets):
                    log_progress(
                        f"[scholar-fetch] fetched {completed}/{len(fetch_targets)} missing citations; found={found}/{total}"
                    )
                    update_run_status(
                        stage="enrich_scholar_fetch",
                        scholar_fetch_total_papers=total,
                        scholar_fetch_cached_papers=total - len(fetch_targets),
                        scholar_fetch_requested_papers=len(fetch_targets),
                        scholar_fetch_completed_papers=completed,
                        scholar_fetch_found=found,
                        scholar_fetch_last_arxiv_id=payload.get("arxiv_id", ""),
                        scholar_fetch_last_status=payload.get("scholar_status", ""),
                    )

    final_rows = [row for row in enriched if row is not None]
    log_progress(f"[scholar-fetch] ready citations for {sum(1 for item in final_rows if item.get('citation_status') == 'found')}/{total} papers")
    return final_rows


def rank_papers(papers: list[dict[str, Any]], scoring_cfg: dict[str, Any]) -> list[dict[str, Any]]:
    decay_lambda = float(scoring_cfg["ranking"]["age_decay_lambda"])
    for paper in papers:
        cited_by_count = paper["cited_by_count"]
        citation_factor = 1.0 + math.log1p(max(0, cited_by_count or 0))
        freshness = math.exp(-decay_lambda * paper["age_days"])
        paper["citation_factor"] = round(citation_factor, 6)
        paper["freshness"] = round(freshness, 6)
        paper["total_score"] = round(citation_factor, 6)
        paper["hot_score"] = round(citation_factor * freshness, 6)
        paper["final_score"] = paper["hot_score"]

    total_sorted = sorted(papers, key=lambda item: (item["total_score"], item["cited_by_count"] or -1, item["published_date"], item["arxiv_id"]), reverse=True)
    hot_sorted = sorted(papers, key=lambda item: (item["hot_score"], item["cited_by_count"] or -1, item["published_date"], item["arxiv_id"]), reverse=True)

    total_ranks = {paper["arxiv_id"]: index for index, paper in enumerate(total_sorted, start=1)}
    hot_ranks = {paper["arxiv_id"]: index for index, paper in enumerate(hot_sorted, start=1)}
    for paper in papers:
        paper["total_rank"] = total_ranks[paper["arxiv_id"]]
        paper["hot_rank"] = hot_ranks[paper["arxiv_id"]]

    return hot_sorted


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            serialized = {field: row.get(field, "") for field in fields}
            writer.writerow(serialized)


def display_cited_by_count(value: int | None) -> int | str:
    return value if value is not None else "missing"


def md_table(rows: list[dict[str, Any]], score_field: str, rank_field: str | None = None) -> str:
    header = "| Rank | Title | Published | Citations | Score |\n| --- | --- | --- | --- | --- |\n"
    lines = []
    for index, paper in enumerate(rows, start=1):
        rank = paper.get(rank_field, index) if rank_field else index
        title = paper["title"].replace("|", " ")
        citations = display_cited_by_count(paper["cited_by_count"])
        lines.append(
            f"| {rank} | [{title}]({paper['abs_url']}) | {paper['published_date']} | {citations} | {paper[score_field]:.3f} |"
        )
    return header + "\n".join(lines)


def build_pages(papers: list[dict[str, Any]], config: dict[str, Any]) -> None:
    generated_at = now_utc().strftime("%Y-%m-%d %H:%M UTC")
    root_topic = config["taxonomy"]["root_topic"]
    root_topic_cfg = config["taxonomy"]["topics"][root_topic]
    topic_name = root_topic_cfg["name"]

    total_sorted = sorted(papers, key=lambda item: (item["total_score"], item["cited_by_count"] or -1, item["published_date"], item["arxiv_id"]), reverse=True)
    hot_sorted = sorted(papers, key=lambda item: (item["hot_score"], item["cited_by_count"] or -1, item["published_date"], item["arxiv_id"]), reverse=True)

    GENERATED_INDEX_PATH.write_text(
        "\n".join(
            [
                f"# {topic_name}",
                "",
                root_topic_cfg["description"],
                "",
                f"- Last updated: {generated_at}",
                f"- Total indexed papers: {len(papers)}",
                "- Data sources: arXiv for discovery, citation cache for enrichment.",
                "",
                "## Total Ranking",
                "",
                md_table(total_sorted[:20], "total_score", "total_rank"),
                "",
                "## Hot Ranking",
                "",
                md_table(hot_sorted[:20], "hot_score", "hot_rank"),
                "",
                "## Rebuild",
                "",
                "```bash",
                "py scripts/pipeline.py run",
                "```",
            ]
        ),
        encoding="utf-8",
    )

    for topic_id, topic_cfg in config["taxonomy"]["topics"].items():
        if topic_id == root_topic:
            continue
        topic_path = TOPICS_DIR / f"{topic_id}.md"
        topic_path.write_text(
            "\n".join(
                [
                    f"# {topic_cfg['name']}",
                    "",
                    "Keyword-query ranking lives in the GitHub Pages site data build.",
                    "",
                    f"Use the main ranking instead: [{topic_name}](index.md)",
                ]
            ),
            encoding="utf-8",
        )


OUTPUT_DROP_FIELDS = {
    "primary_topic",
    "subtopics",
    "relevance_score",
    "subtopic_scores",
    "openalex_id",
    "openalex_title",
}


def clean_output_paper(paper: dict[str, Any]) -> dict[str, Any]:
    current = dict(paper)
    for field in OUTPUT_DROP_FIELDS:
        current.pop(field, None)
    return current


def write_processed_outputs(papers: list[dict[str, Any]]) -> None:
    total_sorted = sorted(papers, key=lambda item: (item["total_score"], item["cited_by_count"] or -1, item["published_date"], item["arxiv_id"]), reverse=True)
    hot_sorted = sorted(papers, key=lambda item: (item["hot_score"], item["cited_by_count"] or -1, item["published_date"], item["arxiv_id"]), reverse=True)
    cleaned_papers = [clean_output_paper(paper) for paper in papers]

    write_jsonl(DATA_PROCESSED / "papers.jsonl", cleaned_papers)
    write_csv(
        DATA_PROCESSED / "ranked.csv",
        [
            {
                "arxiv_id": paper["arxiv_id"],
                "title": paper["title"],
                "published_date": paper["published_date"],
                "published_year": paper["published_year"],
                "cited_by_count": display_cited_by_count(paper["cited_by_count"]),
                "citation_status": paper["citation_status"],
                "total_rank": paper["total_rank"],
                "hot_rank": paper["hot_rank"],
                "total_score": paper["total_score"],
                "hot_score": paper["hot_score"],
                "final_score": paper["final_score"],
                "age_days": paper["age_days"],
                "matched_queries": ",".join(paper.get("matched_queries", [])),
                "abs_url": paper["abs_url"],
            }
            for paper in cleaned_papers
        ],
        ["arxiv_id", "title", "published_date", "published_year", "cited_by_count", "citation_status", "total_rank", "hot_rank", "total_score", "hot_score", "final_score", "age_days", "matched_queries", "abs_url"],
    )
    write_csv(
        DATA_PROCESSED / "total_ranked.csv",
        [
            {
                "rank": paper["total_rank"],
                "arxiv_id": paper["arxiv_id"],
                "title": paper["title"],
                "published_date": paper["published_date"],
                "cited_by_count": display_cited_by_count(paper["cited_by_count"]),
                "total_score": paper["total_score"],
                "abs_url": paper["abs_url"],
            }
            for paper in total_sorted
        ],
        ["rank", "arxiv_id", "title", "published_date", "cited_by_count", "total_score", "abs_url"],
    )
    write_csv(
        DATA_PROCESSED / "hot_ranked.csv",
        [
            {
                "rank": paper["hot_rank"],
                "arxiv_id": paper["arxiv_id"],
                "title": paper["title"],
                "published_date": paper["published_date"],
                "cited_by_count": display_cited_by_count(paper["cited_by_count"]),
                "hot_score": paper["hot_score"],
                "age_days": paper["age_days"],
                "abs_url": paper["abs_url"],
            }
            for paper in hot_sorted
        ],
        ["rank", "arxiv_id", "title", "published_date", "cited_by_count", "hot_score", "age_days", "abs_url"],
    )


def run_pipeline(options: RunOptions) -> list[dict[str, Any]]:
    ensure_dirs()
    config = {
        "taxonomy": load_yaml(CONFIG_DIR / "taxonomy.yaml"),
        "queries": load_yaml(CONFIG_DIR / "queries.yaml"),
        "keywords": load_yaml(CONFIG_DIR / "keywords.yaml"),
        "scoring": load_yaml(CONFIG_DIR / "scoring.yaml"),
    }

    papers = fetch_arxiv(config, options)
    log_progress(f"[pipeline] fetched raw papers={len(papers)}")
    update_run_status(stage="classify", raw_papers=len(papers))
    papers = classify_papers(papers, config)
    log_progress(f"[pipeline] classified papers={len(papers)}")
    update_run_status(stage="enrich_scholar_cache", classified_papers=len(papers))
    papers = enrich_with_scholar_cache(papers)
    log_progress(f"[pipeline] enriched papers={len(papers)}")
    update_run_status(stage="rank_and_write", enriched_papers=len(papers))
    papers = rank_papers(papers, config["scoring"])
    write_processed_outputs(papers)
    build_pages(papers, config)
    log_progress(f"[pipeline] outputs written papers={len(papers)}")
    update_run_status(stage="done", output_papers=len(papers))
    return papers


def refresh_citations_only() -> list[dict[str, Any]]:
    ensure_dirs()
    config = {
        "taxonomy": load_yaml(CONFIG_DIR / "taxonomy.yaml"),
        "queries": load_yaml(CONFIG_DIR / "queries.yaml"),
        "keywords": load_yaml(CONFIG_DIR / "keywords.yaml"),
        "scoring": load_yaml(CONFIG_DIR / "scoring.yaml"),
    }

    papers_path = DATA_PROCESSED / "papers.jsonl"
    papers = load_jsonl(papers_path)
    log_progress(f"[refresh-citations] loaded papers={len(papers)}")
    update_run_status(stage="enrich_scholar_fetch", loaded_papers=len(papers))
    papers = enrich_with_scholar_fetch(papers)
    papers = rank_papers(papers, config["scoring"])
    write_processed_outputs(papers)
    build_pages(papers, config)
    log_progress(f"[refresh-citations] outputs written papers={len(papers)}")
    update_run_status(stage="done", output_papers=len(papers))
    return papers


def rebuild_outputs_from_cache() -> list[dict[str, Any]]:
    ensure_dirs()
    config = {
        "taxonomy": load_yaml(CONFIG_DIR / "taxonomy.yaml"),
        "queries": load_yaml(CONFIG_DIR / "queries.yaml"),
        "keywords": load_yaml(CONFIG_DIR / "keywords.yaml"),
        "scoring": load_yaml(CONFIG_DIR / "scoring.yaml"),
    }

    papers = load_jsonl(DATA_PROCESSED / "papers.jsonl")
    for paper in papers:
        cited_by_count, scholar_status, scholar_query, scholar_url = scholar_info_from_cache(paper["arxiv_id"])
        paper["scholar_cited_by_count"] = cited_by_count
        paper["scholar_status"] = scholar_status
        paper["scholar_query"] = scholar_query
        paper["scholar_url"] = scholar_url
        paper["citation_status"] = scholar_status
        paper["cited_by_count"] = cited_by_count

    papers = rank_papers(papers, config["scoring"])
    write_processed_outputs(papers)
    build_pages(papers, config)
    return papers


def rebuild_from_raw_arxiv(only_queries: set[str] | None = None) -> list[dict[str, Any]]:
    ensure_dirs()
    config = {
        "taxonomy": load_yaml(CONFIG_DIR / "taxonomy.yaml"),
        "queries": load_yaml(CONFIG_DIR / "queries.yaml"),
        "keywords": load_yaml(CONFIG_DIR / "keywords.yaml"),
        "scoring": load_yaml(CONFIG_DIR / "scoring.yaml"),
    }

    papers = load_all_arxiv_raw_papers(config, only_queries=only_queries)
    papers = classify_papers(papers, config)
    papers = enrich_with_scholar_cache(papers)
    papers = rank_papers(papers, config["scoring"])
    write_processed_outputs(papers)
    build_pages(papers, config)
    return papers


def fetch_only(options: RunOptions) -> list[dict[str, Any]]:
    ensure_dirs()
    config = {
        "taxonomy": load_yaml(CONFIG_DIR / "taxonomy.yaml"),
        "queries": load_yaml(CONFIG_DIR / "queries.yaml"),
        "keywords": load_yaml(CONFIG_DIR / "keywords.yaml"),
        "scoring": load_yaml(CONFIG_DIR / "scoring.yaml"),
    }
    return fetch_arxiv(config, options)


def self_check() -> None:
    config_files = [
        CONFIG_DIR / "taxonomy.yaml",
        CONFIG_DIR / "queries.yaml",
        CONFIG_DIR / "keywords.yaml",
        CONFIG_DIR / "scoring.yaml",
    ]
    for path in config_files:
        assert path.exists(), f"missing config: {path}"
        payload = load_yaml(path)
        assert payload, f"empty config: {path}"

    taxonomy = load_yaml(CONFIG_DIR / "taxonomy.yaml")
    root_topic = taxonomy["root_topic"]
    assert root_topic in taxonomy["topics"]
    assert "name" in taxonomy["topics"][root_topic]
    print("self-check passed")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a paper leaderboard from arXiv, citation cache, and static site assets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Fetch, rank, and build pages.")
    run_parser.add_argument("--years-back", type=int, default=None)
    run_parser.add_argument("--max-results-per-query", type=int, default=None)
    run_parser.add_argument("--only-queries", default=None, help="Comma-separated query ids to run.")

    subparsers.add_parser("refresh-citations", help="Reuse existing papers.jsonl and refresh Scholar citation cache only.")

    fetch_parser = subparsers.add_parser("fetch-only", help="Fetch arXiv raw results only, without ranking or citation enrichment.")
    fetch_parser.add_argument("--years-back", type=int, default=None)
    fetch_parser.add_argument("--max-results-per-query", type=int, default=None)
    fetch_parser.add_argument("--only-queries", default=None, help="Comma-separated query ids to run.")

    subparsers.add_parser("rebuild-from-cache", help="Rebuild outputs from existing Scholar citation cache.")
    rebuild_raw_parser = subparsers.add_parser("rebuild-from-raw", help="Rebuild outputs from existing raw arXiv query files.")
    rebuild_raw_parser.add_argument("--only-queries", default=None, help="Comma-separated query ids to include.")

    subparsers.add_parser("self-check", help="Run a tiny config sanity check.")
    return parser.parse_args(argv)


def parse_only_queries(value: str | None) -> set[str] | None:
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return set(items) or None


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    ensure_dirs()
    start_run_status(args.command, argv)
    try:
        if args.command == "self-check":
            self_check()
            finish_run_status("done", stage="done")
            return 0
        if args.command == "run":
            papers = run_pipeline(
                RunOptions(
                    years_back=args.years_back,
                    max_results_per_query=args.max_results_per_query,
                    only_queries=parse_only_queries(args.only_queries),
                )
            )
            print(f"built {len(papers)} papers")
            finish_run_status("done", stage="done", output_papers=len(papers))
            return 0
        if args.command == "fetch-only":
            papers = fetch_only(
                RunOptions(
                    years_back=args.years_back,
                    max_results_per_query=args.max_results_per_query,
                    only_queries=parse_only_queries(args.only_queries),
                )
            )
            print(f"fetched {len(papers)} papers")
            finish_run_status("done", stage="done", output_papers=len(papers))
            return 0
        if args.command == "refresh-citations":
            papers = refresh_citations_only()
            print(f"refreshed citations for {len(papers)} papers")
            finish_run_status("done", stage="done", output_papers=len(papers))
            return 0
        if args.command == "rebuild-from-cache":
            papers = rebuild_outputs_from_cache()
            print(f"rebuilt outputs for {len(papers)} papers")
            finish_run_status("done", stage="done", output_papers=len(papers))
            return 0
        if args.command == "rebuild-from-raw":
            papers = rebuild_from_raw_arxiv(
                only_queries=parse_only_queries(args.only_queries),
            )
            print(f"rebuilt from raw for {len(papers)} papers")
            finish_run_status("done", stage="done", output_papers=len(papers))
            return 0
    except Exception as exc:
        finish_run_status("failed", stage="failed", error_type=type(exc).__name__, error_message=str(exc))
        raise
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
