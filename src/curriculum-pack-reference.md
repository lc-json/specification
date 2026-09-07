# Curriculum Pack Reference (LC-JSON 1.1)

**Last updated:** 2026-09-07

> **Status: Informative.** This document explains and illustrates the CurriculumPack artifact type. The binding requirements are in [`NORMATIVE.md`](NORMATIVE.md) (§3.3.1 incorporates the **CP-1 … CP-17** rule family) and the JSON Schemas; the rules are enumerated and tiered in [`VALIDATION.md`](VALIDATION.md) §16. Where this document differs from NORMATIVE.md, the schemas, or the VALIDATION.md catalog, those sources govern.

### For educators and curriculum teams — *informative*

**What it is:** A portable scheme of work — what to teach, in what order, at roughly what pace, and which learning objectives the plan covers. It can begin as an outline and be linked to the finished materials later.

**Use it when:** you want to lay out a term's or a year's teaching against a set of objectives, kept separate from the specific materials.

**Not to be confused with:** a Course — a Curriculum Pack *arranges* learning content; a Course *contains* it.

**See it:** [a minimal Curriculum Pack](https://lc-json.org/examples/curriculum-pack-manifest.json).

*The technical reference begins below.*

An LC-JSON (Learning Content JSON) **CurriculumPack** (`documentType: "curriculumPack"`) is an **arrangement**: it
sequences and paces content against a vocabulary. Where a SubjectCollection says *what
the concepts and objectives are*, and courses say *what the learning content is*, a pack
says *how a program fits together*: which collection scopes it, which content documents
it draws on, in what order, at what pace, with what assessment checkpoints.

Two properties distinguish a pack from a prose scheme of work:

- **Calendar-relative, never calendar-absolute.** Steps are located by
  `year / term / weekOfTerm`, never by real dates. Term calendars vary by institution
  and hemisphere; consumers map relative pacing onto their own calendar.
- **The plan is machine-checkable.** Because steps reference vocabulary member ids,
  a validator can verify sequencing claims ("nothing is assessed before it is taught")
  and, against the referenced collection, coverage claims ("every objective in scope is
  taught at least once").

## 1. Document shape

```json
{
  "$schema": "https://lc-json.org/1.1/curriculum-pack.schema.json",
  "documentType": "curriculumPack",
  "specVersion": "1.1",
  "globalId": "0d1f4a7e-6f2b-4c1e-9a3d-2b8c5e7f9a01",
  "version": "1.0.0",
  "title": "B2 Adult ESL — 12-Week Speaking & Grammar Pack",
  "packMode": "manifest",
  "license": "unspecified",
  "collectionRefs": [
    { "globalId": "b2-adult-esl", "version": "1.2.0" }
  ],
  "contentRefs": [
    { "type": "course", "id": "3e6f9a2c-1b4d-4e7f-8a90-5c2d7e1f3b45", "version": "2.1" }
  ],
  "pacing": { "years": 1, "termsPerYear": 1, "weeksPerTerm": [12], "lessonsPerWeek": 2 },
  "coverage": {
    "collectionGlobalId": "b2-adult-esl",
    "assertions": ["everyObjectiveTaughtAtLeastOnce"]
  },
  "sequence": [
    {
      "id": "w01",
      "kind": "teaching",
      "label": "Narrative tenses in speaking",
      "year": 1, "term": 1, "weekOfTerm": 1, "durationLessons": 2,
      "objectiveIds": ["9c1b5e7f-…"],
      "contentRef": { "type": "course", "id": "3e6f9a2c-…", "selector": "unit:5a2d…" }
    }
  ]
}
```

Root fields beyond the common envelope (`$schema`/`documentType`/`specVersion`,
identity, title, publication metadata):

| Field | Req | Meaning |
|---|---|---|
| `packMode` | MUST | `"manifest"` or `"bundle"` — see §2 |
| `collectionRefs[]` | MUST (may be empty) | vocabulary source(s) — see §3 |
| `contentRefs[]` | MUST (may be empty) | content bill of materials — see §3 |
| `pacing` | MUST when `sequence[]` is non-empty | the calendar frame — see §5 |
| `coverage` | MAY | the declared, checkable coverage contract — see §6 |
| `recyclingPolicy` | MAY | spaced-revisit policy — see §7 |
| `sequence[]` | MUST (may be empty) | the ordered plan — see §4 |

## 2. `packMode` — one type, two serializations

| Mode | Meaning | Typical use |
|---|---|---|
| `"manifest"` | References by id only. The pack is resolvable only where the referenced documents are available. | Authoring source; institutional catalogs; version control. |
| `"bundle"` | Every reference resolved and embedded. Each embedded resource preserves its own identity (root `globalId`, or a course/questionSet's `sourceCourseId` / `sourceQuestionSetId`), `version`, and provenance. | Distribution; offline delivery; archival. |

A bundle is a *packaging* of the same pack, not a different document: bundling MUST NOT
re-mint any embedded document's identity (its root `globalId` or source-side id) or any
vocabulary member's id. A consumer
importing a bundle applies the ordinary per-document rules to each embedded resource
(courses under the course rules; collections under NORMATIVE §5.7) and then the pack
structure over them.

A bundle carries its resolved resources in a root `embedded` object:

```json
"embedded": {
  "collections": [ { "documentType": "subjectCollection", "globalId": "…", "…": "…" } ],
  "content":     [ { "documentType": "course", "sourceCourseId": "…", "…": "…" } ]
}
```

- A manifest MUST NOT carry `embedded`.
- In a bundle, every `collectionRefs[]` entry MUST resolve to an embedded
  `subjectCollection`, and every `contentRefs[]` entry (and therefore every bound step —
  §4.3) MUST resolve to an embedded document of the matching `documentType`. The refs
  remain the bill of materials; `embedded` is their payload.
- An embedded document nothing in the pack references is advisory-flagged (a
  "stowaway"), as is a ref whose pinned `version` differs from the embedded document's
  version — bundling tools SHOULD surface drift rather than silently substitute.

### 2.1 Completeness is an axis, not a type

A pack whose steps carry no content bindings yet (`contentRef: null` throughout) is a
**blueprint**: the plan alone — sequencing, pacing, and checkpoints — with each step an
authoring slot. As slots are filled the same document becomes a working **manifest**, and
a fully resolved manifest can be packaged as a **bundle**. All three are one schema at
different depths of completion; validators SHOULD report completeness (filled slots /
total slots) rather than treat emptiness as an error.

## 3. References

- `collectionRefs[]` — `{globalId, version}` of the SubjectCollection(s) providing the
  pack's vocabulary. At least one is expected in practice; the schema does not require it
  (a pure sequencing pack over already-classified content is representable).
- `contentRefs[]` — `{type, id, version}` of content documents. `type` is the
  referenced **content document's** `documentType`, from a **producer-closed set**:
  `"course"`, `"questionSet"`, or `"glossary"`. It MUST NOT be `"curriculumPack"` (a pack
  is an arrangement, not embeddable content — 1.1 defines no pack-in-pack nesting) or any
  other value; a SubjectCollection is referenced through `collectionRefs`, not here. The
  vocabulary binds producers only and — like the alignment-claim vocabulary (§5.8) — is
  deliberately left schema-open, so a consumer meeting an unrecognized `type` preserves the
  reference rather than rejecting the document. `id` is the referenced document's **type-directed portable
  identity** (NORMATIVE §4.4, "Document identity by artifact type"): a course's
  `sourceCourseId`, a questionSet's `sourceQuestionSetId`, or a glossary's root
  `globalId` (the three content types a `contentRef` may target; a SubjectCollection is
  referenced via `collectionRefs`, never here). Type-directed because those artifact types identify
  themselves by different fields — a course and a questionSet carry a source-side id,
  not a root `globalId`. A pack MAY reference a `questionSet` this way: question sets
  remain lightweight referencable content resources, not distribution-governed ones (they
  carry no publication block; see NORMATIVE §4.11).

  Because `sourceCourseId` / `sourceQuestionSetId` are only *SHOULD*-emitted, **a pack
  cannot reference a Course or QuestionSet that omits its source-side id** — and a pack
  that names one is non-conforming (the pack is at fault, not the referenced document;
  NORMATIVE §4.4). In practice source authoring tools mint these ids on creation, so a
  course prepared for inclusion in a program already carries one; a bare hand-authored
  file must be given a `sourceCourseId` before a pack can bind it.

`contentRefs[]` is the pack's **bill of materials**: one place to resolve, version-pin,
and license-audit everything the plan binds. Every non-null step `contentRef` (§4.3) MUST
appear in it with a matching `type`.

Version pinning: refs SHOULD carry the `version` the pack was authored against.
A consumer holding a *newer* version of a referenced document MAY offer it, but SHOULD
surface the mismatch rather than silently substituting.

## 4. `sequence[]` — the plan

`sequence[]` is the pack's ordered plan: an array of **steps**, each one unit of work on
a calendar-relative timeline. The array MUST be present (possibly empty — an empty plan
is a valid, if immature, pack). Consumers MUST preserve unrecognized *fields inside* a
step verbatim across read/write cycles (the NORMATIVE §5.5 additive posture); the step
shape itself is firm as of 1.1.

### 4.1 The step object

```json
{
  "id": "y1.t1.w03",
  "kind": "teaching",
  "label": "Gettier cases",
  "year": 1, "term": 1, "weekOfTerm": 3, "durationLessons": 6,
  "objectiveIds": ["edeba475-…"],
  "tagIds": ["32d2f4f2-…"],
  "contentRef": null,
  "authoringNote": "Two original counterexamples, then the fake-barn variant.",
  "dependsOn": ["y1.t1.w02"],
  "checkpoint": null
}
```

| Field | Req | Type / rules |
|---|---|---|
| `id` | MUST | non-empty string, unique within the pack. **Document-local**: step ids are plan labels, never vocabulary member ids, and never leave the pack. A `y{year}.t{term}.{slot}` convention is common but carries no meaning |
| `kind` | MUST | `"teaching"` \| `"review"` \| `"assessment"` \| `"mock"` \| `"buffer"` — see §4.2 |
| `label` | MUST | non-empty display string (a plan label, not learner-facing prose) |
| `year` | MUST | integer ≥ 1; ≤ `pacing.years` |
| `term` | MUST | integer ≥ 1; ≤ `pacing.termsPerYear` |
| `weekOfTerm` | MUST | integer ≥ 1; ≤ `weeksPerTerm[term-1]` when `weeksPerTerm` is declared |
| `durationLessons` | MUST | integer ≥ 1 — the step's length in lessons |
| `objectiveIds[]` | MUST (may be empty) | collection objective member ids. Semantics vary by kind: teaching = *first-teach or re-teach*; review = *revisit*; assessment/mock = *context for the checkpoint* |
| `tagIds[]` | MAY | collection tag member ids (topic/skill focus); default `[]` |
| `contentRef` | MUST (key always present) | `null` (an unauthored slot) or a content binding — see §4.3 |
| `authoringNote` | MAY | author-facing guidance, typically what belongs in an unfilled slot; never learner-visible |
| `dependsOn[]` | MAY | step ids of prerequisite steps; default `[]` — see §4.4 |
| `checkpoint` | conditional | MUST be an object when `kind` is `assessment`/`mock`; MUST be `null` or absent otherwise — see §4.5 |

**Key presence.** The `contentRef` key MUST be present on every step even when its value
is `null` — a null slot is meaningful (blueprint posture, §2.1), and its absence is an
error, so producers whose serializers drop null values must exempt this key. `checkpoint`
is the opposite: on kinds that must not carry one, `null` and an absent key are
equivalent, and producers MAY omit it.

What a step deliberately does NOT carry: real dates (§5 is calendar-relative); objective
or tag *wording* (ids only — wording lives in the collection); per-step license/authors
(the pack-level publication block covers the plan); learner-facing prose (content
documents own that; a pack arranges, it never writes lessons).

### 4.2 `kind` — the five step kinds

| kind | Meaning | objectiveIds | checkpoint |
|---|---|---|---|
| `teaching` | First-teach (or deliberate re-teach) of the listed objectives | SHOULD be non-empty (advisory when empty) | MUST be null/absent |
| `review` | Spaced revisit of *already-taught* objectives (§7) | MUST list only objectives first taught strictly earlier | MUST be null/absent |
| `assessment` | A checkpoint event (formative or summative) | context only | MUST be present |
| `mock` | A full-exam rehearsal: a summative checkpoint in exam format | context only (often empty) | MUST be present, with `kind: "summative"` |
| `buffer` | Slack: catch-up, cross-term spillover, induction/administrative weeks | MAY be empty | MUST be null/absent |

The checkpoint-iff-assessment/mock rule is deliberately strict: it keeps "where are the
checkpoints?" answerable by filtering on `kind`, and it stops checkpoints hiding inside
teaching steps where coverage tooling would miss them.

### 4.3 `contentRef` — the content binding (and the authoring slot)

- `null` — an unauthored **slot** (blueprint posture). The step SHOULD carry an
  `authoringNote` saying what belongs there (advisory; `buffer` steps excepted).
- Filled — `{type, id, version?, selector?}`:
  - `type`/`id`/`version` follow the root `contentRefs[]` rules (§3), and the
    referenced document MUST also appear in root `contentRefs[]` with a matching `type`;
  - `selector` (optional) points *inside* the referenced document, at a **node** (Unit /
    Lesson / Item), which — unlike the document root — always carries a `globalId`. The
    grammar is therefore **node-globalId-bearing**: `"unit:<globalId>"`,
    `"lesson:<globalId>"`, or `"item:<globalId>"` for courses. (Only the document root's
    identity is type-directed via `id`; interior nodes are unaffected.) A selector never
    addresses by title or position, so it survives re-ordering and renaming. Omitted or
    `null` = the whole document.
- In a bundle, every non-null `contentRef` must resolve into `embedded` content (§2).

### 4.4 Timeline and dependencies

- The timeline sort key is `(year, term, weekOfTerm)`. Ties are allowed — parallel
  strands within a week are real (a skills drill alongside a content unit).
- **Within a week, document order is the schedule.** `sequence[]` SHOULD be serialized
  in timeline order (advisory when it is not); between weeks the sort key is
  authoritative, but *within* a week the array order is load-bearing and consumers MUST
  preserve it.
- A `dependsOn` edge MUST point at an existing step that is **strictly earlier** in the
  timeline, **or** in the **same week and earlier in document order**. Self-references
  and backward edges (a later week, or the same week but later in the array) are errors.
  Acyclicity requires no separate check: `(sort key, document position)` is a strict
  total order and every valid edge points backward in it.
- The common case needs no edge at all: a week's several classes are usually *one* step
  whose internal lesson order lives in the bound course, not in the plan. Dependencies
  record genuine prerequisites, typically across weeks.

### 4.5 `checkpoint` — the assessment object

Carried by steps of kind `assessment` or `mock`, and only those:

```json
"checkpoint": {
  "kind": "formative",
  "format": "12-mark question",
  "assessesObjectiveIds": ["edeba475-…", "2e1bdfc6-…"],
  "scope": "listed"
}
```

| Field | Req | Rules |
|---|---|---|
| `kind` | MUST | `"formative"` (informs teaching; low stakes) or `"summative"` (measures attainment). A `mock` step's checkpoint MUST be `"summative"` |
| `format` | MUST | non-empty display text describing the instrument ("12-mark question", "full Paper 1 (100 marks, 3 hours)"). Display, not identity — consumers MUST NOT parse it |
| `assessesObjectiveIds[]` | MUST | collection objective member ids this checkpoint measures. With `scope: "listed"` it MUST be non-empty, and every id MUST be first taught strictly earlier in the timeline |
| `scope` | MAY | `"listed"` (default) or `"allTaughtToDate"` |

`scope: "allTaughtToDate"` declares that the checkpoint assesses **every objective first
taught by any strictly earlier step** — the terminal-mock semantic ("full Paper 1"),
where hand-enumerating ids would rot as the plan grows. With this scope,
`assessesObjectiveIds` MUST be `[]`: the effective set is computed, never stated, so two
sources of truth cannot drift.

The assessment *content* (the actual paper or question set) is simply the step's
`contentRef` — checkpoints need no second content slot. In a blueprint the instrument is
an authoring slot like any other.

Sequencing rules across checkpoints and reviews:

- **Never assess the untaught** (error): every listed assessed objective must be first
  taught (appear in a `teaching` step's `objectiveIds`) strictly earlier in the timeline.
- **Review-before-teach** (error): every objective on a `review` step must be first
  taught strictly earlier.
- **Formative-before-summative** (advisory): an objective reaching a summative
  checkpoint having never passed a formative one is flagged — usually an oversight,
  occasionally intentional.
- **Dead checkpoint** (advisory): a checkpoint whose effective assessed set is empty.

## 5. `pacing` — the calendar frame

Required whenever `sequence[]` is non-empty (an unpaced plan is not checkable):

```json
"pacing": {
  "years": 2,
  "termsPerYear": 3,
  "weeksPerTerm": [13, 11, 11],
  "lessonsPerWeek": 3,
  "teachingWeeksPerYear": 35,
  "note": "free text for authors and consumers"
}
```

| Field | Req | Rules |
|---|---|---|
| `years` | MUST | integer ≥ 1 |
| `termsPerYear` | MAY | integer ≥ 1; default **3** |
| `weeksPerTerm` | MAY | array of `termsPerYear` integers ≥ 1 — teaching weeks per term, applying to every year (uniform years is the deliberate 1.1 simplification) |
| `lessonsPerWeek` | MUST | integer ≥ 1 |
| `teachingWeeksPerYear` | MAY | integer ≥ 1; when both are present it MUST equal `sum(weeksPerTerm)` |
| `note` | MAY | string |

The frame makes pacing arithmetic mechanical. With `weeksPerTerm` declared:

- **Term capacity** (error): for every `(year, term)`, the sum of its steps'
  `durationLessons` MUST NOT exceed `weeksPerTerm[term-1] × lessonsPerWeek`.
- **Span** (error): a step modeled as occupying `ceil(durationLessons / lessonsPerWeek)`
  weeks from `weekOfTerm` MUST NOT run past the end of its term.
- **Week occupancy** (advisory): any single week whose summed lessons exceed
  `lessonsPerWeek` is flagged — parallel strands can legitimately share weeks unevenly,
  so the term-level bound is the hard rule and the week-level one a hint.

## 6. `coverage` — the declared, checkable contract

```json
"coverage": {
  "collectionGlobalId": "b2-adult-esl",
  "assertions": ["everyObjectiveTaughtAtLeastOnce", "everyObjectiveAssessedAtLeastOnce"],
  "exemptObjectiveIds": [],
  "note": "free text"
}
```

- `collectionGlobalId` — MUST be non-empty and MUST appear in `collectionRefs[]`.
- `assertions[]` — the 1.1 vocabulary is exactly two values:
  - `everyObjectiveTaughtAtLeastOnce` — every in-scope objective appears in some
    `teaching` step's `objectiveIds`;
  - `everyObjectiveAssessedAtLeastOnce` — every in-scope objective appears in some
    checkpoint's effective assessed set (§4.5).
  Unknown assertion strings are an **error** — a contract that cannot be checked is not
  a contract.
- `exemptObjectiveIds[]` — objectives deliberately out of the pack's scope (e.g., a
  half-course pack over a full collection). Exemptions apply to every assertion.

Coverage is *declared*, not implied: a validator could always check everything, but packs
legitimately vary — a one-term taster pack should not fail "everything taught." Declaring
the contract in-document makes the pack's claim portable: any consumer holding the
referenced collection can re-verify it. Absent the collection, validators SHOULD skip
member-resolution and coverage checks visibly rather than fail.

## 7. `recyclingPolicy` — spaced revisits

Revisiting is expressed structurally, not by a flag: a step of `kind: "review"` lists
previously-taught objectives in its `objectiveIds`. The optional root block tunes the
spacing check:

```json
"recyclingPolicy": { "minSpacingWeeks": 3 }
```

A review revisiting an objective first taught fewer than `minSpacingWeeks` **absolute**
weeks earlier is advisory-flagged (default **2** when the block is absent) — spacing is
the point of spaced revisiting, and a next-week "revisit" is really still first-teach.
*Absolute weeks* are positions on the whole-pack week line
(`(year−1) × teachingWeeksPerYear + weeks elapsed in prior terms + weekOfTerm`), so
spacing is measured across term and year boundaries, where spaced revisits actually
live. When the week line is under-specified — `weeksPerTerm` absent — validators
compute spacing on a **stated approximation** of term lengths (the reference
implementation documents its formula) rather than skipping; the check is advisory
tier, so an approximated week line is acceptable, but validators SHOULD say when they
are approximating.

What stays out of the pack, deliberately: grading models (pass marks, boundaries,
weightings are consumer/instructor territory — the pack says *what is assessed when*,
never *how it is scored*); learner progress state (runtime data, never document
content); auto-generated revision schedules (a consumer MAY derive one from the
taught-weeks and the spacing policy; the document carries only the authored plan).

## 8. Validation

The rule catalog for packs is in VALIDATION.md (CP-* rules), split as elsewhere into
schema-enforced shape, domain-validated semantics (sequencing, capacity, dependency
direction, checkpoint discipline, bill of materials, bundle closure), and advisory
hygiene. The reference tooling's pack validator implements the full catalog and, on
success, reports **maturity**: step counts by kind, filled/total content slots, capacity
utilization per term, and coverage tallies — the intended authoring feedback loop for
the blueprint → manifest → bundle progression (§2.1).

## 9. Publication metadata

Packs are distributable and carry the same optional publication fields as courses and
collections (NORMATIVE §4.11): `license`, `canonicalUrl`, `derivedFrom[]` alongside
`authors`/`version`. License posture note: a bundle embeds third-party resources — its
own `license` speaks for the arrangement, and `"mixed"`/`"seeComponents"` values signal
that embedded resources carry their own terms.

## 10. Relationship to the other types (informative)

```
SubjectCollection (vocabulary)   what the concepts/objectives ARE
        ↑ collectionRefs
CurriculumPack (arrangement)     how a program fits together
        ↓ contentRefs
Course / QuestionSet / Glossary (content)   what learners actually work through
```

A consumer with no pack support loses nothing about the content documents themselves —
packs add coordination, never meaning that content documents depend on packs (the NORMATIVE
§7.3 additive spirit, applied at document scale). Conversely, consumers can adopt packs
at any depth: catalog display only (title + references), plan rendering (the §4 timeline
as a scheme of work), plan-driven scaffolding (materializing the structure into a
course), or full pacing-aware delivery. Each is a legitimate consumption depth; the
document is the same.
