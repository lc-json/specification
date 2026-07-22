# LC-JSON

**An open learning-content interchange specification.**

LC-JSON (Learning Content JSON) is a JSON-native format, schema set, and producer/consumer behavior contract for portable teacher-authored courses, lessons, questions, feedback, and assessment intent. It covers five artifact types — Course, Question Set, Glossary, Subject Collection, and Curriculum Pack — and 12 implemented question types, designed for portability between authoring tools, learning-management systems, and delivery platforms.

LC-JSON is a content-layer format — complementary to, not competing with, established LMS interop standards (LTI, OneRoster, xAPI, SCORM). See [the Rationale page](src/RATIONALE.md) for the full landscape and what LC-JSON is **not**.

- **Specification site:** <https://lc-json.org>
- **Schemas (1.1-rc.1):** <https://lc-json.org/1.1-rc.1/> *(the `/1.0/` release and the superseded `/1.0-rc.1/`, `/1.0-rc.2/`, and `/1.0-rc.3/` sets remain served and frozen per NORMATIVE.md §8.3)*
- **License:** [Apache 2.0](LICENSE)
- **Current version:** `1.1-rc.1` (release candidate, 2026-07-17). Latest final release: `1.0` (2026-06-30).

## What's in this repository

| Directory / file | What |
|---|---|
| [`README.md`](README.md) (this file) | Repository overview |
| [`src/`](src/) | Specification site source (mdBook) |
| [`schemas/`](schemas/) | JSON Schema files (Draft 7) for every artifact, item type, and question type |
| [`examples/`](examples/) | Example documents — all five artifact types, from minimal documents to fuller Course and QuestionSet samples, plus question, item, unit, and lesson fragments |
| [`tests/`](tests/) | Conformance test corpus (valid and invalid cases per clause) |
| [`tools/`](tools/) | Reference Python tools: validator and conformance corpus harness |
| [`NORMATIVE.md`](src/NORMATIVE.md) | RFC 2119 conformance requirements (the authoritative source for implementers) |
| [`question-types-reference.md`](src/question-types-reference.md) | Per-type property reference |
| [`IMPLEMENTATIONS.md`](src/IMPLEMENTATIONS.md) | Directory of tools that produce, consume, or validate LC-JSON |
| [`CONTRIBUTORS.md`](src/CONTRIBUTORS.md) | Acknowledgments |
| [`CHANGELOG.md`](src/CHANGELOG.md) | Version history |
| [`GOVERNANCE.md`](src/GOVERNANCE.md) | Stewardship model and decision-making process |
| [`CONTRIBUTING.md`](src/CONTRIBUTING.md) | How to file issues and submit PRs |
| [`CODE_OF_CONDUCT.md`](src/CODE_OF_CONDUCT.md) | Contributor Covenant 2.1 |

## Quick start

**Validate an LC-JSON document:**

```bash
pip install jsonschema
python tools/validate_course.py --course-path my-course.json
```

**Use the schemas in your own validator:**

The schemas resolve at stable, versioned URLs:

- `https://lc-json.org/1.1-rc.1/course.schema.json`
- `https://lc-json.org/1.1-rc.1/question-set.schema.json`
- `https://lc-json.org/1.1-rc.1/<schema-name>.schema.json` (27 schema files in total)

VS Code, JetBrains IDEs, and any JSON Schema validator can fetch these URLs for autocomplete and validation. Every published path is immutable: `1.1-rc.1/` is the current publication, and the `1.0/` release plus the earlier `1.0-rc.1/`, `1.0-rc.2/`, and `1.0-rc.3/` paths remain served and frozen (per [`NORMATIVE.md`](src/NORMATIVE.md) §8.3).

**See an example document:**

```bash
cat examples/course-minimal.json
```

## Conformance

A tool may claim conformance to LC-JSON as a *producer*, *consumer*, or unqualified (both), and conformance is scoped per artifact type — a tool that reads only courses claims only that. See [`NORMATIVE.md`](src/NORMATIVE.md) §10 for the full conformance-claim language. The [test corpus](tests/) lets implementations self-verify.

## Project status

LC-JSON `1.1-rc.1` is the **current publication** (2026-07-17) — a release candidate published at immutable `lc-json.org/1.1-rc.1/` URLs. It is a backwards-compatible addition to `1.0`: three new artifact types (Glossary, Subject Collection, Curriculum Pack) plus publication fields and `glossaryRefs` on courses. Every `1.0`-valid document remains valid under `1.1` with no migration or re-export.

LC-JSON `1.0` was released on **2026-06-30** as the accepted final release, and stays served and frozen at `lc-json.org/1.0/` alongside the `/1.0-rc.1/`, `/1.0-rc.2/`, and `/1.0-rc.3/` candidate paths, per `NORMATIVE.md` §8.3.

The specification distils approximately 12 months of internal format iteration. Earlier internal versions were never publicly released and are not part of the public version history.

## License

LC-JSON is licensed under the [Apache License, Version 2.0](LICENSE). The specification text, schemas, examples, conformance tests, and reference tools are all covered. Implementers may build conforming tools without further permission.

"Lesson Commons" is a trademark of Brent Miller and is not asserted over LC-JSON, the names "LC-JSON" or "Learning Content JSON", or any conforming implementation. The canonical sources for the specification are this repository and the published site at [`lc-json.org`](https://lc-json.org); see [`GOVERNANCE.md`](src/GOVERNANCE.md) for the full naming and forking posture.

## Contact

- **Issues and proposals:** open an issue on this repository.
- **Specification site:** <https://lc-json.org>
