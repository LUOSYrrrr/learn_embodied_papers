#!/usr/bin/env python3
"""Build a Zotero-ready RIS batch from arXiv metadata verified in the browser."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
META = Path("/tmp/vla-meta-lines.jsonl")
OUT = ROOT / "pdfs/vla-rl/vla-rl-verified-batch-01.ris"

SLUGS = {
    "2307.15818": "rt-2",
    "2505.19789": "rl-vla-generalization",
    "2605.25477": "expo-ft",
    "2605.17486": "dygro-vla",
    "2605.30226": "bora",
    "2511.00091": "self-improving-vla",
    "2509.04063": "arfm",
    "2508.02219": "co-rft",
    "2605.11151": "rankq",
    "2602.11075": "rise-compositional-world-model",
    "2505.22094": "reinflow",
    "2409.00588": "dppo",
    "2110.06169": "iql",
    "2006.09359": "awac",
    "2410.21845": "hil-serl",
}

VENUES = {
    "2505.22094": ("CONF", "Conference on Neural Information Processing Systems", "2025"),
    "2110.06169": ("CONF", "International Conference on Learning Representations", "2022"),
    "2006.09359": ("CONF", "Conference on Robot Learning", "2020"),
    "2410.21845": ("CONF", "Conference on Robot Learning", "2024"),
}


def ris_author(name: str) -> str:
    parts = name.strip().split()
    return name if len(parts) < 2 else f"{parts[-1]}, {' '.join(parts[:-1])}"


records = []
for line in META.read_text().splitlines():
    item = json.loads(line)
    arxiv_id = item["id"]
    slug = SLUGS[arxiv_id]
    kind, venue, year = VENUES.get(
        arxiv_id, ("RPRT", "", item["date"].split("/")[0])
    )
    pdf = (ROOT / f"pdfs/vla-rl/{slug}.pdf").resolve().as_uri()
    fields = [f"TY  - {kind}", f"TI  - {item['title']}"]
    fields.extend(f"AU  - {ris_author(author)}" for author in item["authors"])
    fields.append(f"PY  - {year}")
    if venue:
        fields.append(f"T2  - {venue}")
    fields.extend(
        [
            f"UR  - https://arxiv.org/abs/{arxiv_id}",
            f"DO  - 10.48550/arXiv.{arxiv_id}",
            "N1  - Verified VLA+RL route item; metadata checked against the arXiv abstract page.",
            f"L1  - {quote(pdf, safe=':/')}",
            "KW  - VLA+RL",
            "KW  - robot reinforcement learning",
            "ER  -",
        ]
    )
    records.append("\n".join(fields))

OUT.write_text("\n\n".join(records) + "\n")
print(f"wrote {len(records)} records to {OUT}")
