# Glossary Reference (LC-JSON 1.1)

**Last updated:** 2026-09-07

> **Status: Informative.** This document explains and illustrates the Glossary artifact type. The binding requirements are in [`NORMATIVE.md`](NORMATIVE.md) (§3.3.1 incorporates the **GL-1 … GL-11** rule family, plus §3.4 member identity) and the JSON Schemas; the rules are enumerated and tiered in [`VALIDATION.md`](VALIDATION.md) §17. Where this document differs from NORMATIVE.md, the schemas, or the VALIDATION.md catalog, those sources govern.

### For educators and curriculum teams — *informative*

**What it is:** A reusable word list for a course, unit, or lesson. In most subjects, an entry is simply a term and its definition. For language teaching and bilingual or multilingual settings, it can also carry part of speech, pronunciation, translations, example sentences, and alternative forms.

**Use it when:** you want a topic's key vocabulary to travel with the course and be reused across its lessons.

**Not to be confused with:** a Subject Collection — a Glossary holds the words and meanings learners *study*; a Subject Collection describes how educators *classify* learning.

**See it:** [a minimal Glossary](https://lc-json.org/examples/glossary-minimal.json).

*The technical reference begins below.*

A **glossary** (`documentType: "glossary"`) is a flat list of **terms** — a vocabulary
list as a portable LC-JSON (Learning Content JSON) file. It is designed
language-education-first: a term can carry pronunciation (IPA, a friendly respelling,
audio), translations, example sentences, and inflected forms — but it serves any subject
(a science course's key words gloss the same way). Field names are chosen for **teacher
readability**: a teacher opening the file in a text editor can read every field name
aloud and know what it means.

Like `questionSet`, a glossary is structurally a lightweight referencable content
document: flat root, stable identity, entries with immutable member ids. Unlike
`questionSet`, it is **distribution-governed**: glossaries are shareable, remixable
artifacts, so they carry the publication field group (`license`, `canonicalUrl`,
`derivedFrom[]` — NORMATIVE §4.11).

## 1. Document shape

```json
{
  "$schema": "https://lc-json.org/1.1/glossary.schema.json",
  "documentType": "glossary",
  "specVersion": "1.1",
  "globalId": "a1-food-vocabulary-en-es",
  "version": "1.0.0",
  "title": "A1 Food Vocabulary (English for Spanish speakers)",
  "language": "en",
  "translationLanguages": ["es"],
  "entries": [
    {
      "id": "0a1b2c3d-…",
      "term": "apple",
      "kind": "word",
      "firstMention": "5a2d81c3-…",
      "partOfSpeech": "noun",
      "definition": "A round fruit with firm flesh and red, green, or yellow skin.",
      "ipa": "/ˈæp.əl/",
      "soundsLike": "AP-uhl",
      "audioUrl": "audio/en/a1/apple.mp3",
      "translations": { "es": "manzana" },
      "otherForms": ["apples"],
      "examples": [
        { "text": "He picked an apple from the tree.",
          "translations": { "es": "Cogió una manzana del árbol." } }
      ],
      "tags": ["topic:food"]
    }
  ]
}
```

`language` (required) is the language of the terms, definitions, and examples.

`translationLanguages` (optional array) is the document's **declared translation
inventory**: the exact set of BCP 47 language keys appearing in any entry's
`translations`, `definitionTranslations`, or example translations. It is a *checkable
claim*, the same posture as a Curriculum Pack's `coverage` block — declared, not
implied — and validators verify it in both directions:

- a translation key in use that the declaration omits is an **error**;
- a declared language that no entry translates into is an **error** (a false claim —
  a catalog reading "es, pt" must not be misled);
- translations present with *no* declaration is only a **warning** (a missing claim is
  not a false one; foreign imports legitimately arrive without the field).

Both directions compare language tags **case-insensitively**, per BCP 47 §2.1.1: a
document declaring `es` and writing the usage key as `ES`, or declaring `pt-BR` and
writing `pt-br`, has a matching inventory and draws neither error. The same
case-insensitive comparison applies to the uniqueness check on the declaration
itself — `["es", "ES"]` declares one language twice, not two languages. The
producer's original spelling is preserved on the wire; only comparison is folded.

An **absent `translationLanguages` and an empty array are equivalent: no claim is
made.** The two ERROR rules above are then vacuous, and translations present without a
declaration draw only the warning — one interpretation, everywhere (prose, schema,
GL rules, validator). Array order MAY be read as preference order by consumers that
must choose a single language to display. There is deliberately **no `supportLanguage` on glossaries**: the
"which one do I show" preference belongs to the delivery context — the attached course's
`supportLanguage` (LOCALIZATION §2.3), or the consumer's knowledge of the user's L1 —
not to the portable artifact. The same glossary attached to an English-for-Spanish
course and an English-for-French course surfaces `es` and `fr` respectively, with no
glossary edit.

### 1.1 Translations are content, not localization

LC-JSON is single-language-per-document, and LOCALIZATION §2.4 deliberately provides no
field-level translation bundles. A glossary does not breach that rule: a term's
`translations` map — and likewise `definitionTranslations` and example translations —
is **content** — data *about the term*, exactly like its `ipa` — not a localized
rendering of the document. The document itself remains one-language; translating the
*glossary* (its title, its own prose) into another delivery language is still done as a
separate document.

Translation maps are keyed by BCP 47 tags (`"es"`, `"pt-BR"`). Keys are data; display
prefixes (`ES: manzana`, `[ES: …]`) are presentation a consumer generates. Because every
translation value arrives with its language in the key, a consumer can always render it
in a correctly `lang`-tagged span (WCAG 3.1.2 Language of Parts) — this is why the keyed
maps replace, rather than supplement, inline `[L1: …]`-style prefixes in glossaries.

## 2. The entry

One entry is one term **in one sense** — the sense the course uses. A word with two
relevant senses is two entries, each with its own immutable `id` (member identity per
NORMATIVE §3.4: mint once, never re-mint, display text is never identity). Entry
identity is **document-scoped**: the identifying key is `(glossary globalId, entry
id)`, ids need be unique only within their glossary, and the same id in a different
glossary is a different entry — cross-document id equality is a collection-member
concept, not a glossary one.

| Field | Req | Meaning |
|---|---|---|
| `id` | MUST | immutable member id |
| `term` | MUST | the term, in the document's `language` |
| `kind` | MAY | `"word"` or `"phrase"` |
| `firstMention` | MAY | GlobalId of the lesson where the term is introduced (§2.1) |
| `partOfSpeech` | MAY | open vocabulary — `"noun"`, `"phrasal verb"`, … |
| `definition` | MAY* | a definition in the document's language |
| `definitionTranslations` | MAY* | BCP 47-keyed renderings of the definition (§1.1) — the keyed-map replacement for inline `[es: …]` gloss prefixes |
| `translations` | MAY* | BCP 47-keyed renderings of the term (§1.1) |
| `examples[]` | MAY | `{text, translations?}` — example sentences, optionally with translated renderings |
| `ipa` | MAY | IPA pronunciation |
| `soundsLike` | MAY | friendly respelling (`"AP-uhl"`) — a companion to `ipa`, never a substitute notation |
| `audioUrl` / `imageUrl` | MAY | pronunciation recording / illustrative image (typically relative URLs; carrying the binary alongside the document is out of scope for 1.1) |
| `otherForms[]` | MAY | inflected/variant forms (`"went"` under *go*) — auto-linking consumers match on these too |
| `tags[]` | MAY | taxonomic display strings, the same colon-namespaced convention as courses |
| `linkAutomatically` | MAY | default `true`; `false` opts the entry out of automatic in-content linking (e.g. a term that appears inside quiz answers) |

**\* The gloss rule (error, at the interchange boundary):** every entry MUST carry **at
least one of**: a `definition`, a `translations` value, or a `definitionTranslations`
value. Any one alone satisfies the rule — the fields are alternatives, not
co-requirements. For learners whose command of the document's `language` is still low
(say, an A1 English course), a translation into a language they already know *is* the
gloss — a definition written in the language being learned would itself need glossing.
In monolingual or subject glossaries the definition carries the load and the document
may contain no translations at all (a French chemistry glossary for French speakers is
complete with definitions only — and then legitimately declares no
`translationLanguages`); an entry with none of the three cannot be glossed, carded, or
popovered.

The gloss rule is a **producer-conformance rule at the interchange boundary**: a
producer MUST NOT *emit* (export, publish, distribute) a glossary containing an entry
that violates it. Authoring tools MAY hold work-in-progress state that would violate it —
a term captured before its gloss is written is a legitimate editing state — and SHOULD
surface such entries as incomplete. A validator run against a work-in-progress document
reports gloss-rule findings as distribution-readiness errors, not as grounds to refuse
the working document.

Validators additionally warn when the same matching surface (a `term` or `otherForm`)
appears on more than one entry — legal, since senses are separate entries, but
auto-linking consumers must then disambiguate. Surfaces are compared after Unicode
normalization to **NFC** and then **`casefold()`**: glossaries are explicitly
multilingual, and simple lowercasing would leave German `Straße` and `STRASSE` as two
surfaces while treating two canonically equivalent spellings of the same accented
character as distinct. Validators also lint declared language codes against
the ISO 639-1 / ISO 3166-1 registries (typo protection; see the GL rules in
VALIDATION.md). The duplicate-surface warning is one an author will often **accept
rather than fix**: two senses of one spelling are the model working as designed, and
the warning exists to inform auto-link disambiguation, not as a defect count to drive
to zero.

### 2.1 `firstMention` — lesson provenance

`firstMention` is the optional GlobalId of the lesson where the term is introduced. It
powers three consumer affordances: per-lesson/per-unit glossary views (filter by first
mention), "students know where the word came from" provenance display, and spoiler-safe
auto-linking (link the term only from its `firstMention` lesson onward — the first
auto-link of a term then lands, by construction, in its first-mention lesson).

Interchange semantics:

- An **absent** `firstMention` is fully legal — imported glossaries whose source format
  carries no lesson provenance simply omit it, and the entry renders as course-scoped
  background vocabulary.
- A `firstMention` naming a lesson **the importer does not hold** is treated as absent.
  It is not an error: the field is a course-specific pointer on a portable artifact, and
  a glossary reused with other content legitimately dangles here.
- An importer that **regenerates lesson GlobalIds** (fresh-copy import, template
  instantiation) MUST remap each entry's `firstMention` alongside the lesson ids it
  rewrites; a remap left undone silently severs every entry's provenance.

## 3. Affordances (consumer-defined)

The fields above are deliberately sufficient for the common consumption patterns, none
of which the spec mandates:

- **Glossary panel / study list** — render entries on the course, unit, or lesson the
  glossary is attached to (attachment via `glossaryRefs`; see §4 and the course schema
  delta). Unit and lesson views MAY filter by `firstMention`.
- **Automatic in-content term linking** — consumers MAY scan rendered content for
  `term` + `otherForms` matches and link the first occurrence to a popover
  (definition/translation, pronunciation, audio). `linkAutomatically: false` excludes
  an entry; consumers SHOULD avoid linking inside interactive answer surfaces, and
  SHOULD gate linking on `firstMention` (§2.1).
- **Translation display** — show **all** translations (each value in a `lang`-tagged
  span, labeled from its key), or a **single language** chosen from the delivery
  context: the user's L1 when known, else the attached course's `supportLanguage`, else
  the first entry of `translationLanguages`.
- **Flashcards and matching games** — front = `term` (+ audio/IPA); back = the chosen
  language's `translations` value or the `definition`; pairs = term ↔ gloss; distractors
  from same-`partOfSpeech` or same-`tags` entries.

## 4. Relationship to other documents

- A **course** attaches glossaries via `glossaryRefs` — plain arrays of glossary
  `globalId` strings at the course, unit, or lesson node, where **placement encodes
  scope** (the same three-level model as `objectiveIds`; junctions stop at Lesson). For
  self-containment, the exporting course SHOULD embed a **carried copy** of each
  referenced glossary in its root `glossaries[]` pool — the whole document, identity
  verbatim, transport not authorship (the `objectives[]`-pool pattern at document
  scale; see [`course.schema.json`](https://lc-json.org/1.1/course.schema.json) `glossaries[]`). One `.json` file then carries the course,
  glossaries included. A ref that resolves to no pool copy and no held document is a
  **dangling ref** — legal: consumers SHOULD surface it ("this course references a
  glossary that isn't included"), SHOULD preserve it for later binding, and MUST NOT
  fail the import over it.
- A **Curriculum Pack** references a glossary through `contentRefs[]` — a
  `{"type": "glossary", "id": …}` envelope whose `id` is the glossary's root
  `globalId` — the way a glossary reaches a *program*.
- Glossaries do **not** attach to Subject Collections: a Collection is vocabulary
  *about* content (tags, objectives); a glossary *is* content-adjacent learning
  material.
