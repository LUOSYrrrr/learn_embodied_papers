# Keyword Extraction Policy

## Goal

Keywords should describe a paper's core contribution type and core method properties.

Do not tag a paper with generic artifacts it merely uses.

Examples of generic artifacts that should usually not become keywords by default:

- `benchmark`
- `dataset`
- `simulation`
- `hardware`
- `web data`
- `human data`

These should only be used when the paper's main contribution is actually the benchmark, dataset, hardware system, or data-centric method itself.

## Recommended pipeline

Use a theme-first, library-constrained workflow.

1. Read the title and abstract.
2. Determine exactly one primary `theme`.
3. Look up the allowed keyword sections for that theme in `config/canonical_keywords_library.yaml`.
4. Select `3-5` keywords from the library only.
5. Re-check every selected keyword against the abstract:
   - it must describe the paper's core contribution,
   - it must not be only an evaluation artifact,
   - it must be supported by the paper's wording.

This is intentionally not a pure string-matching pipeline.

Best practice is:

- `abstract -> theme inference -> library-constrained keyword selection -> abstract evidence check`

Not recommended:

- `library -> abstract` direct matching only:
  too brittle, misses paraphrases, and overweights literal phrase overlap.
- `abstract -> free-form keywords` only:
  too unstable, drifts into ad hoc tags, and breaks consistency across papers.

## Codex extraction prompt

Use the following two-stage prompt logic when Codex extracts keywords.

### Stage A: broad candidate extraction from title + abstract

Goal:

- extract as many meaningful, contribution-bearing candidate concepts as possible,
- but do not finalize them yet.

Prompt template:

```text
Read the paper title and abstract.

Task 1: infer exactly one primary theme from this set:
- model architecture
- training algorithm
- inference / test-time method
- benchmark
- dataset
- control method
- hardware system
- survey / review

Task 2: extract a broad candidate pool of meaningful concepts from the title and abstract.

Requirements for candidate concepts:
- they should reflect model family, training paradigm, inference mechanism, representation, task setting, transfer setting, hardware/interface, or control method;
- they should be semantically meaningful and reusable across papers;
- prefer concepts that are central to the claimed contribution;
- include paraphrased concepts even if the exact canonical keyword does not appear literally in the abstract;
- do not include generic words like data, model, robot, training, method;
- do not include benchmark, dataset, simulation, web data, or human data unless they are part of the paper's actual core contribution.

Return:
1. theme
2. candidate_concepts: a broad list of candidate concepts, typically 6-15 items
3. rationale: one short paragraph explaining the theme choice
```
```

### Stage B: map candidates to the canonical keyword library

Goal:

- convert the broad candidate pool into final library-constrained keywords.

Prompt template:

```text
You are given:
1. a paper title and abstract
2. one inferred theme
3. a candidate concept pool extracted from the abstract
4. the canonical keyword library
5. the theme-to-section mapping

Task:
- only select final keywords from the canonical keyword library;
- only select keywords that are allowed by the inferred theme;
- map paraphrased candidate concepts to the closest canonical keywords;
- prefer 3-5 final keywords, maximum 6;
- drop any candidate that is only an evaluation artifact or peripheral context.

Decision rules:
- a final keyword must be supported by the paper's actual contribution;
- a final keyword should be discriminative across papers;
- if two candidate concepts map to overlapping canonical tags, keep the more central one;
- if no library keyword fits a candidate concept well, drop it instead of inventing a new tag.

Return JSON:
{
  "arxiv_id": "...",
  "title": "...",
  "theme": "...",
  "candidate_concepts": [...],
  "keywords": [...]
}
```
```

In short:

- Stage A should be recall-oriented.
- Stage B should be precision-oriented.

This gives better results than direct literal keyword matching.

## Step 1: Determine the paper theme first

Assign the paper to one primary theme before extracting keywords.

Primary themes:

1. `model architecture`
2. `training algorithm`
3. `inference / test-time method`
4. `benchmark`
5. `dataset`
6. `hardware system`
7. `survey / review`

If a paper spans multiple themes, choose the one that best matches the main claimed contribution in the title and abstract.

Each paper should carry exactly one primary `theme` field.

## Step 2: Theme-specific keyword rules

### 1. Model architecture

Use keywords that reflect the model family and the architectural novelty.

Good keywords:

- `VLA`
- `VLM`
- `world model`
- `diffusion policy`
- `hierarchical control`
- `latent action`
- `memory augmentation`
- `cross-embodiment`
- `3D perception`
- `action tokenization`

Do not add:

- `benchmark`
- `dataset`

unless the paper's central novelty is introducing one.

### 2. Training algorithm

Use keywords that reflect how the model is optimized or adapted.

Good keywords:

- `imitation learning`
- `reinforcement learning`
- `offline RL`
- `online RL`
- `policy optimization`
- `fine-tuning`
- `post-training`
- `co-training`
- `pretraining`
- `preference learning`
- `reward modeling`

Do not add generic resource tags just because the method trains on them.

For example, using a benchmark during experiments does not justify a `benchmark` keyword.

### 3. Inference / test-time method

Use keywords that reflect how the method improves decision-time behavior.

Good keywords:

- `test-time adaptation`
- `reasoning`
- `planning`
- `retrieval augmentation`
- `memory augmentation`
- `chain-of-thought`
- `model predictive control`

### 4. Benchmark

Only use `benchmark` when the paper's main contribution is an evaluation suite, task suite, or systematic evaluation framework.

Then pair it with the problem domain, for example:

- `benchmark`
- `robotic manipulation`
- `dexterous manipulation`
- `bimanual manipulation`

### 5. Dataset

Only use `dataset` when the paper's main contribution is the data resource itself.

Then pair it with the data property, for example:

- `dataset`
- `robot demonstrations`
- `egocentric video`
- `tactile sensing`
- `cross-embodiment`

### 6. Hardware system

Only use hardware-oriented keywords when the paper's main novelty is the physical system, sensor, gripper, hand, teleoperation interface, or platform.

Good keywords:

- `hardware`
- `gripper-design`
- `robot-hand`
- `teleoperation`
- `tactile sensing`
- `force control`

### 7. Survey / review

Only use survey-oriented keywords when the paper is primarily a review or taxonomy paper.

Good keywords:

- `survey`
- `review`
- `taxonomy`

Do not mix survey papers with method keywords unless the survey itself proposes a substantive technical framework.

## Step 3: Keep method keywords discriminative

A keyword should help separate this paper from nearby papers.

Good discriminative examples:

- `VLA`
- `world model`
- `offline RL`
- `co-training`
- `diffusion policy`
- `egocentric video`
- `bimanual manipulation`

Bad low-information examples:

- `data`
- `model`
- `robot`
- `training`
- `benchmark` when the paper only evaluates on one
- `dataset` when the paper only uses one

## Step 4: Prefer contribution-bearing tags over context tags

Prefer:

- the method family
- the optimization method
- the inference mechanism
- the embodiment or task setting if it is central

Only then consider secondary context.

For example, if a paper improves a VLA through offline RL fine-tuning for long-horizon manipulation, the right keywords are closer to:

- `VLA`
- `reinforcement learning`
- `offline RL`
- `fine-tuning`
- `long-horizon planning`

and not:

- `benchmark`
- `dataset`
- `data`

unless those are the actual contribution.

## Step 5: Output style

Each paper should usually have:

- preferred: `3` to `5` keywords
- upper bound: `6` keywords

Prefer canonical short labels.

Examples:

- use `offline RL` instead of `offline reinforcement learning` if both mean the same thing
- use `VLA` instead of repeating `vision-language-action model`
- use `survey` instead of both `survey` and `review`

## Quick sanity checks

Before finalizing a paper's keywords, ask:

1. If I remove this keyword, does the paper's main idea change?
2. Is this keyword describing the contribution, or just the evaluation setup?
3. Would many unrelated papers also get this keyword for trivial reasons?

If the answer to 2 is "evaluation setup" or the answer to 3 is "yes", drop it.

## Output schema

Each extracted paper record should follow this shape:

```json
{
  "arxiv_id": "...",
  "title": "...",
  "theme": "model architecture",
  "keywords": ["VLA", "reasoning", "chain-of-thought", "planning"]
}
```

The `theme` is mandatory for new manual/model-assisted extraction.

## Library constraint

All final keywords must come from `config/canonical_keywords_library.yaml`.

No new keyword should be invented during extraction unless the library is updated first.
