# LC-JSON Specification — Normative Requirements

**Spec version:** 1.0
**Status:** Normative
**Last updated:** 2026-05-24

This document states the requirements that conforming LC-JSON (Learning Content JSON) tools MUST satisfy. It is the authoritative source of truth for compliance; descriptive material elsewhere in the specification illustrates how to meet these requirements but does not relax them.

---

## 1. Scope

This document specifies the requirements for tools that produce, consume, or validate LC-JSON 1.0 documents. It defines:

- The canonical wire format for the two artifact types (Course, QuestionSet).
- Two conformance roles — *producer* and *consumer* — and what each MUST do.
- Versioning rules and URL stability guarantees.
- Conformance-claim language (how a tool may state it conforms).

This document does not prescribe implementation strategies, programming languages, or runtime architecture. Any tool meeting the requirements below conforms, regardless of how it is built.

---

## 2. Conformance Language

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) when, and only when, they appear in all capitals.

A requirement stated in lowercase ("must," "should") is descriptive prose, not a normative requirement.

---

## 3. Document Identity

### 3.1 Canonical URL space

LC-JSON schemas are published at:

```
https://lc-json.org/<spec-version>/<schema-name>.schema.json
```

The `<spec-version>` segment identifies either a released version (`1.0`, `1.1`, `2.0`, …) or a **release candidate** — an immutable draft of an upcoming version, published for review and implementer feedback before the final release is accepted (e.g., `1.0-rc.1`, `1.0-rc.2`, `1.1-rc.1`, …). Each receives its own URL path. For released spec version 1.0, schemas resolve at `https://lc-json.org/1.0/*.schema.json`. For release candidates, schemas resolve at `https://lc-json.org/1.0-rc.N/*.schema.json`, one URL path per candidate.

URLs under any published path — released or release-candidate — are immutable. They MUST NOT be renamed, removed, redirected to a different schema, or repointed to a non-canonical host once published.

The `/X.Y/` URL path is **reserved** for the accepted final `X.Y` release and MUST NOT be populated until that release is published. Release candidates targeting `X.Y` are published at `/X.Y-rc.N/` paths. A document pinned via `$schema` to `/X.Y-rc.N/` does not automatically validate against `/X.Y/`; adoption of the final release is an explicit choice by the publisher (typically a re-export against the new schema URL). See §8.1 and §8.3 for the full versioning and stability contract.

### 3.2 Required root fields

Every conforming LC-JSON document MUST contain at the root, as siblings (not nested under any envelope):

| Field | Required? | Type | Value |
|---|---|---|---|
| `documentType` | MUST | string | `"course"` or `"questionSet"`. The artifact discriminator. |
| `specVersion` | MUST | string | The LC-JSON contract version this document conforms to. Pattern enforced by the schemas; consumer/producer rules in §5.2 / §4.6. |
| `$schema` | MUST (producer) / SHOULD-tolerate (consumer) | string | A URL identifying the schema for this document type at the spec version the producer conforms to (e.g., `https://lc-json.org/1.0-rc.2/<artifact>.schema.json` for an rc.2 producer; `https://lc-json.org/1.0/<artifact>.schema.json` for a 1.0-final producer). Consumers SHOULD accept documents that omit `$schema` (re-import scenarios from older or lenient producers), but MUST reject any other root-field omission. |

A document missing `documentType` or `specVersion` is non-conforming. A producer that emits a document missing `$schema` is non-conforming with respect to that document; a consumer that rejects an otherwise-valid document on the basis of a missing `$schema` is overly strict and SHOULD instead infer the schema from `documentType` + `specVersion`.

### 3.3 Artifact types

Spec version 1.0 defines exactly two artifact types:

- **Course** (`documentType: "course"`) — hierarchical learning content (Course → Units → Lessons → Items → Questions). Validated by `course.schema.json`.
- **QuestionSet** (`documentType: "questionSet"`) — flat list of questions without a course/unit/lesson scaffold. Validated by `question-set.schema.json`.

A producer MUST emit exactly one of these artifact types per document. Mixing artifact types within a single document is non-conforming.

---

## 4. Producer Conformance

A *producer* is any tool that emits LC-JSON documents intended for external consumption.

### 4.1 Wire format

A producer MUST emit documents in the canonical flat-root form: `$schema`, `documentType`, and `specVersion` at the top level, with the artifact payload as flat siblings. Nested envelopes such as `{"course": {...}}` are non-conforming.

### 4.2 Discriminator casing

A producer MUST emit the `type` discriminator on questions in canonical camelCase form: `"simpleGapFill"`, `"trueFalseQuestion"`, `"multipleChoice"`, `"wordBankCloze"`, `"multiGapCloze"`, `"multipleChoiceCloze"`, `"shortAnswer"`, `"essay"`, `"sentenceTransformation"`, `"matching"`, `"ordering"`, `"placement"`.

A producer MUST emit the `type` discriminator on items in canonical lowercase form: `"content"`, `"exercise"`, `"quiz"`, `"contentsequence"`, `"signpost"`.

A producer MUST emit `documentType` in canonical lowercase camelCase form: `"course"` or `"questionSet"`.

### 4.3 Item-type semantics

The `exercise` and `quiz` item-type discriminators are structural distinctions, not policy. They allow consumers to render the two forms differently in the UI and to track their points in separate buckets (enabling weighted grading).

The grading policy of an item is composed independently from its type via the `isGraded`, `isOptional`, and `passMarkPercent` fields. All four combinations of `{exercise, quiz} × {graded, ungraded}` are valid LC-JSON: a graded exercise (e.g. homework that counts), an ungraded exercise (open practice), a graded quiz (typical assessment), and an ungraded quiz (e.g. diagnostic pre-test, self-check) are all conforming.

A producer MUST NOT infer or assert grading state from item type alone, and a consumer MUST NOT reject a document on the basis that an `exercise` is graded or a `quiz` is ungraded.

### 4.4 Identifiers

A producer MUST emit `globalId` values as RFC 4122 UUIDs (any version) where the schema requires them. Specifically: every Unit, Lesson, Item, and Question MUST have a `globalId`; these identify the entity across re-imports, enabling consumers to match unchanged content against existing records and detect modifications.

A producer SHOULD emit a `sourceCourseId` at the course root for any course that may be re-imported or version-tracked. `sourceCourseId` is the stable course-identity field — the same `sourceCourseId` across versions of a course identifies them as the same logical course, enabling consumers to detect re-imports and apply update semantics rather than treating each upload as a fresh course. `sourceCourseId` is generated by the source authoring system; it does not identify a human author.

> **Forward-direction note (informative, not normative for 1.0):** Future versions of LC-JSON may introduce a complementary `coursePlatformId` field for platform-assigned course identifiers, enabling round-trip flows where a teacher exports from a platform and re-imports to an authoring tool with the platform's identity preserved. Implementations should not rely on this field's absence in 1.0 documents being permanent.

### 4.5 Property naming

A producer MUST emit all property names in camelCase. PascalCase, snake_case, and other casings are non-conforming on the wire.

### 4.6 Spec version

A producer MUST emit `specVersion` matching the spec version it implements. For producers conforming to this document, `specVersion` MUST begin with `"1."` (e.g., `"1.0"`, `"1.0.1"`).

`specVersion` carries the contract version regardless of which publication the producer targets. The specific publication — release candidate or final release — is identified by the `$schema` URL (§4.7). A producer conforming to 1.0-rc.2 emits `specVersion: "1.0"` together with `$schema: "https://lc-json.org/1.0-rc.2/course.schema.json"`; a producer conforming to 1.0 final emits the same `specVersion` value together with `$schema: "https://lc-json.org/1.0/course.schema.json"`. `specVersion` does not include release-candidate suffixes — `"1.0-rc.2"` is not a conforming `specVersion` value.

### 4.7 Schema URL

A producer MUST emit a `$schema` URL pointing at the canonical published schema for its `documentType` **at the spec version the producer conforms to**. For example: a producer conforming to LC-JSON 1.0-rc.2 emits `https://lc-json.org/1.0-rc.2/course.schema.json` for courses and `https://lc-json.org/1.0-rc.2/question-set.schema.json` for question sets; a producer conforming to 1.0 final emits `https://lc-json.org/1.0/course.schema.json`. A producer that emits a non-canonical URL or omits the field is non-conforming.

The strict producer / lenient consumer split (§3.2 above) is deliberate: emitting `$schema` makes documents self-describing for IDEs, schema dispatch, and ad-hoc validation; tolerating its absence on import preserves portability across older or otherwise-non-conforming producers without hard-failing re-imports.

### 4.8 Validation before emit

A producer SHOULD validate every emitted document against the published JSON Schemas before delivery. A producer that emits an invalid document is non-conforming with respect to that document.

---

## 5. Consumer Conformance

A *consumer* is any tool that ingests LC-JSON documents from an external source.

**Consumer conformance requires more than schema validation.** Schema validation (§5.1) is necessary but not sufficient: a conformant consumer ALSO satisfies the discriminator-handling rule (§5.3), the unknown-fields rule (§5.4), the reserved-enum-values rule (§5.5), the randomization requirements (§5.6), and — where reserved or unknown question types appear — the round-trip preservation obligations in §6. A generic JSON Schema validator alone does not implement these; consumers MUST implement the relevant §5.x and §6 obligations to claim conformance (see §10.3). See the worked example at the end of this section.

### 5.1 Strict validation

A consumer MUST validate incoming documents against the published JSON Schemas for the declared `documentType` and reject documents that fail schema validation.

**Exception (§6 fallback for unknown types).** Schema-validation failures whose only cause is one or more `type` discriminator values not present in the consumer's implemented `question-base.schema.json` enum do not trigger §5.1 rejection. The consumer applies the §6 fallback to those questions (preserve verbatim, treat earned points as `0`, render placeholder, report to user) and validates the rest of the document under §5.1. All other schema-validation failures — missing required fields, type mismatches, pattern violations on known fields, `additionalProperties` violations on closed objects, etc. — still trigger rejection. This carve-out is what makes §5.2's "accept any 1.x `specVersion`" rule operable: a 1.0-only consumer reading a 1.x+ document with a future-minor question type satisfies both §5.1 and §6 by following this path.

### 5.2 Spec version handling

A consumer MUST accept any `specVersion` value whose major version it implements (e.g., a 1.x consumer accepts `1.0`, `1.1`, `1.0.1`, …; the canonical pattern is enforced by `course.schema.json` / `question-set.schema.json`).

A consumer MUST reject `specVersion` values whose major version exceeds what it implements (a 1.x consumer rejects `2.0`, `2.1`, `3.0`, …). The rejection SHOULD be a clear error indicating the unsupported spec version.

A consumer MUST NOT silently downgrade or interpret unknown spec versions.

### 5.3 Discriminator handling

A consumer MUST recognize canonical camelCase question-type discriminators and canonical lowercase item-type discriminators as defined in §4.2. Non-canonical casings are non-conforming and MUST be rejected.

### 5.4 Unknown fields

A consumer MUST NOT reject a document solely because it contains additional fields not defined by the schema. Such fields are reserved for forward-compatible additions and MUST be ignored or preserved at the consumer's discretion.

### 5.5 Reserved enum values

A consumer MUST accept question types listed in `question-base.schema.json`'s `enum` even when no per-type schema is published for them. Full handling obligations — including round-trip preservation, learner-facing placeholder rendering, and grading semantics — are normative under §6 (Reserved and unknown types).

### 5.6 Randomization requirements for matching and placement

For `matching` and `placement` questions, two surfaces a consumer presents to a learner have no author-defined order:

1. **The choice pool**, comprising every authored answer value (`pairs[].match` or `categories[].label` for matching; `placements[].item` for placement) plus any `distractors`. Source order would directly expose the correct-answer mapping (the N-th option being the correct answer for the N-th row or gap), defeating the question.
2. **The row order in `matching` classification mode**, where each row is one item to be classified. Source order is grouped by category — items belonging to `categories[0]` first, then `categories[1]`, and so on — which directly exposes the answer (the first N rows all share the same category label).

A consumer MUST present both surfaces to learners in randomized order. A consumer MUST NOT render either surface in source order. The randomization algorithm and any seeding strategy are consumer-defined.

These requirements do not apply to:

- `multipleChoice` and other single-question choice lists, where authors may deliberately position the correct option and the question schema's own `shuffleOptions` field governs shuffle policy per question.
- The order of pair rows in `matching` pairs mode, where each item has its own distinct match value and source row order does not directly expose the answer.
- The order of items in `ordering` source-tile pools, where the question's structural design requires the tile pool to be presented in non-source order regardless.

### Forward compatibility: three look-alike situations (informative)

A 1.0-conformant consumer reading a 1.x document may encounter three superficially-similar cases at the JSON layer, each governed by a *different* consumer obligation. A generic JSON Schema validator handles none of them automatically.

1. **An unknown top-level field on a question.** Example: `"explanationVideoUrl": "..."` appears on a `multipleChoice` question. Under §5.4 (Unknown fields), the consumer MUST NOT reject the document; it ignores or preserves the field at its discretion.

2. **An extension-namespaced field.** Example: `"x-somecompany-difficultyBand": "B2"` appears on the same question. Under §7 (Extensions), the consumer MUST NOT reject for it and SHOULD preserve it verbatim across read/write cycles.

3. **An unknown `type` discriminator value.** Example: a question carries `"type": "novelCodingTask"` — a value the consumer's implemented `question-base.schema.json` enum does not include. Per §6.1, *reserved* and *unknown* types are handled identically: it does not matter whether `novelCodingTask` is destined for a future minor version, is a vendor-specific extension type, or will never be standardized at all. Under §5.1 (Strict validation, Exception) and §6.2 (Consumer obligations), the consumer applies the §6 fallback to that question (preserve verbatim, treat earned points as `0`, render a placeholder naming the type, report to user) and validates the rest of the document. Note that earned points are set to `0`, but the question's **possible** points still count toward the item's total — the item's maximum is consumer-independent by design, so a learner who completes the item in a fuller consumer can earn all the points the producer declared while a learner in a more limited consumer earns whatever subset they can; both report grades against the same denominator. Under §6.4 (Round-trip preservation), if the consumer re-exports the document, the `novelCodingTask` question is preserved with every member, value, and nested structure intact (semantic preservation; key order is producer-discretion per §6.2).

These three cases look similar at the JSON layer but are not interchangeable. Implementers using a generic JSON Schema validator (`jsonschema` for Python, Ajv for JavaScript, etc.) MUST add the §5.x and §6 fallback logic above the base validation call — particularly for case 3, where a generic validator would reject the whole document on the unknown `"novelCodingTask"` enum value, but §5.1's Exception is what permits the rest of the document to validate while §6 governs the unknown-type question.

---

## 6. Reserved and Unknown Types

### 6.1 Definitions

A *reserved type* is a `type` discriminator value listed in `question-base.schema.json`'s discriminator enum that does not have a published per-type schema in this spec version. The 1.0 reserved types are: `association`, `hotspot`, `graphicGapMatch`, `graphicAssociate`, `graphicOrder`, `fileUpload`, and `mediaPromptedEssay`.

An *unknown type* is a `type` discriminator value not listed in `question-base.schema.json`'s discriminator enum. Unknown types may appear in 1.x+ documents read by 1.0-only consumers.

For the purposes of this section, reserved and unknown types are handled identically.

### 6.2 Consumer obligations

When a consumer encounters a question whose `type` is reserved or unknown, the consumer:

- **MUST** preserve every member of the question object across read/write cycles — every field name, every value, every nested object and array, and any extension fields present on import. No field dropping, no value mutation, no `globalId` rewriting. (Key order within JSON objects is producer-discretion: producers SHOULD preserve input key order for authoring ergonomics and diff stability, but consumers are not required to — JSON object members are unordered per RFC 8259 §4.)
- **MUST NOT** silently drop the question from the parent item's `questions[]` array. The question's existence is preserved even when its rendering is not supported.
- **MUST** treat the question's earned points as `0` for grading purposes. The question's possible points still count toward the item's total — the maximum is not silently reduced.
- **MUST** report the unsupported question to the user (or upstream caller) at import time, naming the type and the question's `globalId`. Form is implementation-defined (UI banner, log line, returned warning), but the report is required.
- **SHOULD** render a non-interactive placeholder in the learner UI naming the type. Example: *"Question type 'hotspot' is not supported by this application. Skip to the next question."*
- **SHOULD** disable navigation gating for unsupported questions (e.g. do not block lesson completion just because a reserved question was not answered).
- **MAY** offer the learner a way to view the raw question data (instructor preview, debug mode), but **MUST NOT** expose internal field names to the learner UI by default.

### 6.3 Producer obligations

A producer that emits reserved types:

- **SHOULD NOT** emit reserved question types in 1.0 documents intended for cross-implementation distribution. Reserved types are explicitly tool-specific extensions until promoted in a future version.
- **MUST** still satisfy `question-base.schema.json` if it does emit them: valid `type`, valid `globalId`, valid `points`, valid `prompt`, plus any other `question-base` requirements. Consumers' fallback handling can only operate on a structurally well-formed object.
- **SHOULD** document in the tool's README which reserved types it emits and which fields it populates, so other tool authors can interoperate or contribute.

### 6.4 Round-trip preservation

A consumer that imports an LC-JSON document, modifies it, and re-exports MUST preserve every member of every reserved-type question in the exported document — including their `globalId`, `type`, `points`, `prompt`, and any additional fields that were present on import. No field dropping, no value mutation. (Key order within JSON objects is producer-discretion per §6.2; the preservation obligation is semantic, not byte-level.)

The intent is that a teacher exporting from a consumer that does not support `hotspot` can take the file back to a consumer that does, without losing the hotspot question. This is the core interop guarantee for reserved types: consumers MUST NOT strip reserved questions on export even if they cannot render them on import.

### 6.5 Producer guidance (informative)

To make a reserved-type question maximally compatible with future first-class implementations and other producers emitting the same name:

- Use the published reserved name exactly (`hotspot`, not `Hotspot` or `hotspot-question`).
- Always populate `globalId` (UUID), `points`, and `prompt`.
- Use additional fields conservatively — anything beyond `question-base` is by convention only until 1.1 publishes a per-type schema. Document any tool-specific extensions in your README.
- Avoid generic field names that 1.1 schemas may use canonically (`data`, `config`, `settings`).

This subsection is informative — producers that do not follow it still produce valid LC-JSON. But the future first-class schemas are likelier to land cleanly if 1.0 producers stay within the spirit.

---

## 7. Extensions

LC-JSON is deliberately small. Tools frequently need to attach data that is meaningful to themselves but is not part of the interchange contract — authoring provenance, internal identifiers, editor state, analytics hints. Namespaced extensions provide a forward-compatible, collision-free way to carry such data without polluting the core format or requiring a spec revision.

### 7.1 Extension members

An *extension member* is an object member whose key begins with the prefix `x-` followed by a vendor or tool namespace, for example `x-acme-reviewState` or `x-acme.lineage`.

Extension members MAY appear on the document root and on any Course, Unit, Lesson, Item, or Question object. They MUST NOT be added to objects whose schema declares `additionalProperties: false` (in 1.0, the `matching` pair/category entries and `placement` entries), because those objects are closed by contract and would fail validation.

The `x-` prefix is reserved exclusively for extensions. A producer MUST NOT introduce a non-extension field whose name begins with `x-`.

### 7.2 Namespacing

The segment immediately following `x-` is the *namespace* and MUST identify the originating tool or vendor (e.g. `x-acme`). Namespacing prevents two tools from colliding on the same key with incompatible meanings. A producer MUST NOT emit an extension member under a namespace it does not own.

A namespace owner SHOULD document the extension members it emits — their shape and meaning — in its public implementation notes (for known implementations, in [`IMPLEMENTATIONS.md`](IMPLEMENTATIONS.md)).

### 7.3 Additive-only constraint

Extensions are strictly additive. A producer MUST NOT encode in an extension member any data required for a baseline-correct interpretation of the document. A consumer that ignores every extension member MUST still obtain a complete and correct learning experience. Equivalently: removing all `x-` members from a conforming document MUST leave a conforming document with equivalent learner-facing meaning.

This keeps extensions from degenerating into a shadow format that fragments the ecosystem.

### 7.4 Consumer obligations

A consumer MUST NOT reject a document solely because it contains extension members (this restates §5.4 for the namespaced case).

A consumer MUST NOT interpret an extension member outside its own namespace as having any defined meaning. A consumer MAY read and act on extension members within namespaces it understands.

A consumer that imports, modifies, and re-exports a document SHOULD preserve extension members it does not understand, re-attaching each to the same object it arrived on (identified by `globalId` where the object carries one). A consumer that preserves all unrecognized extension members across a round trip is said to be *extension-preserving*; a consumer that cannot SHOULD document the loss.

The SHOULD — rather than MUST — acknowledges that some consumers have fixed internal storage with nowhere to hold arbitrary foreign data. But preservation is what lets a tool use LC-JSON as a faithful transfer or backup format for its own tool-specific state: a document that round-trips through an extension-preserving consumer comes back whole, including data that consumer never understood.

### 7.5 Producer obligations

A producer MAY emit extension members under namespaces it owns, subject to §7.1–§7.3. A producer MUST keep extension content well-formed JSON. A producer SHOULD prefer extension members over overloading core fields (for example, encoding private state in `tags` or `title`) for tool-specific data.

---

## 8. Versioning and Stability

### 8.1 Semantic versioning

Spec versions follow a semver-style scheme: `MAJOR.MINOR[.PATCH]`.

- A **major** version bump (e.g., 1.x → 2.0) signifies a breaking change. New schemas are published at a new URL path (`/2.0/`).
- A **minor** version bump (e.g., 1.0 → 1.1) signifies an additive change. New schemas are published at a new URL path (`/1.1/`).
- A **patch** bump signifies non-normative fixes (description text, examples, clarifications). No URL change.
- A **release candidate** of an upcoming version `X.Y` carries the version label `X.Y-rc.N` (where `N` is `1`, `2`, …) and is published at its own URL path `/X.Y-rc.N/`. RCs allow non-breaking refinements between the candidate and the accepted final release; each RC is its own immutable publication. The final `X.Y` release is published at `/X.Y/` only when accepted. Documents pinned to `/X.Y-rc.N/` do not auto-promote to `/X.Y/` — adopting the final release is an explicit publisher choice (typically a re-export against the new schema URL).

### 8.2 Definition of "breaking"

For the purposes of §8.1, a change is **breaking** if and only if it causes a previously-conforming document to stop validating under the new schema, or to change in meaning under the new schema (i.e., a field that previously had one interpretation now has another).

Loosening the schema so that a previously-non-conforming document begins to validate is **not** breaking by this definition: documents that already conformed continue to conform with unchanged meaning. The additive examples below rely on this asymmetry.

Examples of breaking changes:
- Renaming a property.
- Removing an enum value that existing documents may have used.
- Tightening a constraint (e.g., reducing a string's `maxLength` below an existing value's length).
- Adding a new required property.
- Changing a property's type.

Examples of additive changes:
- Adding an optional property.
- Adding an enum value.
- Loosening a constraint (e.g., increasing `maxLength`).
- Removing a property from an object's `required` list (the field becomes optional).
- Adding an entirely new artifact type with its own `documentType` value.

### 8.3 URL stability

Schemas published at any published version path — released versions and release candidates alike — MUST remain available at that URL with byte-identical content (modulo whitespace) for the lifetime of the specification. Specifically:

- `https://lc-json.org/1.0/*.schema.json` MUST resolve to the 1.0 schemas indefinitely once 1.0 final is published.
- `https://lc-json.org/1.0-rc.N/*.schema.json` MUST resolve to the rc.N schemas indefinitely once rc.N is published.
- These URLs MUST NOT be redirected to a different schema, even one that is "compatible" or "improved."
- These URLs MUST NOT be moved to a non-canonical host.
- The `/X.Y/` URL path MUST NOT be populated until `X.Y` final is published; serving rc.N content at `/X.Y/` is non-conforming and prevents downstream documents from distinguishing the candidate from the final release.

This guarantee enables conforming documents to embed `$schema` URLs that remain valid for the document's entire lifetime in archives, version-control systems, and offline contexts — including across rc.N → final transitions, where rc.N documents continue to validate against their original rc.N URL indefinitely.

### 8.4 Version-path forward compatibility

A document is validated against the schemas at the URL given in its `$schema` field — that URL is the document's **canonical schema location** and the binding target for conformance. The `specVersion` field declares the spec version the document targets; the `$schema` URL identifies the specific schema publication (release or release candidate) it was authored against. Both MUST be present (§3.2) and MUST agree on the targeted version (§4.6, §4.7): a document declaring `specVersion: "1.0"` MUST point `$schema` at either `/1.0/` (the final release, once published) or a `/1.0-rc.N/` candidate path; a document declaring `specVersion: "1.1"` MUST point `$schema` at `/1.1/` or a `/1.1-rc.N/` candidate path.

**Reminder (§4.6):** `specVersion` never carries an `-rc.N` suffix. Every document targeting the 1.0 contract — whether authored against an rc.N candidate or 1.0 final — declares `specVersion: "1.0"`. The specific publication is identified by `$schema`. For example, a document authored during the rc.2 phase looks like:

```json
{
  "$schema":     "https://lc-json.org/1.0-rc.2/course.schema.json",
  "documentType": "course",
  "specVersion":  "1.0",
  ...
}
```

It follows that:

- A document declaring `specVersion: "1.0"` with `$schema` pointing at `/1.0/` MUST validate against the schemas published at `/1.0/`. This is the post-1.0-final scenario; `/1.0/` is reserved until 1.0 ships (§8.3).
- A document declaring `specVersion: "1.0"` with `$schema` pointing at `/1.0-rc.N/` MUST validate against the schemas published at `/1.0-rc.N/` and is not required to validate against `/1.0/`. This is the current rc-cycle case. The rc.N → final transition is an explicit publisher choice (see §8.1, §8.3) — a re-export against the new `$schema` URL — not an automatic upgrade.
- A document declaring `specVersion: "1.1"` SHOULD validate against the schemas at its declared `$schema` URL and SHOULD also validate against `/1.0/` schemas for fields that are unchanged between minor versions.

---

## 9. Deprecation

A field, discriminator value, or shape may be deprecated in a minor version and removed in a subsequent major version.

### 9.1 Deprecation marking

Deprecated fields MUST be marked with `"deprecated": true` in their schema definition and SHOULD include a `description` referencing their replacement.

### 9.2 Producer behavior for deprecated fields

A producer MUST NOT emit deprecated fields in new documents. A producer that re-emits previously-imported documents MAY preserve deprecated fields it received, but SHOULD prefer to emit only the canonical replacement.

### 9.3 Consumer behavior for deprecated fields

A consumer MUST continue to accept deprecated fields for the lifetime of the major version that introduced the deprecation. Removal is permitted only at the next major version bump.

### 9.4 Currently deprecated items (1.0)

No items are deprecated in 1.0. The specification ships clean.

---

## 10. Conformance Claims

### 10.1 Base LC-JSON 1.0 conformance

A tool MAY claim conformance to LC-JSON 1.0 as follows:

- **"Conforms to LC-JSON 1.0 as a producer"** — the tool emits documents satisfying §4.
- **"Conforms to LC-JSON 1.0 as a consumer"** — the tool ingests documents satisfying §5, §6, §7, and the accessibility-preservation obligations of §12.1.
- **"Conforms to LC-JSON 1.0"** without qualification — the tool implements both producer and consumer conformance.

### 10.2 LC-JSON 1.0 Accessibility Profile conformance (opt-in)

A tool that additionally satisfies the obligations in [`ACCESSIBILITY.md`](ACCESSIBILITY.md) MAY claim:

- **"Conforms to the LC-JSON 1.0 Accessibility Profile as a producer"** — the tool emits documents satisfying §4 plus the producer-side obligations in `ACCESSIBILITY.md` §§2–7.
- **"Conforms to the LC-JSON 1.0 Accessibility Profile as a consumer"** — the tool ingests and renders documents satisfying §5/§6/§7/§12.1 plus the consumer-side MUST-level obligations in `ACCESSIBILITY.md` §§2–8.
- **"Conforms to the LC-JSON 1.0 Accessibility Profile"** without qualification — both producer and consumer.

A consumer claiming the Accessibility Profile MUST satisfy all MUST-level items in `ACCESSIBILITY.md` §§2–8 for its role; partial satisfaction is misclaim. See §12 for the profile's binding text.

### 10.3 Claim accuracy

A tool MUST NOT claim conformance unless it satisfies all applicable MUST requirements. A tool MAY publish self-test results against the conformance test corpus (see `tests/`) as evidence.

Three rules guard against the predictable misclaims:

1. **Producer ≠ consumer.** Claim only the roles the tool actually satisfies; a producer-side conformance claim does not extend to the consumer role without satisfying §5.
2. **The Accessibility Profile is fully bound.** Claiming the Accessibility Profile means every MUST-level item in `ACCESSIBILITY.md` §§2–8 (for the claimed role) is satisfied. Partial profile claims are misclaim.
3. **LC-JSON does not certify WCAG conformance.** The LC-JSON Accessibility Profile provides the wire-format affordances and consumer-rendering obligations that *enable* WCAG 2.1 AA delivery; a delivering consumer's own WCAG claim (under EN 301 549, DOJ ADA Title II, Section 508, Section 504, or equivalent) is separate and remains the consumer's responsibility.

### 10.4 Suggested wording (informative)

Implementers may use the following short forms for marketing pages, badges, READMEs, and footers. They are advisory — formal claims live in §10.1 and §10.2.

**Tier 1 — Base LC-JSON 1.0 conformance**

| Form | Wording |
|---|---|
| Badge | **LC-JSON 1.0 Compatible** |
| Sentence | *"Reads and writes LC-JSON 1.0 — the open Learning Content JSON specification at lc-json.org."* |
| Formal | *"Conforms to LC-JSON 1.0 as a producer / consumer / producer and consumer."* |

**Tier 2 — LC-JSON 1.0 Accessibility Profile**

| Form | Wording |
|---|---|
| Badge | **LC-JSON 1.0 Accessibility Profile** |
| Sentence | *"Delivers LC-JSON 1.0 content with accessible rendering — keyboard navigation, screen-reader support, captions, language-aware text direction. Conforms to the LC-JSON 1.0 Accessibility Profile."* |
| Formal | *"Conforms to the LC-JSON 1.0 Accessibility Profile as a producer / consumer / producer and consumer."* |

Role qualifiers (`(producer)` / `(consumer)`) SHOULD accompany the badge or sentence when the implementation supports only one role, so readers do not infer capabilities the tool does not provide.

A Tier 2 claim implies Tier 1 (the Accessibility Profile is additive to base conformance); no double-badging is needed.

### 10.5 Trademark

Trademark rights in "LC-JSON" and "Learning Content JSON" are not asserted against conformance claims. Any tool meeting the requirements above MAY freely state its conformance and use the suggested wording in §10.4.

---

## 11. HTML Safety Profile

LC-JSON 1.0 permits HTML in two fields: `ContentItem.html` and `SignpostItem.customHtml`. The complete normative HTML safety profile — allowed elements, allowed attributes, URL-scheme allowlist, sanitization obligation, link normalization, media handling, and unknown-element handling — is specified in [`HTML_SAFETY.md`](HTML_SAFETY.md).

A producer that emits HTML in any HTML-bearing field MUST emit only constructs permitted by `HTML_SAFETY.md` §2 (elements), §3 (attributes), and §4 (URL schemes).

A consumer that renders HTML from any HTML-bearing field MUST sanitize the HTML against `HTML_SAFETY.md` §5 before rendering, MUST normalize `<a target="_blank">` to include `rel="noopener noreferrer"` per §6.1, and MUST strip-while-preserving-text any unknown element per §6.2. A consumer MUST reject any document containing forbidden constructs listed under §8.1 (`<script>`, event handlers, `javascript:`/`vbscript:` URLs, etc.).

`HTML_SAFETY.md` is normative and forms part of LC-JSON 1.0. The split into a separate document reflects its length, not its status.

---

## 12. Accessibility Profile

LC-JSON's accessibility model distinguishes two layers: **preservation** of accessibility metadata across read/write cycles (binding on every conforming consumer), and **delivery** of accessible rendering to end users (binding only when the Accessibility Profile is claimed).

The motivating concern is that accessibility information must survive transformation. In real ecosystems, educational content is exported, imported, translated, edited, and repackaged across multiple tools; accessibility failures most commonly occur during these transformations rather than during original authoring — alt text silently removed during save operations, transcripts discarded during export, localized accessibility text overwritten, unknown accessibility fields stripped by intermediate tools. The accessibility-preservation floor (§12.1) protects the format against that failure mode in every conforming consumer. The Accessibility Profile (§12.2) is the opt-in commitment to also *deliver* the affordances accessibly.

### 12.1 Base-conformance accessibility preservation

A conforming consumer that re-emits a document MUST NOT degrade its accessibility shape. Specifically:

- `alt` attributes on `<img>` MUST round-trip.
- `<track>` elements (including `kind`, `src`, `srclang`, `label`, `default`) on `<video>` and `<audio>` MUST round-trip.
- `lang` and `dir` attributes on HTML-bearing elements MUST round-trip.
- The required document-root `language` field MUST round-trip. The document-root `supportLanguage` field MUST round-trip when present, including explicit `null`.
- Reserved-type questions MUST round-trip with any accessibility metadata they carry, per §6.4.
- Extension-preserving consumers (§7.4) SHOULD round-trip `x-`-namespaced extension members that carry accessibility data.

These obligations are part of base LC-JSON conformance; a consumer claiming "Conforms to LC-JSON 1.0 as a consumer" satisfies them. The HTML safety profile (§11 / [`HTML_SAFETY.md`](HTML_SAFETY.md)) explicitly allows `alt`, `<track>`, `lang`, and `dir` on every applicable element class to make this preservation possible.

### 12.2 The Accessibility Profile (opt-in)

The accessibility profile defined in [`ACCESSIBILITY.md`](ACCESSIBILITY.md) — alt-text requirements, video caption obligations for instructional content, keyboard alternatives for structured-task question types, non-color feedback, language-aware rendering, accessible reserved-type placeholders, and validator severities — is bound by an opt-in claim (§10.2).

- A consumer claiming the Accessibility Profile MUST satisfy the structured-task keyboard alternatives (`ACCESSIBILITY.md` §4), the non-color-feedback obligations (§5), the language/`dir` rendering obligations (§6), and the reserved-type placeholder accessibility (§7).
- A producer claiming the Accessibility Profile MUST emit the producer-side obligations across `ACCESSIBILITY.md` §§2–7 (alt text on `<img>`, `<track>` for instructional video carrying speech, root `language` matching delivery, etc.).
- Tools that satisfy preservation (§12.1) but not delivery (§12.2) are conforming LC-JSON consumers but are NOT conforming Accessibility Profile consumers, and MUST NOT claim the latter.

### 12.3 Relationship to WCAG

WCAG governs rendered user experiences; LC-JSON governs portability and metadata preservation. A consumer claiming the LC-JSON Accessibility Profile carries the wire-format affordances and consumer-rendering obligations that WCAG 2.1 AA delivery requires (alt text, captions, language/direction, textual feedback, keyboard alternatives); the consumer's own jurisdictional WCAG conformance claim (under EN 301 549, DOJ ADA Title II, Section 508, Section 504, or equivalent) remains separate and is the consumer's responsibility, not LC-JSON's.

A tool MUST NOT claim WCAG 2.1 AA conformance by virtue of LC-JSON Accessibility Profile conformance alone. LC-JSON does not certify WCAG conformance.

`ACCESSIBILITY.md` is normative for tools claiming the Accessibility Profile and forms part of LC-JSON 1.0 in that capacity. The split into a separate document reflects the opt-in scope, not a lesser status.

---

## 13. Validation surface

The requirements in this document are enforced across three sites: the 23 JSON Schemas under [`schemas/`](schemas/), the reference validator [`tools/validate_course.py`](../tools/validate_course.py), and the per-document prose in the companion normative documents ([`HTML_SAFETY.md`](HTML_SAFETY.md), [`ACCESSIBILITY.md`](ACCESSIBILITY.md)). [`VALIDATION.md`](VALIDATION.md) catalogs every documented rule and tags it with its enforcement tier — *schema-enforced*, *domain-validator-enforced*, or *advisory* — and identifies the forward-looking deepenings scheduled for `1.0` final. Implementers building consumers, validators, or producer round-trip tests should consult `VALIDATION.md` for the one-map view of what to check.

`VALIDATION.md` is informative and additive — it introduces no requirements beyond those already stated in this document, in the schemas, or in the companion normative documents. Where it and any of those sources disagree, those sources win.

---

## 14. References

- [RFC 2119 — Key words for use in RFCs to Indicate Requirement Levels](https://www.rfc-editor.org/rfc/rfc2119)
- [RFC 8174 — Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words](https://www.rfc-editor.org/rfc/rfc8174)
- [RFC 4122 — A Universally Unique IDentifier (UUID) URN Namespace](https://www.rfc-editor.org/rfc/rfc4122)
- [RFC 3986 — Uniform Resource Identifier (URI): Generic Syntax](https://www.rfc-editor.org/rfc/rfc3986)
- [JSON Schema Draft 7](https://json-schema.org/draft-07/schema)
- LC-JSON HTML safety profile: [`HTML_SAFETY.md`](HTML_SAFETY.md)
- LC-JSON accessibility profile: [`ACCESSIBILITY.md`](ACCESSIBILITY.md)
- LC-JSON validation surface (informative): [`VALIDATION.md`](VALIDATION.md)
- LC-JSON glossary (informative): [`GLOSSARY.md`](GLOSSARY.md)
- LC-JSON schemas: [`schemas/`](schemas/)
- LC-JSON examples: [`examples/`](examples/)
- LC-JSON conformance test corpus: [`tests/`](tests/)
