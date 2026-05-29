# LC-JSON Specification

**Spec version:** 1.0 (release candidate: rc.2)
**Last updated:** 2026-05-23

This directory contains the LC-JSON (Learning Content JSON) specification for structured learning content, covering the complete hierarchy from Course structure down to individual Question types.

> **Implementing LC-JSON?** See [NORMATIVE.md](NORMATIVE.md) for the conformance requirements (RFC 2119 keywords, producer/consumer roles, versioning rules, URL stability promises). This README is descriptive; NORMATIVE.md is authoritative. For terminology, see [GLOSSARY.md](GLOSSARY.md).

**Complete Coverage:**
- Two artifact types (Course, QuestionSet) sharing a common flat root format
- Course Hierarchy (Course → Units → Lessons → Items)
- 5 Lesson Item Types (Content, Exercise, Quiz, ContentSequence, Signpost)
- 19 Question Types (12 fully implemented + schema-validated; 7 reserved for a future minor version)
- JSON Schemas (23) for validation — strictly enforced by the reference validator
- Minimal + detailed examples (32 files, all schema-clean)

---

## Design Principles

**LC-JSON is machine-validatable, but human-inspectable.**

The documents are validated automatically against [JSON Schema Draft 7](https://json-schema.org/draft-07/schema), but they are also designed so that authored content remains visible in the file. A teacher, curriculum designer, or teacher-developer can recognize **courses, units, lessons, items, questions, prompts, choices, answers, and feedback** without proprietary tooling — opening a course `.json` in any text editor should be enough to inspect what the course actually contains.

Technical fields such as `$schema`, `specVersion`, and `globalId` exist to make documents portable across tools and stable across re-imports, but they should not bury the pedagogical content. Where this trade-off arises in spec evolution — naming, structure, ordering of fields — the spec favors the form that keeps pedagogical content recognizable.

This is a deliberate stance against formats whose meaning only emerges through tooling. It is offered without promise of zero technical fields, because portability requires some; the promise is that the pedagogical structure stays inspectable to the people who authored it.

---

## Wire Format

LC-JSON uses a **flat root** with a `documentType` discriminator (no enclosing envelope around the document). Every conforming document carries `$schema`, `documentType`, and `specVersion` as root-level siblings. The course content itself is hierarchical — Course → Units → Lessons → Items → Questions — and reflects how teachers structure their material.

### Two artifact types

| Artifact | `documentType` | Schema | Description |
|----------|---------------|--------|-------------|
| Course | `"course"` | [`course.schema.json`](schemas/course.schema.json) | Hierarchical course (Units → Lessons → Items). The standard shape for a full course. |
| Question Set | `"questionSet"` | [`question-set.schema.json`](schemas/question-set.schema.json) | Flat list of questions for question-bank exchange and packaged delivery — no hierarchy. |

### Required root fields (both artifact types)

```json
{
  "$schema": "https://lc-json.org/1.0-rc.2/<artifact>.schema.json",
  "documentType": "course",      // or "questionSet"
  "specVersion": "1.0",
  "title": "...",
  ...
}
```

The `$schema` URL serves as a stable, versioned identifier and is used
by integrated development environments (IDEs such as VS Code) for schema
autocomplete. `specVersion` is
forward-compatible across the `1.x` series — conforming consumers MUST
accept any `1.x` value and reject `2.x+` cleanly.

### Reserved question types (targeted for 2027)

Seven question types are reserved in the polymorphic discriminator
set but do not yet have per-type schemas — full authoring and consumer
support is targeted for 2027:

`association`, `hotspot`, `graphicGapMatch`, `graphicAssociate`,
`graphicOrder`, `fileUpload`, `mediaPromptedEssay`

The 12 question types with full per-type schemas — `simpleGapFill`,
`trueFalseQuestion`, `multipleChoice`, `wordBankCloze`, `multiGapCloze`,
`multipleChoiceCloze`, `shortAnswer`, `essay`, `sentenceTransformation`,
`matching`, `ordering`, `placement` — are the spec's stable surface as of 1.0.

**Consumer obligations for reserved (and unknown) types** are normative under [`NORMATIVE.md`](NORMATIVE.md) §6: consumers MUST preserve them verbatim across read/write cycles, MUST NOT silently drop them, MUST treat their earned points as zero, and SHOULD render a non-interactive placeholder. The intent is round-trip preservation: a teacher exporting from a consumer that does not support `hotspot` can take the file back to a consumer that does, without losing the question. Producers SHOULD NOT emit reserved types in 1.0 documents intended for cross-implementation distribution; reserved types are tool-specific extensions until promoted.

### Discriminator casing

Conforming producers emit **camelCase** question discriminators
(`simpleGapFill`, `multipleChoice`, etc.). All examples in this
directory strictly validate against the schemas in their canonical
casing. Non-canonical casings are non-conforming; consumers MUST
reject them.

---

## Directory Structure

```
specification/
├── README.md                          # This file
├── NORMATIVE.md                       # RFC 2119 conformance requirements (authoritative)
├── HTML_SAFETY.md                     # Normative HTML allowlist + sanitization profile
├── ACCESSIBILITY.md                   # Producer/consumer accessibility profile
├── VALIDATION.md                      # Rule catalog — schema / validator / advisory tiers
├── ITEM_PATTERNS.md                   # Informative authoring guide
├── question-types-reference.md        # Complete reference for all 19 question types
├── GLOSSARY.md                        # Terminology
├── schemas/                           # JSON Schema validation files
│   ├── course.schema.json             # Course (top level)
│   ├── question-set.schema.json       # QuestionSet (flat artifact)
│   ├── unit.schema.json               # Unit (within Course)
│   ├── lesson.schema.json             # Lesson (within Unit)
│   ├── item-base.schema.json          # Base schema for all Items
│   ├── content-item.schema.json       # ContentItem type
│   ├── exercise-item.schema.json      # ExerciseItem type
│   ├── quiz-item.schema.json          # QuizItem type
│   ├── content-sequence-item.schema.json  # ContentSequenceItem type
│   ├── signpost-item.schema.json      # SignpostItem type (intro/summary navigation)
│   ├── question-base.schema.json      # Base schema for all Questions
│   ├── simple-gap-fill.schema.json    # SimpleGapFill validation
│   ├── true-false-question.schema.json # TrueFalseQuestion validation
│   ├── multiple-choice.schema.json    # MultipleChoice validation
│   ├── word-bank-cloze.schema.json    # WordBankCloze validation
│   ├── multi-gap-cloze.schema.json    # MultiGapCloze validation
│   ├── multiple-choice-cloze.schema.json  # MultipleChoiceCloze validation
│   ├── short-answer.schema.json       # ShortAnswer validation
│   ├── essay.schema.json              # Essay validation
│   ├── sentence-transformation.schema.json  # SentenceTransformation validation
│   ├── matching.schema.json           # Matching validation
│   ├── ordering.schema.json           # Ordering validation
│   └── placement.schema.json          # Placement type validation
└── examples/                          # Example JSON files (32 total)
    ├── course-minimal.json            # Minimal Course example
    ├── question-set-minimal.json      # Minimal QuestionSet example
    ├── question-set-10-true-false.json # Richer QuestionSet showcase
    ├── unit-minimal.json              # Minimal Unit example
    ├── lesson-minimal.json            # Minimal Lesson example
    ├── 10-content-item.json           # ContentItem with HTML
    ├── 11-exercise-item.json          # ExerciseItem (graded homework example)
    ├── 12a-graded-quiz-item.json      # QuizItem, isGraded:true (typical assessment)
    ├── 12b-ungraded-quiz-item.json    # QuizItem, isGraded:false (diagnostic pre-test)
    ├── 13-content-sequence-item.json  # ContentSequenceItem
    ├── 14-signpost-item.json          # SignpostItem
    ├── 01-simple-gap-fill.json        # Per-question examples (01-09)
    ├── ...                            # 09-sentence-transformation.json
    ├── 15-matching.json               # Matching example
    ├── 16-ordering.json               # Ordering example (word-level)
    ├── 16b-sentence-ordering.json     # Ordering example (sentence-level — process narrative)
    ├── 16c-paragraph-ordering.json    # Ordering example (paragraph-level — essay structure)
    ├── 17a-sentence-placement.json    # Placement example (sentence-mode — Cambridge B2 First Part 6 style)
    ├── 17b-paragraph-placement.json   # Placement example (paragraph-mode — IELTS Reading Matching Information style)
    ├── 17c-section-label-placement.json # Placement example (sectionLabel-mode — IELTS Matching Headings)
    ├── 17d-toefl-insertion-placement.json # Placement example (TOEFL Sentence Insertion — decoy-gaps variant)
    └── sample-course-with-questions.json    # Full course example
```

**Total:** 23 schemas (4 [course, questionSet, unit, lesson] + 1 item-base + 5 item types + 1 question-base + 12 question types).

---

## Course Hierarchy

A Course document has the following nested structure:

```
Course (top level)
└─ Units[] (array of units)
   └─ Lessons[] (array of lessons)
      └─ Items[] (array of items - 5 types)
         ├─ ContentItem (reading/content pages)
         ├─ ExerciseItem (questions; structural form, grading via isGraded)
         ├─ QuizItem (questions; structural form, grading via isGraded)
         ├─ ContentSequenceItem (grouped content)
         └─ SignpostItem (intro/summary with objectives)
            └─ Questions[] (only for ExerciseItem and QuizItem)
```

**Minimal Examples for Quick Reference:**
- [course-minimal.json](examples/course-minimal.json) - Bare minimum Course structure
- [unit-minimal.json](examples/unit-minimal.json) - Bare minimum Unit
- [lesson-minimal.json](examples/lesson-minimal.json) - Bare minimum Lesson

---

## Lesson Item Types

Every Lesson contains an `items` array with one or more of these 5 item types:

| Item Type | Schema | Example | Description |
|-----------|--------|---------|-------------|
| **ContentItem** | [content-item.schema.json](schemas/content-item.schema.json) | [10-content-item.json](examples/10-content-item.json) | Reading/content pages with HTML content (subject to [HTML_SAFETY.md](HTML_SAFETY.md)) |
| **ExerciseItem** | [exercise-item.schema.json](schemas/exercise-item.schema.json) | [11-exercise-item.json](examples/11-exercise-item.json) | Exercise-shaped questions container. Grading independent (`isGraded`). |
| **QuizItem** (graded) | [quiz-item.schema.json](schemas/quiz-item.schema.json) | [12a-graded-quiz-item.json](examples/12a-graded-quiz-item.json) | Quiz-shaped, `isGraded: true` — typical assessment. |
| **QuizItem** (ungraded) | [quiz-item.schema.json](schemas/quiz-item.schema.json) | [12b-ungraded-quiz-item.json](examples/12b-ungraded-quiz-item.json) | Quiz-shaped, `isGraded: false` — diagnostic pre-test, self-check. Same schema, different policy. |
| **ContentSequenceItem** | [content-sequence-item.schema.json](schemas/content-sequence-item.schema.json) | [13-content-sequence-item.json](examples/13-content-sequence-item.json) | Grouped content with layout options (carousel, tabs, accordion) |
| **SignpostItem** | [signpost-item.schema.json](schemas/signpost-item.schema.json) | [14-signpost-item.json](examples/14-signpost-item.json) | Structural navigation (intro/summary) with objectives and stats; `customHtml` subject to [HTML_SAFETY.md](HTML_SAFETY.md) |

> **Exercise vs. Quiz.** These are structural distinctions only. They render differently in the UI and contribute to separate point buckets (enabling weighted grading). Whether the score counts toward a learner's grade is the `isGraded` flag, set independently. The examples model this: [`11-exercise-item.json`](examples/11-exercise-item.json) is a graded homework exercise (`isGraded: true`); [`12a-graded-quiz-item.json`](examples/12a-graded-quiz-item.json) and [`12b-ungraded-quiz-item.json`](examples/12b-ungraded-quiz-item.json) use the same content under the same schema to show that quiz can be either graded or ungraded. The fourth combination (ungraded exercise / open practice) is conventional and not given its own example.
>
> For an authoring guide that walks through the full design space of `type` × `isGraded` × `isOptional` × `passMarkPercent` — common patterns (graded homework, diagnostic pre-test, exit ticket, etc.) and how different consumers may interpret each combination — see [`ITEM_PATTERNS.md`](ITEM_PATTERNS.md).

**Key Properties (all items inherit from [item-base.schema.json](schemas/item-base.schema.json)):**
- `type` (required) - Discriminator: "content", "exercise", "quiz", "contentsequence", or "signpost"
- `title` (required) - Display title for the item
- `sequence` - Display order within lesson (0-based)
- `instructions` - Instructions shown to learner
- `suggestedTime` - Estimated time in minutes
- `isOptional` - Whether item can be skipped

**Questions Array:**
- Only **ExerciseItem** and **QuizItem** have a `questions` array
- ContentItem, ContentSequenceItem, and SignpostItem do NOT contain questions

**SignpostItem Properties:**
- `signpostType` (required) - "intro" or "summary"
- `scope` (required) - "course", "unit", or "lesson"
- `customHtml` (optional) - Custom HTML content to override auto-generated message

---

## Documentation Files

### 1. [question-types-reference.md](./question-types-reference.md)
**Complete JSON Format Reference**

- **All 19 Question Types** with detailed specifications
- **Property tables** showing required/optional fields
- **Examples** for each question type
- **Validation rules** and best practices
- **Common properties** inherited by all questions
- **Complete course example** showing nested structure

**When to use:**
- Creating new course JSON files
- Understanding question type requirements
- Troubleshooting import errors

---

### 2. JSON Schema Files (`schemas/`)
**Machine-Readable Validation**

JSON Schema files for automated validation using tools like `ajv`, `jsonschema`, or IDE validators.

**Course Hierarchy Schemas:**
- `course.schema.json` - Course (top level)
- `unit.schema.json` - Unit (within Course)
- `lesson.schema.json` - Lesson (within Unit)

**Item Type Schemas:**
- `item-base.schema.json` - Base schema for all Items
- `content-item.schema.json` - ContentItem type
- `exercise-item.schema.json` - ExerciseItem type
- `quiz-item.schema.json` - QuizItem type
- `content-sequence-item.schema.json` - ContentSequenceItem type
- `signpost-item.schema.json` - SignpostItem type (intro/summary navigation)

**Question Type Schemas:**
- `question-base.schema.json` - Base properties for all questions
- `simple-gap-fill.schema.json` - SimpleGapFill type validation
- `true-false-question.schema.json` - TrueFalseQuestion type validation
- `multiple-choice.schema.json` - MultipleChoice type validation
- `word-bank-cloze.schema.json` - WordBankCloze type validation
- `multi-gap-cloze.schema.json` - MultiGapCloze type validation
- `multiple-choice-cloze.schema.json` - MultipleChoiceCloze type validation
- `short-answer.schema.json` - ShortAnswer type validation
- `essay.schema.json` - Essay type validation
- `sentence-transformation.schema.json` - SentenceTransformation type validation
- `matching.schema.json` - Matching type validation
- `ordering.schema.json` - Ordering type validation
- `placement.schema.json` - Placement type validation

**Strict enforcement:** the reference validator (`validate_course.py`) runs every document through these schemas as a primary pass via the `jsonschema` package (≥4.18, modern `referencing` Registry API). Per-question type-specific dispatch keys off the `type` discriminator. Install dependencies with `pip install -r tools/requirements.txt`.

**Usage Example (Node.js with ajv):**
```javascript
const Ajv = require('ajv');
const ajv = new Ajv();

const baseSchema = require('./schemas/question-base.schema.json');
const simpleGapFillSchema = require('./schemas/simple-gap-fill.schema.json');

const validate = ajv.compile(simpleGapFillSchema);
const valid = validate(questionData);

if (!valid) {
  console.error(validate.errors);
}
```

---

### 3. Example Files (`examples/`)
**Ready-to-Use Templates**

#### Minimal Hierarchy Examples - **Quick Format Reference**
Ultra-minimal examples for quick consultation when creating courses:

- **course-minimal.json** - Bare minimum Course structure with required properties
- **unit-minimal.json** - Minimal Unit within a course
- **lesson-minimal.json** - Minimal Lesson within a unit

Use these as exact-format references (e.g., a unit on Travel + present perfect).

#### Item Type Examples (10-13) - **Item Structure Reference**
Individual examples for each of the Lesson Item types:

- **10-content-item.json** — ContentItem with rich HTML content (Declaration of Independence reading)
- **11-exercise-item.json** — ExerciseItem framed as graded homework (5 T/F world-rivers questions; `isGraded: true`)
- **12a-graded-quiz-item.json** — QuizItem as a graded assessment (`isGraded: true`, `passMarkPercent: 70`); same content as 11
- **12b-ungraded-quiz-item.json** — QuizItem as an ungraded diagnostic pre-test (`isGraded: false`); same content as 11 and 12a — demonstrates that quiz vs. exercise is structural, grading is policy
- **13-content-sequence-item.json** — ContentSequenceItem with carousel layout

#### Individual Question Examples (01-09) - **RECOMMENDED**
Standalone JSON files for each implemented question type with **complete feedback bundles**:

1. **01-simple-gap-fill.json** - Articles with indefinite article rule
2. **02-true-false-question.json** - Science fact with per-choice feedback
3. **03-multiple-choice.json** - Programming languages with detailed choiceFeedback
4. **04-word-bank-cloze.json** - Articles in context with per-gap feedback
5. **05-multi-gap-cloze.json** - Prepositions open cloze (FCE Part 2 style, 8 gaps)
6. **06-multiple-choice-cloze.json** - Vocabulary with nested gapOptionFeedback
7. **07-short-answer.json** - Astronomy fact recall
8. **08-essay.json** - IELTS Task 2 with comprehensive rubric
9. **09-sentence-transformation.json** - FCE Part 4 with chunk feedback

**Features Demonstrated:**
- Complete feedback bundle (correct, incorrect, choiceFeedback)
- Strategic hints that guide without revealing answers
- Multi-level tagging (grammar:articles:indefinite, exam:fce, level:B2)
- Realistic educational content
- Production-ready quality

**Use these as templates** - they showcase all features including feedback mechanisms that are integral to effective course design.

The 7 reserved-for-2027 graphic types (association, hotspot,
graphicGapMatch, graphicAssociate, graphicOrder, fileUpload,
mediaPromptedEssay) are declared in `question-base.schema.json`'s
`enum` for forward compatibility, but no example payloads ship — full
authoring and rendering support is targeted for 2027.

#### `sample-course-with-questions.json`
Complete course JSON showing:
- **Full hierarchy**: Course → Units → Lessons → Items → Questions
- **Mixed item types**: ContentItem, ExerciseItem, QuizItem
- **Real-world structure**: Lessons with intro content + exercises and quizzes
- **Cambridge FCE alignment**: Exam-style questions with proper tags
- **Best practices**: Proper tagging, feedback, hints, difficulty levels

---

## Quick Start Guide

### For Content Creators

**Creating a Simple Course:**

1. **Start with a template:**
   ```bash
   cp examples/sample-course-with-questions.json my-course.json
   ```

2. **Modify the course metadata:**
   ```json
   {
     "title": "Your Course Title",
     "subtitle": "Your subtitle",
     "description": "Course description",
     "tags": ["level:B1", "grammar"]
   }
   ```

3. **Add or modify questions** using the per-type example files (`01-simple-gap-fill.json` through `09-sentence-transformation.json`, plus `15-matching.json` and the `16…` ordering family).

4. **Validate the result** with any conforming consumer or the reference validator:
   ```bash
   python ../tools/validate_course.py --course-path my-course.json
   ```

---

### For Developers

**Validating LC-JSON in code:**

Implementations may use any JSON Schema (Draft 7) validator. The earlier `ajv` snippet (Node.js) is one example; common alternatives:

- **Python:** `pip install jsonschema` (≥ 4.18) → `Draft7Validator`
- **Java:** `everit-org/json-schema` or `networknt/json-schema-validator`
- **Go:** `santhosh-tekuri/jsonschema`
- **Rust:** `Stranger6667/jsonschema`
- **Ruby:** `voxpupuli/json-schema`

The reference Python validator (`tools/validate_course.py` in this repository) layers domain checks (HTML allowlist, gap-marker counts, points consistency, signpost-without-objectives) on top of schema validation. Re-implementations are welcome.

**Adding a new question type to the spec** (PR-driven contributions):

1. Create a JSON schema in `schemas/` for the new type.
2. Add the discriminator value to `question-base.schema.json`'s `enum`.
3. Add a per-type example file under `examples/` (e.g. `17-new-type.json`).
4. Document in `question-types-reference.md`.
5. Add positive and negative test cases under `tests/`.

---

## Question Types — Implementation Status

**Implemented** (12 types, fully schema-validated as of 1.0-rc.2):

| Question Type | Example | Use Case |
|---|---|---|
| `simpleGapFill` | 01-simple-gap-fill.json | Single gap fill-in-the-blank |
| `trueFalseQuestion` | 02-true-false-question.json | Binary choice (True/False, Yes/No) |
| `multipleChoice` | 03-multiple-choice.json | Single or multiple selection MCQ |
| `wordBankCloze` | 04-word-bank-cloze.json | Gap fill from word pool |
| `multiGapCloze` | 05-multi-gap-cloze.json | Open cloze (FCE Reading Part 2) |
| `multipleChoiceCloze` | 06-multiple-choice-cloze.json | Dropdown cloze (FCE Reading Part 1) |
| `shortAnswer` | 07-short-answer.json | Free text short response |
| `essay` | 08-essay.json | Long-form writing with rubric |
| `sentenceTransformation` | 09-sentence-transformation.json | FCE Use of English Part 4 |
| `matching` | 15-matching.json | Term-definition matching |
| `ordering` | 16-ordering.json | Sequence/chronological ordering |
| `placement` | 17a-sentence-placement.json | Place items into anchored gaps in a structured passage (sentence / paragraph / sectionLabel; supports decoy gaps for TOEFL Sentence Insertion) |

**Reserved** (7 types declared in the discriminator enum for forward compatibility; per-type schemas and authoring/consumer support targeted for 2027):

| Question Type | Use Case |
|---|---|
| `association` | Categorization/grouping |
| `hotspot` | Click regions on image |
| `graphicGapMatch` | Drag-and-drop on image |
| `graphicAssociate` | Match text with images |
| `graphicOrder` | Order images sequentially |
| `fileUpload` | Document submission |
| `mediaPromptedEssay` | Audio/video recording |

**Status definitions:**
- **Implemented** — per-type schema, example, and conformance fixtures present.
- **Reserved** — declared in the `question-base.schema.json` discriminator enum for forward compatibility; no per-type schema or example ships yet.

The 12 implemented types are the entire user-facing surface as of 1.0. The 7 reserved types are targeted for 2027.

---

## Common Validation Errors

### Error: "Number of gaps doesn't match accepted answers"
**Cause:** Mismatch between numbered `@@@N` markers in `passage` and entries in `gapAcceptedAnswers`.
**Fix:** Count `@@@1`, `@@@2`, … markers in the passage and ensure `gapAcceptedAnswers` has matching string keys (`"1"`, `"2"`, …).

### Error: "Unknown question type: simplegapfill"
**Cause:** Type discriminator uses non-canonical casing.
**Fix:** Use camelCase: `"simpleGapFill"`, not `"SimpleGapFill"` or `"simplegapfill"`. Per [`NORMATIVE.md`](NORMATIVE.md) §5.3, conforming consumers MUST reject non-canonical casings.

### Error: "globalId does not match UUID pattern"
**Cause:** `globalId` is missing or not in RFC 4122 UUID form (any version; shape-only validation against the 8-4-4-4-12 hex pattern).
**Fix:** Generate a UUID for every Unit, Lesson, Item, and Question. Use any standard UUID library; v4 is recommended.

### Error: "Unsupported specVersion '2.0'"
**Cause:** The document declares a `specVersion` whose major version exceeds 1.
**Fix:** This validator implements LC-JSON 1.x. Either update the validator or correct the `specVersion` to a 1.x value.

---

## Related Documentation

- [`NORMATIVE.md`](NORMATIVE.md) — RFC 2119 conformance requirements (the authoritative source for what implementations must do)
- [`HTML_SAFETY.md`](HTML_SAFETY.md) — Normative HTML allowlist for `ContentItem.html` and `SignpostItem.customHtml` (elements, attributes, URL schemes, sanitization)
- [`ACCESSIBILITY.md`](ACCESSIBILITY.md) — Producer/consumer accessibility obligations (alt text, captions, keyboard, language/direction) with WCAG 2.1 AA cross-references and recommended ARIA patterns; the opt-in Accessibility Profile claim binds these as MUSTs per NORMATIVE.md §12
- [`VALIDATION.md`](VALIDATION.md) — Catalog of every documented validation rule, tagged schema-enforced / domain-validator-enforced / advisory, with citations to the enforcing site (schemas, `validate_course.py`, or prose). One-map view for implementers building consumers, validators, or round-trip tests.
- [`ITEM_PATTERNS.md`](ITEM_PATTERNS.md) — Informative authoring guide for items + signposts + objectives
- [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) — Directory of tools that produce, consume, or validate LC-JSON
- [`CONTRIBUTORS.md`](CONTRIBUTORS.md) — Acknowledgments
- [`schemas/`](schemas/) — JSON Schema files (the contract)
- [`examples/`](examples/) — Example documents for every artifact and question type
- [`tests/`](tests/) — Conformance test corpus (valid and invalid cases)
- [`question-types-reference.md`](question-types-reference.md) — Per-type property reference

---

## Version History

### v1.0-rc.2 (target: 2026-05-30) — initial public release candidate

- Two artifact types under a common flat root: `course` (hierarchical) and `questionSet` (flat).
- 12 user-facing question types fully implemented and schema-validated; 7 graphic/upload types reserved for a 2027 minor version.
- 23 JSON Schemas (Draft 7) covering every artifact, item type, and question type.
- 32 example files; conformance test corpus under [`tests/`](tests/) (13 valid + 25 invalid = 38 cases).
- Reference validator (`tools/validate_course.py`) and conformance corpus harness (`tools/run_corpus.py`).
- **`prompt` field correction (the rc.1 → rc.2 change):** `prompt` remains required but `minLength` is `0`, so an empty string `""` is valid. `prompt` is defined as **non-authoritative** for the eight symbolic question types (gap-fill family, sentence transformation, matching, ordering, placement), whose structured fields carry the question's meaning; for those types it MAY be empty or MAY carry a brief producer-derived readable summary. A reference-validator domain rule still flags an empty `prompt` on the four real-content types (true/false, multiple choice, short answer, essay), where it *is* the question. Backwards-compatible widening — every rc.1-valid document remains valid under rc.2.
- Apache 2.0 throughout. Release-candidate schemas are published as **immutable** at `https://lc-json.org/1.0-rc.2/*.schema.json`; the `https://lc-json.org/1.0/*.schema.json` URL space is reserved for the accepted final release.

### v1.0-rc.1 — internal release candidate (superseded, never announced)

- Frozen and served at `https://lc-json.org/1.0-rc.1/*.schema.json` for transparency, but never publicly announced; rc.2 is the first announced prerelease. The only substantive difference is the backwards-compatible `prompt` `minLength` `1` → `0` correction above; the `/1.0-rc.1/` schema URLs remain immutable and any document valid under rc.1 is valid under rc.2.

### v1.0 (planned: 2026-06-30) — accepted final release

- Will publish schemas as immutable at `https://lc-json.org/1.0/*.schema.json`.
- Deepens [`ACCESSIBILITY.md`](ACCESSIBILITY.md) (the rc.2 release) additively: per-criterion normative cross-reference table, expanded ARIA patterns, screen-reader announcement timing, accessibility-conformance fixtures, with select producer obligations promoted into [`NORMATIVE.md`](NORMATIVE.md).
- Any non-breaking refinements caught during the release-candidate cycle land here, or in subsequent immutable `/1.0-rc.N/` releases prior to final.

> *LC-JSON 1.0 is the format's first public release. Internal iteration prior to publication is not reflected in the version history.*

---

## Contributing

PRs welcome. To propose a new question type or modify an existing one, see [`Adding a new question type`](#for-developers) above. For non-trivial changes, open an issue first to discuss the proposal.

See [`CONTRIBUTORS.md`](CONTRIBUTORS.md) for acknowledgments.

---

## Support

- **GitHub Issues:** open an issue on the spec repository.
- **Conformance questions:** consult [`NORMATIVE.md`](NORMATIVE.md); it is the authoritative source for implementer requirements.

---

**LC-JSON Specification v1.0-rc.2**
