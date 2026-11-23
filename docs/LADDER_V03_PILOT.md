# ConceptLadder v0.3: local pilot calibration

Date: 2026-11-23.

## Setup

- Benchmark: Ladder v0.3, 15 concept families x 4 levels x 4 variants = 240 questions per form
- Three runs per model: question/answer seeds (17/17), (17/63), (41/17)
- Local inference: llama.cpp llama-server, RTX 4090, temperature 0, max_tokens 64, no thinking, context 4096
- 14B: Qwen3-14B-Q4_K_M.gguf, Hugging Face revision a04a82c4739b3ef5fa6da7d10261db2c67dd1985, file SHA256 5eaa0870bd81ed3b58a630a271234cfa604e43ffb3a19cd68e54a80dd9d52a66
- 32B: Qwen3-32B-Q4_K_M.gguf, Hugging Face revision 931c84066f88693a02ab8de820cfcd066d913241, file SHA256 8df67573b2c23484e02ec7af295e39bed7ee774f3771d5fda2978265b59370e7
- 4B-class: local without-imatrix-q4-k-m.gguf, file SHA256 36968ed7eebbd0522074bd36d70b41d5703a14c315ef514f799753c7a011be6d
- llama-server binary SHA256 7c459348db492ff15fbe44474b1b4770eecc44ee9005600061e478a7e3a05398
- Unambiguous first-line answers are reparsed from saved raw responses when the older strict parser marked them invalid.

## Aggregate accuracy

| Question / answer seed | 4B Q4 | 14B Q4 | 32B Q4 |
| --- | ---: | ---: | ---: |
| 17 / 17 | 88/240 (36.7%) | 133/240 (55.4%) | 120/240 (50.0%) |
| 17 / 63 | 81/240 (33.8%) | 125/240 (52.1%) | 131/240 (54.6%) |
| 41 / 17 | 87/240 (36.3%) | 118/240 (49.2%) | 117/240 (48.8%) |
| Unweighted mean | 35.6% | 52.2% | 51.1% |

The 14B and 32B models consistently exceed the 4B baseline, but 32B does **not** consistently exceed 14B. The modest 1.1 percentage-point mean gap between 14B and 32B is not evidence of a true ranking.

## Per-level accuracy, aggregated across three forms

| Level | 4B | 14B | 32B |
| --- | ---: | ---: | ---: |
| L1 | 41.7% | 72.2% | 65.6% |
| L2 | 34.4% | 54.4% | 57.2% |
| L3 | 38.3% | 50.0% | 51.7% |
| L4 | 27.8% | 32.2% | 30.0% |

The 14B and 32B aggregate curves descend from L1 to L4. The 4B L3 rate still exceeds L2. Some concept-level ladders invert even for the larger models, so levels remain provisional.

## Sensitivity and limitations

- Same questions, reordered answers (17/17 vs 17/63): 14B changes by 8/240 (3.3 percentage points); 4B by 7/240 (2.9pp); 32B by 11/240 (4.6pp).
- Different generated values, fixed answer-order seed (17/17 vs 41/17): 14B changes by 15/240 (6.3pp); 4B by 1/240 (0.4pp); 32B by 3/240 (1.3pp).
- Hard v0.2 had a larger 14B difference of 27/240 (11.3pp) between seeds 17 and 41. Different benchmark versions are not directly equivalent.
- Only 15 underlying concepts; parameter variants and alternative orderings are correlated observations, not independent skills.
- Models differ in size and/or architecture; this is not a within-model BF16-versus-Q4 quantization-retention experiment.
- Scores depend on token budget, template, answer position and decoding. One 32B answer was the exact correct option text (the SQLite error code 0517), rather than a letter; v0.3.1 accepts such exact matches. Earlier strict-parsing tallies gave 130/240 rather than 131/240 on form 17/63. This pilot does not establish psychometric validity or statistical significance.

## Reproduce

    python3 -m conceptladder validate --suite ladder --seed 17
    python3 -m conceptladder run --suite ladder --seed 17 --answer-seed 17 --variants 4 --model local --url http://127.0.0.1:8080/v1 --out results/q17a17.json
    python3 -m conceptladder run --suite ladder --seed 17 --answer-seed 63 --variants 4 --model local --url http://127.0.0.1:8080/v1 --out results/q17a63.json
    python3 -m conceptladder calibrate results/q17a17.json results/q17a63.json --out results/calibration.json

The --suite hard v0.2 generator remains unchanged for legacy reproduction.
