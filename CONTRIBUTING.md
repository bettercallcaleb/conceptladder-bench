# Contributing

New benchmark packs need one unambiguous correct choice per question, three plausible incorrect choices, four progressively harder questions per concept, and a primary technical source.

Before opening a pull request, validate the pack and run unit tests:

```bash
python3 -m conceptladder validate
python3 -m unittest discover -s tests
```

Please explain each answer with a source link in the pull request, identify the domain assumption being tested, and ask a second reviewer to challenge the distractors. Do not submit unpublished model evaluation results as evidence that the answer key is correct.

Changing an existing correct answer or prompt changes the dataset fingerprint. Mark such changes in release notes rather than quietly replacing benchmark versions.
