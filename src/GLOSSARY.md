# LC-JSON Glossary

**Status:** Informative.
**Spec version:** 1.0
**Last updated:** 2026-06-13

This glossary defines the terms LC-JSON (Learning Content JSON) uses throughout the specification. It is informative — definitive normative meaning lives in [`NORMATIVE.md`](NORMATIVE.md) — but implementers should treat the entries below as the project's working vocabulary.

Terms are organized in five groups: **core concepts**, **artifact and hierarchy**, **conformance**, **language and localization**, and **identity, versioning, and extensions**.

---

## Core concepts

### artifact

A top-level document type defined by the specification. LC-JSON 1.0 defines two artifact types: **Course** (hierarchical) and **QuestionSet** (flat). The artifact a document represents is signaled by its `documentType` root field.

### document

A single instance of an artifact — one JSON file (or in-memory equivalent) that carries `$schema`, `documentType`, `specVersion`, and the artifact payload as flat root siblings. A document is the unit of validation, exchange, and storage.

### wire format

The on-disk / on-the-wire JSON shape that conforming tools produce and consume. The wire format is what the specification binds; how a tool represents the same content internally (database rows, AST, runtime DTOs, etc.) is outside the spec.

### producer

Any tool that emits LC-JSON documents intended for external consumption. Producer obligations are listed in [`NORMATIVE.md`](NORMATIVE.md) §4. Examples: course-authoring tools, AI-assisted authoring scripts, format converters that export to LC-JSON.

### consumer

Any tool that ingests LC-JSON documents from an external source. Consumer obligations are listed in [`NORMATIVE.md`](NORMATIVE.md) §5. Examples: learning-management systems, delivery platforms, conversion tools that import from LC-JSON, validators.

### validator

A tool that checks whether a document conforms to the spec. A conforming validator runs each document against the published JSON Schemas at the appropriate version URL, plus the domain rules described in NORMATIVE.md §5.1. The reference validator is [`tools/validate_course.py`](../tools/validate_course.py).

### round-trip preservation

The property that a document survives a read → modify → write cycle through a consumer without losing or silently dropping data the consumer didn't understand. LC-JSON requires round-trip preservation for reserved question types (§6.4) and recommends it for `x-`-namespaced extension members (§7.4). Round-trip preservation is what lets one tool use LC-JSON as a faithful transfer or backup format for another tool's content.

---

## Artifact and hierarchy

### Course

The hierarchical artifact type: a course contains units, each unit contains lessons, each lesson contains items, and items of type `exercise` or `quiz` contain questions. Identified at the root by `documentType: "course"`. Schema: [`course.schema.json`](schemas/course.schema.json).

### QuestionSet

The flat artifact type: a question set is a list of questions without any enclosing course/unit/lesson scaffold. Used for question-bank exchange and packaged delivery of curated question batches. Identified at the root by `documentType: "questionSet"`. Schema: [`question-set.schema.json`](schemas/question-set.schema.json).

### Unit

The second tier of a Course's hierarchy. A unit groups related lessons under a single banner (e.g., a topic, a module, a week). Carries `title`, `globalId`, an `objectiveIds` reference list, and a `lessons` array.

### Lesson

The third tier of a Course's hierarchy. A lesson groups related items under a single banner (e.g., a class period, a sub-topic). Carries `title`, `globalId`, an `objectiveIds` reference list, and an `items` array.

### Item

The fourth tier of a Course's hierarchy — the atomic unit a learner interacts with. Items come in five types: `content` (reading material), `exercise` (practice questions), `quiz` (graded assessment), `contentsequence` (a content item paired with related exercises/quizzes), and `signpost` (intro/summary marker). Items of type `exercise` or `quiz` carry a `questions` array.

### Question

A single assessment unit inside an `exercise` or `quiz` item. LC-JSON 1.0 defines 19 question types: 12 implemented (with full per-type schemas) and 7 reserved for a future minor version. Every question carries a `type` discriminator, a `globalId`, and type-specific fields.

### HTML-bearing field

A spec field whose value is HTML markup rather than plain text or a structured object. The two HTML-bearing fields are `ContentItem.html` and `SignpostItem.customHtml`. Both are subject to the HTML safety profile in [`HTML_SAFETY.md`](HTML_SAFETY.md), which constrains the allowed elements, attributes, URL schemes, and inline CSS.

---

## Conformance

### conformance

The state of meeting all `MUST`-level requirements of NORMATIVE.md for a given role (producer, consumer, or both). A tool MAY claim conformance to LC-JSON 1.0 per NORMATIVE.md §10. Conformance is per-role and per-spec-version.

### strict mode

A validator-configuration mode in which warnings are treated as errors. The reference validator's default mode reports warnings as warnings; `--strict` promotes them to errors and exits non-zero on any warning. Useful in CI pipelines that require an unambiguous pass/fail signal.

### schema-clean

A document that validates without errors against the published JSON Schemas at its declared `specVersion`. "Schema-clean" excludes domain-rule warnings (e.g., HTML allowlist violations, gap-count mismatches) — those are reported separately by the reference validator's domain pass.

### validator (cross-reference)

See [validator](#validator) under Core concepts above.

---

## Language and localization

See [`LOCALIZATION.md`](LOCALIZATION.md) for the full model.

### delivery language

The single primary language a document is authored and delivered in, declared in the root `language` field. LC-JSON 1.x is single-language-per-document: a document has exactly one delivery language, and multiple languages are delivered as multiple documents.

### language of parts

A run of HTML content in a language different from the delivery language, marked with the `lang` attribute (and `dir` where script direction differs). This is the WCAG 3.1.2 mechanism; it concerns correct rendering and pronunciation, not translation.

### support language

The learner's first language (L1), declared in the optional root `supportLanguage` field, for a document whose delivery language is a second language being taught. It signals that L1 support (glosses, hints) is appropriate; how a consumer surfaces that support is consumer-defined.

### language tag

A [BCP 47](https://www.rfc-editor.org/info/bcp47) tag identifying a language, used by `language`, `supportLanguage`, and HTML `lang`. Commonly a bare ISO 639-1 primary subtag (`en`, `es`); region and script subtags (`pt-BR`, `zh-Hant`) are permitted, and a consumer may act on only the primary subtag.

---

## Identity, versioning, and extensions

### globalId

An RFC 4122 UUID (any version; shape-only validation against the 8-4-4-4-12 hex pattern) assigned to every Unit, Lesson, Item, and Question. `globalId` identifies an entity across re-imports, enabling consumers to match unchanged content against existing records and detect modifications. Required per NORMATIVE.md §4.4.

### sourceCourseId

A stable, course-level identity field. The same `sourceCourseId` across multiple exports identifies them as the same logical course; consumers use this to detect re-imports and apply update semantics rather than treating each upload as a fresh course. Generated by the source authoring system; does not identify a human author. QuestionSet artifacts use the parallel `sourceQuestionSetId` field with the same semantics.

### specVersion

A required root field declaring which contract version of LC-JSON the document conforms to. Pattern: `^1\.[0-9]+(\.[0-9]+)?$` (e.g., `"1.0"`, `"1.0.1"`) — anchored to major version 1, since the LC-JSON contract is currently in the 1.x family. **Distinct from the author-provided `version` root field**, which carries the content's own version (pattern `^[0-9]+(\.[0-9]+){0,2}$`, 1 to 3 segments) and tracks revisions to the content rather than to the spec contract. `specVersion` does not carry release-candidate suffixes — the candidate vs final-release distinction is carried by the `$schema` URL, not by `specVersion`. A consumer MUST reject documents whose major version exceeds what it supports (NORMATIVE.md §5.2).

### `$schema`

A required root field carrying the canonical URL of the JSON Schema for the document's artifact type at the specific publication the producer targets. A 1.0-rc.3 Course document carries `"$schema": "https://lc-json.org/1.0-rc.3/course.schema.json"`; a 1.0-final Course document carries `"$schema": "https://lc-json.org/1.0/course.schema.json"`. URLs at any published path — released versions and release candidates alike — are immutable for the lifetime of the spec (§8.3).

### implemented question type

A question type that has a published per-type JSON Schema in the current spec version, full authoring-tool support, and reference-runtime scoring. LC-JSON 1.0 has 12 implemented types: `simpleGapFill`, `trueFalseQuestion`, `multipleChoice`, `wordBankCloze`, `multiGapCloze`, `multipleChoiceCloze`, `shortAnswer`, `essay`, `sentenceTransformation`, `matching`, `ordering`, `placement`.

### reserved question type

A `type` discriminator value listed in [`question-base.schema.json`](schemas/question-base.schema.json)'s discriminator enum that does **not** yet have a published per-type schema. The 1.0 reserved types are `association`, `hotspot`, `graphicGapMatch`, `graphicAssociate`, `graphicOrder`, `fileUpload`, and `mediaPromptedEssay`. Consumers MUST preserve reserved-type questions in full across read/write cycles — every field, value, and nested structure (§6.4; semantic preservation, key order is producer-discretion per §6.2).

### unknown question type

A `type` discriminator value **not** listed in the spec's discriminator enum at all — typically a tool-specific extension under a `type` name that the producer's tooling recognizes but other tools do not. Unknown types follow the same round-trip preservation contract as reserved types (§6).

### extension member

A root-level or per-object JSON member whose key begins with `x-` and identifies vendor-specific data not defined by the LC-JSON spec. Extension members let tools carry authoring provenance, internal identifiers, editor state, analytics hints, etc., without polluting the core format. Defined in NORMATIVE.md §7.

### namespace

The segment of an extension-member key immediately following `x-`. The namespace identifies the originating tool or vendor (e.g., `x-acme.workflow-id` has namespace `acme`). Namespacing prevents collisions: a producer MUST NOT emit an extension member under a namespace it does not own (§7.2).

---

## See also

- [`NORMATIVE.md`](NORMATIVE.md) — binding conformance requirements (the authoritative source for all terms above).
- [`README.md`](README-spec.md) — descriptive specification overview.
- [`HTML_SAFETY.md`](HTML_SAFETY.md) — the HTML allowlist for HTML-bearing fields.
- [`ACCESSIBILITY.md`](ACCESSIBILITY.md) — accessibility expectations for producers and consumers.
- [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md) — directory of conforming implementations.
