# LC-JSON Validation Surface

**Status:** Informative reference. The authoritative rules live in [`NORMATIVE.md`](NORMATIVE.md), the JSON Schemas under [`schemas/`](schemas/), and the reference validator [`tools/validate_course.py`](../tools/validate_course.py). This document catalogs them in one place.
**Spec version:** 1.0
**Last updated:** 2026-05-24

This document maps every documented validation rule in LC-JSON (Learning Content JSON) 1.0 to the place where it is enforced. The audience is implementers building consumers, validators, or producer round-trip tests — the same audience as [`NORMATIVE.md`](NORMATIVE.md).

The catalog is **additive and descriptive**: it introduces no new normative rules. The inventory pass that built this catalog (2026-05-24) surfaced eight documented-but-unenforced rules; all eight were closed in the same rc.1-polish session by extending [`tools/validate_course.py`](../tools/validate_course.py) (no schema changes). See [§14 Forward-looking deepenings](#14-forward-looking-deepenings-10-final) for what's still scheduled for `1.0` final.

---

## 1. Scope and structure

LC-JSON's validation surface is split across four enforcement sites:

- **23 JSON Schemas** in [`schemas/`](schemas/) — declarative constraints (Draft 7) enforced by any conforming JSON Schema validator.
- **[`NORMATIVE.md`](NORMATIVE.md)** — RFC 2119 prose obligations that may or may not be representable in JSON Schema.
- **[`tools/validate_course.py`](../tools/validate_course.py)** (the reference validator) — domain checks that run after schema validation, plus consumer-friendly diagnostics.
- **Companion normative documents and informative references** — [`HTML_SAFETY.md`](HTML_SAFETY.md) (normative) and [`ACCESSIBILITY.md`](ACCESSIBILITY.md) (normative for tools claiming the Accessibility Profile; preservation obligations bind every consumer per [`NORMATIVE.md`](NORMATIVE.md) §12.1); per-type prose in [`question-types-reference.md`](question-types-reference.md) and authoring patterns in [`ITEM_PATTERNS.md`](ITEM_PATTERNS.md) (both informative).

A consumer that only runs schema validation will accept documents the spec considers invalid (e.g. an MCQ with no correct option, a `placement` whose `placements[].gap` points at a missing `@@@N` marker). A consumer that re-implements the reference validator from prose will miss rules. This catalog gives implementers one map of *"these are all the things a conforming consumer must check, and here's where each rule is enforced."*

### 1.1 The three enforcement tiers

The rule tables below tag each rule with one tier:

| Tier | Meaning | Citation format |
|---|---|---|
| **Schema-enforced** | Expressed in one of the JSON Schemas under [`schemas/`](schemas/). Any Draft-7 validator catches violations. | `schemas/<file>.schema.json: <json-pointer>` |
| **Domain-validator-enforced** | Not (or not cleanly) expressible in JSON Schema; the reference validator [`tools/validate_course.py`](../tools/validate_course.py) checks it. Conforming consumers MUST replicate these checks to round-trip and grade correctly. | `validate_course.py: <function-name>` + NORMATIVE § where cited |
| **Advisory** | Described in prose ([`NORMATIVE.md`](NORMATIVE.md), [`README.md`](README-spec.md), [`question-types-reference.md`](question-types-reference.md), [`ITEM_PATTERNS.md`](ITEM_PATTERNS.md)) but not mechanically enforced anywhere. SHOULD/MAY rules, naming conventions, behaviors the spec hints at but lets consumers vary. Listed so implementers know what they are choosing. | Document and section |

A fourth, implicit tier — **runtime-enforced** — covers grading policy, navigation gating, gradebook display. Out of scope for this document; LC-JSON specifies *document validity*, not runtime behavior.

### 1.2 Severity (Domain-validator rows)

The reference validator distinguishes three severities on its domain-rule pass. Schema-enforced rows are always hard errors (any schema violation fails the document); Advisory rows are not enforced. Domain rows carry one of:

- **ERROR** — the validator returns non-zero exit; the document is non-conforming. Consumers MUST reject.
- **WARN** — the document is reported as suspect but still parses; the validator returns success. Conforming consumers SHOULD surface the warning to the user.
- **NOTE** — informational only (e.g. `item.points` intentionally weighted away from the sum of question points). The validator returns success without raising; no consumer obligation.

Where a single rule is enforced at multiple tiers (e.g. schema + validator double-check for friendlier messages), the row lists both. Satisfying the strictest tier suffices.

### 1.3 Strict mode and the lenient migration path

The reference validator [`tools/validate_course.py`](../tools/validate_course.py) accepts a `--strict` flag. The default (lenient) mode emits a warning and falls through with reduced enforcement when it encounters two pre-1.0 document shapes: the wrapped envelope `{"course": {...}}` and the bare payload `{"units": [...]}` with no `documentType`. Neither shape is part of the published 1.0 contract; the lenient handling is a **maintainer-side migration aid** that allows pre-1.0 document shapes to be ingested during the upgrade — it is not a published affordance third-party producers may rely on.

Under `--strict`, both shapes are fatal errors. The conformance corpus harness [`tools/run_corpus.py`](../tools/run_corpus.py) always invokes the validator with `--strict` (every fixture is run through the validator); CI runs the harness on every PR; and per [`NORMATIVE.md`](NORMATIVE.md) §10.3 conformance claims under §10 are evaluated in `--strict` mode. **The published conformance contract is the `--strict` behavior** — third-party consumers and producers should treat the lenient path as a maintainer-side migration aid only.

Rows in the tables below that depend on this distinction explicitly say "ERROR under `--strict`; WARN otherwise"; everywhere else, the rule applies uniformly.

---

## 2. Where to look

| What | Where |
|---|---|
| JSON Schemas | [`schemas/*.schema.json`](schemas/) — 23 files |
| Reference validator | [`tools/validate_course.py`](../tools/validate_course.py) |
| Conformance language (RFC 2119 MUSTs/SHOULDs/MAYs) | [`NORMATIVE.md`](NORMATIVE.md) |
| Per-type property reference | [`question-types-reference.md`](question-types-reference.md) |
| HTML safety profile (elements, attributes, URL schemes, sanitization) | [`HTML_SAFETY.md`](HTML_SAFETY.md) |
| Accessibility profile (preservation + opt-in delivery claim) | [`ACCESSIBILITY.md`](ACCESSIBILITY.md) |
| Item authoring patterns (consumer-policy plurality) | [`ITEM_PATTERNS.md`](ITEM_PATTERNS.md) |
| Conformance test fixtures | [`tests/`](tests/) — manifest + valid/invalid sets |

---

## 3. Root document

Required root fields ([`NORMATIVE.md`](NORMATIVE.md) §3.2). Both artifact types (`course`, `questionSet`) share these.

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| **Producer** MUST emit `$schema` pointing at the canonical published schema URL | Schema-enforced (producer validity) | `course.schema.json: /required[*]="$schema"`, `question-set.schema.json: /required[*]="$schema"` | §3.2, §4.7 |
| **Consumer** SHOULD tolerate documents that omit `$schema` (infer the schema from `documentType` + `specVersion`); MUST reject any other root-field omission | Advisory (consumer-side import tolerance) | [`NORMATIVE.md`](NORMATIVE.md) §3.2 | §3.2 |
| `$schema`, when present, is a URI | Schema-declared via `format: "uri"` (annotation; not universally enforced by Draft-7 validators — see [§13](#13-conformance-note)) | `course.schema.json: /properties/$schema/format="uri"`, `question-set.schema.json: /properties/$schema/format="uri"` | §4.7 |
| `documentType` required at root | Schema-enforced | `course.schema.json: /required[*]="documentType"`, `question-set.schema.json: /required[*]="documentType"` | §3.2 |
| `documentType` is `"course"` (course document) | Schema-enforced | `course.schema.json: /properties/documentType/const="course"` | §3.2, §4.2, §5.3 |
| `documentType` is `"questionSet"` (question-set document) | Schema-enforced | `question-set.schema.json: /properties/documentType/const="questionSet"` | §3.2, §4.2, §5.3 |
| Non-canonical `documentType` casing rejected (`"Course"`, `"questionset"`, `"question-set"`) | Schema-enforced (via `const`) | `course.schema.json` / `question-set.schema.json` `const`; `validate_course.py: dispatch_document_shape` provides casing-tolerant dispatch as a maintainer-side migration aid ([§1.3](#13-strict-mode-and-the-lenient-migration-path)) — disabled under `--strict` | §4.2, §5.3 |
| `specVersion` required at root | Schema-enforced | `course.schema.json: /required[*]="specVersion"`, `question-set.schema.json: /required[*]="specVersion"` | §3.2, §4.6 |
| `specVersion` matches `^1\.[0-9]+(\.[0-9]+)?$` | Schema-enforced + Domain-validator-enforced (ERROR for `2.x`+) | `course.schema.json: /properties/specVersion/pattern`; `validate_course.py: check_spec_version` | §4.6, §5.2 |
| `specVersion` MUST NOT carry an `-rc.N` suffix | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §4.6, §8.4 | §4.6 |
| `language` required at root | Schema-enforced | `course.schema.json: /required[*]="language"`, `question-set.schema.json: /required[*]="language"` | §12.1 |
| `language` SHOULD be a 2-letter ISO 639-1 code (course) | Advisory | `course.schema.json: /properties/language/description` (no `pattern`) | §12.1, [`ACCESSIBILITY.md`](ACCESSIBILITY.md) §6.1 |
| `supportLanguage` is a 2-letter ISO 639-1 code (or omitted/null) | Domain-validator-enforced (WARN; schema typed only) | `validate_course.py: validate_course_level` (course path) and `validate_question_set_flat` (question-set path) | §12.1 |
| Pre-1.0 wrapped envelope `{"course": {...}}` rejected (published contract; lenient migration aid in default mode) | Domain-validator-enforced (ERROR under `--strict`; WARN otherwise — see [§1.3](#13-strict-mode-and-the-lenient-migration-path)) | `validate_course.py: validate_course` (`--strict` branch) | §3.2, §4.1 |
| Pre-1.0 bare payload `{"units": [...]}` rejected (published contract; lenient migration aid in default mode) | Domain-validator-enforced (ERROR under `--strict`; WARN otherwise — see [§1.3](#13-strict-mode-and-the-lenient-migration-path)) | `validate_course.py: validate_course` (`--strict` branch) | §3.2, §4.1 |
| Property names are camelCase | Advisory (consumer-side import is lenient via `JsonNormalizer`-style helpers) | [`NORMATIVE.md`](NORMATIVE.md) §4.5 | §4.5 |
| Extension members keyed `x-<namespace>` MAY appear on root + Course/Unit/Lesson/Item/Question | Advisory (schemas do not restrict `additionalProperties` on those objects) | [`NORMATIVE.md`](NORMATIVE.md) §7.1 | §7.1 |
| Extension members MUST NOT appear on `matching.pairs[*]`, `matching.categories[*]`, or `placement.placements[*]` | Schema-enforced | `matching.schema.json: /allOf/1/then/properties/pairs/items/additionalProperties=false` etc.; `placement.schema.json: /allOf/1/properties/placements/items/additionalProperties=false` | §7.1 |
| Producer MUST NOT introduce a non-extension field beginning with `x-` | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §7.1 | §7.1 |
| Consumer MUST NOT reject documents solely for unknown fields or `x-` members | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §5.4, §7.4 | §5.4, §7.4 |

---

## 4. Course-level

Course payload fields on a `documentType: "course"` document.

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `title` required, `minLength: 1` | Schema-enforced + Domain-validator-enforced | `course.schema.json: /properties/title`, `/required[*]="title"`; `validate_course.py: validate_course_level` | §3.2 |
| `sourceCourseId`, when present, matches the RFC 4122 UUID pattern (any version; shape-only validation) | Schema-enforced + Domain-validator-enforced (WARN if non-UUID) | `course.schema.json: /properties/sourceCourseId/pattern`; `validate_course.py: validate_course_level` | §4.4 |
| `sourceCourseId` SHOULD be emitted for re-importable or version-tracked courses | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §4.4 | §4.4 |
| `version`, when present, matches `^[0-9]+(\.[0-9]+){0,2}$` (1–3 numeric segments) | Schema-enforced + Domain-validator-enforced (WARN) | `course.schema.json: /properties/version/pattern`; `validate_course.py: validate_course_level` | §4.4 |
| Pre-1.0 identity fields (`authorId`, `authorCourseId`) trigger a migration warning | Domain-validator-enforced (WARN) | `validate_course.py: validate_course_level` | (none — migration aid) |
| Course `objectives[*].id` and `objectives[*].text` required | Schema-enforced | `course.schema.json: /properties/objectives/items/required` | (none) |
| Course `objectives[*].difficultyBand` enum: `"Recall"`, `"Understand"`, `"Apply"`, `"Analyze"`, null | Schema-enforced | `course.schema.json: /properties/objectives/items/properties/difficultyBand/enum` | (none) |
| `courseObjectiveIds[*]` reference `course.objectives[].id` | Domain-validator-enforced (WARN) | `validate_course.py` (objective-reference integrity check) | (none — warning-tier integrity check; unresolved references break signpost auto-rendering) |
| `estimatedDurationMinutes >= 0` | Schema-enforced | `course.schema.json: /properties/estimatedDurationMinutes/minimum` | (none) |
| Course `tags[*]` are strings (Unit/Lesson/Item additionally enforce `minLength: 1`) | Schema-enforced | `course.schema.json: /properties/tags/items/type="string"`; `unit.schema.json` / `lesson.schema.json` / `item-base.schema.json: /properties/tags/items/minLength=1` | (none) |
| `units[]` MUST be present at the root (course); is an array when present | Domain-validator-enforced (ERROR if missing); Schema-enforced (array type when present) | `validate_course.py: validate_course` ("Missing 'units' array at root level"); `course.schema.json: /properties/units/type="array"` (the schema's `default: []` would otherwise admit a missing field) | (none) |

---

## 5. Unit-level

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `globalId` required | Schema-enforced + Domain-validator-enforced | `unit.schema.json: /required[*]="globalId"`; `validate_course.py: validate_unit` | §4.4 |
| `globalId` matches the RFC 4122 UUID pattern (any version; shape-only validation) | Schema-enforced + Domain-validator-enforced (WARN if non-UUID) | `unit.schema.json: /properties/globalId/pattern`; `validate_course.py: validate_unit` (via `is_valid_uuid`) | §4.4 |
| `title` required, `minLength: 1` | Schema-enforced + Domain-validator-enforced | `unit.schema.json: /properties/title`, `/required[*]="title"`; `validate_course.py: validate_unit` | (none) |
| `description` defaults to `""` | Schema-declared (annotation; not enforced — see [§13](#13-conformance-note)) | `unit.schema.json: /properties/description/default` | (none) |
| `tags[*]` `minLength: 1` | Schema-enforced | `unit.schema.json: /properties/tags/items/minLength` | (none) |
| `sequence >= 0` | Schema-enforced | `unit.schema.json: /properties/sequence/minimum` | (none — import uses array position, not `sequence`) |
| `sequence` duplicates/gaps within siblings | Domain-validator-enforced (WARN, advisory) | `validate_course.py: validate_sequence_order` | (none) |
| `objectiveIds[*]` reference `course.objectives[].id` | Domain-validator-enforced (WARN) | `validate_course.py` (objective-reference integrity check) | (none) |
| `lessons[]` array (default `[]` schema-declared) | Schema-enforced (type) | `unit.schema.json: /properties/lessons` | (none) |

---

## 6. Lesson-level

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `globalId` required + RFC 4122 UUID pattern (any version; shape-only validation) | Schema-enforced + Domain-validator-enforced (WARN) | `lesson.schema.json: /required`, `/properties/globalId/pattern`; `validate_course.py: validate_lesson` | §4.4 |
| `title` required, `minLength: 1` | Schema-enforced + Domain-validator-enforced | `lesson.schema.json`; `validate_course.py: validate_lesson` | (none) |
| `items[]` is an array of `content`/`exercise`/`quiz`/`contentsequence`/`signpost` (`oneOf` dispatch) | Schema-enforced | `lesson.schema.json: /properties/items/items/oneOf` | (none) |
| `items` missing or empty — informational | Domain-validator-enforced (WARN) | `validate_course.py: validate_lesson` ("empty lesson") | (none) |
| `sequence` duplicates/gaps within siblings (lesson item ordering) | Domain-validator-enforced (WARN, advisory) | `validate_course.py: validate_sequence_order` | (none) |
| `objectiveIds[*]` reference `course.objectives[].id` | Domain-validator-enforced (WARN) | `validate_course.py` (objective-reference integrity check) | (none) |

---

## 7. Item-level — common

Properties inherited by every item type via `item-base.schema.json`.

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` required, enum: `content`, `exercise`, `quiz`, `contentsequence`, `signpost` | Schema-enforced + Domain-validator-enforced | `item-base.schema.json: /properties/type/enum`, `/required`; `validate_course.py: validate_item` | §4.2, §5.3 |
| Non-canonical item-type casing (`Content`, `ExerciseItem`) rejected | Schema-enforced (via `enum`/`const`) + Domain-validator-enforced (WARN; tolerated via `normalize_item_type`) | `item-base.schema.json`; `validate_course.py: validate_item` | §4.2, §5.3 |
| `globalId` required + RFC 4122 UUID pattern (any version; shape-only validation) | Schema-enforced + Domain-validator-enforced (WARN) | `item-base.schema.json: /required`, `/properties/globalId/pattern`; `validate_course.py: validate_item` | §4.4 |
| `title` required, `minLength: 1` | Schema-enforced + Domain-validator-enforced (WARN if missing) | `item-base.schema.json`; `validate_course.py: validate_item` | (none) |
| `tags[*]` `minLength: 1` | Schema-enforced | `item-base.schema.json: /properties/tags/items/minLength` | (none) |
| `suggestedTime >= 0` | Schema-enforced | `item-base.schema.json: /properties/suggestedTime/minimum` | (none) |
| `isOptional` boolean, default `false` (schema-declared) | Schema-enforced (type) | `item-base.schema.json: /properties/isOptional` | (none) |

### 7.1 ContentItem

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"content"` | Schema-enforced | `content-item.schema.json: /allOf/1/properties/type/const="content"` | §4.2 |
| `html` required | Schema-enforced + Domain-validator-enforced | `content-item.schema.json: /allOf/1/required[*]="html"`; `validate_course.py: validate_item` (`normalized_type == "content"`) | (none) |
| Deprecated `body` property → use `html` | Domain-validator-enforced (WARN) | `validate_course.py: validate_item` | (none) |
| `html` content satisfies the HTML safety profile | Domain-validator-enforced (ERROR / WARN per [`HTML_SAFETY.md`](HTML_SAFETY.md) §8) | `validate_course.py: validate_html_content` | §11, [`HTML_SAFETY.md`](HTML_SAFETY.md) (see [§12](#12-cross-cutting) below) |

### 7.2 ExerciseItem

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"exercise"` | Schema-enforced | `exercise-item.schema.json: /allOf/1/properties/type/const="exercise"` | §4.2 |
| `questions[]` required | Schema-enforced + Domain-validator-enforced | `exercise-item.schema.json: /allOf/1/required[*]="questions"`; `validate_course.py: validate_item` | (none) |
| `instructions` required (PascalCase `Instructions` triggers WARN) | Domain-validator-enforced (ERROR if missing, WARN on PascalCase) | `validate_course.py: validate_item` | (none) |
| `isGraded` boolean, default `false` (schema-declared) | Schema-enforced (type) | `exercise-item.schema.json: /allOf/1/properties/isGraded/default=false` | §4.3 |
| `passMarkPercent` is a number `0 <= x <= 100`, default `70.0` (schema-declared) | Schema-enforced (type/range) | `exercise-item.schema.json: /allOf/1/properties/passMarkPercent/{minimum,maximum,default}` | (none — consumer-policy gated; see [`ITEM_PATTERNS.md`](ITEM_PATTERNS.md) §3) |
| `points >= 0` | Schema-enforced | `exercise-item.schema.json: /allOf/1/properties/points/minimum` | (none) |
| Producer/consumer MUST NOT infer grading state from item type alone | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §4.3 | §4.3 |

### 7.3 QuizItem

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"quiz"` | Schema-enforced | `quiz-item.schema.json: /allOf/1/properties/type/const="quiz"` | §4.2 |
| `questions[]` required, `isGraded` required | Schema-enforced | `quiz-item.schema.json: /allOf/1/required[*]={"questions","isGraded"}` | (none) |
| `isGraded` boolean, default `true` (schema-declared) | Schema-enforced (type) | `quiz-item.schema.json: /allOf/1/properties/isGraded/default=true` | §4.3 |
| `passMarkPercent` is a number `0 <= x <= 100`, default `70.0` (schema-declared) | Schema-enforced (type/range) | `quiz-item.schema.json: /allOf/1/properties/passMarkPercent` | (none — see [`ITEM_PATTERNS.md`](ITEM_PATTERNS.md) §3) |
| `points >= 0` | Schema-enforced | `quiz-item.schema.json: /allOf/1/properties/points/minimum` | (none) |
| `item.points` vs `sum(question.points)` mismatch is intentional weighting | Domain-validator-enforced (NOTE) | `validate_course.py` (weighted-points NOTE collection) | (none) |

### 7.4 ContentSequenceItem

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"contentsequence"` | Schema-enforced | `content-sequence-item.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `contentItemId` required; value is a UUID | Schema-enforced (required) + Domain-validator-enforced (WARN if non-UUID) | `content-sequence-item.schema.json: /allOf/1/required`, `/properties/contentItemId/format="uuid"` (annotation — see [§13](#13-conformance-note)); `validate_course.py: validate_item` (via `is_valid_uuid`) | (none) |
| `relatedItemIds[*]` are UUIDs | Domain-validator-enforced (WARN); schema declares `format: "uuid"` as annotation | `content-sequence-item.schema.json: /allOf/1/properties/relatedItemIds/items/format="uuid"` (annotation); `validate_course.py: validate_item` (via `is_valid_uuid`) | (none) |
| `relatedItemIds` non-empty array | Domain-validator-enforced (ERROR if missing or empty) | `validate_course.py: validate_item` | (none) |
| `layout` enum: `"Auto"`, `"Split"`, `"Vertical"`, default `"Auto"` (schema-declared) | Schema-enforced (enum) + Domain-validator-enforced (WARN if other) | `content-sequence-item.schema.json: /allOf/1/properties/layout/enum`; `validate_course.py: validate_item` | (none) |
| `contentItemId` resolves to a sibling `content` item declared earlier in the lesson | Domain-validator-enforced (ERROR) | `validate_course.py: validate_item` (CSI branch) | (none) |
| Each `relatedItemIds[*]` resolves to a sibling `exercise`/`quiz` item declared earlier in the lesson | Domain-validator-enforced (ERROR) | `validate_course.py: validate_item` (CSI branch) | (none) |

### 7.5 SignpostItem

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"signpost"` | Schema-enforced | `signpost-item.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `signpostType` required, enum: `"intro"`, `"summary"` | Schema-enforced + Domain-validator-enforced (ERROR if missing or other) | `signpost-item.schema.json: /allOf/1/required`, `/properties/signpostType/enum`; `validate_course.py: validate_item` | (none) |
| `scope` required, enum: `"course"`, `"unit"`, `"lesson"` | Schema-enforced + Domain-validator-enforced (ERROR if missing or other) | `signpost-item.schema.json: /allOf/1/required`, `/properties/scope/enum`; `validate_course.py: validate_item` | (none) |
| Signpost items MUST NOT carry `questions` | Domain-validator-enforced (ERROR) | `validate_course.py: validate_item` (signpost branch) | (none) |
| `customHtml`, when present, satisfies the HTML safety profile | Domain-validator-enforced (ERROR / WARN per [`HTML_SAFETY.md`](HTML_SAFETY.md) §8) | `validate_course.py: validate_html_content` | §11, [`HTML_SAFETY.md`](HTML_SAFETY.md) |
| A signpost with no objectives (and no `customHtml`) renders an empty stub | Advisory | [`ITEM_PATTERNS.md`](ITEM_PATTERNS.md) §5 | (none) |

---

## 8. Question-level — common

Properties inherited by every question via `question-base.schema.json`. Required by NORMATIVE §4.4: every question MUST carry a `globalId`.

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` required + enum (19 values: 12 implemented + 7 reserved) | Schema-enforced + Domain-validator-enforced | `question-base.schema.json: /required[*]="type"`, `/properties/type/enum`; `validate_course.py: validate_question` | §4.2, §5.3, §6.1 |
| Non-canonical question-type casing (`MultipleChoice`, `simplegapfill`) rejected | Schema-enforced (via `enum`) + Domain-validator-enforced (ERROR for unknown discriminator) | `question-base.schema.json: /properties/type/enum`; `validate_course.py` (per-type question dispatch) | §4.2, §5.3 |
| `globalId` required + RFC 4122 UUID pattern (any version; shape-only validation) | Schema-enforced + Domain-validator-enforced (WARN if non-UUID) | `question-base.schema.json: /required[*]="globalId"`, `/properties/globalId/pattern`; `validate_course.py: validate_question` | §4.4 |
| `prompt` required, `minLength: 0` (may be empty); empty/whitespace `prompt` is an **ERROR** for the 4 real-content types (`trueFalseQuestion`, `multipleChoice`, `shortAnswer`, `essay`), valid (empty) for the 8 symbolic types, and unconstrained for the 7 reserved types (deferred to v1.1) | Schema-enforced (`required`, `minLength: 0`) + Domain-validator-enforced (ERROR on real-content empty; WARN if missing) | `question-base.schema.json: /required[*]="prompt"`, `/properties/prompt/minLength`; `validate_course.py: validate_question` | (none) |
| `points` is a non-negative number, MAY be null, default `1.0` (schema-declared) | Schema-enforced (type/range) + Domain-validator-enforced (WARN if missing) | `question-base.schema.json: /properties/points/{type,minimum,default}`; `validate_course.py: validate_question` | (none) |
| `difficulty` is a number `0.0 <= x <= 10.0`, default `5.0` (schema-declared) | Schema-enforced (type/range) | `question-base.schema.json: /properties/difficulty/{minimum,maximum,default}` | (none — author estimate; see [`question-types-reference.md`](question-types-reference.md) Common Properties) |
| `tags[*]` strings | Schema-enforced | `question-base.schema.json: /properties/tags/items/type` | (none) |
| `hint` is string or null, default null | Schema-enforced | `question-base.schema.json: /properties/hint` | (none) |
| `feedback` is an object or null; `feedback.{correct,incorrect}` are strings; `feedback.choiceFeedback` is `{string: string}` | Schema-enforced | `question-base.schema.json: /properties/feedback` | (none) |
| Deprecated `questionType` (instead of `type`) | Domain-validator-enforced (ERROR) | `validate_course.py: validate_question` | (none — migration aid) |
| For non-question fields: producer MUST NOT embed HTML in plain-text fields | Advisory | [`HTML_SAFETY.md`](HTML_SAFETY.md) §1.1 | §11 |

---

## 9. Question-level — by type (12 implemented)

Properties enforced per question-type schema, plus per-type domain-validator rules. The 7 reserved types are covered in [§10](#10-reserved-and-unknown-types).

### 9.1 simpleGapFill

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"simpleGapFill"` | Schema-enforced | `simple-gap-fill.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `sentence` required, contains `@@@`, `minLength: 4` | Schema-enforced | `simple-gap-fill.schema.json: /allOf/1/required`, `/properties/sentence/{pattern,minLength}` | (none) |
| `acceptedAnswers` required, `minItems: 1`, each `minLength: 1` | Schema-enforced | `simple-gap-fill.schema.json: /allOf/1/required`, `/properties/acceptedAnswers/{minItems,items/minLength}` | (none) |
| `caseSensitive` boolean, default `false` (schema-declared) | Schema-enforced (type) | `simple-gap-fill.schema.json: /allOf/1/properties/caseSensitive` | (none) |

### 9.2 trueFalseQuestion

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"trueFalseQuestion"` | Schema-enforced | `true-false-question.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `correctAnswer` required, boolean | Schema-enforced + Domain-validator-enforced (ERROR if missing both v1 and v2 forms, ERROR if non-boolean, WARN on boolean-ish coercion) | `true-false-question.schema.json: /allOf/1/required`, `/properties/correctAnswer/type`; `validate_course.py: validate_true_false_question` | (none) |
| Pre-1.0 TF shape (`options` / `optionsAndPoints`) deprecated | Domain-validator-enforced (WARN; multiple positive-points options WARN; zero positives WARN) | `validate_course.py: validate_true_false_question` | (none) |
| `displayStyle` enum: `"TrueFalse"`, `"CorrectIncorrect"`, `"CheckmarkX"`, default `"TrueFalse"` (schema-declared) | Schema-enforced (enum) + Domain-validator-enforced (WARN if other) | `true-false-question.schema.json: /allOf/1/properties/displayStyle/enum`; `validate_course.py: validate_true_false_question` | (none) |
| `penalizeIncorrect` boolean, default `false` (schema-declared) | Schema-enforced (type) | `true-false-question.schema.json: /allOf/1/properties/penalizeIncorrect` | (none) |
| `incorrectPenaltyPercent` is `0..100`, default `50.0` (schema-declared) | Schema-enforced (type/range) + Domain-validator-enforced (WARN if out of range) | `true-false-question.schema.json: /allOf/1/properties/incorrectPenaltyPercent/{minimum,maximum}`; `validate_course.py: validate_true_false_question` | (none) |
| `feedback.choiceFeedback` deprecated on TF | Domain-validator-enforced (WARN) | `validate_course.py: validate_true_false_question` | (none — TF v2 forbids the field; see [`question-types-reference.md`](question-types-reference.md)) |

### 9.3 multipleChoice

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"multipleChoice"` | Schema-enforced | `multiple-choice.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `options` required, `minItems: 2`, each `minLength: 1` | Schema-enforced | `multiple-choice.schema.json: /allOf/1/required`, `/properties/options/{minItems,items/minLength}` | (none) |
| `optionsAndPoints` required, `{string: number}` map | Schema-enforced | `multiple-choice.schema.json: /allOf/1/required`, `/properties/optionsAndPoints` | (none) |
| At least one `optionsAndPoints` value > 0 (an MCQ MUST have a correct answer) | Domain-validator-enforced (ERROR) | `validate_course.py: validate_multiple_choice` | (none) |
| `optionsAndPoints` keys cover every entry in `options` | Domain-validator-enforced (ERROR if missing; WARN if `optionsAndPoints` contains extras not in `options`) | `validate_course.py: validate_multiple_choice` | (none) |
| `allowMultipleCorrect` boolean, default `false` (schema-declared) | Schema-enforced (type) | `multiple-choice.schema.json: /allOf/1/properties/allowMultipleCorrect` | (none) |
| `allowPartialCredit` boolean, default `true` (schema-declared) | Schema-enforced (type) | `multiple-choice.schema.json: /allOf/1/properties/allowPartialCredit` | (none) |
| `penalizeIncorrect` boolean, default `false` (schema-declared) | Schema-enforced (type) | `multiple-choice.schema.json: /allOf/1/properties/penalizeIncorrect` | (none) |
| `showLetterLabels` boolean, default `false` (schema-declared) | Schema-enforced (type) | `multiple-choice.schema.json: /allOf/1/properties/showLetterLabels` | (none) |
| `shuffleOptions` governs per-question option randomization (per-question discretion) | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §5.6 (multipleChoice is explicitly exempt from the §5.6 randomization MUST) | §5.6 |

### 9.4 wordBankCloze

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"wordBankCloze"` | Schema-enforced | `word-bank-cloze.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `passage` required, matches `@@@\d+`, `minLength: 4` | Schema-enforced | `word-bank-cloze.schema.json: /allOf/1/required`, `/properties/passage/{pattern,minLength}` | (none) |
| `wordBank` required, `minItems: 1`, each `minLength: 1` | Schema-enforced | `word-bank-cloze.schema.json: /allOf/1/required`, `/properties/wordBank` | (none) |
| `gapAcceptedAnswers` required, `{"^[0-9]+$": [string]}`, each gap `minItems: 1`, each accepted answer `minLength: 1` | Schema-enforced | `word-bank-cloze.schema.json: /allOf/1/required`, `/properties/gapAcceptedAnswers/patternProperties` | (none) |
| `passage` `@@@N` marker set MUST equal `gapAcceptedAnswers` key set | Domain-validator-enforced (ERROR) | `validate_course.py: validate_word_bank_cloze` (cloze gap-consistency check) | (none) |
| `@@@N` marker numbers SHOULD be sequential starting at 1 | Domain-validator-enforced (WARN) | `validate_course.py: validate_word_bank_cloze` (cloze gap-consistency check) | (none) |
| `allowWordReuse` boolean, default `false` (schema-declared) | Schema-enforced (type) | `word-bank-cloze.schema.json: /allOf/1/properties/allowWordReuse` | (none) |
| `bankPosition` enum: `"above"`, `"below"`, `"side"` | Schema-enforced | `word-bank-cloze.schema.json: /allOf/1/properties/bankPosition/enum` | (none) |
| `gapCaseSensitive` / `gapFeedback` value types | Schema-enforced | `word-bank-cloze.schema.json: /allOf/1/properties/gapCaseSensitive`, `gapFeedback` | (none) |

### 9.5 multiGapCloze

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"multiGapCloze"` | Schema-enforced | `multi-gap-cloze.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `passage` required, matches `@@@\d+`, `minLength: 4` | Schema-enforced | `multi-gap-cloze.schema.json: /allOf/1/required`, `/properties/passage` | (none) |
| `gapAcceptedAnswers` required | Schema-enforced | `multi-gap-cloze.schema.json: /allOf/1/required` | (none) |
| Each accepted answer MUST NOT contain `,` or `:` (scoring-engine wire format) | Schema-enforced + Domain-validator-enforced (ERROR) | `multi-gap-cloze.schema.json: /allOf/1/properties/gapAcceptedAnswers/patternProperties/.../items/not/pattern="[,:]"`; `validate_course.py: validate_multi_gap_cloze` | (none — wire-format consequence) |
| Other punctuation in answers SHOULD be limited to apostrophes and hyphens | Domain-validator-enforced (WARN) | `validate_course.py: validate_multi_gap_cloze` | (none) |
| `passage` `@@@N` marker set MUST equal `gapAcceptedAnswers` key set | Domain-validator-enforced (ERROR) | `validate_course.py: validate_multi_gap_cloze` (cloze gap-consistency check) | (none) |
| `@@@N` marker numbers SHOULD be sequential starting at 1 | Domain-validator-enforced (WARN) | `validate_course.py: validate_multi_gap_cloze` (cloze gap-consistency check) | (none) |
| `allowPartialCredit` boolean, default `true` (schema-declared) | Schema-enforced (type) | `multi-gap-cloze.schema.json: /allOf/1/properties/allowPartialCredit` | (none) |

### 9.6 multipleChoiceCloze

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"multipleChoiceCloze"` | Schema-enforced | `multiple-choice-cloze.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `passage`, `gapOptions`, `correctAnswers` required | Schema-enforced | `multiple-choice-cloze.schema.json: /allOf/1/required` | (none) |
| Each gap's `gapOptions` has `minItems: 2` | Schema-enforced | `multiple-choice-cloze.schema.json: /allOf/1/properties/gapOptions/patternProperties/.../minItems` | (none) |
| `correctAnswers[N]` is a non-negative integer | Schema-enforced | `multiple-choice-cloze.schema.json: /allOf/1/properties/correctAnswers/patternProperties/.../{type,minimum}` | (none) |
| `correctAnswers[N]` index in bounds of `gapOptions[N]` | Domain-validator-enforced (ERROR) | `validate_course.py: validate_multiple_choice_cloze` | (none) |
| `passage` `@@@N` marker set MUST equal `gapOptions` key set | Domain-validator-enforced (ERROR) | `validate_course.py: validate_multiple_choice_cloze` (cloze gap-consistency check) | (none) |
| `gapOptions` key set MUST equal `correctAnswers` key set | Domain-validator-enforced (ERROR) | `validate_course.py: validate_multiple_choice_cloze` | (none) |
| `@@@N` marker numbers SHOULD be sequential starting at 1 | Domain-validator-enforced (WARN) | `validate_course.py: validate_multiple_choice_cloze` (cloze gap-consistency check) | (none) |
| `shuffleOptions` boolean, default `false` (schema-declared) | Schema-enforced (type) | `multiple-choice-cloze.schema.json: /allOf/1/properties/shuffleOptions` | (none) |

### 9.7 shortAnswer

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"shortAnswer"` | Schema-enforced | `short-answer.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `acceptedAnswers` required, `minItems: 1`, each `minLength: 1` | Schema-enforced | `short-answer.schema.json: /allOf/1/required`, `/properties/acceptedAnswers` | (none) |
| `acceptedAnswers[0]` is the canonical form for display | Advisory ([`question-types-reference.md`](question-types-reference.md) §7) | (no enforcement) | (none) |
| `caseSensitive` boolean, default `false` (schema-declared) | Schema-enforced (type) | `short-answer.schema.json: /allOf/1/properties/caseSensitive` | (none) |

### 9.8 essay

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"essay"` | Schema-enforced | `essay.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `expectedAnswer` required (string, may be empty) | Schema-enforced | `essay.schema.json: /allOf/1/required` | (none) |
| `expectedLines`, `minWords`, `maxWords` are integers `>= 0` (0 = no limit) | Schema-enforced | `essay.schema.json: /allOf/1/properties/{expectedLines,minWords,maxWords}` | (none) |
| `maxWords >= minWords` when both > 0 | Domain-validator-enforced (WARN) | `validate_course.py: validate_essay` | (none) |
| `rubricText` is Markdown when present | Advisory ([`question-types-reference.md`](question-types-reference.md) §8) | (none) | (none) |

### 9.9 sentenceTransformation

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"sentenceTransformation"` | Schema-enforced | `sentence-transformation.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `promptSentence`, `keyword`, `targetSentence`, `acceptedChunks` required | Schema-enforced + Domain-validator-enforced (ERROR if missing) | `sentence-transformation.schema.json: /allOf/1/required`; `validate_course.py: validate_sentence_transformation` | (none) |
| `targetSentence` contains exactly one `@@@` placeholder (`minLength: 4`); multiple `@@@` markers are non-conforming because SentenceTransformation chunks are sequential answer pieces typed at that single position, not separate gaps | Schema-enforced (pattern requires at least one `@@@`; `minLength`) + Domain-validator-enforced (ERROR if more than one `@@@`; WARN if zero) | `sentence-transformation.schema.json: /allOf/1/properties/targetSentence/{pattern,minLength}`; `validate_course.py: validate_sentence_transformation` | (none) |
| `acceptedChunks` keys are `^[0-9]+$`, each value `minItems: 1`, each chunk `minLength: 1` | Schema-enforced | `sentence-transformation.schema.json: /allOf/1/properties/acceptedChunks/patternProperties` | (none) |
| Chunk numbers SHOULD be sequential starting at 1 | Domain-validator-enforced (WARN) | `validate_course.py: validate_sentence_transformation` | (none) |
| `keyword` SHOULD be uppercase | Domain-validator-enforced (WARN) | `validate_course.py: validate_sentence_transformation` | (none) |
| Deprecated PascalCase chunks/keyword fields (`AcceptedChunks`, `Keyword`, …) → camelCase | Domain-validator-enforced (WARN) | `validate_course.py: validate_sentence_transformation` (`deprecated_props` map) | (none) |
| `allOrNothing` boolean, default `false` (schema-declared); `chunkCaseSensitive` / `chunkFeedback` typed maps | Schema-enforced (types) + Domain-validator-enforced (WARN if not boolean / not dict) | `sentence-transformation.schema.json`; `validate_course.py: validate_sentence_transformation` | (none) |

### 9.10 matching

`matching` carries an `if`/`then`/`else` branch in the schema, keyed off `matchingMode`.

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"matching"` | Schema-enforced | `matching.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `matchingMode` required, enum: `"pairs"`, `"classification"` | Schema-enforced | `matching.schema.json: /allOf/1/required`, `/properties/matchingMode/enum` | (none) |
| `pairs` mode: `pairs[]` required, `minItems: 2`, each `{item,match}` required, `additionalProperties: false` | Schema-enforced | `matching.schema.json: /allOf/1/then/{required,properties/pairs}` | §7.1 (closed object disallows `x-` extensions inside) |
| `pairs` mode: `categories` MUST NOT be present | Schema-enforced | `matching.schema.json: /allOf/1/then/not/required[*]="categories"` | (none) |
| `classification` mode: `categories[]` required, `minItems: 2`, each `{label,items}` required (`items.minItems: 1`), `additionalProperties: false` | Schema-enforced | `matching.schema.json: /allOf/1/else/{required,properties/categories}` | §7.1 |
| `classification` mode: `pairs` MUST NOT be present | Schema-enforced | `matching.schema.json: /allOf/1/else/not/required[*]="pairs"` | (none) |
| `distractors[*]` non-empty strings | Schema-enforced | `matching.schema.json: /allOf/1/properties/distractors/items/minLength` | (none) |
| `allowPartialCredit` boolean, default `true` (schema-declared) | Schema-enforced (type) | `matching.schema.json: /allOf/1/properties/allowPartialCredit` | (none) |
| Consumers MUST randomize the choice pool (matches + distractors) | Advisory + runtime obligation | [`NORMATIVE.md`](NORMATIVE.md) §5.6 | §5.6 |
| Consumers MUST randomize row order in `classification` mode | Advisory + runtime obligation | [`NORMATIVE.md`](NORMATIVE.md) §5.6 | §5.6 |

### 9.11 ordering

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"ordering"` | Schema-enforced | `ordering.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `sourceText` required, `minLength: 1` | Schema-enforced | `ordering.schema.json: /allOf/1/required`, `/properties/sourceText/minLength` | (none) |
| `items` required, `minItems: 2`, each `minLength: 1` | Schema-enforced | `ordering.schema.json: /allOf/1/required`, `/properties/items` | (none) |
| `distractors[*]` non-empty strings, default `[]` (schema-declared) | Schema-enforced (item type) | `ordering.schema.json: /allOf/1/properties/distractors` | (none) |
| `scoringMode` enum: `"strict"`, `"kendall"` (when present) | Schema-enforced | `ordering.schema.json: /allOf/1/properties/scoringMode/enum` | (none) |
| `scoringMode` default: `"strict"` for `orderingUnit:"word"`, `"kendall"` for `"sentence"`/`"paragraph"` | Advisory (description prose; no JSON Schema literal `default`) | `ordering.schema.json: /allOf/1/properties/scoringMode/description` | (none) |
| `orderingUnit` enum: `"word"`, `"sentence"`, `"paragraph"`, default `"word"` (schema-declared; advisory display hint) | Schema-enforced (enum) | `ordering.schema.json: /allOf/1/properties/orderingUnit/{enum,default}` | (none) |

### 9.12 placement

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `type` is `"placement"` | Schema-enforced | `placement.schema.json: /allOf/1/properties/type/const` | §4.2 |
| `placementUnit`, `passage`, `placements` required | Schema-enforced | `placement.schema.json: /allOf/1/required` | (none) |
| `placementUnit` enum: `"sentence"`, `"paragraph"`, `"sectionLabel"`, default `"sentence"` (schema-declared) | Schema-enforced (enum) | `placement.schema.json: /allOf/1/properties/placementUnit/enum` | (none) |
| `passage` `minLength: 1`, MUST contain at least one `@@@N` marker | Schema-enforced | `placement.schema.json: /allOf/1/properties/passage/{minLength,pattern}` | (none) |
| `placements` `minItems: 1`, each `{gap >= 1, item.minLength >= 1}`, `additionalProperties: false` | Schema-enforced | `placement.schema.json: /allOf/1/properties/placements/items` | §7.1 (closed) |
| Every `placements[*].gap` references a `@@@N` marker present in `passage` | Domain-validator-enforced (ERROR) | `validate_course.py: validate_placement` | (none) |
| No duplicate `gap` values within `placements[]` | Domain-validator-enforced (ERROR) | `validate_course.py: validate_placement` | (none) |
| `@@@N` markers SHOULD be sequential starting at 1 | Domain-validator-enforced (WARN) | `validate_course.py: validate_placement` | (none) |
| `placementUnit: "paragraph"` — marker SHOULD stand alone in its paragraph | Domain-validator-enforced (WARN) | `validate_course.py: validate_placement` | (none) |
| `placementUnit: "sectionLabel"` — marker SHOULD be at the start of a paragraph followed by a space | Domain-validator-enforced (WARN) | `validate_course.py: validate_placement` | (none) |
| Extra `@@@N` markers without a `placements[]` entry are valid decoy gaps (TOEFL Sentence Insertion variant) | Advisory | `placement.schema.json: /allOf/1/properties/placements/description`, [`question-types-reference.md`](question-types-reference.md) §11 | (none) |
| `distractors[*]` non-empty strings | Schema-enforced | `placement.schema.json: /allOf/1/properties/distractors/items/minLength` | (none) |
| Consumers MUST randomize the choice pool (placements items + distractors) | Advisory + runtime obligation | [`NORMATIVE.md`](NORMATIVE.md) §5.6 | §5.6 |

---

## 10. Reserved and unknown types

The 7 reserved question types — `association`, `hotspot`, `graphicGapMatch`, `graphicAssociate`, `graphicOrder`, `fileUpload`, `mediaPromptedEssay` — are declared in `question-base.schema.json`'s `enum` but have no per-type schemas in 1.0. Their handling is normative under [`NORMATIVE.md`](NORMATIVE.md) §6 (the fallback contract):

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| Reserved-type discriminator MUST be accepted by consumers | Schema-enforced | `question-base.schema.json: /properties/type/enum` | §5.5, §6.1 |
| Reserved-type question MUST satisfy `question-base.schema.json` (`type`, `globalId`, `prompt` required; `points` validated against the base type/range when present, defaulting to `1.0` schema-declared) | Schema-enforced (required fields + type/range on `points`) | `question-base.schema.json: /required=["type","globalId","prompt"]`, `/properties/points/{type,minimum,default}`; validator dispatches reserved types to `question-base.schema.json` | §6.3 |
| Consumer MUST preserve reserved-type question objects verbatim across read/write cycles | Advisory (round-trip preservation — runtime obligation, not document-validity) | [`NORMATIVE.md`](NORMATIVE.md) §6.2, §6.4 | §6.2, §6.4 |
| Consumer MUST NOT silently drop reserved-type questions from `questions[]` | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §6.2 | §6.2 |
| Consumer MUST treat reserved-type earned points as 0 (max still counts) | Advisory (runtime obligation) | [`NORMATIVE.md`](NORMATIVE.md) §6.2 | §6.2 |
| Consumer MUST report the unsupported question to the user at import (UI banner / log / returned warning) | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §6.2 | §6.2 |
| Consumer SHOULD render a non-interactive placeholder naming the type | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §6.2, [`ACCESSIBILITY.md`](ACCESSIBILITY.md) §7 | §6.2, §12 |
| Consumer SHOULD disable navigation gating for unsupported questions | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §6.2 | §6.2 |
| Producer SHOULD NOT emit reserved types in cross-implementation distribution | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §6.3 | §6.3 |
| Producer SHOULD use the published reserved name exactly (`hotspot`, not `Hotspot`); SHOULD document tool-specific extensions in IMPLEMENTATIONS.md / README | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §6.5 | §6.5 |
| **Producer**: emitting a discriminator value not listed in `question-base.schema.json`'s `enum` is non-conforming at 1.0 — the schema rejects it; the reference validator surfaces it with a friendlier message naming the allowed values | Schema-enforced + Domain-validator-enforced (ERROR) | `question-base.schema.json: /properties/type/enum`; `validate_course.py` (per-type question dispatch) | §6.1 |
| **Consumer** (1.0-only) reading a 1.x+ document with a type discriminator unknown to the consumer: apply the §6 fallback (preserve verbatim, treat earned points as 0, render placeholder, report to user) — do NOT reject the document | Advisory (runtime / forward-compat obligation, not document-validity) | [`NORMATIVE.md`](NORMATIVE.md) §6.1, §6.2, §6.4 | §6.1, §6.2 |

The two rows above are not in conflict: the producer-validity row describes the 1.0 strict-validator behavior on a document whose `type` enum is exhausted at 1.0 (the schema and the reference validator agree it's a malformed 1.0 document). The consumer-import row describes the runtime obligation a 1.0-only consumer carries when it ingests a 1.x+ document whose newer `type` it does not recognize — there, NORMATIVE §6 binds the consumer to graceful fallback rather than rejection. A 1.0 consumer cannot validate a 1.x+ document under a 1.0 schema and therefore SHOULD NOT use schema validation as the ingest gate when reading future-minor content; consumer-side ingest is governed by §6, not by `question-base.schema.json`.

---

## 11. Question Sets (flat artifact)

A `documentType: "questionSet"` document is a flat questions list with no course hierarchy. Required root fields apply (see [§3](#3-root-document)) plus:

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `title` required, `minLength: 1` | Schema-enforced | `question-set.schema.json: /required[*]="title"`, `/properties/title/minLength` | §3.2 |
| `language` required at root | Schema-enforced | `question-set.schema.json: /required[*]="language"` | §12.1 |
| `questions[]` required (may be empty) | Schema-enforced | `question-set.schema.json: /required[*]="questions"` | (none) |
| `sourceQuestionSetId`, when present, matches the RFC 4122 UUID pattern (any version; shape-only validation) | Schema-enforced | `question-set.schema.json: /properties/sourceQuestionSetId/pattern` | (none) |
| `version` matches `^[0-9]+(\.[0-9]+){0,2}$`, default `"1.0"` (schema-declared) | Schema-enforced (pattern) | `question-set.schema.json: /properties/version/pattern` | (none) |
| Each `questions[*]` validates against its per-type schema (per-question dispatch) | Domain-validator-enforced (ERROR on schema failure or unknown discriminator) | `validate_course.py` (per-type question dispatch), `validate_question_set_flat` | §5.1, §5.3 |

---

## 12. Cross-cutting

### 12.1 HTML safety profile

HTML appears in two fields: `ContentItem.html` and `SignpostItem.customHtml`. The full normative profile is in [`HTML_SAFETY.md`](HTML_SAFETY.md). The reference validator's HTML checks live in `validate_course.py: validate_html_content` and mirror that profile.

| Surface | Severity ([`HTML_SAFETY.md`](HTML_SAFETY.md) §8) | Validator function |
|---|---|---|
| Forbidden elements (`<script>`, `<iframe>`, `<form>`, `<input>`, `<button>`, `<style>`, `<link>`, `<meta>`, `<base>`, `<svg>`, `<math>`, etc.) | ERROR — consumer MUST reject | `validate_html_content` (HTML_FORBIDDEN_TAGS) |
| Event-handler attributes (`onclick`, `onload`, `onerror`, …) | ERROR | `validate_html_content` (`attr_name.startswith("on")`) |
| Form-submission attributes (`srcdoc`, `formaction`, …) | ERROR | `validate_html_content` |
| `javascript:` or `vbscript:` URL in any URL-bearing attribute | ERROR | `validate_html_content` |
| `expression(...)` / `javascript:` inside `style` CSS value | ERROR | `validate_html_content` |
| `data:` URL in any URL-bearing attribute (including `<img src>`) | WARN | `validate_html_content` |
| Other forbidden URL schemes (`blob:`, `file:`, `chrome:`, `ftp:`, `ws:`, `gopher:`, `view-source:`) | WARN | `validate_html_content` |
| `tel:` URL (consumer-policy gated; see [`ITEM_PATTERNS.md`](ITEM_PATTERNS.md) §3) | WARN | `validate_html_content` |
| Unknown element (not in `HTML_ALLOWED_TAGS`, not in forbidden list) | WARN — strip while preserving text | `validate_html_content` |
| Unknown attribute on an allowed element (outside §3 allowlist) | WARN — strip the attribute | `validate_html_content` |
| CSS property outside the [`HTML_SAFETY.md`](HTML_SAFETY.md) §3.4 allowlist | WARN — strip the property | `validate_html_content` |
| `<a target="_blank">` without `rel="noopener noreferrer"` | WARN — consumer MUST normalize | `validate_html_content` |
| `<img>` without `alt` attribute | WARN — empty `alt=""` permitted for decorative images | `validate_html_content` |
| `<video>`/`<audio>` with `autoplay` or `loop` | WARN — producer MUST NOT emit; consumer SHOULD ignore | `validate_html_content` |

A conforming consumer MUST sanitize HTML before render regardless of producer claims ([`HTML_SAFETY.md`](HTML_SAFETY.md) §5).

### 12.2 Accessibility preservation

[`ACCESSIBILITY.md`](ACCESSIBILITY.md) defines two layers: a base-conformance preservation floor that binds every consumer, and an opt-in Accessibility Profile claim that binds delivery.

Round-trip preservation (base conformance, [`NORMATIVE.md`](NORMATIVE.md) §12.1):

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `alt` on `<img>` MUST round-trip | Advisory (runtime / round-trip obligation) | [`NORMATIVE.md`](NORMATIVE.md) §12.1 | §12.1 |
| `<track>` elements (incl. `kind`, `src`, `srclang`, `label`, `default`) MUST round-trip on `<video>`/`<audio>` | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §12.1 | §12.1 |
| `lang` and `dir` attributes on HTML-bearing elements MUST round-trip | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §12.1 | §12.1 |
| Document-root `language` MUST round-trip | Schema-enforced (required) + runtime preservation obligation | `course.schema.json: /required[*]="language"`; [`NORMATIVE.md`](NORMATIVE.md) §12.1 | §12.1 |
| Document-root `supportLanguage` MUST round-trip when present (including explicit `null`) | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §12.1 | §12.1 |
| Reserved-type questions MUST round-trip with any accessibility metadata they carry | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §6.4, §12.1 | §6.4, §12.1 |
| Extension-preserving consumers (§7.4) SHOULD round-trip `x-`-namespaced extension members carrying accessibility data | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §12.1 | §12.1 |

Opt-in Accessibility Profile delivery obligations (binding only when claimed): see [`ACCESSIBILITY.md`](ACCESSIBILITY.md) §§2–8. Not duplicated here.

Validator severity for accessibility issues at the current baseline ([`ACCESSIBILITY.md`](ACCESSIBILITY.md) §8):

| Issue | Severity | Validator function |
|---|---|---|
| Missing `alt` on `<img>` | WARN | `validate_html_content` |
| `<video>` without `<track kind="captions"\|"subtitles">` | WARN (current baseline; promotion to ERROR under the `--accessibility` flag is targeted for 1.0 final) | `validate_html_content` (post-pass scan for `<video>…</video>` blocks) |
| `<iframe>`, `<script>`, event handlers | ERROR | `validate_html_content` |
| Missing `language` at document root | ERROR (schema-enforced) | `course.schema.json` / `question-set.schema.json` `required` |
| Reserved-type question without `title` | NOTE | (advisory; not currently surfaced) |

### 12.3 Randomization requirements

[`NORMATIVE.md`](NORMATIVE.md) §5.6 binds two surfaces. These are *consumer rendering* obligations, not document-validity rules — a document is conforming whether or not consumers randomize it. Listed here so implementers know what they MUST do at render time:

- **Choice pool** for `matching` (pairs/classification) and `placement` MUST be presented in randomized order.
- **Row order in `matching` classification mode** MUST be randomized.
- The randomization algorithm and any seeding strategy are consumer-defined.
- Exemptions: `multipleChoice` (per-question `shuffleOptions` instead), `matching` pairs rows, `ordering` source tiles.

### 12.4 Extensions (`x-` members)

Extension rules from [`NORMATIVE.md`](NORMATIVE.md) §7. Round-trip preservation by extension-preserving consumers is a runtime obligation, not a document-validity rule.

| Rule | Tier | Source | NORMATIVE § |
|---|---|---|---|
| `x-` keys MAY appear on root + Course/Unit/Lesson/Item/Question | Advisory (schemas omit `additionalProperties: false` on these objects) | [`NORMATIVE.md`](NORMATIVE.md) §7.1 | §7.1 |
| `x-` keys MUST NOT appear on closed objects (`matching.pairs[*]`, `matching.categories[*]`, `placement.placements[*]`) | Schema-enforced | `matching.schema.json` / `placement.schema.json` (`additionalProperties: false`) | §7.1 |
| Producer MUST NOT emit non-extension fields whose name begins with `x-` | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §7.1 | §7.1 |
| Producer MUST NOT emit an extension under a namespace it does not own | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §7.2 | §7.2 |
| Extensions are strictly additive — removing every `x-` member MUST leave a conforming document with equivalent learner-facing meaning | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §7.3 | §7.3 |
| Consumer MUST NOT reject documents solely for `x-` members or interpret members outside its own namespace | Advisory | [`NORMATIVE.md`](NORMATIVE.md) §7.4 | §7.4 |
| Extension-preserving consumers SHOULD round-trip unrecognized `x-` members on the same object | Advisory (round-trip behavior) | [`NORMATIVE.md`](NORMATIVE.md) §7.4 | §7.4 |

### 12.5 Versioning and URL stability

[`NORMATIVE.md`](NORMATIVE.md) §8 binds publication-side guarantees. Not document-validity rules per se, but consumers SHOULD enforce them when resolving `$schema`:

- `$schema` URL identifies the specific publication; `specVersion` identifies the contract version (§4.6, §4.7, §8.4).
- `/X.Y/` paths are reserved for accepted final releases; `/X.Y-rc.N/` paths are immutable once published; rc.N → final adoption is an explicit re-export (§8.1, §8.3).
- A document declaring `specVersion: "1.0"` with `$schema` at `/1.0-rc.N/` validates against `/1.0-rc.N/` and is not required to validate against `/1.0/` (§8.4).

### 12.6 Discriminator casing

Reiteration of [§3](#3-root-document), [§7](#7-item-level--common), [§8](#8-question-level--common): conforming consumers MUST reject non-canonical casings on `documentType`, item `type`, and question `type` ([`NORMATIVE.md`](NORMATIVE.md) §4.2, §5.3). The schemas enforce these via `const` / `enum`. The reference validator additionally provides lenient migration paths (PascalCase → camelCase warnings, casing-tolerant `documentType` dispatch) that are disabled under `--strict`.

---

## 13. Conformance note

The catalog tiers describe what `validate_course.py --strict` enforces today; the published conformance contract is the `--strict` behavior ([§1.3](#13-strict-mode-and-the-lenient-migration-path)).

**Producers** MUST emit documents that satisfy every **Schema-enforced** rule and every **Domain-validator-enforced (ERROR)** rule. **Producers** SHOULD additionally honor `Domain-validator-enforced (WARN)` rules; the validator's warnings flag suspect-but-not-rejected content that authors typically want to fix.

**Consumers** MUST reject documents that fail any **Schema-enforced** or **Domain-validator-enforced (ERROR)** rule, with one explicit exception: where a row distinguishes producer-emission from consumer-import (the `$schema` rows in [§3](#3-root-document) are the canonical example), the consumer-side row applies. This matches [`NORMATIVE.md`](NORMATIVE.md) §3.2's strict-producer / lenient-consumer split — a producer that omits `$schema` is non-conforming with respect to that document, but a consumer that rejects an otherwise-valid document on the basis of a missing `$schema` is overly strict. **Domain-validator-enforced (WARN)** rules describe sanitization, accessibility, or migration-aid behavior — consumers SHOULD surface them but are not required to reject on their basis. **NOTE-tier** rows are informational only.

**Advisory** rules carry the RFC 2119 weight stated in the cited section ([`NORMATIVE.md`](NORMATIVE.md) `MUST`/`SHOULD`/`MAY`, [`HTML_SAFETY.md`](HTML_SAFETY.md) §8 severity, [`ACCESSIBILITY.md`](ACCESSIBILITY.md) §8). Consumers that diverge from advisory `SHOULD`/`MAY` rules are non-canonical but not non-conforming. Where a rule is enforced in multiple tiers (schema + validator), satisfying the strictest tier suffices.

**A note on JSON Schema `format` keywords.** Several rows above cite `format: "uri"` or `format: "uuid"` from the schemas. Under JSON Schema Draft 7, `format` is an *annotation* by default — a validator only enforces it when configured with a `FormatChecker` (or equivalent). The reference validator's `Draft7Validator` instance runs without explicit format assertions, so `format`-only claims are not guaranteed by the schema pass alone. Rows that depend on these formats also cite a regex `pattern` (for UUIDs on `globalId` properties) or a domain-validator backstop (`validate_course.py: validate_item` via `is_valid_uuid` for `contentItemId` / `relatedItemIds`). Implementers re-implementing the validator in other languages should either enable format-assertion in their JSON Schema library or replicate the regex/domain backstops.

**A note on JSON Schema `default` keywords.** Several rows above cite a property's `default` value (e.g. `isGraded` defaults to `true` on `quiz`, `points` defaults to `1.0` on questions, `placementUnit` defaults to `"sentence"`). Under JSON Schema Draft 7, `default` is an *annotation* — most validators (including `jsonschema` for Python, AJV with default options, etc.) do not apply or enforce it. A producer that omits the property emits a document that validates; a consumer that reads such a document MUST apply the default itself if it wants the documented behavior. The defaults are listed here so implementers know what the spec intends absent an explicit value — they are *schema-declared*, not *schema-enforced*. Consumers SHOULD NOT rely on the validator filling in defaults; producers SHOULD emit explicit values when the documented default does not match their intent.

Where the reference validator and a normative document disagree, the normative document wins. Discrepancies should be reported as issues against this spec; the validator is updated to track.

---

## 14. Forward-looking deepenings (1.0 final)

The inventory pass that produced this catalog (2026-05-24) surfaced eight documented-but-unenforced rules. All eight were closed in the same rc.1-polish session by extending `tools/validate_course.py` (no schema changes — the closures land in the domain-validator pass). The corresponding rows in the per-type tables above are tagged **Domain-validator-enforced** rather than **Advisory**; new invalid conformance fixtures (`tests/invalid/21-mcq-no-correct-option.json`, `22-mcq-options-points-missing-entry.json`, `23-word-bank-cloze-gap-count-mismatch.json`, `24-multiple-choice-cloze-index-out-of-bounds.json`) pin the ERROR-tier checks. The corpus runs 38/38 under `python tools/run_corpus.py` (the harness invokes `validate_course.py --strict` internally on every fixture; the 36 fixtures at the time of that rc.1 pass plus the two `prompt`-correction fixtures added in rc.2).

Three areas remain explicitly forward-looking for `1.0` final or beyond:

- **`--accessibility` validator flag.** The `<video>` without `<track kind="captions"\|"subtitles">` check (§12.2) is WARN at the current baseline. The 1.0-final `--accessibility` flag promotes it (and related accessibility warnings) to ERROR so tooling that wants to fail-build on accessibility-profile claims can do so.
- **Tag namespace conventions.** Optional best-practice tag prefixes (`stage:`, `level:`, `exam:`, …) are described informally in [`ITEM_PATTERNS.md`](ITEM_PATTERNS.md) §1. No schema-level constraint, no validator check; left to convention for `1.0`. Referential-integrity validation on `objectiveIds` is closed at rc.1 (consumers MUST report unresolved IDs per the validator).
- **Reserved-type per-type schemas.** The 7 reserved question types (`hotspot`, `association`, etc.) validate against `question-base.schema.json` only in 1.0 (§10). First-class per-type schemas are targeted for the `1.1` minor.

Future deepenings (a new accessibility rule promoted to ERROR, a new cross-document rule added by `1.1`) will surface as new rows in the per-type tables above or as new entries in this section. The published `/1.0-rc.2/` schema URLs remain immutable per [`NORMATIVE.md`](NORMATIVE.md) §8.3; any future closures land at `/1.0/` or a later version path.
