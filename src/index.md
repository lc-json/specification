# LC-JSON

## An open learning-content interchange specification.

LC-JSON (Learning Content JSON) is a JSON-native format, schema set, and producer/consumer behavior contract for portable teacher-authored courses, lessons, questions, feedback, and assessment intent. A course authored in one tool can be validated, transferred, and delivered in another, with predictable behavior on both ends.

The specification is open. The schemas are public, stable, and versioned. The license is permissive (Apache 2.0). Implementers can build conforming tools without permission.

LC-JSON is a content-layer format — complementary to LMS interop standards (LTI, OneRoster, xAPI, SCORM) rather than competing with them. See [the Rationale](RATIONALE.md) for the full landscape and what LC-JSON is **not**.

---

## What you can do with it

**Take your courses with you.**
Course content in LC-JSON is independent of the tool that authored it. Schools, publishers, and authors can move content between platforms without rewriting it.

**Validate before you ship.**
Every LC-JSON document validates against published JSON Schemas. Authoring errors are caught before delivery, not after a learner gets stuck.

**Build with confidence.**
Schema URLs at every published version path — `lc-json.org/1.1-rc.1/`, `lc-json.org/1.0/`, the frozen `lc-json.org/1.0-rc.N/` candidate paths, and any future minor or major release — are immutable. A document that validates today will validate forever. Forward-compatible additions land at new URL paths; existing files keep working.

---

## Read the specification

- **[Specification overview](README-spec.html)** — what LC-JSON looks like, with worked examples.
- **[NORMATIVE.md](NORMATIVE.html)** — the conformance requirements (RFC 2119 keywords, producer/consumer roles).
- **[Question types reference](question-types-reference.html)** — per-type property reference for all 12 implemented question types.
- **[Schemas](https://github.com/lc-json/specification/tree/main/schemas)** — Draft-7 JSON Schemas for every artifact and question type.
- **[Examples](https://github.com/lc-json/specification/tree/main/examples)** — examples spanning all five artifact types, from minimal documents to fuller Course and QuestionSet samples, plus question, item, unit, and lesson fragments.

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

## What's covered in 1.1

Five artifact types sharing a common flat root format:

- **Course** — hierarchical: Course → Units → Lessons → Items → Questions.
- **Question Set** — flat list of questions for question-bank exchange and packaged delivery.
- **Glossary** — flat list of terms with pronunciation, translations, examples, and inflected forms; attaches to a course, unit, or lesson.
- **Subject Collection** — a reusable classification vocabulary: the tags and learning objectives for one subject at one level.
- **Curriculum Pack** — an arrangement: sequence, pacing, and assessment checkpoints over a collection plus content documents.

The three 1.1 additions are abstract at first read. Two distinctions do most of the work of telling the five types apart:

| Type | Plain role | What sets it apart |
|---|---|---|
| **Course** | Learning content | Contains what learners work through |
| **Question Set** | Assessment resource | Contains reusable questions |
| **Glossary** | Learner reference | Contains the terms learners study |
| **Subject Collection** | Curriculum vocabulary | Describes how educators *classify* content and objectives |
| **Curriculum Pack** | Curriculum plan | *Arranges* and references content without becoming the content |

- A **Subject Collection** describes how educators *classify* learning; a **Glossary** contains the words and meanings learners *study*.
- A **Curriculum Pack** *arranges* learning content; a **Course** *contains* it.

Each type's reference page opens with a plain-English summary for educators and curriculum teams; the rest of each page is the technical contract.

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

**Version `1.1-rc.1` — current publication** (2026-07-17), a release candidate at immutable `lc-json.org/1.1-rc.1/` URLs. It adds three artifact types — Glossary, Subject Collection, and Curriculum Pack — plus publication fields and `glossaryRefs` on courses. The addition is backwards-compatible: every `1.0`-valid document remains valid under `1.1` with no migration or re-export. As a candidate, `1.1-rc.1` may take backwards-compatible corrections before the `1.1` final release; the `/1.1/` path is not populated until then.

**Version `1.0` — accepted final release** (2026-06-30). The 1.0 wire format is stable and schema URLs at `lc-json.org/1.0/` are immutable per `NORMATIVE.md` §8.3. `1.0` is a pure URL rebase of `1.0-rc.3` with no wire/content delta: the rc.3 schema set is republished unchanged at the final path, with only `$id`/`$schema` URL strings and document version labels updated. Every `1.0-rc.3`-valid document is valid under `1.0` with no migration or re-export. The earlier release-candidate paths — `/1.0-rc.1/`, `/1.0-rc.2/`, and `/1.0-rc.3/` — stay served and frozen.

LC-JSON's public history begins with the 1.0 release-candidate line — `1.0-rc.2` (2026-05-30) was its first publicly announced release. Internal iteration before the candidate line is not reflected in the version history.

LC-JSON is maintained under a single-maintainer steward model; see [GOVERNANCE.md](GOVERNANCE.html) for the decision-making process and the criteria for transitioning to a working group.
