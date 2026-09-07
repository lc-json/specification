# LC-JSON Item Patterns — Authoring Guide

**Status:** Informative. See [NORMATIVE.md](NORMATIVE.md) for binding requirements.
**Spec version:** 1.0
**Last updated:** 2026-05-02

This document is a guide for authors and developers working with LC-JSON (Learning Content JSON) items (`exercise`, `quiz`). It explains the four policy fields available on each item, names the common combinations teachers use, and surveys how different consumers may interpret them.

It is **informative**, not normative. Nothing here adds requirements to producers or consumers — it describes the affordances the wire format already gives you, and how to think about composing them.

---

## 1. The four policy fields

Every Exercise or Quiz item carries four fields that an author composes to express pedagogical intent. They are **independent**: any combination is valid LC-JSON.

| Field | What it is on the wire | What it isn't |
|---|---|---|
| **`type`** | Structural form: `"exercise"` or `"quiz"`. Signals the consumer's UI rendering (different chrome, different settings panes) and tells the consumer to track points in separate buckets — enabling future weighted-grading schemes (e.g., "exercises = 30%, quizzes = 70%"). | A grading-policy signal. `quiz` does not mean graded; `exercise` does not mean ungraded. |
| **`isGraded`** | Boolean. Whether the score on this item should be recorded against the learner's grade. | A navigation signal. Whether the learner can move forward despite a low score is a separate consumer-policy question. |
| **`isOptional`** | Boolean. Whether the learner is required to attempt this item to be considered "done" with the lesson. | A grading or navigation signal in itself — but consumers often combine it with completion-tracking. |
| **`passMarkPercent`** | Number 0–100. The threshold at which a score counts as "passing." | A gating directive. The wire format does not say what the consumer does when a learner falls below the threshold. |

**The crucial point:** `passMarkPercent` is a *threshold*, not a *gate*. What happens when a learner scores below it is **consumer policy**, not spec mandate. See §3 below.

### Plus: `tags` (metadata, not policy)

Items also carry an optional `tags` array — taxonomic strings used for filtering, search, gradebook grouping, and similar metadata operations. Tags are *not* policy fields (they don't affect grading, navigation, or threshold logic). Conventional namespaces use colons:

| Namespace | Example | Use |
|---|---|---|
| Domain hierarchy | `history:immigration:united-states` | Subject → topic → sub-topic |
| Stage | `stage:lower-secondary`, `grade:9`, `year:9`, `level:B2` | Pick the convention your audience knows; the spec doesn't impose a single vocabulary |
| Cognitive skill | `fact-recall`, `analysis`, `synthesis` | Bloom-style levels |
| Exam alignment | `exam:cambridge-fce`, `exam:ap-history` | When content is targeted at a specific exam |

Item-level tags are **independent** of any tags on inner questions. A `quiz` with three tagged questions can itself be tagged differently — the quiz's tags describe the assessment as a whole; the questions' tags describe each item.

### Note on ContentSequenceItem (CSI) tagging

A `contentsequence` item references a `contentItemId` plus zero or more `relatedItemIds` (typically Exercise/Quiz items). Each of those referenced items may carry its own tags. **The wire format does not specify how a consumer should compose tags across the CSI and its referenced items** — that is consumer policy. Reasonable choices include:

- **Surface only the CSI's own tags** in search/filter UIs (treat the CSI as the authoritative metadata source for the bundle)
- **Surface the union of CSI tags + related-items' tags** (the bundle inherits everything contributed)
- **Surface only the related items' tags** when the CSI is being treated as a thin wrapper
- **Combine with namespace-aware deduplication** (e.g., union of `history:*` tags but only the CSI's own `grade:*` tag)

Authors should apply tags to whichever items make sense for their content; consumers should document their composition policy so authors know what to expect.

---

## 2. Common authoring patterns

### Question-level display hints

A few question types carry advisory display hints that don't change the wire shape but help consumers pick a fitting layout. The clearest example is **ordering**: an `ordering` question can carry `orderingUnit: "word" | "sentence" | "paragraph"`, signalling tile size — inline tokens for word-level, stacked card blocks for sentence- or paragraph-level (see `examples/16-ordering.json`, `16b-sentence-ordering.json`, `16c-paragraph-ordering.json`). The discriminator stays `ordering` in all three cases; the hint lets the consumer choose layout. Consumers MAY render uniformly regardless. **Placement** carries the parallel `placementUnit: "sentence" | "paragraph" | "sectionLabel"` hint with the same advisory framing — see [`question-types-reference.md`](question-types-reference.md) §11.

### Two-mode shape: matching

Matching questions carry a `matchingMode: "pairs" | "classification"` discriminator, with two distinct sub-shapes underneath: `pairs: [{ item, match }]` for 1:1 matching and `categories: [{ label, items }]` for classification (many-to-one). In `pairs` mode, consumers MAY render two columns with drag-and-drop pairing or a per-row dropdown of candidate matches. In `classification` mode, consumers MAY render items as draggable chips and category labels (plus distractors) as drop zones. Both modes use the same `distractors[]` field for extra unmatched values. The two presentations are consumer-defined; the spec describes the structural relationship and hints at the affordance. See `examples/15-matching.json` (pairs) and `examples/15b-matching-classification.json` (classification).

### Item-level patterns

The four item-level fields generate a wide design space. These patterns are common enough to have names:

| Pattern | `type` | `isGraded` | `isOptional` | `passMarkPercent` | Use case |
|---|---|---|---|---|---|
| **Open practice** | `exercise` | `false` | `false` | `0` | Free practice; no stakes. Learners try as much as they want. |
| **Graded homework** | `exercise` | `true` | `false` | `70` (varies) | Counts toward grade. Threshold defines "passing the homework." |
| **Mastery exercise** | `exercise` | `true` | `false` | `80–100` | Must (typically) demonstrate mastery before continuing — depends on consumer's gating model. |
| **Diagnostic pre-test** | `quiz` | `false` | `false` | `0` | "What do you know going in?" Surfaces baseline; never blocks; learner sees their score for self-awareness. |
| **Typical assessment** | `quiz` | `true` | `false` | `70` | Standard quiz. Counts toward grade. |
| **Exit ticket** | `quiz` | `true` | `false` | `0` | Quick check at end of lesson. Recorded in gradebook (so the teacher can see attempts), but no threshold gate. |
| **Bonus / enrichment** | `exercise` or `quiz` | varies | `true` | varies | Skippable. Some teachers grade bonus work, some don't. |
| **Self-check** | `quiz` | `false` | `true` | `0` | Optional, ungraded reflection. Pure metacognition. |

Pick the row that matches your intent. Or compose your own combination — the spec doesn't enumerate "valid" patterns; the patterns above just happen to be common.

---

## 3. How consumers may interpret these fields

The wire format describes what the fields *are*. It does **not** prescribe what a consumer *does* with them. Different consumers — even different modes of the same consumer — can interpret the same payload differently. Some examples:

### Consumer-policy patterns (illustrative)

- **Open-navigation LMS:** Learner moves freely between items in any order. `passMarkPercent` is used for the score-display badge and for the gradebook-column threshold; it doesn't gate forward progress.
- **Sequential-navigation LMS:** Learner moves in order. A graded item below `passMarkPercent` blocks forward progress until passed; ungraded items always allow forward progress regardless of score. The "is this graded?" question is what determines whether a low score gates anything.
- **Mastery-routing LMS:** Scores below `passMarkPercent` route the learner to remediation content; scores above route to enrichment. Grading is recorded but doesn't block progress (the routing handles it).
- **Reporting-only consumer:** Uses `passMarkPercent` purely for the gradebook-column display. Doesn't affect navigation. Ungraded items don't appear in the gradebook at all.
- **Strict-gate consumer:** Gates forward progress on every item with a `passMarkPercent > 0`, regardless of `isGraded`. (This is more restrictive than the spec mandates, but it's a real pattern in some LMS.)

Many consumers also implement a common **gradebook-semantics** pattern: items where the learner has scored ≥ `passMarkPercent` (and the item is graded) are reported as **Completed** in the teacher's gradebook view. Whether "completed" maps to a letter grade is a separate gradebook configuration.

The point is plurality. **Author intent is portable across consumers only insofar as the author composes it across multiple fields.** Setting `passMarkPercent: 0` alongside `isGraded: false` is the most permissive combination — virtually no consumer policy can construct a friction surface from "ungraded + no threshold."

### Consumer plurality on `tel:` links (HTML safety profile, §7)

The same consumer-plurality principle governs the HTML safety profile's URL allowlist. `tel:` links are permitted in `<a href>` (per [`HTML_SAFETY.md`](HTML_SAFETY.md) §4.1), but whether the consumer makes them actionable is consumer-policy:

- **K–12 / school-aged-audience consumer:** gates `tel:` links behind a configuration flag, default off. When the flag is off, the link's text remains visible but the `href` is neutralized so taps don't open the dialer.
- **Adult/corporate-training consumer:** typically enables `tel:` unconditionally — calling a sales contact or support line is a legitimate authoring affordance.
- **Print/export consumer:** renders the phone number as plain text; no actionable link.
- **Reporting-only consumer:** treats `tel:` no differently from `mailto:` — passes through verbatim.

The safety profile's domain validator emits a warning (not an error) for `tel:` links so producers know to verify their target audience before shipping. Consumers MUST NOT reject documents that contain `tel:` links; the choice of how to render them is consumer policy.

### Authored-text line-break conventions

Plain-text authored-text fields — `description`, `prompt`, `passage`, `hint`, `feedback.correct`, `feedback.incorrect`, etc. — carry literal newline characters as part of the field value (escaped as `\n` in JSON per RFC 8259). The spec is silent on how consumers should render those characters: a runtime might collapse all whitespace and treat the field as a single block, or honor line breaks, or wrap paragraphs in semantic block elements. The wire format is a string; what consumers do with embedded newlines is consumer policy.

Where consumers want portable rendering across the ecosystem, a useful convention is:

- **`\n\n` (a blank-line boundary) denotes a paragraph break.** Consumers MAY render each paragraph as a block element (e.g. `<p>...</p>`).
- **A single `\n` denotes a line break within a paragraph.** Consumers MAY render it as `<br>` or equivalent.

Producers using this convention get aligned rendering across consumers that adopt it; producers ignoring it get whatever the consumer chooses.

**Some consumers implement this convention** as: `\n\n` becomes `<p>` blocks, single `\n` becomes `<br>`, both with HTML-safe encoding of authored content. **Other consumer models** may legitimately:

- Collapse all whitespace and render the field as a single inline block (typical of grid-cell renderers, screen-reader-first consumers).
- Honor single `\n` as `<br>` but treat `\n\n` the same way (line-break-only convention).
- Render the field through a Markdown processor that gives `\n\n` paragraph semantics plus richer features (lists, emphasis, etc.) — out of scope for this spec but a legitimate consumer choice.

This convention applies only to plain-text authored fields. Trusted-HTML surfaces (`ContentItem.html`, `SignpostItem.customHtml`) carry HTML directly, sanitized per [`HTML_SAFETY.md`](HTML_SAFETY.md), and use the producer's chosen block elements (`<p>`, `<h2>`, `<blockquote>`, etc.) — they do not rely on newline-character conventions.

---

## 4. Author tips

- **For diagnostics, exit tickets, and any item where you don't want a threshold to matter at all:** set `passMarkPercent: 0`. Combined with `isGraded: false` (where appropriate), this is the lowest-friction signal across all consumer models.

- **`isGraded: false` + `passMarkPercent: 0` is the universal "let-them-through" combination.** No consumer policy can reasonably construct a navigation gate from these values.

- **`isGraded: true` + `passMarkPercent: 0`** is a real pattern (exit ticket): graded for record so the teacher sees attempts, but no threshold gate.

- **If you target multiple consumers, prefer composing intent across multiple fields rather than relying on one alone.** A reading of `isGraded: false` alone might still be paired by some consumer with a default 70% threshold and friction. Setting `passMarkPercent: 0` explicitly makes the intent self-evident.

- **Test your content against the consumer you target.** The spec defines the wire format; it doesn't guarantee navigation behavior. Different consumers — and different navigation modes within a consumer — will produce different learner experiences from the same payload.

- **Document author intent in `instructions`.** When a learner sees "Your score doesn't count toward your grade — this is just to help you see where you're starting from," they understand the experience regardless of how the consumer chooses to interpret the fields. The wire payload is for the consumer; the prose is for the human.

---

---

## 5. Signposts + Learning Objectives

A `signpost` item is a structural marker — typically the first or last item in a unit or lesson — that consumers use to orient learners ("In this unit, you will be able to:") or close a section ("You can now:").

**The wire format does not bind a specific rendering**, but the field design suggests an expected pattern that any consumer can implement:

| Field | Wire-level meaning | Expected use |
|---|---|---|
| `signpostType: "intro"` or `"summary"` | The structural role of the signpost | Intro signposts open a section; summary signposts close it |
| `scope: "course" / "unit" / "lesson"` | Which structural level the signpost belongs to | Determines which `objectiveIds[]` set the consumer can read |
| `customHtml` (optional) | Authored prose | When provided, lets the author add motivational/orientational text beyond the auto-rendered objectives |

**The expected pattern (consumer-defined):**

When a course/unit/lesson has objectives assigned via `objectiveIds[]`, consuming applications are expected to render them in or near the matching signpost — typically:

- **Intro signpost:** a header phrase like "*In this unit, you will be able to:*" followed by a bulleted list of the unit's objectives (resolved from `course.objectives[]` via the unit's `objectiveIds`).
- **Summary signpost:** a header phrase like "*You can now:*" followed by a checklist (often with checkmarks) of the same objectives.

The `customHtml` field, when set, lets the author add prose ABOVE or alongside this auto-rendered objectives block — typically motivational framing, an evocative image, an applications-of-the-topic list, etc. The author writes the hook; the consumer auto-renders the objectives.

**Implication for authors:**

- Don't restate the objectives in `customHtml` — the consumer is expected to render them automatically. Doing so creates duplication.
- Don't open `customHtml` with phrasing that clashes with the consumer's likely auto-render header (e.g., "By the end of this unit, you will…" — that's typically what the consumer prepends to the objectives list).
- Do use `customHtml` for what the auto-render can't say: the *why* of the unit, an opening image or visual, an "applications in:" list, a motivational closing.
- For courses delivered to multiple consumers with different rendering policies, prefer brief `customHtml` so the consumer's auto-rendered objectives are always the dominant orientation surface.

**Fallback when there are no objectives:**

If a unit/lesson has no `objectiveIds[]` and no `customHtml`, consumers may render nothing, render a generic placeholder, or skip the signpost entirely — that policy is consumer-defined. Authors who include signposts SHOULD also assign objectives or provide `customHtml`, lest some consumers render an empty stub.

---

## See also

- [NORMATIVE.md](NORMATIVE.md) — binding producer/consumer requirements
- [README.md](README-spec.md) — spec overview
- [examples/11-exercise-item.json](https://lc-json.org/examples/11-exercise-item.json) — graded homework exercise
- [examples/12a-graded-quiz-item.json](https://lc-json.org/examples/12a-graded-quiz-item.json) — typical graded assessment
- [examples/12b-ungraded-quiz-item.json](https://lc-json.org/examples/12b-ungraded-quiz-item.json) — ungraded diagnostic pre-test
- [schemas/exercise-item.schema.json](https://lc-json.org/1.1/exercise-item.schema.json), [schemas/quiz-item.schema.json](https://lc-json.org/1.1/quiz-item.schema.json) — formal schemas
