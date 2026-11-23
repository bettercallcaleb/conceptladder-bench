# ConceptLadder v0.3: local pilot calibration

Date: 2026-11-23.

## Setup

- Benchmark: Ladder v0.3, 15 concept families x 4 levels x 4 variants = 240 questions per form
- Three runs per model: question/answer seeds (17/17), (17/63), (41/17)
- Local inference: llama.cpp llama-server, RTX 4090, temperature 0, max_tokens 64, no thinking, context 4096
- 14B: Qwen3-14B-Q4_K_M.gguf, Hugging Face revision a04a82c4739b3ef5fa6da7d10261db2c67dd1985, file SHA256 5eaa0870bd81ed3b58a630a271234cfa604e43ffb3a19cd68e54a80dd9d52a66
- 4B-class: local without-imatrix-q4-k-m.gguf, file SHA256 36968ed7eebbd0522074bd36d70b41d5703a14c315ef514f799753c7a011be6d
- llama-server binary SHA256 7c459348db492ff15fbe44474b1b4770eecc44ee9005600061e478a7e3a05398
- Unambiguous first-line answers are reparsed from saved raw responses when the older strict parser marked them invalid.

## Aggregate accuracy

| Question / answer seed | 4B Q4 | 14B Q4 |
| --- | ---: | ---: |
| 17 / 17 | 88/240 (36.7%) | 133/240 (55.4%) |
| 17 / 63 | 81/240 (33.8%) | 125/240 (52.1%) |
| 41 / 17 | 87/240 (36.3%) | 118/240 (49.2%) |
| Unweighted mean | 35.6% | 52.2% |

The 14B model leads on all three tested forms.

## Per-level accuracy, aggregated across three forms

| Level | 4B | 14B |
| --- | ---: | ---: |
| L1 | 41.7% | 72.2% |
| L2 | 34.4% | 54.4% |
| L3 | 38.3% | 50.0% |
| L4 | 27.8% | 32.2% |

The 14B aggregate descends from L1 to L4. The 4B L3 rate still exceeds L2. Some concepts invert even for 14B, so levels remain provisional.

## Sensitivity and limitations

- Same questions, reordered answers (17/17 vs 17/63): 14B changes by 8/240 (3.3 percentage points); 4B by 7/240 (2.9pp).
- Different generated values, fixed answer-order seed (17/17 vs 41/17): 14B changes by 15/240 (6.3pp); 4B by 1/240 (0.4pp).
- Hard v0.2 had a larger 14B difference of 27/240 (11.3pp) between seeds 17 and 41. Different benchmark versions are not directly equivalent.
- Only 15 underlying concepts; parameter variants and alternative orderings are correlated observations, not independent skills.
- Models differ in size and/or architecture; this is not a within-model BF16-versus-Q4 quantization-retention experiment.
- Scores depend on token budget, template, answer position and decoding. This pilot does not establish psychometric validity or statistical significance.

## Reproduce

    python3 -m conceptladder validate --suite ladder --seed 17
    python3 -m conceptladder run --suite ladder --seed 17 --answer-seed 17 --variants 4 --model local --url http://127.0.0.1:8080/v1 --out results/q17a17.json
    python3 -m conceptladder run --suite ladder --seed 17 --answer-seed 63 --variants 4 --model local --url http://127.0.0.1:8080/v1 --out results/q17a63.json
    python3 -m conceptladder calibrate results/q17a17.json results/q17a63.json --out results/calibration.json

The --suite hard v0.2 generator remains unchanged for legacy reproduction.
