# Contributing to LC-JSON

Thank you for your interest in contributing to the LC-JSON (Learning Content JSON) specification. This document describes how to file issues, propose changes, and submit pull requests.

## Quick orientation

- **Specification text:** [`README-spec.md`](README-spec.md), [`NORMATIVE.md`](NORMATIVE.md), [`question-types-reference.md`](question-types-reference.md).
- **Schemas:** [`schemas/`](https://github.com/lc-json/specification/tree/main/schemas) — JSON Schema Draft 7.
- **Examples:** [`examples/`](https://github.com/lc-json/specification/tree/main/examples) — 35 examples spanning all five artifact types, including complete documents and question, item, and structure fragments.
- **Conformance tests:** [`tests/`](https://github.com/lc-json/specification/tree/main/tests) — valid and invalid cases per clause; see [`tests/README.md`](https://github.com/lc-json/specification/tree/main/tests/README.md).
- **Implementation directory:** [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md).

## Filing issues

Open an issue for:

- **Bugs in the specification text, schemas, or examples.** Please include the file and line, the text in question, and a clear description of the discrepancy.
- **Proposals for new question types or new properties.** Describe the use case (which audience, which exam or subject, which scoring semantics), the rationale, and a draft schema or example if you have one.
- **Conformance questions.** First check [`NORMATIVE.md`](NORMATIVE.md); it is the authoritative source for implementer requirements. If the spec is ambiguous, file an issue noting the ambiguous passage.
- **Implementations to list.** See [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) for the listing format.

A short, focused issue is more useful than a long one. If you are not sure whether something belongs as an issue or a discussion, open an issue.

## Submitting pull requests

| Change type | Process |
|---|---|
| Typo, broken link, small clarification | PR directly. |
| Schema or example fix | Open an issue describing the bug; reference it in the PR. Include a conformance test case under [`tests/valid/`](tests/valid/) or [`tests/invalid/`](tests/invalid/) if applicable. |
| New schema or new question type | Open an issue first to discuss. PRs without prior discussion may be closed pending alignment. |
| Spec text revisions | Open an issue first if the change is substantive (more than a clarification or typo). |

### What a good PR looks like

- A clear PR title summarizing the change.
- A description tying the PR to an issue (if one exists) and explaining the rationale.
- For schema or example changes: positive and negative test cases under [`tests/`](tests/), if applicable.
- For new question types: a reference schema, an example file, an entry in [`question-types-reference.md`](question-types-reference.md), and at least one positive test case.
- A [`CHANGELOG.md`](CHANGELOG.md) entry if the change is observable to implementers.

### Tests and CI

CI for this repository runs the conformance test corpus using `tools/run_corpus.py`, which reads `tests/manifest.json` and dispatches each fixture to the reference validator for its `documentType`: `validate_course.py --strict` for `course` and `questionSet`, and `lc_collection.py`, `lc_pack.py` or `lc_glossary.py` for the three artifact types added in 1.1.

The harness exits non-zero unless every valid fixture exits `0` and every invalid fixture is adjudicated as definitively non-conforming (exit `1`). An exit `3` is **indeterminate**, not a violation: the document was never checked, so the rule the fixture exists to prove went unverified. The harness therefore fails on `3` rather than accepting it as a rejection. PRs that break a corpus expectation will not merge.

To reproduce locally before opening a PR:

```bash
pip install -r tools/requirements.txt
python tools/run_corpus.py
```

If your change requires updating a test fixture or the manifest, do so in the same PR and call it out in the description.

## Contribution license

By submitting a contribution, you agree that your contribution is licensed under the terms of the [Apache License, Version 2.0](LICENSE). No separate Contributor License Agreement (CLA) is required at this stage.

If you contribute substantively (more than a typo fix), you may add yourself to [`CONTRIBUTORS.md`](CONTRIBUTORS.md) in the same PR.

## Code of Conduct

This project follows the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.

## Scope and direction

LC-JSON is a specification for portable learning-content interchange. Contributions that align with this scope are welcome:

- Schema fixes and clarifications.
- New question types with clear use cases and pedagogical motivation.
- Improvements to the conformance test corpus.
- Translations of the specification text (open an issue first to discuss).

Out of scope for the specification repository:

- Implementations (these belong in their own repositories; list them in [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md)).
- Authoring UIs, editors, content libraries, or delivery platforms.
- Pedagogical guidance unrelated to the JSON wire format.

## Decision-making

Substantive proposals are reviewed by the maintainer per [`GOVERNANCE.md`](GOVERNANCE.md). Acceptance, modification, or rejection is the maintainer's discretion at this stage; a working-group governance model will replace this when the criteria in `GOVERNANCE.md` are met.

Decisions are made publicly via Issues and PRs. If a discussion is going long or complex, the maintainer may summarize the resolution in a `proposals/` RFC document for durable reference (the directory is added when the first such RFC lands).

## Thank you

Open standards depend on people who care enough to file issues and read drafts. If you have noticed something that could be better, please tell us — the cost of an issue is small, the value of catching a problem early is large.
