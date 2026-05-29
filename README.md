# LC-JSON

**An open learning-content interchange specification.**

LC-JSON (Learning Content JSON) is a JSON-native format, schema set, and producer/consumer behavior contract for portable teacher-authored courses, lessons, questions, feedback, and assessment intent. It covers two artifact types (Course and Question Set) and 12 implemented question types, designed for portability between authoring tools, learning-management systems, and delivery platforms.

LC-JSON is a content-layer format — complementary to, not competing with, established LMS interop standards (LTI, OneRoster, xAPI, SCORM). See [the Rationale page](src/RATIONALE.md) for the full landscape and what LC-JSON is **not**.

- **Specification site:** <https://lc-json.org>
- **Schemas (1.0-rc.2):** <https://lc-json.org/1.0-rc.2/> *(the `/1.0/` URL path is reserved for 1.0 final per NORMATIVE.md §8.3; the superseded `/1.0-rc.1/` set remains served and frozen)*
- **License:** [Apache 2.0](LICENSE)
- **Current version:** `1.0-rc.2` (release candidate; `1.0` final targeted 2026-06-30)

## What's in this repository

| Directory / file | What |
|---|---|
| [`README.md`](README.md) (this file) | Repository overview |
| [`src/`](src/) | Specification site source (mdBook) |
| [`schemas/`](schemas/) | JSON Schema files (Draft 7) for every artifact, item type, and question type |
| [`examples/`](examples/) | Example documents — minimal and full courses, per-question fragments |
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

- `https://lc-json.org/1.0-rc.2/course.schema.json`
- `https://lc-json.org/1.0-rc.2/question-set.schema.json`
- `https://lc-json.org/1.0-rc.2/<type>.schema.json` (and 19 other type-specific schemas)

VS Code, JetBrains IDEs, and any JSON Schema validator can fetch these URLs for autocomplete and validation. The `1.0/` URL path is stable per [`NORMATIVE.md`](src/NORMATIVE.md) §8.3.

**See an example document:**

```bash
cat examples/course-minimal.json
```

## Conformance

A tool may claim conformance to LC-JSON 1.0 as a *producer*, *consumer*, or unqualified (both). See [`NORMATIVE.md`](src/NORMATIVE.md) §10 for the full conformance-claim language. The [test corpus](tests/) lets implementations self-verify.

## Project status

LC-JSON `1.0-rc.2` is the public release candidate (target: 2026-05-30) and the first formally announced prerelease. It is stable enough to build against — schema URLs at `lc-json.org/1.0-rc.2/` are immutable per `NORMATIVE.md` §8.3 (each release candidate gets its own immutable URL path; `/1.0/` is reserved for 1.0 final). rc.2 supersedes an earlier internal candidate, `1.0-rc.1`, which was never publicly announced; its `/1.0-rc.1/` schema set remains served and frozen. The only substantive rc.1 → rc.2 change is a backwards-compatible `prompt` correction — empty strings are permitted where no author-supplied prompt is required — so every rc.1-valid document stays valid under rc.2. Minor non-breaking refinements (additional conformance fixtures, validator `--strict` polish) may land before `1.0` final on 2026-06-30 at a later `/1.0-rc.N/` path.

The specification distils approximately 12 months of internal format iteration. Earlier internal versions were never publicly released and are not part of the public version history.

## License

LC-JSON is licensed under the [Apache License, Version 2.0](LICENSE). The specification text, schemas, examples, conformance tests, and reference tools are all covered. Implementers may build conforming tools without further permission.

"Lesson Commons" is a trademark of Brent Miller and is not asserted over LC-JSON, the names "LC-JSON" or "Learning Content JSON", or any conforming implementation. The canonical sources for the specification are this repository and the published site at [`lc-json.org`](https://lc-json.org); see [`GOVERNANCE.md`](src/GOVERNANCE.md) for the full naming and forking posture.

## Contact

- **Issues and proposals:** open an issue on this repository.
- **Specification site:** <https://lc-json.org>
