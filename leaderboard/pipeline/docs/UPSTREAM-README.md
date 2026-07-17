# Paper Leaderboard For You

<p align="center">
  <img src="./docs/paper-leaderboard-logo-d.svg" alt="Paper Leaderboard logo" width="160" />
</p>

Build a paper leaderboard for your own field.

This repository provides a **reusable workflow**, including:

- field-specific search phrase design
- arXiv paper retrieval
- citation enrichment
- ranking
- keyword tagging
- a static frontend

The goal is not just to collect papers, but to help you build a field-specific paper leaderboard that is actually reusable and publishable.

[中文说明](./README.zh-CN.md) | [Demo](https://dreamfallenflowers.github.io/Paper-Leaderboard-For-Robot-Manipulation/)

## What this repository includes

- reusable pipeline scripts
- example configs
- keyword policy docs
- a canonical keyword library
- a static frontend reference

## Before you start

Keep these two things in mind first:

- if you want reliable retrieval, you must first design `config/queries.yaml` carefully
- if you want citation counts, you must configure `SERPER_API_KEY` or `SERPER_API_KEYS`

Install the only required dependency:

```bash
python -m pip install -r requirements.txt
```

## Build your own paper leaderboard

### Pipeline overview

<p align="center">
  <img src="./docs/pipeline-diagram.svg" alt="Paper leaderboard pipeline diagram" width="100%" />
</p>

1. build the search keywords and query expressions for your field
2. use those queries to retrieve arXiv paper metadata
3. use the Serper API to search Google Scholar for the corresponding arXiv papers and collect citation counts
4. compute paper scores and rankings
5. for a minimal demo, keywords are optional; but for a truly filterable, explorable, publishable leaderboard, they are almost essential
6. build the frontend site data and publish the leaderboard

**In practice, the only parts that usually require real manual effort are Serper setup and keyword extraction policy**. The rest is exactly where the model helps most, which is why the overall workflow can stay very simple.

### Build the search queries

Edit `config/queries.yaml`.

This is your hand-designed retrieval plan.
It decides which papers you will capture at all.

A better workflow is:

- first list the terms, task names, model families, and neighboring concepts in your field
- manually test those phrases
- group them into query blocks
- then write them into `config/queries.yaml`

Then use those queries to fetch basic arXiv metadata such as title, abstract, authors, and published date.

Edit `config/taxonomy.yaml`.

This file defines:

- the root topic name
- subtopic names
- the short descriptions used in generated pages

Edit `config/keywords.yaml`.

This file is **not** the canonical keyword library.
It is the phrase-level relevance and subtopic matching config used by the pipeline.

## Keyword extraction policy

This template assumes a **keyword workflow constrained by a canonical keyword library**.

Keyword extraction is usually the **hardest part of the whole pipeline**.

If you only want to run a minimal version, you can skip it temporarily.

But if you want your leaderboard to support practical keyword filtering, this step is very close to unavoidable.

The rough logic is:

- infer the paper theme first
- extract candidate concepts from the title and abstract
- map those candidates to the canonical keyword library
- only keep tags that describe the actual core contribution

Read:

- `config/keyword_extraction_policy.md`
- `config/canonical_keywords_library.md`
- `config/canonical_keywords_library.yaml`

**You should modify `config/keyword_extraction_policy.md`**.

At minimum, you should adapt it for your own field:

- how themes should be divided
- what should count as a keyword

If this policy is not adapted to your field, the extracted keywords will often look plausible but still fail at real filtering and ranking.

If you use a model for keyword extraction, do not let it invent arbitrary tags. Keep it constrained by the keyword library.

Also note:

- `scripts/pipeline.py` itself does **not** generate model keywords
- `scripts/build_site_data.py` only reads keyword files if they already exist
- in the real workflow, keyword extraction is an **explicit extra step**
- and that extra step is formally based on LLM extraction from arXiv abstracts

## Repository structure

```text
config/     query, taxonomy, keyword, and scoring config
scripts/    fetch / rebuild / export scripts
site/       static frontend reference
topics/     generated markdown ranking pages
data/       local caches and outputs
```

The `data/` folders are intentionally empty in this template.

## Main commands

### Full pipeline

```bash
python scripts/pipeline.py run
```

Fetch, rank, and rebuild outputs.

### Fetch raw arXiv results only

```bash
python scripts/pipeline.py fetch-only
```

Useful when you want to check retrieval coverage before deciding how to rank the results.

### Refresh citations only

```bash
python scripts/pipeline.py refresh-citations
```

Useful when you already have `data/processed/papers.jsonl` and only want to refresh citation counts.

The current template implementation does this by:

- using the **Serper API**
- searching for the corresponding **arXiv paper** in Google Scholar
- caching the citation data locally

### Rebuild from existing raw files

```bash
python scripts/pipeline.py rebuild-from-raw
```

Useful when you changed filtering or scoring logic but do not want to fetch arXiv again.

### Rebuild frontend site data

```bash
python scripts/build_site_data.py
```

This generates the JSON files used by the frontend.

### Keyword extraction with an LLM

The real keyword extraction workflow is:

- read each paper's arXiv title and abstract
- infer the paper theme first
- extract candidate concepts that reflect the core contribution
- map those candidates to the canonical keyword library
- write the final keyword rows into:
- `data/processed/model_keywords/`

The official keyword workflow is therefore **LLM-assisted extraction from arXiv abstracts**, not a fixed-rule baseline.

This entire workflow is handled by the model. What you really need to check before running it is the rule file and the canonical keyword library. See [Keyword extraction policy](#keyword-extraction-policy).

The recommended output format is a JSONL keyword file keyed by `arxiv_id`, so that `scripts/build_site_data.py` can consume it directly.

Reference command:

```bash
python scripts/extract_model_keywords.py
```

## Expected outputs

Processed outputs:

- `data/processed/papers.jsonl`
- `data/processed/ranked.csv`
- `data/processed/total_ranked.csv`
- `data/processed/hot_ranked.csv`

Frontend outputs:

- `site/data/papers.min.json`
- `site/data/tags.json`
- `site/data/aliases.json`
- `site/data/stats.json`

Generated markdown outputs:

- `topics/index.md`
- `topics/<subtopic>.md`

## How to adapt this template to your own field

### 1. Build the search queries first

Edit `config/queries.yaml`.

This is your hand-designed search plan.
It controls which papers are fetched at all.

A good workflow is:

- brainstorm the phrases, task names, model families, neighboring concepts, and terminology that define your field
- test and refine those phrases manually
- group them into query blocks
- place those blocks into `config/queries.yaml`

Then use those query blocks to fetch arXiv paper metadata such as title, abstract, authors, and published date.

If the query design is weak, the leaderboard will be weak no matter how polished the rest of the pipeline is.

### 2. Replace the taxonomy

Edit `config/taxonomy.yaml`.

This file defines:

- the root topic name
- subtopic names
- short descriptions used by generated pages

### 3. Replace the relevance phrases

Edit `config/keywords.yaml`.

This file is not the canonical keyword library.
It is the phrase-level relevance and subtopic matching config used by the pipeline.

### 4. Replace the site keyword aliases

Edit `config/site_keywords.yaml`.

This file drives frontend alias normalization and search convenience.

Each entry is shaped like:

```yaml
keywords:
  - label: Example Keyword
    aliases:
      - example
      - example keyword
```

If you leave the example values unchanged, your search aliases will be meaningless for your own field.

## Keyword extraction policy

This template assumes a **library-constrained** keyword workflow.

Keyword extraction is usually the **hardest part of the whole pipeline**.

It is technically optional if you only want a bare ranking demo.
It is practically essential if you want a leaderboard that people can explore, filter, and reuse seriously.

In practice, leaderboard quality is often limited less by the ranking formula and more by whether the keyword policy actually matches the structure of your field.

That means:

- infer the paper's theme first
- collect candidate concepts from the title and abstract
- map those concepts to a canonical keyword library
- only keep contribution-bearing tags

Read:

- `config/keyword_extraction_policy.md`
- `config/canonical_keywords_library.md`
- `config/canonical_keywords_library.yaml`

You should expect to modify `config/keyword_extraction_policy.md` for your own field.

In particular, you will usually need to adjust:

- what counts as a core contribution
- which themes are appropriate
- which artifacts should be treated as keywords vs evaluation context
- how conservative or broad the keyword assignment should be

If this policy is not adapted to your field, the extracted keywords will often look superficially plausible but be poor for real filtering and ranking.

If you use a model for keyword extraction, do not let it invent arbitrary tags.

Important:

- `scripts/pipeline.py` does **not** generate model keywords by itself
- `scripts/build_site_data.py` only consumes keyword files if they already exist
- keyword extraction is therefore an explicit extra step in your real workflow
- the intended extra step is LLM-based extraction from arXiv abstracts

## Frontend reference

The `site/` folder is a static reference implementation.

Preview locally:

```bash
cd site
python -m http.server 8000
```

Then open:

```text
http://127.0.0.1:8000/
```

The frontend becomes useful only after `site/data/*.json` has been generated.

Once site data has been built, this reference frontend supports both publication-date filtering and keyword filtering.

Here are the parts you will most likely want to modify:

- title and copy
- default sort labels

### Replace frontend keyword aliases

Edit `config/site_keywords.yaml`.

It handles alias normalization and search convenience on the frontend.

The format is roughly:

```yaml
keywords:
  - label: Example Keyword
    aliases:
      - example
      - example keyword
```

If you do not change this file, the frontend keyword aliases will have little meaning for your own field.

## Important caveats

### Citation coverage matters

If your citation cache only covers a small share of papers, your rankings will systematically undercount the rest.

### Query design matters more than code polish

Most leaderboard quality comes from:

- good query coverage
- good filtering
- good keyword policy

not from fancy frontend behavior.

### Serper setup is required for live citation refresh

For this template as currently shipped:

- `refresh-citations` uses the Serper API to search for the corresponding arXiv paper in Google Scholar results
- you need `SERPER_API_KEY` or `SERPER_API_KEYS` in your environment for live citation fetching
- without those keys, citation status will remain missing unless you already have local scholar cache files

## Build your own leaderboard

I strongly believe that real citation signal is more valuable than loud promotion.

If you build and publish a paper leaderboard for your own field, it can genuinely help more people.

Pull requests are welcome, and you are encouraged to submit the repository link to your own paper leaderboard here. If you do, do not forget to attach the corresponding frontend page in your GitHub project homepage.

https://github.com/DreamFallenFlowers/Paper-Leaderboard-For-Robot-Manipulation
