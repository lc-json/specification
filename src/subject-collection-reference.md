# Subject Collection Reference (LC-JSON 1.1)

**Last updated:** 2026-07-22

> **Status: Informative.** This document explains and illustrates the SubjectCollection artifact type. The binding requirements are in [`NORMATIVE.md`](NORMATIVE.md) (§3.3.1 incorporates the **SC-1 … SC-14** rule family, plus §3.4, §4.9, §4.10, §4.11) and the JSON Schemas; the rules are enumerated and tiered in [`VALIDATION.md`](VALIDATION.md) §15. Where this document differs from NORMATIVE.md, the schemas, or the VALIDATION.md catalog, those sources govern.

### For educators and curriculum teams — *informative*

**What it is:** A shared list of the topics, skills, and learning objectives a subject covers — the common curriculum language several courses can classify against instead of re-typing or renaming it in every file.

**Use it when:** a department wants its courses to describe their content against one agreed set of objectives and topics.

**Not to be confused with:** a Glossary — a Subject Collection describes how educators *classify* learning; a Glossary holds the words and meanings learners *study*.

**See it:** [a minimal Subject Collection](https://lc-json.org/examples/subject-collection-minimal.json).

*The technical reference begins below.*

An LC-JSON (Learning Content JSON) **SubjectCollection** (`documentType: "subjectCollection"`) is a reusable classification
**vocabulary**: the tags and learning objectives for a structured
`(subject, level, audience, purpose, jurisdiction)` scope, packaged as one portable
document. It carries no learner-facing content — it classifies and describes the content
that courses deliver.

Collections exist to make three things portable that free-text tagging cannot:

1. **Shared concepts.** A tag is a stable member with an immutable id; the same id in two
   documents *is the same concept*. Two independently-authored courses tagged with member
   `X` are comparably classified — enabling cross-course search, curriculum mapping, and
   learner-progress analytics keyed on shared ids.
2. **Reusable objectives.** Writing a good can-do objective is expensive. A collection
   owns each objective once; any number of courses reference it (and course documents
   carry copies for portability — see *Carried copies* below).
3. **Scoped curricula.** The structured `scope` plus typed `externalAlignments` let a
   collection say precisely *what it covers and by whose definition* — a national
   curriculum section, an official training catalog entry, an exam specification —
   without re-implementing the external framework.

## 1. Document shape

```json
{
  "$schema": "https://lc-json.org/1.1-rc.1/subject-collection.schema.json",
  "documentType": "subjectCollection",
  "specVersion": "1.1",
  "globalId": "b2-adult-esl",
  "version": "1.2.0",
  "title": "B2 Adult ESL — General English",
  "description": "Vocabulary for general-English courses at CEFR B2 for adult learners.",
  "scope": {
    "subject":      { "scheme": null, "id": "english-language", "label": "English Language" },
    "level":        { "scheme": "CEFR", "id": "B2", "label": "B2" },
    "audience":     [ { "scheme": null, "id": "adult", "label": "Adult" } ],
    "purpose":      [ { "scheme": null, "id": "general", "label": "General English" } ],
    "jurisdiction": null
  },
  "license": "CC-BY-4.0",
  "authors": [ "Example Vocabulary Project" ],
  "canonicalUrl": null,
  "derivedFrom": [],
  "externalAlignments": [
    { "claim": "alignedTo", "scheme": "CEFR", "id": "B2", "label": "CEFR B2 (vantage)" }
  ],
  "categories": [
    { "id": "grammar", "name": "Grammar", "description": null, "sortOrder": 1, "icon": null }
  ],
  "tags": [
    {
      "id": "5f0a1c22-9d84-4a10-9a51-3f36f3a1b001",
      "slug": "grammar:conditionals",
      "name": "Conditionals",
      "description": null,
      "categoryId": "grammar",
      "parentId": null,
      "level": 0,
      "sortOrder": 0,
      "aliases": null,
      "color": null,
      "icon": null,
      "isActive": true
    }
  ],
  "objectives": [
    {
      "id": "9c1b7e40-2f6d-4f7e-8f21-64a4a9b2c002",
      "text": "Can use the second conditional to describe hypothetical situations.",
      "difficultyBand": "Apply",
      "tagIds": [ "5f0a1c22-9d84-4a10-9a51-3f36f3a1b001" ]
    }
  ]
}
```

## 2. Root fields

| Field | Required | Type | Notes |
|---|---|---|---|
| `$schema`, `documentType`, `specVersion` | MUST | — | The root triplet (NORMATIVE §3.2). `documentType` is the literal `"subjectCollection"`. |
| `globalId` | MUST | string | Portable document identity. Immutable; preserved verbatim on import, never re-minted. Opaque; stable human-readable slugs and UUIDs are both conventional. |
| `version` | MUST | string | Content version of this vocabulary (dotted numeric, 1–3 segments). Revisions — rewording, adding members, re-organizing categories — bump `version`; they never change `globalId` or member ids. |
| `title` | MUST | string | Display title. |
| `description` | optional | string \| null | What this vocabulary covers and who it is for. |
| `scope` | MUST | object | Structured scope (§3). `scope.subject` is the only required scope field. |
| `license` | SHOULD (distribution) | string | Publication posture (NORMATIVE §4.11): `"unspecified"` only for private drafts; a concrete license (e.g. `"CC-BY-4.0"`) for anything distributed. |
| `authors` | optional | string[] | Display credits. |
| `canonicalUrl` | optional | string \| null | Where the authoritative copy of this document lives, when one exists. |
| `derivedFrom` | optional | array of `{globalId, version}` | Provenance chain: the document(s) this one was revised or remixed from. |
| `externalAlignments` | optional | array | Typed claims against external frameworks (§6). |
| `categories` | MUST (may be empty) | array | Display buckets for tags (§4). |
| `tags` | MUST (may be empty) | array | Tag members (§4). |
| `objectives` | MUST (may be empty) | array | Objective members (§5). |

## 3. Structured scope

Each populated scope field is a `{scheme, id, label}` object. `scheme` is optional and
names the namespace the `id` comes from (`"CEFR"`, `"US-grade"`, `"UK-KS"`, an exam
board, a ministry code); `scheme: null` means the id is a local/common-usage value.
**There are no closed global enums** — local categories are always representable, and a
scheme-qualified value is always more portable than an unqualified one.

| Scope field | Cardinality | Examples |
|---|---|---|
| `subject` | required, single | `{scheme: null, id: "english-language", label: "English Language"}` |
| `level` | optional, single | `{scheme: "CEFR", id: "B1-B2", label: "B1–B2"}`; `{scheme: "UK-A-Level", id: "a-level", label: "A-Level"}` |
| `audience` | optional, array | adult; upper-secondary; jobseeker-worker |
| `purpose` | optional, array | exam-prep; school-curriculum; vocational; general |
| `jurisdiction` | optional, single | `{scheme: "ISO-3166", id: "ES", label: "Spain"}` |

Consumers SHOULD treat scope as the primary discovery surface (filtering and grouping
collections); they MUST NOT use scope fields for member identity.

## 4. Categories and tags

**Categories** are shared display buckets, not identity: `{id, name, description,
sortOrder, icon}`. Category `id`s are stable slugs; consumers merge categories from
different documents by id (the first-seen display fields win, or the consumer's own
policy applies). Because they are display-level, reusing well-known category ids
(`grammar`, `vocabulary`, `skills`, `functions`) across collections is encouraged —
merged buckets keep multi-collection browsing coherent.

**Tags** are the concept members:

| Field | Required | Notes |
|---|---|---|
| `id` | MUST | The immutable member id (NORMATIVE §3.4). Opaque; UUID RECOMMENDED. |
| `slug` | MUST | Mutable, human-readable lookup key, unique within the document. Convention: lowercase, colon-separated path (`grammar:conditionals:second`). A slug rename is a content revision; identity stays with `id`. |
| `name` | MUST | Display name. |
| `categoryId` | MUST | Resolves within `categories[]` (closure, NORMATIVE §4.9). |
| `parentId` | optional | The **member id** (never the slug) of the parent tag, which must be in this document, and the parent chain must be acyclic (SC-7). Hierarchy is per-document display structure; the member itself is flat and portable. |
| `level`, `sortOrder` | optional | Display ordering hints — advisory data only. `level` restates the depth implied by the parent chain for display convenience; validators do not check it against the chain, and consumers SHOULD derive depth from `parentId` when it matters. |
| `description`, `aliases`, `color`, `icon`, `isActive` | optional | Display and search affordances. Omit or set null when unused. |

**Membership, not ownership.** A tag listed in a collection is a *member of* that
collection; the same tag (same id) may be a member of any number of collections. A
general concept like *work vocabulary* belongs simultaneously to an A2 general-English
collection, a B2 exam-prep collection, and a vocational-English collection — one member,
three memberships. Producers of related collections SHOULD reuse member ids for shared
concepts rather than minting look-alike duplicates; that reuse is what makes the
collections comparable.

## 5. Objectives

| Field | Required | Notes |
|---|---|---|
| `id` | MUST | Immutable member id. |
| `text` | MUST | The can-do statement. Convention: completes "…be able to:" — an active-verb capability, not a topic name. |
| `difficultyBand` | optional | One of `"Recall"`, `"Understand"`, `"Apply"`, `"Analyze"`, or null. |
| `tagIds` | optional | Member ids of this document's tags the objective exercises. Every entry MUST resolve within the document (closure). |

**Single-owner.** Unlike tags, an objective has exactly one owning document — its wording
is scope-specific (the introductory-level phrasing of a capability is a different sentence from the advanced-level
phrasing). Other documents *reference* objectives and carry copies of them (below), but
only the owner revises the wording. To adapt an objective's wording for a different
scope, fork it: mint a new member id and record provenance (document-level `derivedFrom`,
or an extension member for per-member lineage).

**Carried copies.** A course document that assigns collection-owned objectives embeds a
copy of each in its own `objectives[]` pool, member id preserved (NORMATIVE §4.9), so the
course file is self-contained. On import, a consumer that already holds the member links
to it and ignores the copy's wording; a consumer that does not hold it creates it
verbatim (NORMATIVE §5.7). A carried copy is transport, not a fork.

## 6. External alignments

An external alignment is a typed claim that connects the collection to an external framework or
registry, declaring the relationship — `references`, `alignedTo`, or `covers` — in
machine-readable form without embedding or restating the external target's content
(NORMATIVE §4.10). The target need not be an official standard, and the relationship can be as
loose as a plain reference. Alignments are also not limited to academic curricula: the example
below uses the stronger `alignedTo` claim to anchor a collection to an official entry in SEPE's
nationwide *Catálogo de Especialidades Formativas*, the catalog of training specialties within
Spain's National Employment System.

```json
{ "claim": "alignedTo", "scheme": "sepe-especialidad", "id": "SSCE04",
  "label": "Inglés B2 (240 h) — Catálogo de Especialidades Formativas" }
```

| Claim | Meaning |
|---|---|
| `references` | The external item informed this collection or is relevant context. The weakest claim. |
| `alignedTo` | The collection is organized to track the external item's structure/requirements. |
| `covers` | The collection's members span the external item's content. The strongest 1.1 claim. |
| `assesses`, `verifiedBy` | **Reserved** (future version). Producers MUST NOT emit; consumers preserve without interpreting. |

`scheme` + `id` identify the external item in its own registry (a spec code, a statute
identifier, a standards-body URI); `label` is display text. Alignments point — they never
embed the external framework's content.

## 7. Authoring guidance (informative)

- **Mint ids once.** Keep a persistent id registry keyed by a stable authoring key (e.g.
  the slug); regenerate documents freely — members that persist keep their ids, only
  genuinely new members get new ids.
- **Slugs are paths, ids are identity.** Colon-path slugs (`skills:speaking:turn-taking`)
  make vocabularies readable and diffable; nothing may depend on them for identity.
- **Prefer membership to duplication.** Before minting a tag, check whether a related
  collection already has the concept — reuse its id.
- **Wording discipline for objectives.** One capability per objective; active verb;
  testable. Link each objective to the tags it exercises — tag links are what let
  consumers offer "find content practicing this objective."
- **Leave display fields empty rather than filling them with noise.** `description`,
  `icon`, `color`, `aliases` are affordances, not obligations; a null is better than a
  restated name.
- **Scope narrowly, align precisely.** A collection per coherent scope (one level band,
  one purpose) beats a monolith; shared members keep the family connected, and
  `externalAlignments` carry the official anchors.
