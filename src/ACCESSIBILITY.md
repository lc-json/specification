# LC-JSON Accessibility Profile

**Status:** Released for `1.0-rc.2`. Additive deepenings (per-criterion normative cross-reference table, expanded ARIA patterns, screen-reader timing requirements, conformance fixtures) land in `1.0` final on 2026-06-30 — see §11. Obligations stated here are committed for `1.0` final and will not be retracted or contradicted.
**Spec version:** 1.0 (release candidate: rc.2)
**Last updated:** 2026-05-23

This document collects the accessibility expectations for LC-JSON (Learning Content JSON) producers and consumers. The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**, and **RECOMMENDED** are to be interpreted as in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174). RFC 2119 language binds wire-format obligations; ARIA-pattern guidance is informative — the spec hints at affordances rather than mandating a single canonical UI (see [`README.md`](README-spec.md) §"Wire Format").

---

## 1. Scope

LC-JSON is a portable interchange format. The wire format does not render anything itself — accessibility outcomes depend on consumer rendering. The role of this document is to:

- Specify **producer obligations** that make accessible rendering possible (alt text, captions, language tags).
- Specify **consumer obligations** for rendering that don't drop accessibility affordances the producer already provided.
- Cross-reference [`HTML_SAFETY.md`](HTML_SAFETY.md) where HTML-bearing fields constrain accessibility-bearing markup (`<img alt>`, `<track>`, `lang`, `dir`).

Accessibility for the **authoring tools** that produce LC-JSON, and for the **delivery surfaces** that render it, is the responsibility of those tools — not the wire format. This document binds the wire-format obligations only.

### 1.1 The two-layer duty (informative)

Accessibility is achievable downstream **if and only if** the format can carry the affordances a renderer needs, *and* the rendering consumer surfaces them correctly. These are two distinct, non-interchangeable layers:

1. **The wire format (LC-JSON).** Cannot produce an accessible experience on its own; it can only *enable* one — by carrying alt text, captions, language/direction signals, textual feedback, and position semantics for structured tasks. If the format cannot represent an affordance, no conforming consumer can ever deliver it.
2. **The consumer (the renderer).** Where a disabled end-user actually meets the content, and therefore where every accessibility law attaches. The consumer's duty is to surface the affordances the producer provided.

A perfectly capable format rendered by a non-conformant consumer is still inaccessible. A conformant consumer cannot rescue a format that never carried the affordance. Both layers must hold.

### 1.2 Legal context (informative)

WCAG governs rendered user experiences; LC-JSON governs portability and metadata preservation. These layers are complementary but distinct — see [`NORMATIVE.md`](NORMATIVE.md) §12.3.

The technical accessibility target for educational and commercial delivery in the EU and US converges on **WCAG 2.1 Level AA**:

- **EU — European Accessibility Act, Directive (EU) 2019/882** (applicable since 28 June 2025): points at the harmonized standard **EN 301 549**, which references WCAG 2.1 AA.
- **EU — Web Accessibility Directive (EU) 2016/2102**: binds public-sector bodies (public universities, schools) to **EN 301 549 → WCAG 2.1 AA**.
- **US — DOJ ADA Title II final rule** (April 2024): explicitly adopts **WCAG 2.1 AA** for state/local government, including public schools and universities, with compliance deadlines in **April 2026 / April 2027**.
- **US — Section 508 / Section 504**: WCAG-based conformance for federal procurement and recipients of federal financial assistance.

LC-JSON supports WCAG 2.1 AA by carrying the wire-format affordances a conforming renderer needs (alt text, captions, `lang`/`dir` signals, textual feedback, position semantics for structured tasks). The delivering consumer remains responsible for the full WCAG conformance claim under its applicable jurisdiction.

### 1.3 ATAG vs WCAG (producers vs consumers)

- **Web consumers** (the renderers that display LC-JSON content to learners) fall under **WCAG**. The obligations in §§2–7 are written from this perspective.
- **Authoring tools** that produce LC-JSON (whether browser-based editors, desktop applications, AI-assisted authoring scripts, or import converters) fall under W3C **[ATAG 2.0](https://www.w3.org/TR/ATAG20/)**, not WCAG. ATAG covers two things: (a) making the authoring environment itself accessible to author-users (ATAG Part A), and (b) supporting authors in producing accessible content — e.g. prompting for `alt` text, captions, transcripts (ATAG Part B). Producer obligations in this document map to ATAG Part B: the authoring tool's job is to make the affordances easy to author and hard to forget.
- **Desktop authoring tools** are additionally outside WCAG's scope entirely — WCAG governs web content. Desktop accessibility is governed by platform standards (e.g. UIAutomation on Windows; Section 508 / EN 301 549 *software* clauses).

### 1.4 Five conformance requirements for a WCAG 2.1 AA claim (informative)

A WCAG 2.1 AA claim by a delivering consumer is valid only if **all five** hold; failing any one voids the claim independent of per-criterion passes:

1. **Conformance level** — all Level A and Level AA criteria are met (50 criteria total: 30 A + 20 AA).
2. **Full pages** — conformance is claimed for complete pages, including dynamically loaded states; partial-page exclusions are not permitted.
3. **Complete processes** — every page in a multi-step process must conform (e.g. login → course → item → submission → results). A conformant results page after a non-conformant quiz flow does not pass.
4. **Accessibility-supported technologies** — reliance only on technologies that work with assistive technology (HTML + ARIA + native form controls is the baseline).
5. **Non-interference** — even non-relied-on content must not break 1.4.2 (Audio Control), 2.1.2 (No Keyboard Trap), 2.2.2 (Pause, Stop, Hide), or 2.3.1 (Three Flashes or Below Threshold).

This document specifies what LC-JSON producers and consumers must do to make the per-criterion items achievable. The five claim-level gates are properties of a delivering consumer, not of the wire format.

### 1.5 Versions targeted

This profile targets **WCAG 2.1 Level AA** as the primary claim baseline. Selected criteria from **WCAG 2.2** are designed-in for new interactive components to avoid near-term rework:

- **2.5.7 Dragging Movements** (2.2, A) — every drag interaction MUST ship a single-pointer, non-drag alternative. Governs structured-task question types in §4.
- **2.5.8 Target Size (Minimum)** (2.2, AA) — interactive targets SHOULD be ≥ 24×24 CSS px.

Other WCAG 2.2 additions are out of the 2.1 claim baseline. **4.1.1 Parsing** is treated as satisfied-by-default (modern browsers/AT; W3C errata; obsolete in WCAG 2.2).

---

## 2. Image alt text — WCAG 1.1.1

### 2.1 Producer obligations

A producer MUST emit an `alt` attribute on every `<img>` element in HTML-bearing fields ([`HTML_SAFETY.md`](HTML_SAFETY.md) §3.3).

- For **informative** images (diagrams, screenshots, photographs that carry meaning), `alt` MUST be a meaningful textual description.
- For **decorative** images (visual flourishes, spacers, redundant illustrations of adjacent text), `alt=""` (empty string) is RECOMMENDED. An empty `alt` is a positive signal to assistive technology that the image carries no content; it is not a missing attribute.

Question types that carry image references in tool-specific extension fields (e.g. reserved-type `hotspot`, `graphicGapMatch`) SHOULD include an alt-text-equivalent property when those types are promoted to first-class schemas (1.0 final, see §11).

### 2.2 Consumer obligations

A consumer MUST render the `alt` text exposed to assistive technology when an image is rendered. A consumer that strips `<img>` (e.g. when sanitization fails) MUST surface the `alt` text as fallback content rather than silently dropping the image entirely.

A missing `alt` attribute SHOULD trigger a domain-validation warning per [`HTML_SAFETY.md`](HTML_SAFETY.md) §8.2; the consumer MUST still render the image (the failure mode is a warning to the author, not a refused document).

---

## 3. Video and audio: captions, transcripts, descriptions — WCAG 1.2.1, 1.2.2, 1.2.3, 1.2.5

### 3.1 Producer obligations

For **prerecorded instructional video that contains speech or meaningful audio**, producers **MUST** emit at least one `<track kind="captions">` or `<track kind="subtitles">` element with a valid `src` and `srclang` when claiming Accessibility Profile conformance. This satisfies WCAG **1.2.2 Captions (Prerecorded)** at Level A. WebVTT is the RECOMMENDED caption format (broad browser support; AT-compatible).

For all other `<video>` content (decorative, non-speech, ambient), producers SHOULD emit a `<track kind="captions">` or `<track kind="subtitles">` element where the content carries any information the learner is expected to receive ([`HTML_SAFETY.md`](HTML_SAFETY.md) §7.5).

For pre-recorded video/audio that carries instructional content, producers SHOULD additionally provide a transcript — either as adjacent `ContentItem.html` prose or as a linked resource — so learners who cannot use captions still receive the information.

`<track kind="descriptions">` (audio descriptions of visual-only information) is RECOMMENDED for video where visual content is essential to the pedagogy and not redundantly narrated. This pairs with WCAG **1.2.5 Audio Description (Prerecorded)** at AA.

### 3.2 Consumer obligations

A consumer that renders `<video>` or `<audio>` MUST surface caption/subtitle controls when `<track>` elements are present. A consumer MUST NOT auto-play media ([`HTML_SAFETY.md`](HTML_SAFETY.md) §7.1, §7.2) — the `<video>` rendering pipeline is user-driven, which is itself an accessibility requirement (motion-sensitivity, screen-reader interruption, bandwidth control). Auto-play would also violate WCAG **1.4.2 Audio Control**.

A consumer SHOULD render `<track kind="descriptions">` as either a switchable audio track or a synchronized text alternative.

---

## 4. Keyboard alternatives for structured-task question types — WCAG 2.1.1, 2.5.1, 2.5.2, 2.5.3, 2.5.7 (2.2 designed-in), 4.1.2, 1.3.1

Three implemented question types involve drag-and-drop or pointer-driven interaction — `matching`, `ordering`, and `placement`. The cloze family (`wordBankCloze`, `multiGapCloze`) is structurally similar; `multipleChoiceCloze` is dropdown-based and inherently keyboard-accessible. The reserved-for-2027 `hotspot`, `graphicGapMatch`, `graphicAssociate`, and `graphicOrder` types compound the same pattern with image regions.

### 4.1 Consumer obligations

A consumer that renders these types MUST provide a fully keyboard-navigable interaction. Pointer-only implementations are non-conforming for accessibility purposes regardless of LC-JSON conformance. Per WCAG **2.5.7 (designed-in from 2.2)**, every drag interaction MUST additionally ship a single-pointer, non-drag alternative.

Concretely:

- `matching` (`pairs` mode) — Tab-to-item, Enter-to-select, Tab-to-match, Enter-to-pair (or equivalent two-step keyboard model) MUST work without a pointer. Native `<select>` per item is the simplest conforming pattern (see §4.2.2).
- `matching` (`classification` mode) — Tab through the item pool, Enter-to-select an item, Tab-to-category, Enter-to-place. Many items can target the same category.
- `ordering` — Up/Down (or Left/Right for `orderingUnit: "word"`) keys MUST move a focused tile within the sequence. The interaction model SHOULD be discoverable from focus state alone. See §4.2.1 for a recommended ARIA pattern.
- `placement` — Tab through the distractor pool and the gap targets; Enter-to-select an item, Tab-to-gap, Enter-to-place. The interaction MUST work without a pointer regardless of `placementUnit` mode. A labeled `<select>` per gap is the simplest conforming pattern.
- `wordBankCloze`, `multiGapCloze` — Bank-token selection and gap-placement MUST be reachable by keyboard. `multipleChoiceCloze`'s `<select>` rendering is inherently keyboard-accessible and is the RECOMMENDED fallback pattern when richer drag-and-drop interactions cannot be made keyboard-equivalent.

Focus indicators on interactive elements MUST be visible (WCAG **2.4.7 Focus Visible**) and SHOULD meet 3:1 contrast against adjacent backgrounds (WCAG **1.4.11 Non-text Contrast**).

### 4.1.1 The accessible alternative is expressible from the document data

The position/target semantics a consumer needs to render a keyboard- and AT-navigable alternative are already carried by the schemas, so the accessible path is expressible from the document rather than improvised at render time: `ordering` by item **position** (`items[i]` is the tile for position `i`); `placement` by **gap number** (`@@@N` markers correspond to `placements[].gap`); `matching` by **item↔match** value (`pairs`) or **item→category** value (`classification`). Element identity is positional or by value rather than a durable token — sufficient for rendering and for scoring, including repeated values, which are disambiguated by position. A consumer that needs durable per-element identity across systems (for example, portable response or analytics interchange) supplies it at its own layer; the wire format intentionally does not carry it.

### 4.2 Recommended ARIA patterns (informative)

The following patterns are RECOMMENDED for consumers; they satisfy 4.1.2 (Name, Role, Value), 1.3.1 (Info and Relationships), and 2.5.3 (Label in Name) for the structured-task question types. They are informative — a consumer that satisfies the §4.1 obligations through a different ARIA pattern is conforming.

#### 4.2.1 Ordering

- **Bank** — `role="group"` with `aria-labelledby` pointing at a visible label ("Available tiles" or equivalent).
- **Answer area** — `role="listbox"` with `aria-orientation="horizontal"` for `orderingUnit: "word"` and `aria-orientation="vertical"` for `sentence`/`paragraph`; `aria-labelledby` for the answer label; `aria-describedby` pointing at visible keyboard-and-pointer instructions.
- **Slots inside the listbox** — `role="presentation"` so the listbox→option relationship is preserved across intervening layout elements.
- **Tiles** — `tabindex="0"` on every tile so all tiles are reachable while arrow keys remain available for movement. Each tile's accessible name (`aria-label`) carries the content **and** position information when placed (e.g. *"goes, position 2 of 5"*). When a tile is placed, set `aria-selected="true"`.
- **Live region** — a visually-hidden `aria-live="polite" aria-atomic="true"` element for movement announcements (tile picked up, tile moved, tile returned to bank). This satisfies WCAG **4.1.3 Status Messages** for the interaction's transient state.
- **Single-pointer alternative** — click-to-place from the bank, click-to-pick-up from a placed tile, click-to-place at another position. Distinct visual indication when a tile is "picked up" (separate from the focus indicator, since both can show simultaneously).
- **Discoverable instructions** — keyboard-and-pointer instructions SHOULD be visible (not buried in `aria-label`) and referenced by `aria-describedby` on the listbox.

An alternative satisfying the same obligations is the **WAI-ARIA Authoring Practices** grab/drop model: Space to "grab," arrows move only while grabbed, single-roving `tabindex`. The pattern above (per-tile `tabindex`) is the recommended baseline for short sequences; the grab/drop model scales better for long sequences at the cost of a mode step.

#### 4.2.2 Matching, Placement

The simplest conforming pattern is **native form controls**:

- **`matching` (`pairs`)** — one `<select>` per item, options drawn from `match` values + `distractors` (shuffled per §5.6 of [`NORMATIVE.md`](NORMATIVE.md)). Each `<select>` is labeled with the item text via a visible `<label>` or `aria-labelledby`.
- **`matching` (`classification`)** — one `<select>` per item, options drawn from the category labels.
- **`placement`** — one `<select>` per `@@@N` gap, options drawn from `placements[].item` values + `distractors`. Each `<select>` is labeled with surrounding-passage context or a gap label.

Native `<select>` is inherently keyboard-accessible, satisfies 2.5.3 by carrying its visible label as its accessible name, and avoids the ARIA-listbox complexity of §4.2.1. Richer drag-and-drop renderings are permitted but MUST ship the keyboard and single-pointer alternatives per §4.1.

#### 4.2.3 Cloze family

`simpleGapFill`, `wordBankCloze`, `multiGapCloze`, `multipleChoiceCloze` MAY be rendered with native text inputs (`<input type="text">`) or selects (`<select>`). Each gap MUST have a programmatic label — either an associated `<label>` element, or `aria-label`, or `aria-labelledby` pointing at adjacent gap-context prose.

### 4.3 Producer obligations

Producers MAY include hint text guiding learners who use keyboard or assistive technology, as `hint` strings on the question or as adjacent `ContentItem.html` prose. The wire format does not currently carry interaction-specific accessibility hints; this is intentional (consumer-defined affordance), but producers SHOULD assume diverse interaction modalities when authoring.

> *1.0 final will deepen this with: an `aria-grabbed`/`aria-dropeffect` deprecation note, modern `aria-activedescendant` patterns as an alternative to per-tile `tabindex`, focus-management requirements during placement, and screen-reader announcement timing requirements for partial-credit feedback.*

---

## 5. Feedback: not by color alone — WCAG 1.4.1, 4.1.3

Question types that emit feedback ([`question-types-reference.md`](question-types-reference.md), Common Properties — `feedback`, `choiceFeedback`) carry textual content. Consumers MUST render this textual feedback in addition to any visual indicators of correctness (green/red highlighting, check/cross icons).

A consumer MUST NOT convey correctness solely through color or icon. Conformant rendering provides at minimum:

- An accessible textual indicator ("Correct", "Incorrect", or the producer-supplied feedback string) — WCAG **1.4.1 Use of Color**.
- A non-color visual indicator (icon, position, label) for sighted users with color-vision differences.
- An assistive-technology-readable announcement when feedback updates dynamically — WCAG **4.1.3 Status Messages**.

This binds **consumer rendering**. The wire format already carries the textual indicators; the obligation is to render them.

### 5.1 Recommended live-region pattern (informative)

Per-question feedback that updates dynamically (without a page reload) SHOULD be exposed to assistive technology via an ARIA live region:

- Routine feedback (per-question correct/incorrect, score updates): `aria-live="polite"` so the announcement does not interrupt the learner's current speech.
- Critical feedback (final score, submission confirmation, error states): `role="alert"` (implicit `aria-live="assertive"`).
- Score summaries that change after submission: live region MUST contain the textual indicator before any visual transition begins.

Status-message regions SHOULD NOT receive focus; focus management for status announcements is governed by 4.1.3 — *expose to AT without moving focus*.

---

## 6. Language and direction — WCAG 3.1.1, 3.1.2

The `language` field requirement is also tied to **EN 301 549 5.4** (Closed functionality) for educational content delivery.

### 6.1 Producer obligations

Every Course or QuestionSet carries a `language` field (ISO 639-1) at the document root. Producers MUST set `language` to the primary delivery language. When the document carries content in a secondary language (typically the learner's L1 for `[L1:]` translation/support tags), producers SHOULD also set `supportLanguage`.

Within HTML-bearing fields, producers MAY use the `lang` attribute to mark spans of content in a different language than the document default (per [`HTML_SAFETY.md`](HTML_SAFETY.md) §3.1). Producers SHOULD use `lang` for any in-line foreign-language quotation or term — this satisfies WCAG **3.1.2 Language of Parts**.

Producers MUST set the root `language` to the document's primary delivery language. If the primary delivery language is a right-to-left language (Arabic, Hebrew, Persian, Urdu, etc.), producers SHOULD indicate document-level direction where the consumer supports it. For embedded RTL passages inside an LTR document — for example, an English lesson that quotes Arabic, Hebrew, Persian, or Urdu in the body — producers SHOULD mark the relevant HTML span or block with local `lang` and `dir` attributes (per [`HTML_SAFETY.md`](HTML_SAFETY.md) §3.1). See `examples/course-rtl-writing-systems.json` for a worked LTR-document-with-embedded-RTL example.

### 6.2 Consumer obligations

A consumer MUST honor the document-level `language` field when setting the rendering surface's `lang` attribute. For web consumers, this means setting `<html lang>` from the document `language` rather than hardcoding a single locale. This satisfies WCAG **3.1.1 Language of Page**.

A consumer MUST honor the `dir` attribute on HTML-bearing elements when rendering RTL content; failure to do so produces unintelligible bidirectional text. For RTL document languages (`ar`, `he`, `fa`, `ur`), a web consumer SHOULD additionally emit `<html dir="rtl">` so the browser's bidirectional algorithm is engaged for the whole rendering surface.

A consumer MUST NOT strip `lang` or `dir` attributes during sanitization. Both attributes are explicitly allowed on every element class in [`HTML_SAFETY.md`](HTML_SAFETY.md) §3.1.

> *1.0 final will deepen this with: BCP 47 vs ISO 639-1 reconciliation, localization-model decisions (field-level translation, fallback strategy via `supportLanguage`), and explicit RTL rendering tests in the conformance corpus.*

---

## 7. Reserved and unknown question types: placeholder accessibility — WCAG 1.3.1, 4.1.2

Per [`NORMATIVE.md`](NORMATIVE.md) §6, consumers MUST preserve reserved/unknown question types in full (every field, value, and nested structure) and SHOULD render a non-interactive placeholder for them.

The placeholder MUST be accessible:

- Surfaced to assistive technology with a meaningful description (at minimum: the question's `title`, the type name, and the fact that the consumer cannot render this question).
- Distinguishable from rendered questions (so a screen-reader user understands the question is informational, not interactive) — WCAG **1.3.1 Info and Relationships**.
- Not announced as "interactive" or "form control" when no interaction is possible — WCAG **4.1.2 Name, Role, Value**.

A consumer MUST NOT silently skip the placeholder for assistive-technology users; the §6 round-trip-preservation philosophy applies equally to the rendering surface.

### 7.1 Recommended placeholder pattern (informative)

A conforming placeholder SHOULD use:

- `role="region"` — surfaces the placeholder as a labeled landmark, distinguishable from form controls.
- `aria-label` carrying the question's `title`, the unsupported `type` discriminator, and an indication that the renderer can't display this type. Recommended template: *"Unsupported question: `<title>`. This question type (`<type>`) can't be displayed by this viewer."*
- A visible visual treatment that signals "informational, not interactive" (e.g. a warning or info alert styling).
- No interactive children (`<input>`, `<button>`, `<select>`) — the placeholder is announced as a region, not a form control.

> *1.0 final will deepen this with: example placeholder text in multiple languages and producer guidance for emitting accessibility metadata on tool-specific extensions to reserved types.*

---

## 8. Validator severity (current baseline, established in rc.1)

The reference validator surfaces accessibility issues at the following severities. WCAG SC references are cross-references — accessibility violations in producer output are content-validation issues, not just renderer concerns.

| Issue | Severity | WCAG SC | Cross-reference |
|---|---|---|---|
| Missing `alt` on `<img>` | warning | 1.1.1 | [`HTML_SAFETY.md`](HTML_SAFETY.md) §8.2; §2 above |
| `<video>` without `<track kind="captions">` or `kind="subtitles"` | warning | 1.2.2 | §3.1 |
| `<iframe>`, `<script>`, event handlers (inaccessible regardless) | error | 4.1.2 (would-be) | [`HTML_SAFETY.md`](HTML_SAFETY.md) §8.1 |
| Missing `language` at document root | error (schema-enforced) | 3.1.1 | §6.1 |
| Reserved-type question without a `title` | informational note (recommended for placeholder) | 1.3.1, 4.1.2 | §7 |

> *1.0 final will deepen this with: an `--accessibility` validator flag (analogous to `--strict`) for tooling that wants to fail-build on warnings, additional severity entries for the reserved-type placeholder surface, and conformance fixtures exercising accessibility-related warnings/errors.*

---

## 9. WCAG 2.1 AA mapping (informative)

The table below indexes which sections of this document cover which Success Criteria. This is an informative cross-reference; per-criterion normative obligations live in the section bodies.

| WCAG 2.1 AA SC | Level | Topic | This profile |
|---|---|---|---|
| 1.1.1 Non-text Content | A | Alt text on images | §2 |
| 1.2.1 Audio-only/Video-only | A | Transcript or alt media | §3 |
| 1.2.2 Captions (Prerecorded) | A | `<track kind="captions">` | §3 |
| 1.2.3 Audio Desc. or Media Alt. | A | Description track or transcript | §3 |
| 1.2.5 Audio Description (Prerecorded) | AA | `<track kind="descriptions">` | §3 |
| 1.3.1 Info and Relationships | A | ARIA roles/labels, structured-task semantics, placeholder landmark | §4, §7 |
| 1.4.1 Use of Color | A | Textual + non-color correctness cues | §5 |
| 1.4.2 Audio Control | A | No autoplay | §3.2 |
| 1.4.11 Non-text Contrast | AA | Focus indicator contrast | §4.1 |
| 2.1.1 Keyboard | A | Keyboard alternatives for structured tasks | §4 |
| 2.4.7 Focus Visible | AA | Visible focus indicators | §4.1 |
| 2.5.1 Pointer Gestures | A | Single-pointer alternatives | §4 |
| 2.5.2 Pointer Cancellation | A | Activation on up-event | §4 (consumer behavior) |
| 2.5.3 Label in Name | A | Accessible name contains visible label | §4.2 |
| **2.5.7 Dragging Movements** | **A (2.2 — designed-in)** | Single-pointer alternative for every drag | §4 |
| **2.5.8 Target Size (Minimum)** | **AA (2.2 — designed-in)** | ≥ 24×24 px interactive targets | §1.5 |
| 3.1.1 Language of Page | A | Document `language` → `<html lang>` | §6 |
| 3.1.2 Language of Parts | AA | Inline `lang` on foreign-language spans | §6 |
| 4.1.2 Name, Role, Value | A | ARIA semantics on custom widgets and placeholders | §4, §7 |
| 4.1.3 Status Messages | AA | Live regions for dynamic feedback | §5 |

Criteria not listed (e.g. 1.3.2, 2.4.1, 3.2.2, 3.3.x) are properties of a delivering consumer rather than wire-format affordances. A delivering consumer's full WCAG 2.1 AA claim covers them per its own conformance plan.

---

## 10. Cross-references

- [`NORMATIVE.md`](NORMATIVE.md) — RFC 2119 conformance requirements; `language` field requirement; reserved-type round-trip; randomization requirements (§5.6).
- [`HTML_SAFETY.md`](HTML_SAFETY.md) — `<img alt>`, `<track>`, `lang`, `dir`, validator severity.
- [`question-types-reference.md`](question-types-reference.md) — per-type feedback fields and structured-task definitions.
- [`GLOSSARY.md`](GLOSSARY.md) — terminology.
- **WCAG 2.1** — <https://www.w3.org/TR/WCAG21/>
- **WCAG 2.1 Quick Reference (filterable SC list)** — <https://www.w3.org/WAI/WCAG21/quickref/>
- **WAI-ARIA Authoring Practices Guide (APG)** — <https://www.w3.org/WAI/ARIA/apg/> — pattern recommendations (listbox, grab/drop, status messages).
- **ATAG 2.0** — <https://www.w3.org/TR/ATAG20/> — authoring-tool obligations referenced in §1.3.
- **EN 301 549** — <https://www.etsi.org/deliver/etsi_en/301500_301599/301549/> — EU harmonized standard pointing at WCAG 2.1 AA.

---

## 11. From the current baseline to 1.0 final

This document is the `1.0-rc.2` accessibility profile. The obligations stated here are committed for `1.0` final and will not be retracted or contradicted; the `1.0` final deepenings are **additive** and shaped by feedback during the rc.2 period.

Planned `1.0` final additions (2026-06-30):

- **Per-criterion normative cross-reference table** — promote select rows of §9 from informative cross-reference to normative obligation. Currently §9 cross-references WCAG SCs for orientation; in `1.0` final, specific producer/consumer obligations become MUST-level under their SC where the wire format alone determines conformance.
- **Expanded ARIA patterns** — patterns for `matching` `classification` mode, richer screen-reader announcement requirements for partial-credit feedback (§4), per-language placeholder text examples (§7).
- **Screen-reader timing requirements** — announcement timing for auto-grading flows (§5).
- **Producer obligations promoted into NORMATIVE.md** — currently some producer obligations are stated SHOULD here; in `1.0` final, select obligations (alt-text presence on informative images, captions on instructional speech-bearing video) become MUST in `NORMATIVE.md` rather than in this advisory profile.
- **`--accessibility` validator flag** — analogous to `--strict`; promotes accessibility-profile warnings (missing `alt`, missing `<track>` on speech-bearing video) to errors for tooling that wants to fail-build on accessibility issues.
- **Conformance fixtures for accessibility** — expanded fixture coverage beyond the current baseline (a round-trip preservation fixture and a missing-language invalid fixture are part of the current baseline, established in rc.1; the 1.0-final additions exercise the `--accessibility` flag's warning-to-error promotion).
- **Reserved-type accessibility metadata schema** — guidance for emitting accessibility metadata on `hotspot`, `graphicGapMatch`, and the other graphic types when their per-type schemas land (post-1.0).
- **Multilingual accessibility metadata shape** — design for localized alt text / transcripts / accessible-name fields per locale. Not in 1.0; flagged as a known forward direction.
- **BCP 47 vs ISO 639-1 reconciliation** — locale-tag normalization for `language` / `supportLanguage` / inline `lang`.

Implementers building against `1.0-rc.2` can rely on the obligations stated above. The `1.0` final release lands on **2026-06-30**.
