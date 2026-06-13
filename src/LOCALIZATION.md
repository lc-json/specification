# LC-JSON Localization and Language Model

**Status:** New in `1.0-rc.3`. Clarification document for the `1.0` contract; codifies the language model that has been implicit since `1.0-rc.1`; introduces no breaking change. The `language` root field and `lang`/`dir` annotation behave exactly as they did in rc.1/rc.2 — this document states the model explicitly and sets expectations.
**Spec version:** 1.0 (release candidate: rc.3)
**Last updated:** 2026-06-13

This document defines how LC-JSON represents natural language: what the `language` and `supportLanguage` fields mean, how `lang`/`dir` annotate individual spans, which language-tag forms are accepted, and — importantly for implementers — what the format can and cannot promise about pronunciation in assistive technology. The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**, and **RECOMMENDED** are interpreted as in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174).

---

## 1. Scope

The word "language" does four different jobs in a learning document, and conflating them is the most common source of confusion for implementers. This document separates them:

| Concept | Field / mechanism | What it is |
|---|---|---|
| **Delivery language** | `language` (root) | The single primary language the document is authored in. |
| **Language of parts** | `lang` / `dir` on HTML | Individual spans in a *different* language from the delivery language. |
| **Support language** | `supportLanguage` (root) | An optional pedagogical layer: the learner's first language (L1), surfaced to aid comprehension of second-language (L2) content. |
| **Translation bundles** | *(not in 1.x)* | Parallel copies of the same content in multiple languages within one document — **explicitly out of scope**; see §2.4. |

LC-JSON's wire format is language-neutral: a document may declare any natural language and any script. This document governs how that language is *declared and annotated*, not which languages are permitted (all are).

---

## 2. The four roles of "language"

### 2.1 Delivery language — `language`

`language` is a **required** root field on both the `course` and `questionSet` artifacts. It declares the single primary language the document is authored and delivered in — e.g. `"language": "en"` means the document is an English document.

- A document has exactly **one** delivery language. LC-JSON 1.x is single-language-per-document (see §2.4).
- A delivering consumer SHOULD set the rendering surface's primary language from this field (for a web consumer, `<html lang="…">`), so that assistive technology, hyphenation, and font selection default correctly.
- `language` is the document's identity, not a runtime choice: a consumer does not "switch" a document's delivery language; it renders the document in the language it declares.

### 2.2 Language of parts — `lang` and `dir` on HTML

Within HTML-bearing fields (`ContentItem.html`, `SignpostItem.customHtml`), a run of text in a language *other than* the delivery language is marked with the standard HTML `lang` attribute (and `dir` where the script direction differs). This is the [WCAG 3.1.2 Language of Parts](https://www.w3.org/WAI/WCAG21/Understanding/language-of-parts.html) mechanism.

```json
{
  "type": "content",
  "html": "<p>The French call it <span lang=\"fr\">l'esprit de l'escalier</span> — the wit of the staircase.</p>"
}
```

Language of parts is about **correct rendering and pronunciation**, not translation: the Spanish span in an English document is content *in* Spanish, not an English string's Spanish equivalent. `lang`/`dir` are part of the HTML safety profile's universal-attribute allowlist ([`HTML_SAFETY.md`](HTML_SAFETY.md) §3.1) and MUST survive a consumer's sanitization and round-trip ([`NORMATIVE.md`](NORMATIVE.md) §12.1).

### 2.3 Support language — `supportLanguage`

`supportLanguage` is an **optional** root field (nullable). It names the learner's first language (L1) for a document whose delivery language is a second language (L2) being taught. It exists for the language-teaching case: an English course built for Spanish-speaking learners declares `"language": "en", "supportLanguage": "es"`, signaling that L1 (Spanish) support — glosses, hints, translations of key terms — is appropriate.

`supportLanguage` is a **signal**, not a rendering instruction. *How* a consumer surfaces L1 support — inline glosses, hover tooltips, a toggle, a glossary panel, or not at all — is consumer-defined. One consumer's convention is an inline bracket tag (`[L1: una hipoteca]`) that its renderer expands to a `lang`-annotated span; that is an authoring/rendering convention of that consumer, not a wire-format construct. The wire format carries `supportLanguage` plus ordinary text and `lang`-annotated parts; the pedagogy is layered on by the consumer.

When `supportLanguage` is absent or `null`, no L1 support is implied and a consumer SHOULD render the document monolingually.

### 2.4 Out of scope for 1.x — translation bundles

LC-JSON 1.x does **not** provide field-level localization. There is no shape in which a single field carries parallel translations (no `"title": {"en": "...", "es": "..."}` maps, no per-locale field bundles). A document is authored in one delivery language.

**Multiple languages are delivered as multiple documents.** An English course and its Spanish translation are two separate LC-JSON documents, each with its own single `language`. This keeps the wire format simple, keeps validation unambiguous, and matches how content interchange formats in adjacent ecosystems treat translation (as separate artifacts, not multiplexed fields).

This is a deliberate boundary, not an oversight. Producers MUST NOT assume a future minor version will add localized field bundles; if it ever does, it will be additive and will not change the meaning of the single-`language` documents defined here.

---

## 3. Language tags

Language-tag values (`language`, `supportLanguage`, and HTML `lang`) are [BCP 47](https://www.rfc-editor.org/info/bcp47) language tags.

- The common case is a bare ISO 639-1 primary subtag: `en`, `es`, `fr`, `ar`. Producers SHOULD use the bare primary subtag when region and script do not matter.
- Region and script subtags are **permitted** where they carry meaning: `pt-BR`, `es-MX`, `en-GB`, `zh-Hant`. These are most useful for selecting a regional voice or regional spelling.
- A conforming consumer MAY act on only the primary subtag (treating `es-MX` as `es`) when it has no region-specific behavior. Producers therefore SHOULD NOT rely on a consumer honoring a region subtag, but MAY emit one so that consumers which *do* (for example, choosing a regional text-to-speech voice) can use it.

The reference validator performs a plausibility check on these fields (well-formed primary subtag, optional script, optional region) and emits a `WARN` — not an error — on a malformed tag. It does not validate the full BCP 47 registry.

---

## 4. Text direction — `dir`

The delivery language's script direction is the document default; for a right-to-left (RTL) delivery language a consumer SHOULD set the rendering surface direction accordingly. Within content, the `dir` attribute marks spans or blocks whose direction differs from the surrounding text — an Arabic phrase embedded in an English paragraph, or an English term inside an Arabic passage.

Producers SHOULD emit `dir` alongside `lang` whenever an annotated part's script direction differs from its surroundings; a `lang` without the matching `dir` can render with incorrect bidirectional ordering. The full producer/consumer direction obligations live in [`ACCESSIBILITY.md`](ACCESSIBILITY.md) §6; the worked example `examples/course-rtl-writing-systems.json` demonstrates LTR-with-embedded-RTL across four writing systems.

---

## 5. Producer obligations

- A producer **MUST** emit a `language` root field matching the document's delivery language (§2.1).
- A producer **SHOULD** mark any HTML span in a language other than the delivery language with `lang` (§2.2, WCAG 3.1.2), and **SHOULD** add `dir` where that span's script direction differs (§4).
- A producer **MAY** emit `supportLanguage` for language-teaching documents (§2.3), and **MUST** leave it absent or `null` otherwise.
- A producer **SHOULD** use bare ISO 639-1 primary subtags unless a region/script subtag carries real meaning (§3).

## 6. Consumer obligations

- A consumer **SHOULD** set the rendering surface's primary language and direction from the document `language` (§2.1).
- A consumer **MUST** preserve `lang` and `dir` on HTML through sanitization and round-trip (binds [`NORMATIVE.md`](NORMATIVE.md) §12.1).
- A consumer **MAY** act on only the primary subtag of any language tag (§3).
- A consumer **MAY** surface `supportLanguage`-driven L1 support in any form, or none (§2.3).

---

## 7. Screen readers and pronunciation — expectations (informative)

This section exists because the gap it describes is invisible to most implementers until a screen-reader user hits it.

Emitting `lang` on a foreign-language span is **necessary but not sufficient** for that span to be *pronounced* correctly. `lang` is an instruction to the assistive technology; whether the instruction is acted on depends on the delivery environment, which the format cannot control:

- The reader must support **automatic language switching**, and it must be enabled. Support varies by product — NVDA and JAWS switch reliably; Windows Narrator's automatic switching is comparatively limited; VoiceOver sits in between.
- The matching **voice / pronunciation data must be installed** on the device. A reader with only an English voice will read a correctly-tagged `lang="es"` span in the English voice — mispronouncing it — even though the markup is perfect.

The practical consequence for implementers: a producer's job is to emit the affordance (`lang`/`dir`) faithfully; a delivering consumer's job is to preserve it and honor it on the rendering surface. Correct pronunciation is then completed by the end user's screen reader and installed voices, which is outside the format's and often the consumer's control. This does **not** make `lang` optional — without it, no reader can switch at all, so the affordance is the floor, not the ceiling. It does mean that "the document is correctly tagged" and "every user hears flawless pronunciation" are different claims, and only the first is within an LC-JSON producer's or consumer's power to guarantee.

---

## 8. Relationship to the Accessibility Profile

The language-of-parts and direction obligations here overlap the [`ACCESSIBILITY.md`](ACCESSIBILITY.md) §6 obligations and are bound by the same opt-in Accessibility Profile claim ([`NORMATIVE.md`](NORMATIVE.md) §10.2). This document adds the language *model* (the four roles, the single-document boundary, the language-tag rules) and the pronunciation-expectations framing; `ACCESSIBILITY.md` §6 remains the home for the per-criterion WCAG cross-references.
