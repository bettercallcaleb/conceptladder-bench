# ConceptLadder Bench

**Does the model know the rule, understand why it works, and still apply it when the situation changes?**

ConceptLadder is a small, open-source knowledge-depth benchmark. Instead of mixing unrelated trivia, it puts four progressively harder questions around the *same technical concept*. It also compares the exact same questions across two model builds, including original GGUF and a Q4Fit quantization.

**v0.3:** three reproducible suites: **Classic** (36 basic MCQs), **Hard v0.2** (the original 240 challenging technical scenarios, unchanged), and **Ladder v0.3** (240 scenarios with redesigned L1 entry questions and separately controlled question and answer seeds). MIT licensed. Python standard library only.

## Ladder v0.3: calibrated pilot

The previous Hard v0.2 was useful for challenging small models, but its four levels were not consistently ordered: a Qwen3 14B pilot scored *worse* on L1 than on L2. Instead of rewriting past benchmark data, v0.3 introduces a separate `--suite ladder`. The old `--suite hard` stays unchanged for exact reproduction of published runs.

Ladder v0.3 makes the entry task simpler for 11 of 15 concepts (including TCP ACKs, SQLite, DNS, file offsets, JWT and RBAC) while leaving the difficult cases at L2–L4. Answers are still determined by local computations or real SQLite/POSIX operations. The initial 14B pilot displayed a strictly descending **aggregate** L1→L4 success rate on three forms; individual concepts can still violate this order, so the levels remain provisional rather than psychometrically validated.

```bash
python3 -m conceptladder validate --suite ladder
python3 -m conceptladder run   --suite ladder --variants 4 --seed 17 --answer-seed 63   --url http://127.0.0.1:8080/v1 --model local   --out results/ladder-q17-a63.json
```

`--seed` changes the **scenario values**. `--answer-seed` independently changes A/B/C/D choice ordering. Set both the same across models for fair paired comparisons; hold the question seed fixed and change only the answer seed to measure positional bias. If omitted, `--answer-seed` equals `--seed` and existing run behavior is preserved.

Use `python3 -m conceptladder calibrate results/*.json --out results/calibration.json` to see per-level/per-family accuracy, option-position sensitivity, and matching-model comparisons. Raw unambiguous letter responses are reparsed in this audit; original run files remain unchanged.

### Initial local calibration (no thinking, temperature 0)

| Question / answer seeds | Qwen3 4B-class Q4 | Qwen3 14B Q4_K_M |
| --- | ---: | ---: |
| 17 / 17 | 88/240 | 133/240 |
| 17 / 63 (same questions, reordered options) | 81/240 | 125/240 |
| 41 / 17 (different scenarios) | 87/240 | 118/240 |

The 14B entry-to-boundary level rates averaged across these three runs are approximately 72%, 54%, 50%, 32%. These results are *exploratory*: the 240 questions are generated from only 15 concept families; answer placement, chat formatting, reasoning budget and model architecture all affect scores. A BF16-vs-Q4 inference requires matching model lineage and a stronger reference baseline.

## Hard suite: 240 technical scenarios

Hard is the recommended stress test when a model saturates Classic. Instead of obvious distractors, all four answers have the same character length, and the correct answer's position is independently randomized by question.

The 15 scenario families shared by Hard and Ladder cover:
- **Networking (96 questions):** TCP reassembly with wraparound, TCP send-window calculations, longest-prefix routing, IPv4 re-fragmentation, CIDR boundary logic, DNS TTL dependencies.
- **Databases (48 questions):** real SQLite WAL transaction schedules, SQL window frames, LEFT JOIN + NULL behavior.
- **Linux/systems (48 questions):** actual POSIX `dup` and file-offset behavior, umask/chmod transformations, endian and bitfield computations.
- **Security/Kubernetes (48 questions):** JWT time/audience/issuer boundaries, RBAC namespace/subresource scope, hard scheduling feasibility filters.

```bash
python3 -m conceptladder list --suite hard
python3 -m conceptladder validate --suite hard
python3 -m conceptladder run   --suite hard --variants 4 --seed 17   --url http://127.0.0.1:8080/v1 --model local   --out results/hard-local.json
```

To run one domain only, add `--packs net-hard`, `--packs db-hard`, `--packs sys-hard`, or `--packs security-hard`. Run `python3 -m conceptladder score results/hard-local.json` to grade a saved run. Comparisons require the same question-set hash and answer-order seed.

**Important calibration limit:** this is a hard procedural-reasoning stress test, not 240 independent facts. Generated examples are different variants of 15 underlying concepts, so report both item accuracy and per-concept performance. A 4B model may perform near the 25% guessing baseline; if so, a BF16-to-Q4 comparison on that model does not meaningfully measure retention. Use Classic and Hard as complementary diagnostics and include a stronger-model baseline before claiming discrimination.

The Hard source-generation code lives in `conceptladder/hardcases/`; SQLite and POSIX answers are computed using live standard-library operations. Numerical answers come from deterministic reference functions. Test cases have corresponding original documentation links.

## What it measures

Each concept has one question at each level:

| Level | Test |
| --- | --- |
| 1 · Recognition | Identify the fact or rule |
| 2 · Mechanism | Explain the operative condition |
| 3 · Transfer | Apply the rule to a different scenario |
| 4 · Boundary | Know when the usual shortcut fails |

Two complementary scores are reported:

- **Accuracy:** correct answers divided by all questions.
- **Contiguous depth:** for each concept, count levels passed consecutively from level 1 until the first failure (0–4). Average across concepts. Passing level 4 while failing level 2 does not magically grant depth 4.

With one question per level, the depth score is a *pilot diagnostic*, not a psychometrically validated measure of expertise. Do not interpret a one-question difference as proof that a model has gained or lost a capability.

All questions are independently answerable multiple choice; nothing is disclosed from an earlier answer. Answer alternatives are pseudorandomly positioned across A/B/C/D; per-form balance must be audited rather than assumed. Scoring requires no LLM judge.

## Run it

Requirements: Python 3.9+ and an OpenAI-compatible chat-completions endpoint, for example `llama-server`.

```bash
git clone https://github.com/bettercallcaleb/conceptladder-bench
cd conceptladder-bench
python3 -m conceptladder list
python3 -m conceptladder validate
python3 -m unittest discover -s tests
```

Start your high-precision GGUF with llama.cpp in another terminal:

```bash
./llama-server -m /models/original-f16.gguf --port 8080 -ngl 99
```

Evaluate:

```bash
python3 -m conceptladder run \
  --url http://127.0.0.1:8080/v1 \
  --model original \
  --seed 17 \
  --out results/original.json
```

Restart the server with your quantized GGUF (standard Q4_K or a custom Q4Fit build), keeping the same inference settings:

```bash
./llama-server -m /models/my-q4.gguf --port 8080 -ngl 99
python3 -m conceptladder run \
  --url http://127.0.0.1:8080/v1 \
  --model my-q4 \
  --seed 17 \
  --out results/my-q4.json
```

Compare *paired* answers:

```bash
python3 -m conceptladder compare results/original.json results/my-q4.json --out results/comparison.json
```

You'll see accuracy, average contiguous depth, exactly which questions flipped, and a **knowledge loss rate**: the fraction of previously correct reference answers that the candidate got wrong. It also reports reverse flips, where the candidate gains an answer. Neither direction proves the cause is quantization unless the backend, model provenance, prompt template, and decoding setup are controlled.

Run a single subject pack with `--packs tcp`, `--packs tls13`, or `--packs sqlite` on *both* builds. Read a saved run using `python3 -m conceptladder score results/original.json`.

The runner uses temperature 0 and asks for one letter. Some reasoning-model APIs ignore low token budgets or include commentary. Unparseable outputs count as wrong and are reported, never silently dropped. The request format and results are plain JSON.

## Packs and evidence

| Pack | Three knowledge ladders | Reference |
| --- | --- | --- |
| `tcp` | handshake, flow control, FIN semantics | [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html) |
| `tls13` | early data, forward secrecy, authentication | [RFC 8446](https://www.rfc-editor.org/rfc/rfc8446.html) |
| `sqlite` | WAL concurrency, snapshot upgrades, checkpoints | [SQLite isolation](https://www.sqlite.org/isolation.html), [WAL docs](https://www.sqlite.org/wal.html) |

These are original scenarios authored for ConceptLadder, not reworded benchmark datasets. The reference links let contributors check technical claims; the question set has not yet undergone independent expert review.

Each pack is a JSON file under `conceptladder/packs/`. A concept defines four questions in order; each question contains one correct option and three plausible alternatives. The benchmark validates uniqueness and structure, creates reproducible answer positions using a seed, and fingerprints the complete dataset. Comparisons reject mismatched datasets and seeds.

## Add a new cluster

1. Copy the structure of an existing `conceptladder/packs/*.json` file and choose a new pack ID.
2. Add 3–5 tightly defined technical concepts, with four *linked* levels per concept.
3. Use primary documentation as the source; specify assumptions in the question so exactly one answer is true.
4. Run `python3 -m conceptladder validate` and `python3 -m unittest discover -s tests`.
5. Request independent review of every answer and distractor before claiming a stable benchmark release.

Keep the core suite small. Add packs only when every question can be defended from a primary source. Suggested future packs: Linux virtual memory, DNSSEC, database locking, and GGUF quantization behavior.

## Interpretation and limits

This is a *pilot instrument*, not a replacement for MMLU-Pro, GPQA, or expert-rated evaluation. Multiple choice permits guesses (25% random baseline); four linked questions per concept are too few to diagnose knowledge precisely. Results on public items may be contaminated by training or targeted tuning.

For credible original-vs-quant comparisons, run at least three independent seeds or question paraphrases per model, report per-item paired flips, note ambiguous or invalid output rates, and verify the effect on independent holdouts. Dataset hashes and seeds ensure artifact consistency; they do not establish statistical significance. The implementation does not collect hidden chain-of-thought or use an external LLM for grading.

This suite complements [Q4Fit](https://github.com/bettercallcaleb/q4fit). Q4Fit's KLD can measure next-token distribution changes; ConceptLadder measures discrete task outcomes. The two metrics are related but **not interchangeable**.

## License

MIT. Contributions are welcome; please include a source and a short explanation for each correct answer in your pull request.
