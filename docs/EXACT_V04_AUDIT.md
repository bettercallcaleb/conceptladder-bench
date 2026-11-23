# Exact v0.4 — adversarial review and pilot

Date: 2026-11-23. Recommended suite: Exact v0.4 (240 open-answer technical scenarios).

## Why the old multiple-choice scores are invalid

Ladder v0.3 was compromised by answer-option artifacts. Choosing the second-smallest numeric option without reading the question scored 63–65% across multiple forms. This rule beat the Q4 model baselines. Classic, Hard and Ladder remain for reproduction but are not recommended for leaderboards.

Exact v0.4 removes all alternatives, uses typed answer normalization without an LLM grader, and replaces short count answers with ordered per-request/per-node decision masks in several families. It retains the 15 technical concept templates, four nominal levels and four parameter variants.

## Automatic prompt-blind attack

The built-in blind-audit command trains a most-frequent-answer lookup using only concept family and level on seeds 17 and 41. It then evaluates on disjoint seeds 91, 123 and 777 without looking at question text.

| Held-out seed | Correct | Accuracy |
| --- | ---: | ---: |
| 91 | 31/240 | 12.9% |
| 123 | 28/240 | 11.7% |
| 777 | 28/240 | 11.7% |
| Total | 87/720 | 12.1% |

Run:

    python3 -m conceptladder validate --suite exact
    python3 -m conceptladder blind-audit --out results/blind-audit.json

The baseline is not a chance rate; different attacks could succeed. The entire dataset and generator are public.

## Reproducibility

- Gold oracles use deterministic calculations and selected actual SQLite/POSIX operations.
- The Exact suite has no A/B/C/D positions. Answer ordering seed does not affect it.
- All raw responses, invalid-format outcomes and dataset hashes are retained.
- Historical Classic, Hard and Ladder question fingerprints are frozen and tested.
- No independent expert audit of every scenario or psychometric validation has been completed.

## Local Q4 pilot

Inference: RTX 4090, llama.cpp, temperature=0, 4096 context, max_tokens=64, thinking disabled.

| Model | Seed 17 | Seed 41 | Combined | Invalid format |
| --- | ---: | ---: | ---: | ---: |
| Local 4B-class Q4 | 25/240 | 30/240 | 55/480 (11.5%) | 40 + 37 |
| Qwen3-14B Q4_K_M | 72/240 | 81/240 | 153/480 (31.9%) | 15 + 15 |
| Qwen3-32B Q4_K_M | 91/240 | 98/240 | 189/480 (39.4%) | 11 + 9 |

The 32B beat the 14B on both paired forms, by 19/240 and 17/240. A descriptive bootstrap resampling the 15 technical families (not individual generated questions) gave a 32B–14B difference of +7.5pp, with an approximate 95% interval of +2.1 to +12.7pp. Given the small number of families, shared template structure, and test-time format dependence, this should not be treated as a validated general capability ranking.

On the **same** model-evaluation seeds (17 and 41), a family/level-only prompt-blind baseline trained on seeds 91 and 123 achieved 29/240 and 37/240 respectively, i.e. 66/480 (13.75%). Thus the 4B-class model is at or below a trivial blind baseline and the reference model should not be used for small BF16-to-Q4 retention comparisons on this suite.

By level, the 32B scored L1: 83/120, L2: 52/120, L3: 42/120, L4: 12/120. Level 4 is near the performance floor and not a well-calibrated difficulty measure.

Frozen scenario fingerprint for seed 17, four variants: 437d994c1a2c027902951811f2fd43b45468bc2ed4fd78f3d90e63c97743011a.
Only the Exact-v0.4 response format and dataset hash should be compared between runs; it is not comparable to earlier multiple-choice scores.

Scores across MCQ and Exact protocols are not comparable. In Exact, a model may include calculation steps rather than a single final value; if these lack an unambiguous first-line value or a FINAL line, they are graded as invalid. Format adherence thus affects task accuracy. For claims about quantization, pair original and quantized GGUF weights of the same model and repeat with unseen scenario seeds.

## Implementation

- conceptladder/exact.py: exact prompts, typed parsers and SQLite reference cases
- conceptladder/exact_balanced.py: varied scenarios, bit-string decision masks
- conceptladder/audit.py: prompt-blind control
- tests/test_exact_oracles.py: independent recomputation of DNS timelines, RBAC, Kubernetes eligibility, JWT claims and actual POSIX chmod permissions
- conceptladder/cli.py: run, score, compare, blind-audit

This is a reproducible technical stress test, not a validated general intelligence or knowledge-depth score.
