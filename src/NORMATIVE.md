# LC-JSON Specification — Normative Requirements

**Spec version:** 1.1
**Status:** Normative (release candidate — published at /1.1-rc.1/)
**Last updated:** 2026-07-22

This document states the requirements that conforming LC-JSON (Learning Content JSON) tools MUST satisfy. It is the authoritative source of truth for compliance; descriptive material elsewhere in the specification illustrates how to meet these requirements but does not relax them.

---

## 1. Scope

This document specifies the requirements for tools that produce, consume, or validate LC-JSON 1.1 documents. It defines:

- The canonical wire format for the five artifact types (Course, QuestionSet, Glossary, SubjectCollection, CurriculumPack).
- Two conformance roles — *producer* and *consumer* — and what each MUST do.
- Versioning rules and URL stability guarantees.
- Conformance-claim language (how a tool may state it conforms).

This document does not prescribe implementation strategies, programming languages, or runtime architecture. Any tool meeting the requirements below conforms, regardless of how it is built.

LC-JSON 1.1 is a purely additive minor version over 1.0 (§8.2): every conforming 1.0 document is a conforming 1.1 document with unchanged meaning. The additions are the three new artifact types (§3.3) — two vocabulary/arrangement types and the glossary content type — the member-identity and self-containment rules that make them portable (§3.4, §4.9–§4.11, §5.7), and the optional course-root additions: three publication-metadata fields and the `glossaryRefs` attachment arrays (Appendix A).

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

The `<spec-version>` segment identifies either a released version (`1.0`, `1.1`, `2.0`, …) or a **release candidate** — an immutable draft of an upcoming version, published for review and implementer feedback before the final release is accepted (e.g., `1.0-rc.1`, `1.0-rc.2`, `1.0-rc.3`, `1.1-rc.1`, …). Each receives its own URL path. For released spec version 1.0, schemas resolve at `https://lc-json.org/1.0/*.schema.json`. For release candidates, schemas resolve at `https://lc-json.org/1.0-rc.N/*.schema.json`, one URL path per candidate.

URLs under any published path — released or release-candidate — are immutable. They MUST NOT be renamed, removed, redirected to a different schema, or repointed to a non-canonical host once published.

The `/X.Y/` URL path is **reserved** for the accepted final `X.Y` release and MUST NOT be populated until that release is published. Release candidates targeting `X.Y` are published at `/X.Y-rc.N/` paths. A document pinned via `$schema` to `/X.Y-rc.N/` does not automatically validate against `/X.Y/`; adoption of the final release is an explicit choice by the publisher (typically a re-export against the new schema URL). See §8.1 and §8.3 for the full versioning and stability contract.

### 3.2 Required root fields

Every conforming LC-JSON document MUST contain at the root, as siblings (not nested under any envelope):

| Field | Required? | Type | Value |
|---|---|---|---|
| `documentType` | MUST | string | `"course"`, `"questionSet"`, `"glossary"`, `"subjectCollection"`, or `"curriculumPack"`. The artifact discriminator. |
| `specVersion` | MUST | string | The LC-JSON contract version this document conforms to. Pattern enforced by the schemas; consumer/producer rules in §5.2 / §4.6. |
| `$schema` | MUST (producer) / SHOULD-tolerate (consumer) | string | A URL identifying the schema for this document type at the spec version the producer conforms to (e.g., `https://lc-json.org/1.1-rc.1/<artifact>.schema.json` for a 1.1-rc.1 producer; `https://lc-json.org/1.0/<artifact>.schema.json` for a 1.0-final producer). Consumers SHOULD accept documents that omit `$schema` (re-import scenarios from older or lenient producers), but MUST reject any other root-field omission. |

A document missing `documentType` or `specVersion` is non-conforming. A producer that emits a document missing `$schema` is non-conforming with respect to that document; a consumer that rejects an otherwise-valid document on the basis of a missing `$schema` is overly strict and SHOULD instead infer the schema from `documentType` + `specVersion`.

### 3.3 Artifact types

Spec version 1.1 defines exactly five artifact types:

- **Course** (`documentType: "course"`) — hierarchical learning content (Course → Units → Lessons → Items → Questions). Validated by `course.schema.json`.
- **QuestionSet** (`documentType: "questionSet"`) — flat list of questions without a course/unit/lesson scaffold. Validated by `question-set.schema.json`.
- **Glossary** (`documentType: "glossary"`) — a flat list of **terms** with immutable member ids: pronunciation, translations, examples, inflected forms. Content-adjacent learning material a student studies — not vocabulary *about* content (contrast SubjectCollection). Validated by `glossary.schema.json`. See [`glossary-reference.md`](glossary-reference.md).
- **SubjectCollection** (`documentType: "subjectCollection"`) — a reusable classification **vocabulary**: tags and learning objectives for a structured `(subject, level, audience, purpose, jurisdiction)` scope. Validated by `subject-collection.schema.json`. See [`subject-collection-reference.md`](subject-collection-reference.md).
- **CurriculumPack** (`documentType: "curriculumPack"`) — an **arrangement**: sequence, pacing, and checkpoints referencing a SubjectCollection plus content documents. Validated by `curriculum-pack.schema.json`. See [`curriculum-pack-reference.md`](curriculum-pack-reference.md).

Course, QuestionSet, and Glossary are *content* documents; SubjectCollection is a *vocabulary* document; CurriculumPack is an *arrangement* document. The vocabulary/arrangement types never carry learner-facing content items or questions — they classify and organize content documents. A glossary carries learner-facing study material (its terms) but never items or questions.

A producer MUST emit exactly one of these artifact types per document. Mixing artifact types within a single document is non-conforming.

### 3.3.1 Conformance rules by artifact type (normative)

A conforming document MUST satisfy the rules for its artifact type. For Course and QuestionSet those rules are stated in §4–§6, in §12 (accessibility preservation), and in the JSON Schemas. For the artifact types introduced in 1.1 the rules are, in addition to §3.4 (member identity), §4.9 (self-containment), §4.10 (alignment claims), and §4.11 (publication metadata):

- **SubjectCollection** — the structural, member-identity, closure, and alignment-claim rules identified **SC-1 … SC-14**.
- **CurriculumPack** — the step-shape, pacing, checkpoint, taught-before-used, term-capacity, dependency-direction, bill-of-materials, coverage, and bundle-closure rules identified **CP-1 … CP-17**.
- **Glossary** — the structural, gloss, and declared-translation-inventory rules identified **GL-1 … GL-11**.
- **Course (1.1 deepenings)** — the specVersion↔`$schema` agreement rule **RD-1**, and the objective-pool and glossary-attachment rules identified **CO-1 … CO-5**.

**These rule families are normative requirements of this specification.** [`VALIDATION.md`](VALIDATION.md) §15–§19 enumerates each rule, cites its source, and tags its enforcement tier (*schema-enforced*, *domain-validator-enforced*, or *advisory*); each rule's severity (ERROR / WARN / NOTE) is as tagged there. The three reference documents — [`subject-collection-reference.md`](subject-collection-reference.md), [`curriculum-pack-reference.md`](curriculum-pack-reference.md), and [`glossary-reference.md`](glossary-reference.md) — are **informative**: they explain and illustrate these rules but do not add to or relax them. Where a reference document differs from this document, the JSON Schemas, or the VALIDATION.md catalog, this document and the schemas govern.

### 3.4 Member identity (vocabulary and glossary documents)

A SubjectCollection's entries — `tags[]` and `objectives[]` — and a Glossary's `entries[]` are the owning document's **members**. Members are identified by portable, stable ids, and those ids are the unit of interoperability across documents, tools, and time:

- Every member MUST carry an `id` that is **immutable for the life of the member**. Renaming a tag, re-wording an objective, re-parenting a tag, or moving a member between display categories are content revisions of the owning document (a new document `version`), never id changes.
- **Display text is never identity.** `slug`, `name`, and `label` are mutable presentation and lookup fields; no conforming tool may key member identity on them.
- For **SubjectCollection members** (tags and objectives), a member `id` encountered in another document **identifies the same member**. Two documents that both carry tag id `X` are both referring to one shared concept — this is what makes classification comparable across independently-authored content (see §5.7 for the consumer obligations this creates). **Glossary entry identity is narrower — see the glossary bullet below.**
- A document's `globalId` is likewise portable and immutable: consumers MUST preserve it verbatim on import and MUST NOT re-mint it.

The membership model is deliberately asymmetric between the two member kinds:

- A **tag** may be a member of any number of SubjectCollections. A document listing a tag asserts *membership*, not exclusive ownership.
- An **objective** has exactly one owning document (its wording is scope-specific). Other documents may *reference* and *carry copies of* an objective (§4.9), but only the owner revises its wording.
- A **glossary entry** is single-owner, like an objective, and its identity is **document-scoped**: the identifying key is the pair `(glossary globalId, entry id)`, and entry ids are required to be unique only within their owning glossary. An entry id encountered in a *different* glossary is a different entry — the cross-document same-id-same-member rule above applies to collection members only. Entries are not carried into other documents in 1.1 — a course references a whole glossary (`glossaryRefs`), never individual entries — so entry ids exist for re-import reconciliation (§5.7): the same entry id in a later version of *the same glossary* (same `globalId`) is the same entry, updated in place, never duplicated or re-minted.

---

## 4. Producer Conformance

A *producer* is any tool that emits LC-JSON documents intended for external consumption.

### 4.1 Wire format

A producer MUST emit documents in the canonical flat-root form: `$schema`, `documentType`, and `specVersion` at the top level, with the artifact payload as flat siblings. Nested envelopes such as `{"course": {...}}` are non-conforming.

### 4.2 Discriminator casing

A producer MUST emit the `type` discriminator on questions in canonical camelCase form: `"simpleGapFill"`, `"trueFalseQuestion"`, `"multipleChoice"`, `"wordBankCloze"`, `"multiGapCloze"`, `"multipleChoiceCloze"`, `"shortAnswer"`, `"essay"`, `"sentenceTransformation"`, `"matching"`, `"ordering"`, `"placement"`.

A producer MUST emit the `type` discriminator on items in canonical lowercase form: `"content"`, `"exercise"`, `"quiz"`, `"contentsequence"`, `"signpost"`.

A producer MUST emit `documentType` in canonical camelCase form: `"course"`, `"questionSet"`, `"glossary"`, `"subjectCollection"`, or `"curriculumPack"`.

### 4.3 Item-type semantics

The `exercise` and `quiz` item-type discriminators are structural distinctions, not policy. They allow consumers to render the two forms differently in the UI and to track their points in separate buckets (enabling weighted grading).

The grading policy of an item is composed independently from its type via the `isGraded`, `isOptional`, and `passMarkPercent` fields. All four combinations of `{exercise, quiz} × {graded, ungraded}` are valid LC-JSON: a graded exercise (e.g. homework that counts), an ungraded exercise (open practice), a graded quiz (typical assessment), and an ungraded quiz (e.g. diagnostic pre-test, self-check) are all conforming.

A producer MUST NOT infer or assert grading state from item type alone, and a consumer MUST NOT reject a document on the basis that an `exercise` is graded or a `quiz` is ungraded.

### 4.4 Identifiers

A producer MUST emit `globalId` values as RFC 4122 UUIDs (any version) where the schema requires them. Specifically: every Unit, Lesson, Item, and Question MUST have a `globalId`; these identify the entity across re-imports, enabling consumers to match unchanged content against existing records and detect modifications.

Within a single document, `globalId` values MUST be unique across all entities (Units, Lessons, Items, and Questions share one namespace). A document in which two entities carry the same `globalId` does not conform: a consumer keyed on `globalId` cannot tell the entities apart, so re-import matching breaks and updates can land on the wrong record. `globalId` comparison is case-insensitive (the hexadecimal digits of a UUID carry no case significance).

A producer SHOULD emit a `sourceCourseId` at the course root for any course that may be re-imported or version-tracked. `sourceCourseId` is the stable course-identity field — the same `sourceCourseId` across versions of a course identifies them as the same logical course, enabling consumers to detect re-imports and apply update semantics rather than treating each upload as a fresh course. `sourceCourseId` is generated by the source authoring system; it does not identify a human author. A QuestionSet carries the analogous `sourceQuestionSetId` at its root, with the same source-side semantics.

Vocabulary- and glossary-document identifiers follow §3.4: a producer MUST emit an `id` on every SubjectCollection member and every Glossary entry, and MUST NOT re-mint an id when regenerating or revising a document (the member persists; the document's `version` changes). Member ids are opaque strings; RFC 4122 UUIDs are RECOMMENDED. Document identity for both types is the root `globalId` (an opaque string chosen by the original publisher; stable, human-readable slugs and UUIDs are both conventional) together with `version`.

**Document identity by artifact type.** The **portable document identity** — the value another document uses when it references this one — depends on the document's `documentType`:

| `documentType` | Portable document identity |
|---|---|
| `course` | `sourceCourseId` |
| `questionSet` | `sourceQuestionSetId` |
| `subjectCollection` | `globalId` |
| `glossary` | `globalId` |
| `curriculumPack` | `globalId` |

Course and QuestionSet identity is source-side (`sourceCourseId` / `sourceQuestionSetId`); the three 1.1 artifact types carry a publisher-chosen root `globalId`. A Curriculum Pack references content by the value above for the referenced document's `type`, carried in the reference's `id` field (§3 of [`curriculum-pack-reference.md`](curriculum-pack-reference.md); step-level binding in §4.3). Because a producer only SHOULD emit `sourceCourseId` / `sourceQuestionSetId`, **a Curriculum Pack producer MUST NOT emit a `contentRef` to a Course or QuestionSet that does not carry the identifier its `type` resolves against** — like the §4.9 closure rules, this is a producer-emission requirement: a conforming validator reports a pack that references an id-less course as an error, but a Course is never obliged to carry `sourceCourseId` merely to exist standalone. SubjectCollection and Glossary always carry a root `globalId`, so a reference to one always resolves. The identity-by-type table above defines how each artifact type is identified **when it is referenced**; it does not itself make every type a `contentRef` target. A Curriculum Pack's `contentRefs` bind **content documents only** — Course, QuestionSet, or Glossary — and a pack **MUST NOT** reference another Curriculum Pack: an arrangement is not embeddable content, and 1.1 does not define pack-in-pack nesting (SubjectCollections are referenced through `collectionRefs`, not `contentRefs`). The `contentRefs[].type` vocabulary is **closed for producers**: a producer MUST emit one of `course`, `questionSet`, or `glossary`, and MUST NOT emit `curriculumPack` or any other value. Like the alignment-claim vocabulary (§4.10, §5.5), it binds producers only and is deliberately left schema-open (§5.8): a consumer that meets a `contentRefs[].type` it does not recognize MUST NOT reject the document — it treats the reference as unresolvable and preserves it across read/write cycles. Consumers MUST NOT conflate a source-side id with a platform-assigned identifier (see the forward-direction note below): a `contentRef` resolves against source-side identity, never against a platform id.

> **Forward-direction note (informative, not normative for 1.0):** Future versions of LC-JSON may introduce a complementary `coursePlatformId` field for platform-assigned course identifiers, enabling round-trip flows where a teacher exports from a platform and re-imports to an authoring tool with the platform's identity preserved. Implementations should not rely on this field's absence in 1.0 documents being permanent. A platform-assigned identifier is deployment-scoped and is **not** the identity a Curriculum Pack `contentRef` resolves against (which is always the source-side `sourceCourseId` / `sourceQuestionSetId`), so introducing it does not change pack reference resolution.

### 4.5 Property naming

A producer MUST emit all property names in camelCase. PascalCase, snake_case, and other casings are non-conforming on the wire.

### 4.6 Spec version

A producer MUST emit `specVersion` matching the spec version it implements. For producers conforming to this document, `specVersion` MUST begin with `"1."` (e.g., `"1.0"`, `"1.1"`, `"1.1.1"`).

`specVersion` carries the contract version regardless of which publication the producer targets. The specific publication — release candidate or final release — is identified by the `$schema` URL (§4.7). A producer conforming to 1.1-rc.1 emits `specVersion: "1.1"` together with `$schema: "https://lc-json.org/1.1-rc.1/course.schema.json"`; a producer conforming to a later 1.1 final release emits the same `specVersion` value together with that release's `$schema` URL (the `/1.1/` path, which is reserved and is not populated until the 1.1 final release ships — see §8.3). `specVersion` does not include release-candidate suffixes — `"1.1-rc.1"` is not a conforming `specVersion` value.

### 4.7 Schema URL

A producer MUST emit a `$schema` URL pointing at the canonical published schema for its `documentType` **at the spec version the producer conforms to**. For example: a producer conforming to LC-JSON 1.1-rc.1 emits `https://lc-json.org/1.1-rc.1/course.schema.json` for courses and `https://lc-json.org/1.1-rc.1/subject-collection.schema.json` for subject collections; a producer conforming to 1.0 final emits `https://lc-json.org/1.0/course.schema.json`. A producer that emits a non-canonical URL or omits the field is non-conforming.

The strict producer / lenient consumer split (§3.2 above) is deliberate: emitting `$schema` makes documents self-describing for IDEs, schema dispatch, and ad-hoc validation; tolerating its absence on import preserves portability across older or otherwise-non-conforming producers without hard-failing re-imports.

### 4.8 Validation before emit

A producer SHOULD validate every emitted document against the published JSON Schemas before delivery. A producer that emits an invalid document is non-conforming with respect to that document.

### 4.9 Self-containment of vocabulary references (closure and carried copies)

**SubjectCollection closure.** A conforming SubjectCollection document is self-contained:

- `categories[]` MUST include every category referenced by any `tags[].categoryId`. Categories are shared display buckets, not identity; consumers merge them by category id.
- Every `objectives[].tagIds` entry MUST resolve to a member of the document's own `tags[]`.
- Every `tags[].parentId` MUST be the member id of another tag in the document (parents are member ids, never slugs).
- The `parentId` relation MUST be **acyclic**: no tag may be its own parent, and no sequence of `parentId` links may return to a tag already visited along that sequence. Because each tag has at most one parent, an acyclic relation is a forest — every tag reaches a root in finitely many steps. A document containing a `parentId` cycle of any length is non-conforming, and a consumer walking the hierarchy is entitled to assume termination.

A producer MUST NOT emit a SubjectCollection whose members link outside the document. A document that violates closure is non-conforming.

**Carried copies in content documents.** A course document may assign objectives that originate in a SubjectCollection (its `courseObjectiveIds` / `objectiveIds` arrays reference them). A producer emitting such a course MUST embed a copy of every referenced objective in the course's `objectives[]` pool — **with the member id preserved verbatim** — so the document remains self-contained. Such an embedded copy is a *carried copy*: it travels for portability and does not transfer ownership or revise the member's wording (§5.7 governs what a consumer does with it). A course document **declaring `specVersion` 1.1 or later** whose objective-id references do not all resolve within its own `objectives[]` pool is non-conforming. Documents declaring `specVersion` 1.0 retain their 1.0 meaning unchanged: unresolved objective references were an advisory (warning-tier) condition in 1.0 and remain so for 1.0 documents — this rule tightens only what 1.1 producers emit, which is what keeps 1.1 additive under §8.2.

The same pattern applies at document scale for glossaries: a producer emitting a course whose `glossaryRefs` reference glossaries it holds SHOULD embed a carried copy of each referenced glossary document — whole, with `globalId` and entry member ids preserved verbatim — in the course's root `glossaries[]` pool, so a single course file is self-contained. The obligation is SHOULD, not MUST: a glossary ref that resolves to no carried copy is legal (a *dangling ref* — consumers surface it and never fail the import; see §4.9 and [`glossary-reference.md`](glossary-reference.md) §4), because the course's learner-facing content is complete without its glossary panel, which is not true of assigned objectives.

### 4.10 Alignment claims

A SubjectCollection may assert typed alignments to external frameworks and registries via `externalAlignments[]`. Each entry carries `{claim, scheme, id, label}`:

- `claim` MUST be one of the 1.1 claim types: `"references"`, `"alignedTo"`, or `"covers"`. The values `"assesses"` and `"verifiedBy"` are **reserved** for a future version; a 1.1 producer MUST NOT emit them. This vocabulary binds **producers only** and is deliberately not closed in the schema: a consumer never rejects a document over a claim value it does not recognize (§5.5) — the schema leaves `claim` open precisely so the §5.1 schema-validation obligation and the §5.5 preservation obligation cannot collide.
- `scheme` and `id` MUST both be present and non-empty: `scheme` names the external namespace (e.g., a standards body, a national curriculum register, an official catalog), and `id` is the identifier **within that namespace**. `label` is optional display text.

External registries are referenced, never re-implemented: an alignment entry points at an external identifier; it does not embed or restate the external framework's content. A consumer MUST NOT reject a document for carrying an alignment whose `scheme` it does not recognize, and MUST preserve alignment entries across read/write cycles; interpretation of any given scheme is consumer-defined.

### 4.11 Publication metadata

The distributable artifact types — Course, SubjectCollection, CurriculumPack, and Glossary — carry publication metadata as optional top-level fields: `license`, `canonicalUrl`, and `derivedFrom[]` (alongside the type's existing `authors`/`version` fields). QuestionSet is excluded by role: it is a lightweight referencable resource, not a distribution-governed one. A glossary shares QuestionSet's *structural* lightness (flat root, referencable) but is distribution-governed: glossaries are shareable, remixable artifacts, which is precisely what the publication fields exist for.

- A producer SHOULD populate `license` on any document intended for distribution beyond its authoring environment. The value `"unspecified"` is appropriate only for private drafts.
- `derivedFrom[]` entries (`{globalId, version}`) record provenance: the document(s) this one was revised or remixed from. A producer creating a new document by modifying an existing one SHOULD record the source there.
- A producer MUST NOT encode commerce data (price, entitlement, buyer identity) in publication metadata or anywhere else in an LC-JSON document.

---

## 5. Consumer Conformance

A *consumer* is any tool that ingests LC-JSON documents from an external source.

**Consumer conformance requires more than schema validation.** Schema validation (§5.1) is necessary but not sufficient: a conformant consumer ALSO satisfies the discriminator-handling rule (§5.3), the unknown-fields rule (§5.4), the reserved-enum-values rule (§5.5), the randomization requirements (§5.6), the member-identity rules where vocabulary members appear (§5.7), and — where reserved or unknown question types appear — the round-trip preservation obligations in §6. A generic JSON Schema validator alone does not implement these; consumers MUST implement the relevant §5.x and §6 obligations to claim conformance (see §10.3). See the worked example at the end of this section.

### 5.1 Strict validation

A consumer MUST validate incoming documents against the published JSON Schemas for the declared `documentType` and reject documents that fail schema validation.

**Exception (§6 fallback for unknown types).** Schema-validation failures whose only cause is one or more `type` discriminator values not present in the consumer's implemented `question-base.schema.json` enum do not trigger §5.1 rejection. The consumer applies the §6 fallback to those questions (preserve verbatim, treat earned points as `0`, render placeholder, report to user) and validates the rest of the document under §5.1. All other schema-validation failures — missing required fields, type mismatches, pattern violations on known fields, `additionalProperties` violations on closed objects, etc. — still trigger rejection. This carve-out is what makes §5.2's "accept any 1.x `specVersion`" rule operable: a 1.0-only consumer reading a 1.x+ document with a future-minor question type satisfies both §5.1 and §6 by following this path.

**Unimplemented artifact types.** A consumer is not required to implement every artifact type. A consumer that does not implement a document's declared `documentType` MUST reject that document cleanly, naming the unsupported type — it MUST NOT attempt a partial or coerced interpretation. Conformance claims are scoped per artifact type (§10.1).

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

The same forward-compatible posture applies to alignment-claim values (§4.10): a consumer encountering an `externalAlignments[].claim` value outside the 1.1 set MUST NOT reject the document, MUST NOT interpret the claim, and MUST preserve the entry verbatim across read/write cycles.

### 5.6 Randomization requirements for matching and placement

For `matching` and `placement` questions, two surfaces a consumer presents to a learner have no author-defined order:

1. **The choice pool**, comprising every authored answer value (`pairs[].match` or `categories[].label` for matching; `placements[].item` for placement) plus any `distractors`. Source order would directly expose the correct-answer mapping (the N-th option being the correct answer for the N-th row or gap), defeating the question.
2. **The row order in `matching` classification mode**, where each row is one item to be classified. Source order is grouped by category — items belonging to `categories[0]` first, then `categories[1]`, and so on — which directly exposes the answer (the first N rows all share the same category label).

A consumer MUST present both surfaces to learners in randomized order. A consumer MUST NOT render either surface in source order. The randomization algorithm and any seeding strategy are consumer-defined.

These requirements do not apply to:

- `multipleChoice` and other single-question choice lists, where authors may deliberately position the correct option and the question schema's own `shuffleOptions` field governs shuffle policy per question.
- The order of pair rows in `matching` pairs mode, where each item has its own distinct match value and source row order does not directly expose the answer.
- The order of items in `ordering` source-tile pools, where the question's structural design requires the tile pool to be presented in non-source order regardless.

### 5.7 Member-identity handling

When a consumer that maintains a persistent store of vocabulary members ingests a document carrying members (a SubjectCollection, or a course with carried copies per §4.9), the member ids govern reconciliation:

- **An incoming member id the consumer already holds identifies the same member.** The consumer MUST NOT create a duplicate member for it.
- **Tags — record membership.** When a SubjectCollection lists a tag the consumer already holds, the consumer records the tag's membership in that collection. It MUST NOT duplicate the tag, and MUST NOT transfer or revoke the tag's other memberships.
- **Objectives — link, never overwrite.** When a document carries an objective the consumer already holds, the consumer links to its existing member. It MUST NOT modify the existing member's wording, difficulty, or tag links from the incoming copy **unless the incoming document is the member's owning document** (a revision of the owning SubjectCollection, or a re-import of the course that owns the objective). Carried copies (§4.9) are read-only with respect to the member they duplicate.
- **Ownership is determinable only as far as the wire permits — 1.1 carries no owner/provenance marker.** An objective listed in a SubjectCollection's `objectives[]` is owned by that collection (§3.4: collections own their objectives), and a consumer MAY treat that as an authoritative ownership claim. A course's `objectives[]` pool is deliberately ambiguous — it holds the course's own objectives and carried copies without distinction, and nothing on the wire says which — so **a consumer cannot determine from a course document alone whether that course owns a given objective id or merely carries a copy of one owned elsewhere.** Because of that, a consumer MUST NOT overwrite one document's wording for an objective id with another's on the basis of an inferred course ownership (**link-never-overwrite**): it reconciles by id, keeps the ingested wordings, and SHOULD surface a divergence between two sources for the same id rather than silently picking one, offering a **fork** (a new member id) as the keep-mine path. When a SubjectCollection listing an id is ingested, the collection's wording MAY be treated as authoritative for that id from then on; absent any collection claim, an id seen only in course pools has no determinable owner and is treated as shared-by-reference. Two SubjectCollections both listing the same objective id is a document-set conflict the consumer SHOULD surface — the model gives objectives exactly one owner. A per-copy provenance marker on carried copies, which would let a consumer resolve course-level ownership deterministically, is reserved for a future minor version (alongside the reserved course→collection reference); until it exists, the obligations above are the whole of what a 1.1 consumer is required to do.
- **Absent members are created verbatim.** A member id the consumer does not hold is created from the incoming copy with its id preserved — never re-minted — so that a later document carrying the same id reconciles to it.
- **Glossary entries reconcile like objectives.** When a consumer re-ingests a glossary it already holds (same document `globalId`), entry ids govern the update: an entry id already held is the same entry (update in place, never duplicate); an absent id is created verbatim; ids are never re-minted. A glossary entry's `firstMention` naming a lesson the consumer does not hold is treated as absent; a consumer that regenerates lesson `globalId`s on import MUST remap `firstMention` on glossaries imported alongside.
- **Identity-less members are rejected; closure is a producer-validity rule.** The §4.9 closure rules and §3.4 identity rule are **producer-emission requirements**: a producer MUST NOT emit a violating SubjectCollection, and such a document is non-conforming (a conforming validator reports it as an error). On the **consumer** side the two rules differ in strictness, mirroring the strict-producer / lenient-consumer split of §3.2 and §5.1:
  - A consumer MUST reject a SubjectCollection whose members lack ids — identity is non-optional (§3.4) and there is nothing to reconcile against.
  - A consumer SHOULD reject a SubjectCollection that violates the §4.9 closure rules, reporting the specific violations; a lenient consumer MAY instead ingest it with the violations surfaced (for example, treating an unresolved `categoryId` as an uncategorized tag). Closure is what a *producer* must guarantee; a consumer is not obliged to fail an otherwise-usable document over it.
- **Display collisions never override identity.** If an incoming member's `slug` (or other display/lookup field) collides with a *different* member the consumer already holds, the consumer resolves the collision on the display field (e.g., by qualifying the incoming slug) — it MUST NOT merge the two members or reassign the id.

A consumer with no persistent member store (e.g., a single-document validator or converter) satisfies §5.7 vacuously, but MUST still preserve member ids verbatim across any read/write cycle.

### 5.8 Consumer validation order (informative)

The §5.x obligations compose into one algorithm; implementers who follow it satisfy the strict-validation and forward-compatibility rules simultaneously:

1. Parse the JSON. A parse failure is fatal.
2. Dispatch the schema from `documentType` + the `$schema` URL (inferring from `documentType` + `specVersion` when `$schema` is absent, per §3.2). An unimplemented `documentType` is rejected cleanly, naming the type (§5.1).
3. Validate against the schema. A failure whose **only** cause is one or more unknown question-`type` discriminators routes those questions to the §6 fallback and the rest of the document continues (§5.1, Exception). **Every other schema failure is import-fatal.** Note what does *not* fail schema validation by design: unknown fields on open objects (§5.4 — LC-JSON objects are open unless §7.1 names them closed), and vocabulary values the spec deliberately leaves schema-open because their vocabularies bind producers only (alignment `claim`, pack `contentRefs[].type`).
4. Apply the domain rules cataloged in `VALIDATION.md` at their stated tiers — ERROR-tier domain failures reject; WARN/NOTE-tier are surfaced, never fatal.
5. Ignore-or-preserve unknown fields (§5.4) and extension members (§7.4); reconcile members (§5.7); apply the §6 obligations to any fallback questions.

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

> **Note (1.1):** this version promotes no reserved question types to first-class schemas; the 1.0 reserved-type list is unchanged in 1.1.

---

## 7. Extensions

LC-JSON is deliberately small. Tools frequently need to attach data that is meaningful to themselves but is not part of the interchange contract — authoring provenance, internal identifiers, editor state, analytics hints. Namespaced extensions provide a forward-compatible, collision-free way to carry such data without polluting the core format or requiring a spec revision.

### 7.1 Extension members

An *extension member* is an object member whose key begins with the prefix `x-` followed by a vendor or tool namespace, for example `x-acme-reviewState` or `x-acme.lineage`.

Extension members MAY appear on the document root and on any Course, Unit, Lesson, Item, or Question object, and — in vocabulary, arrangement, and glossary documents — on any category, tag, objective, alignment, reference, or glossary entry. They MUST NOT be added to objects whose schema declares `additionalProperties: false` (in 1.0, the `matching` pair/category entries and `placement` entries), because those objects are closed by contract and would fail validation.

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

LC-JSON 1.1 is additive by this definition: its changes are three new artifact types, new optional properties on the course document (publication metadata at the root; `glossaryRefs` at course/unit/lesson), and new enum values. Every conforming 1.0 document validates unchanged under the 1.1 schemas with unchanged meaning.

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

**Reminder (§4.6):** `specVersion` never carries an `-rc.N` suffix. Every document targeting the 1.1 contract — whether authored against an rc.N candidate or 1.1 final — declares `specVersion: "1.1"`. The specific publication is identified by `$schema`. For example, a document authored during the 1.1-rc.1 phase looks like:

```json
{
  "$schema":     "https://lc-json.org/1.1-rc.1/subject-collection.schema.json",
  "documentType": "subjectCollection",
  "specVersion":  "1.1",
  ...
}
```

It follows that:

- A document declaring `specVersion: "1.0"` with `$schema` pointing at `/1.0/` MUST validate against the schemas published at `/1.0/`. The 1.0 final release has shipped; `/1.0/` is populated and frozen (§8.3).
- A document declaring `specVersion: "1.0"` with `$schema` pointing at `/1.0-rc.N/` MUST validate against the schemas published at `/1.0-rc.N/` and is not required to validate against `/1.0/`. The rc.N → final transition is an explicit publisher choice (see §8.1, §8.3) — a re-export against the new `$schema` URL — not an automatic upgrade.
- A document declaring `specVersion: "1.1"` MUST validate against the schemas at its declared `$schema` URL. Backward compatibility runs the other way and is defined by consumer obligation, not by cross-schema validation: a 1.1 consumer MUST continue to accept any valid 1.0 document (1.1 adds artifact types and optional fields; it removes nothing a 1.0 document relies on). "Validate a 1.1 document against 1.0 schemas" is not defined — the 1.1 artifact types have no 1.0 schema, and additive fields would fail a strict 1.0 schema.

---

## 9. Deprecation

A field, discriminator value, or shape may be deprecated in a minor version and removed in a subsequent major version.

### 9.1 Deprecation marking

Deprecated fields MUST be marked with `"deprecated": true` in their schema definition and SHOULD include a `description` referencing their replacement.

### 9.2 Producer behavior for deprecated fields

A producer MUST NOT emit deprecated fields in new documents. A producer that re-emits previously-imported documents MAY preserve deprecated fields it received, but SHOULD prefer to emit only the canonical replacement.

### 9.3 Consumer behavior for deprecated fields

A consumer MUST continue to accept deprecated fields for the lifetime of the major version that introduced the deprecation. Removal is permitted only at the next major version bump.

### 9.4 Currently deprecated items

No items are deprecated in 1.0 or 1.1. The specification ships clean.

---

## 10. Conformance Claims

### 10.1 Base LC-JSON conformance

A tool MAY claim conformance to LC-JSON 1.1 as follows:

- **"Conforms to LC-JSON 1.1 as a producer"** — the tool emits documents satisfying §4.
- **"Conforms to LC-JSON 1.1 as a consumer"** — the tool ingests documents satisfying §5, §6, §7, and the accessibility-preservation obligations of §12.1.
- **"Conforms to LC-JSON 1.1"** without qualification — the tool implements both producer and consumer conformance.

Conformance is scoped to the artifact types the tool implements. A tool that implements only Course and QuestionSet MAY claim LC-JSON 1.1 conformance **for those artifact types** — provided it satisfies every applicable requirement, including §5.1's clean rejection of documentTypes it does not implement and §5.2's acceptance of 1.x `specVersion` values on the types it does. A claim SHOULD name its artifact-type scope when it is narrower than the full set (e.g., *"Conforms to LC-JSON 1.1 as a consumer (course, questionSet)"*). A claim without a scope qualifier asserts all five artifact types.

### 10.2 LC-JSON Accessibility Profile conformance (opt-in)

A tool that additionally satisfies the obligations in [`ACCESSIBILITY.md`](ACCESSIBILITY.md) MAY claim:

- **"Conforms to the LC-JSON 1.1 Accessibility Profile as a producer"** — the tool emits documents satisfying §4 plus the producer-side obligations in `ACCESSIBILITY.md` §§2–7.
- **"Conforms to the LC-JSON 1.1 Accessibility Profile as a consumer"** — the tool ingests and renders documents satisfying §5/§6/§7/§12.1 plus the consumer-side MUST-level obligations in `ACCESSIBILITY.md` §§2–8.
- **"Conforms to the LC-JSON 1.1 Accessibility Profile"** without qualification — both producer and consumer.

A consumer claiming the Accessibility Profile MUST satisfy all MUST-level items in `ACCESSIBILITY.md` §§2–8 for its role; partial satisfaction is misclaim. See §12 for the profile's binding text.

### 10.3 Claim accuracy

A tool MUST NOT claim conformance unless it satisfies all applicable MUST requirements. A tool MAY publish self-test results against the conformance test corpus (see `tests/`) as evidence.

Three rules guard against the predictable misclaims:

1. **Producer ≠ consumer.** Claim only the roles the tool actually satisfies; a producer-side conformance claim does not extend to the consumer role without satisfying §5.
2. **The Accessibility Profile is fully bound.** Claiming the Accessibility Profile means every MUST-level item in `ACCESSIBILITY.md` §§2–8 (for the claimed role) is satisfied. Partial profile claims are misclaim.
3. **LC-JSON does not certify WCAG conformance.** The LC-JSON Accessibility Profile provides the wire-format affordances and consumer-rendering obligations that *enable* WCAG 2.1 AA delivery; a delivering consumer's own WCAG claim (under EN 301 549, DOJ ADA Title II, Section 508, Section 504, or equivalent) is separate and remains the consumer's responsibility.

### 10.4 Suggested wording (informative)

Implementers may use the following short forms for marketing pages, badges, READMEs, and footers. They are advisory — formal claims live in §10.1 and §10.2.

**Tier 1 — Base LC-JSON 1.1 conformance**

| Form | Wording |
|---|---|
| Badge | **LC-JSON 1.1 Compatible** |
| Sentence | *"Reads and writes LC-JSON 1.1 — the open Learning Content JSON specification at lc-json.org."* |
| Formal | *"Conforms to LC-JSON 1.1 as a producer / consumer / producer and consumer."* |

**Tier 2 — LC-JSON 1.1 Accessibility Profile**

| Form | Wording |
|---|---|
| Badge | **LC-JSON 1.1 Accessibility Profile** |
| Sentence | *"Delivers LC-JSON 1.1 content with accessible rendering — keyboard navigation, screen-reader support, captions, language-aware text direction. Conforms to the LC-JSON 1.1 Accessibility Profile."* |
| Formal | *"Conforms to the LC-JSON 1.1 Accessibility Profile as a producer / consumer / producer and consumer."* |

Role qualifiers (`(producer)` / `(consumer)`) SHOULD accompany the badge or sentence when the implementation supports only one role, so readers do not infer capabilities the tool does not provide.

A Tier 2 claim implies Tier 1 (the Accessibility Profile is additive to base conformance); no double-badging is needed.

### 10.5 Trademark

Trademark rights in "LC-JSON" and "Learning Content JSON" are not asserted against conformance claims. Any tool meeting the requirements above MAY freely state its conformance and use the suggested wording in §10.4.

---

## 11. HTML Safety Profile

LC-JSON permits HTML in two fields: `ContentItem.html` and `SignpostItem.customHtml`. The complete normative HTML safety profile — allowed elements, allowed attributes, URL-scheme allowlist, sanitization obligation, link normalization, media handling, and unknown-element handling — is specified in [`HTML_SAFETY.md`](HTML_SAFETY.md). SubjectCollection, CurriculumPack, and Glossary documents carry no HTML-bearing fields; their text fields (`name`, `description`, objective `text`, glossary `definition`, translation values, …) are plain text, and a consumer SHOULD render them as such.

A producer that emits HTML in any HTML-bearing field MUST emit only constructs permitted by `HTML_SAFETY.md` §2 (elements), §3 (attributes), and §4 (URL schemes).

A consumer that renders HTML from any HTML-bearing field MUST sanitize the HTML against `HTML_SAFETY.md` §5 before rendering, MUST normalize `<a target="_blank">` to include `rel="noopener noreferrer"` per §6.1, and MUST strip-while-preserving-text any unknown element per §6.2. A consumer MUST reject any document containing forbidden constructs listed under §8.1 (`<script>`, event handlers, `javascript:`/`vbscript:` URLs, etc.).

`HTML_SAFETY.md` is normative and forms part of LC-JSON 1.1. The split into a separate document reflects its length, not its status.

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

These obligations are part of base LC-JSON conformance; a consumer claiming "Conforms to LC-JSON 1.1 as a consumer" satisfies them. The HTML safety profile (§11 / [`HTML_SAFETY.md`](HTML_SAFETY.md)) explicitly allows `alt`, `<track>`, `lang`, and `dir` on every applicable element class to make this preservation possible.

Base conformance is **preservation only**: it never requires a producer to *author* accessibility content (alt text, captions, transcripts). A small or non-institutional producer is therefore never non-conforming for omitting them — the reference validator surfaces omissions as non-blocking warnings. The obligation to *author* accessibility content is part of the opt-in Accessibility Profile (§12.2). The two-layer split is intentional: accessibility information is never silently stripped or ignored on read/write (base), while the heavier "the content must actually be accessible" bar is opt-in for the products — typically institutional, or those with legal or marketing accessibility commitments — that need it.

### 12.2 The Accessibility Profile (opt-in)

The accessibility profile defined in [`ACCESSIBILITY.md`](ACCESSIBILITY.md) — alt-text requirements, video caption obligations for instructional content, keyboard alternatives for structured-task question types, non-color feedback, language-aware rendering, accessible reserved-type placeholders, and validator severities — is bound by an opt-in claim (§10.2).

- A consumer claiming the Accessibility Profile MUST satisfy the structured-task keyboard alternatives (`ACCESSIBILITY.md` §4), the non-color-feedback obligations (§5), the language/`dir` rendering obligations (§6), and the reserved-type placeholder accessibility (§7).
- A producer claiming the Accessibility Profile MUST emit the producer-side authoring obligations across `ACCESSIBILITY.md` §§2–7. These include, at minimum: `alt` on every `<img>` (§2.1); `<track>` captions on prerecorded instructional video carrying speech, **plus a transcript** for that video, and a transcript for prerecorded audio-only instructional content (§3.1); and root `language` matching the delivery language (§6). These authoring MUSTs apply only under a Profile claim — they are not base-conformance obligations (§12.1).
- Tools that satisfy preservation (§12.1) but not delivery (§12.2) are conforming LC-JSON consumers but are NOT conforming Accessibility Profile consumers, and MUST NOT claim the latter.

### 12.3 Relationship to WCAG

WCAG governs rendered user experiences; LC-JSON governs portability and metadata preservation. A consumer claiming the LC-JSON Accessibility Profile carries the wire-format affordances and consumer-rendering obligations that WCAG 2.1 AA delivery requires (alt text, captions, language/direction, textual feedback, keyboard alternatives); the consumer's own jurisdictional WCAG conformance claim (under EN 301 549, DOJ ADA Title II, Section 508, Section 504, or equivalent) remains separate and is the consumer's responsibility, not LC-JSON's.

A tool MUST NOT claim WCAG 2.1 AA conformance by virtue of LC-JSON Accessibility Profile conformance alone. LC-JSON does not certify WCAG conformance.

`ACCESSIBILITY.md` is normative for tools claiming the Accessibility Profile and forms part of LC-JSON 1.1 in that capacity. The split into a separate document reflects the opt-in scope, not a lesser status.

---

## 13. Localization and language

LC-JSON 1.x is **single-language-per-document**. A document declares one delivery language in the root `language` field; multiple languages are delivered as multiple documents, not as localized field bundles within one document. The full model — the distinct roles of `language` (delivery), `lang`/`dir` (language of parts), and `supportLanguage` (the optional pedagogical L1 layer), the accepted language-tag forms, and the expectations around assistive-technology pronunciation — is specified in [`LOCALIZATION.md`](LOCALIZATION.md).

Binding requirements (restated here; full detail in `LOCALIZATION.md`):

- A producer **MUST** emit a `language` root field matching the document's delivery language.
- Language-tag values (`language`, `supportLanguage`, HTML `lang`) are BCP 47 tags. Producers SHOULD use the bare ISO 639-1 primary subtag unless a region/script subtag carries meaning; a consumer MAY act on only the primary subtag.
- A producer **SHOULD** mark HTML spans whose language differs from the delivery language with `lang` (and `dir` where script direction differs); a consumer **MUST** preserve `lang`/`dir` through sanitization and round-trip (see §12.1).
- `lang` is the *necessary* affordance for assistive-technology language switching, but correct pronunciation also depends on the end user's screen reader and installed voices — outside the format's control. Emitting `lang` is not optional on that account; it is the floor (`LOCALIZATION.md` §7).

`LOCALIZATION.md` is normative for the obligations it states and informative for the pronunciation-expectations discussion. Where it and this document disagree, this document wins.

The root-`language` producer MUST above (and the §12.1 round-trip obligations on `language`/`supportLanguage`) bind **per document type, for the types that define those fields**: Course, QuestionSet, and Glossary. SubjectCollection and CurriculumPack documents do not carry a root `language` field in 1.1 — omitting it there is not a conformance failure: a vocabulary's member wording is authored in one language as a matter of practice, but the classification it expresses is language-neutral, and the structured `scope` (subject/level/audience/purpose/jurisdiction) is the discovery surface. A future version may add an optional `language` field to the vocabulary types if implementer experience shows the need; producers wanting to record wording language today may use an extension member (§7).

Glossary documents are single-language like courses: the required root `language` names the language of terms, definitions, and examples. Per-entry translation maps (`translations`, `definitionTranslations`, example translations) are **content** — data about the term — not field-level document localization, so they do not breach the single-language rule; the optional root `translationLanguages` array declares their exact language inventory as a checkable claim. Glossaries carry **no** `supportLanguage`: the which-translation-to-display preference belongs to the delivery context (the attached course's `supportLanguage`, or the consumer's knowledge of the user's L1), not to the portable artifact. See [`glossary-reference.md`](glossary-reference.md) §1.

---

## 14. Validation surface

The requirements in this document are enforced across three sites: the 27 JSON Schemas under [`schemas/`](https://github.com/lc-json/specification/tree/main/schemas) in the published tree (23 from 1.0, plus `subject-collection.schema.json`, `curriculum-pack.schema.json`, `glossary.schema.json`, and the shared `publication-fields.schema.json`), the reference validators (the course validator, the vocabulary-document validator covering the §4.9 closure rules and §3.4 identity rules, the Curriculum Pack validator covering the CP-1 … CP-17 step, pacing, checkpoint, coverage, and bundle-closure rules, and the glossary validator covering the gloss rule and translation-inventory rules), and the per-document prose in the companion normative documents ([`HTML_SAFETY.md`](HTML_SAFETY.md), [`ACCESSIBILITY.md`](ACCESSIBILITY.md), [`LOCALIZATION.md`](LOCALIZATION.md)). [`VALIDATION.md`](VALIDATION.md) catalogs every documented rule and tags it with its enforcement tier — *schema-enforced*, *domain-validator-enforced*, or *advisory*. Implementers building consumers, validators, or producer round-trip tests should consult `VALIDATION.md` for the one-map view of what to check.

`VALIDATION.md` is a catalog: it enumerates and tiers the rules whose normative force comes from this document (including the §3.3.1 artifact-type rule families it incorporates), from the schemas, and from the companion normative documents. It introduces no requirements of its own beyond those sources. Where its wording and any of those sources disagree, those sources win.

The four reference validators named above are **non-authoritative reference implementations**. Only this document (including the rule families it incorporates at §3.3.1), the companion normative documents, and the JSON Schemas' constraints are authoritative. A validator's behavior — in any mode, including `--strict` — never defines the conformance contract: where a validator diverges from these sources, the validator is defective and the sources govern.

The three artifact-type reference documents (`subject-collection-reference.md`, `curriculum-pack-reference.md`, `glossary-reference.md`) are **informative** — they explain and illustrate the rules incorporated by §3.3.1 but are not themselves authoritative (§3.3.1).

Schema `description` strings sometimes restate normative requirements (including RFC 2119 keywords) for implementer convenience at the point of use. Those restatements are not independently binding: this document and the JSON Schemas are authoritative, and where a schema description's wording diverges from this document, this document wins; where the schema's *constraints* apply, they bind as stated in §5.1. The schema's *constraints* (types, patterns, `required`, enums) are binding as stated in §5.1.

---

## 14a. Security and privacy considerations (informative)

LC-JSON documents are content, and 1.1 widens what they can carry: external URLs (`canonicalUrl`, `officialSourceURI`-style alignment ids, glossary `audioUrl`/`imageUrl`), whole embedded documents (pack bundles, the course `glossaries[]` pool), globally portable identifiers, and preserved unknown fields. Implementers should hold four postures:

- **URLs are references, never instructions.** A consumer SHOULD NOT dereference document-carried URLs automatically without a policy the deploying institution controls (allowlists, user gesture, or no fetching at all). `canonicalUrl` and alignment ids are provenance to *display*, not endpoints to call; media URLs are resolved subject to the consumer's own content policy. Nothing in LC-JSON conformance requires network access.
- **Embedded documents are untrusted input.** A bundle's `embedded` block and a course's `glossaries[]` pool are imports like any other: validate each embedded document under its own rules before use, and apply the full `HTML_SAFETY.md` sanitization to any HTML-bearing field regardless of how the document arrived.
- **Portable artifacts carry no person data.** LC-JSON documents describe learning content, never learners: no learner identities, progress, grades, or contact data belong in any field of a portable artifact (grading *policy* fields like `passMarkPercent` are content; grade *records* are not). §4.11 already excludes commerce data; the same posture applies to personal data. `authors` is public display credit a contributor chose to assert.
- **Extensions inherit the same duty.** `x-` members are preserved verbatim across tools and jurisdictions (§7.4); a producer SHOULD NOT place personal data or secrets in extension members, precisely because faithful consumers will carry them everywhere the document goes.

This section is informative: it creates no new conformance requirements, but implementers claiming conformance should expect deployers to ask these questions.

---

## 15. References

- [RFC 2119 — Key words for use in RFCs to Indicate Requirement Levels](https://www.rfc-editor.org/rfc/rfc2119)
- [RFC 8174 — Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words](https://www.rfc-editor.org/rfc/rfc8174)
- [RFC 4122 — A Universally Unique IDentifier (UUID) URN Namespace](https://www.rfc-editor.org/rfc/rfc4122)
- [RFC 3986 — Uniform Resource Identifier (URI): Generic Syntax](https://www.rfc-editor.org/rfc/rfc3986)
- [BCP 47 — Tags for Identifying Languages](https://www.rfc-editor.org/info/bcp47)
- [JSON Schema Draft 7](https://json-schema.org/draft-07/schema)
- LC-JSON HTML safety profile: [`HTML_SAFETY.md`](HTML_SAFETY.md)
- LC-JSON accessibility profile: [`ACCESSIBILITY.md`](ACCESSIBILITY.md)
- LC-JSON localization and language model: [`LOCALIZATION.md`](LOCALIZATION.md)
- LC-JSON validation surface (informative): [`VALIDATION.md`](VALIDATION.md)
- LC-JSON glossary (informative): [`GLOSSARY.md`](GLOSSARY.md)
- LC-JSON schemas: [`schemas/`](https://github.com/lc-json/specification/tree/main/schemas)
- LC-JSON examples: [`examples/`](https://github.com/lc-json/specification/tree/main/examples)
- LC-JSON conformance test corpus: [`tests/`](tests/)
- LC-JSON glossary reference: [`glossary-reference.md`](glossary-reference.md)
- LC-JSON subject-collection reference: [`subject-collection-reference.md`](subject-collection-reference.md)
- LC-JSON curriculum-pack reference: [`curriculum-pack-reference.md`](curriculum-pack-reference.md)

---

## Appendix A — Changes from 1.0 (informative)

LC-JSON 1.1 is additive per §8.2. The complete change list:

1. **Three new artifact types.** `subjectCollection` (vocabulary: tags + learning objectives with structured scope), `curriculumPack` (arrangement: sequence/pacing/checkpoints referencing a collection plus content), and `glossary` (content: a flat term list with pronunciation, translations, examples). New schemas `subject-collection.schema.json`, `curriculum-pack.schema.json`, and `glossary.schema.json`; `documentType` gains the three values (§3.2, §3.3, §4.2).
2. **Member identity and membership.** New §3.4 (immutable member ids; display is never identity; the same **collection-member** id in another document is the same member, while glossary entry identity is document-scoped as `(glossary globalId, entry id)`; tags many-membership, objectives and glossary entries single-owner), §4.9 (collection closure + carried copies in course documents), and §5.7 (consumer reconciliation: no duplication, membership recording for tags, link-never-overwrite for objectives, ownership resolution from ingested claims, entry reconciliation on glossary re-import, verbatim creation of absent members, identity-less rejection, display-collision handling).
3. **Alignment claims.** New §4.10: `externalAlignments[]` with claim types `references` / `alignedTo` / `covers`; `assesses` and `verifiedBy` reserved; forward-compatible consumer handling in §5.5.
4. **Publication metadata.** New §4.11: optional `license`, `canonicalUrl`, and `derivedFrom[]` on the distributable types (Course, SubjectCollection, CurriculumPack, Glossary), added to the course root as plain optional top-level fields (composition via the shared [`publication-fields.schema.json`](https://lc-json.org/1.1-rc.1/publication-fields.schema.json)). QuestionSet excluded by role. Commerce data stays out of LC-JSON.
5. **Glossary attachment.** Optional `glossaryRefs` arrays on the course root, units, and lessons — plain glossary `globalId` strings whose *placement* encodes scope (nearest attachment wins; junctions stop at Lesson) — plus an optional root `glossaries[]` pool carrying a whole-document copy of each referenced glossary, identity verbatim, for single-file self-containment (§4.9). A ref that resolves to no pool copy and no held document is legal and consumer-surfaced, never an import failure (see [`glossary-reference.md`](glossary-reference.md) §4 and [`course.schema.json`](https://lc-json.org/1.1-rc.1/course.schema.json)).
6. **Unimplemented-artifact-type handling.** §5.1 addition: clean rejection naming the unsupported type; §10.1 addition: conformance claims scoped per artifact type.
7. **Extension surface.** §7.1 extended to the vocabulary/arrangement/glossary objects.
8. **No other changes.** Question types (implemented and reserved), item types, HTML safety, the Accessibility Profile, and the localization model are unchanged from 1.0. Course/QuestionSet `tags` remain free wire strings — the opaque member ids of collections do not replace them; an optional member-id reference alongside the string arrays is reserved for future coordination.
