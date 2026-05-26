# LC-JSON

## An open learning-content interchange specification.

LC-JSON (Learning Content JSON) is a JSON-native format, schema set, and producer/consumer behavior contract for portable teacher-authored courses, lessons, questions, feedback, and assessment intent. A course authored in one tool can be validated, transferred, and delivered in another, with predictable behavior on both ends.

The specification is open. The schemas are public, stable, and versioned. The license is permissive (Apache 2.0). Implementers can build conforming tools without permission.

---

## What you can do with it

**Take your courses with you.**
Course content in LC-JSON is independent of the tool that authored it. Schools, publishers, and authors can move content between platforms without rewriting it.

**Validate before you ship.**
Every LC-JSON document validates against published JSON Schemas. Authoring errors are caught before delivery, not after a learner gets stuck.

**Build with confidence.**
Schema URLs at every published version path — `lc-json.org/1.0-rc.1/` today, `lc-json.org/1.0/` once 1.0 final ships, and any future minor or major release — are immutable. A document that validates today will validate forever. Forward-compatible additions land at new URL paths; existing files keep working.

---

## Read the specification

- **[Specification overview](README-spec.html)** — what LC-JSON looks like, with worked examples.
- **[NORMATIVE.md](NORMATIVE.html)** — the conformance requirements (RFC 2119 keywords, producer/consumer roles).
- **[Question types reference](question-types-reference.html)** — per-type property reference for all 12 implemented question types.
- **[Schemas](https://github.com/lc-json/specification/tree/main/schemas)** — Draft-7 JSON Schemas for every artifact and question type.
- **[Examples](https://github.com/lc-json/specification/tree/main/examples)** — minimal and full course examples; per-type fragments.

## For implementers

- **[Conformance test corpus](https://github.com/lc-json/specification/tree/main/tests)** — valid and invalid cases per clause, with a machine-readable manifest. Run your validator over the corpus to verify conformance.
- **Reference tools:** `validate_course.py` (validator) and `run_corpus.py` (corpus harness for spec contributors + the spec repo's CI). See [`tools/`](https://github.com/lc-json/specification/tree/main/tools).
- **[GitHub repository](https://github.com/lc-json/specification)** — issues, discussions, releases.

---

## Who is this for?

| If you are… | LC-JSON gives you… |
|---|---|
| **A teacher or course author** | Confidence that the courses you write are not locked into any single tool. |
| **A school or institution** | A portable, vendor-neutral format for learning content. Procurement decisions don't lock in pedagogical content. |
| **An EdTech tool builder** | A clean import/export target. Conforming tools interoperate without bespoke adapters. |
| **A learning-platform vendor** | Reduced friction in onboarding teacher-authored content from any source. |

---

## What's covered in 1.0

Two artifact types sharing a common flat root format:

- **Course** — hierarchical: Course → Units → Lessons → Items → Questions.
- **Question Set** — flat list of questions for question-bank exchange and packaged delivery.

Twelve question types fully implemented and schema-validated:

`simpleGapFill` · `trueFalseQuestion` · `multipleChoice` · `wordBankCloze` · `multiGapCloze` · `multipleChoiceCloze` · `shortAnswer` · `essay` · `sentenceTransformation` · `matching` · `ordering` · `placement`

Seven additional types are reserved for a future minor version (targeted for 2027).

Five lesson item types: content, exercise, quiz, content-sequence, signpost.

---

## License

LC-JSON is licensed under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0). The license includes a patent grant. Conforming implementations require no further permission.

"Lesson Commons" is a separate trademark and is not asserted over LC-JSON or its conforming implementations.

---

## Project status

**Version `1.0-rc.1` — public release candidate** (target: 2026-05-30). The wire format is stable and schema URLs at `lc-json.org/1.0-rc.1/` are immutable per `NORMATIVE.md` §8.3 — early adopters can build against `rc.1` with confidence. Each release candidate gets its own immutable URL path; the `/1.0/` URL is reserved for 1.0 final. Minor non-breaking refinements (additional conformance fixtures, the `ACCESSIBILITY.md` companion, validator `--strict` polish) may land before `1.0` final on 2026-06-30 — those would publish at `/1.0-rc.2/`, leaving `/1.0-rc.1/` frozen.

LC-JSON 1.0 is the format's first public release. Internal iteration prior to publication is not reflected in the version history.

LC-JSON is maintained under a single-maintainer steward model; see [GOVERNANCE.md](GOVERNANCE.html) for the decision-making process and the criteria for transitioning to a working group.
