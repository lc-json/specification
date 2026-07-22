# LC-JSON Question Types — Format Reference

**Spec version:** 1.0
**Purpose:** Per-type property reference for LC-JSON (Learning Content JSON) — the 12 implemented question types and the 7 reserved-for-2027 types.

---

## Table of Contents

1. [Overview](#overview)
2. [Common Properties](#common-properties)
3. [Phase 1: Core Foundation](#phase-1-core-foundation)
4. [Phase 2: Cloze Family](#phase-2-cloze-family)
5. [Phase 3: Text Entry](#phase-3-text-entry)
6. [Phase 4: Structured Tasks (Implemented)](#phase-4-structured-tasks-implemented)
7. [Reserved Types](#reserved-types)
8. [Validation Rules](#validation-rules)

---

## Overview

LC-JSON questions are tagged-union objects. Every question carries a `type` field whose value selects the per-type schema that applies. Consumers dispatch on `type` to validate and render.

**Key requirements:**
- The `type` discriminator value uses canonical **camelCase** (`simpleGapFill`, `multipleChoice`, …). Conforming consumers MUST reject non-canonical casings (`NORMATIVE.md` §5.3).
- All property names use camelCase.
- Every question carries a `globalId` in RFC 4122 UUID form (any version; shape-only validation against the 8-4-4-4-12 hex pattern).
- See [`NORMATIVE.md`](NORMATIVE.md) for the full conformance requirements.

**Supported Question Types (19 total):**

**Phase 1 - Core Foundation:**
1. `simpleGapFill` - Single gap with free text entry
2. `trueFalseQuestion` - Binary choice questions
3. `multipleChoice` - Single or multiple correct answers

**Phase 2 - Cloze Family:**
4. `wordBankCloze` - Gap fill from word bank
5. `multiGapCloze` - Multiple free-text gaps
6. `multipleChoiceCloze` - Multiple dropdown gaps

**Phase 3 - Text Entry:**
7. `shortAnswer` - Free text response
8. `essay` - Long-form text with word limits

**Phase 4 - Structured tasks (implemented):**
9. `matching` - Pair items 1:1, or classify items into categories
10. `ordering` - Sequence items (word / sentence / paragraph variants)
11. `placement` - Place items into anchored gaps in a structured passage (sentence / paragraph / sectionLabel variants; supports decoy gaps for TOEFL Sentence Insertion)
12. `sentenceTransformation` - Cambridge exam-style controlled paraphrase

**Reserved types (per `NORMATIVE.md` §6 — preserved on round-trip; per-type schemas targeted for 2027):**
13. `association` - Group items into categories
14. `hotspot` - Click regions on image
15. `graphicGapMatch` - Visual drag-and-drop
16. `graphicAssociate` - Associate items with images
17. `graphicOrder` - Order items based on images
18. `fileUpload` - Submit documents
19. `mediaPromptedEssay` - Record audio/video

---

## Common Properties

All question types inherit these base properties:

```json
{
  "type": "simpleGapFill",
  "globalId": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Question title",
  "prompt": "",
  "tags": ["tag1", "tag2"],
  "difficulty": 5.0,
  "points": 1.0,
  "hint": "Optional hint text",
  "feedback": {
    "correct": "Feedback shown when the answer is correct",
    "incorrect": "Feedback shown when the answer is incorrect",
    "choiceFeedback": {
      "choice1": "Per-choice feedback (where applicable)"
    }
  }
}
```

**Property Details:**

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `type` | string | ✅ Yes | - | Question type discriminator. Canonical camelCase form. |
| `globalId` | string (UUID) | ✅ Yes | - | RFC 4122 UUID (any version; shape-only validation); stable across versions of the question. |
| `title` | string | ❌ No | `""` | Short title for editorial/list views. |
| `prompt` | string | ✅ Yes | `""` | Main question text. Required for every type; **may be empty** (`""`). Authoritative for the real-content types (true/false, multiple choice, short answer, essay), where it *is* the question. Non-authoritative for the symbolic types, whose structured fields carry the meaning — there it MAY be empty or MAY carry a brief producer-derived readable summary (see the symbolic-type note below). |
| `tags` | string[] | ❌ No | `[]` | Tag array for categorization. |
| `difficulty` | number | ❌ No | `5.0` | Estimated difficulty for the intended learners (0.0 = extremely easy, 10.0 = extremely difficult). |
| `points` | number | ❌ No | `1.0` | Points awarded for a correct answer. |
| `hint` | string | ❌ No | `null` | Optional hint shown to the learner. |
| `feedback` | object | ❌ No | `null` | Optional feedback bundle (see *FeedbackBundle* below). |

`difficulty` is an author estimate, not a subject level, grade level, CEFR level, or Bloom band. It estimates how challenging the question is for its intended learners. Applications SHOULD display it in teacher-readable form, commonly rounded to the nearest whole number on the 0-10 scale, and MAY later compare it with observed first-attempt success rates.

---

## Phase 1: Core Foundation

### 1. SimpleGapFill

**Description:** Single gap with free text entry and multiple acceptable answers.

**Use Case:** Simple fill-in-the-blank questions.

**Example:** "The capital of France is ___."

```json
{
  "type": "simpleGapFill",
  "globalId": "550e8400-e29b-41d4-a716-446655440001",
  "prompt": "",
  "title": "Capital of France",
  "tags": ["geography", "level:A1"],
  "difficulty": 2.0,
  "points": 1.0,
  "sentence": "The capital of France is @@@.",
  "acceptedAnswers": ["Paris", "paris"],
  "caseSensitive": false
}
```

**Type-Specific Properties:**

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `sentence` | string | ✅ Yes | `""` | Sentence with `@@@` marking gap position |
| `acceptedAnswers` | string[] | ✅ Yes | `[]` | List of acceptable answers |
| `caseSensitive` | boolean | ❌ No | `false` | Whether answer matching is case-sensitive |

---

### 2. TrueFalseQuestion

**Description:** Binary choice question with boolean `correctAnswer` as single source of truth. Supports configurable display styles and penalty system.

**Use Case:** True/False, Correct/Incorrect, or visual checkmark/X questions.

**Example:** "Water boils at 100°C at sea level. True or False?"

```json
{
  "type": "trueFalseQuestion",
  "globalId": "550e8400-e29b-41d4-a716-446655440002",
  "prompt": "Water boils at 100°C at sea level.",
  "title": "Boiling Point",
  "tags": ["science", "level:A2"],
  "difficulty": 1.0,
  "points": 1.0,
  "correctAnswer": true,
  "displayStyle": "TrueFalse",
  "penalizeIncorrect": false,
  "incorrectPenaltyPercent": 50.0
}
```

**Type-Specific Properties:**

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `correctAnswer` | boolean | ✅ Yes | - | The correct answer (`true` or `false`). Single source of truth for scoring. |
| `displayStyle` | string | ❌ No | `"TrueFalse"` | UI label style: "TrueFalse", "CorrectIncorrect", "CheckmarkX". Presentation only — does not affect scoring. |
| `penalizeIncorrect` | boolean | ❌ No | `false` | Whether to apply a point penalty for a wrong answer. Independent of item type and `isGraded` — author's choice. Common: `false` when you want learners to try without risk; `true` when guessing should cost something. |
| `incorrectPenaltyPercent` | number | ❌ No | `50.0` | Penalty percentage (0-100). 0%=no penalty, 50%=partial, 100%=full penalty. |

**Import normalization (pre-1.0 lenient migration affordance — NOT conforming behavior).** Some authoring tools historically emitted non-boolean `correctAnswer` values for True/False questions. A consumer MAY accept and normalize the following on read, **purely as a migration aid for ingesting pre-1.0 documents**:

- `true`, `"true"`, `"True"`, `"correct"`, `"tick"`, `"✓"`, `1` → normalized to `true`
- `false`, `"false"`, `"False"`, `"incorrect"`, `"cross"`, `"✗"`, `0` → normalized to `false`

**Conforming behavior under LC-JSON 1.0 is unambiguous:** the schema requires `correctAnswer` to be a JSON boolean (`true` / `false`). Conforming producers MUST emit it as a boolean. Conforming consumers in strict mode MUST reject non-boolean values per [`NORMATIVE.md`](NORMATIVE.md) §5.1 — the reference validator's `--strict` mode (which `tools/run_corpus.py` invokes on every fixture) does so. Tools relying on the normalization above should treat it as a transitional ingestion aid that does not survive into a `--strict`-conforming document on re-export.

**Note:** For True/False/Not Mentioned questions (3 options), use MultipleChoice instead.

---

### 3. MultipleChoice

**Description:** Single or multiple correct answers with optional partial credit and shuffling.

**Use Case:** Traditional multiple-choice questions (MCQ).

**Example:** "Which of the following are programming languages? (Select all that apply)"

```json
{
  "type": "multipleChoice",
  "globalId": "550e8400-e29b-41d4-a716-446655440003",
  "prompt": "Which of the following are programming languages?",
  "title": "Programming Languages",
  "tags": ["programming", "level:B1"],
  "difficulty": 3.0,
  "points": 2.0,
  "options": ["Python", "HTML", "Java", "CSS"],
  "optionsAndPoints": {
    "Python": 1.0,
    "HTML": 0.0,
    "Java": 1.0,
    "CSS": 0.0
  },
  "allowMultipleCorrect": true,
  "allowPartialCredit": true,
  "penalizeIncorrect": false,
  "shuffleOptions": true,
  "showLetterLabels": true
}
```

**Type-Specific Properties:**

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `options` | string[] | ✅ Yes | `[]` | Array of answer choices |
| `optionsAndPoints` | object | ✅ Yes | `{}` | Dictionary mapping options to points (>0 = correct) |
| `allowMultipleCorrect` | boolean | ❌ No | `false` | Allow selecting multiple answers |
| `allowPartialCredit` | boolean | ❌ No | `true` | Award partial credit for partially correct answers |
| `penalizeIncorrect` | boolean | ❌ No | `false` | Deduct points for incorrect selections |
| `shuffleOptions` | boolean | ❌ No | `false` | Randomize option order for each student |
| `showLetterLabels` | boolean | ❌ No | `false` | Display A, B, C, D labels |

---

## Phase 2: Cloze Family

### 4. WordBankCloze

**Description:** Passage with gaps filled from a shared word pool (includes distractors).

**Use Case:** Cambridge FCE/CAE, vocabulary exercises.

**Example:** "Fill in the blanks using words from the word bank."

```json
{
  "type": "wordBankCloze",
  "globalId": "550e8400-e29b-41d4-a716-446655440004",
  "prompt": "",
  "title": "Word Bank Exercise",
  "tags": ["grammar:articles", "level:B1"],
  "difficulty": 5.0,
  "points": 5.0,
  "passage": "I saw @@@1 cat and @@@2 dog in @@@3 park yesterday. @@@4 cat was chasing @@@5 dog.",
  "wordBank": ["a", "an", "the", "some"],
  "gapAcceptedAnswers": {
    "1": ["a"],
    "2": ["a"],
    "3": ["the"],
    "4": ["The"],
    "5": ["the"]
  },
  "gapCaseSensitive": {
    "4": true
  },
  "allowWordReuse": true,
  "bankPosition": "above",
  "gapFeedback": {
    "1": "Remember: 'a' is used before consonants"
  },
  "allowPartialCredit": true
}
```

**Type-Specific Properties:**

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `passage` | string | ✅ Yes | `""` | Text with numbered `@@@1`, `@@@2`, etc. marking gaps (1-based) |
| `wordBank` | string[] | ✅ Yes | `[]` | Pool of words to choose from (includes distractors) |
| `gapAcceptedAnswers` | object | ✅ Yes | `{}` | Dictionary: gap number (1-based) → array of accepted answers |
| `gapCaseSensitive` | object | ❌ No | `null` | Dictionary: gap number → boolean (default: false) |
| `allowWordReuse` | boolean | ❌ No | `false` | Can same word be used multiple times? |
| `bankPosition` | string | ❌ No | `"above"` | Word bank position: "above", "below", "side" |
| `gapFeedback` | object | ❌ No | `null` | Dictionary: gap number → feedback string |
| `allowPartialCredit` | boolean | ❌ No | `true` | Award partial credit for some correct answers |

---

### 5. MultiGapCloze

**Description:** Passage with multiple gaps, each accepting free text with multiple valid answers.

**Use Case:** Cambridge FCE/CAE Reading Part 2 (Open Cloze).

**Example:** "Fill in the blanks (no word bank provided)."

```json
{
  "type": "multiGapCloze",
  "globalId": "550e8400-e29b-41d4-a716-446655440005",
  "prompt": "",
  "title": "Open Cloze Exercise",
  "tags": ["grammar:prepositions", "exam:fce", "level:B2"],
  "difficulty": 6.0,
  "points": 8.0,
  "passage": "She walked @@@1 the park and sat @@@2 a bench @@@3 the lake.",
  "gapAcceptedAnswers": {
    "1": ["through", "in", "into"],
    "2": ["on"],
    "3": ["by", "near", "beside"]
  },
  "gapCaseSensitive": {
    "1": false,
    "2": false,
    "3": false
  },
  "gapFeedback": {
    "2": "We use 'on' with bench"
  },
  "allowPartialCredit": true
}
```

**Type-Specific Properties:**

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `passage` | string | ✅ Yes | `""` | Text with numbered `@@@1`, `@@@2`, etc. marking gaps (1-based) |
| `gapAcceptedAnswers` | object | ✅ Yes | `{}` | Dictionary: gap number (1-based) → array of accepted answers |
| `gapCaseSensitive` | object | ❌ No | `null` | Dictionary: gap number → boolean (default: false) |
| `gapFeedback` | object | ❌ No | `null` | Dictionary: gap number → feedback string |
| `allowPartialCredit` | boolean | ❌ No | `true` | Award partial credit for some correct answers |

---

### 6. MultipleChoiceCloze

**Description:** Passage with multiple gaps, each gap has 3-4 discrete options (dropdown).

**Use Case:** Cambridge FCE/CAE Reading Part 1.

**Example:** "Choose the correct word for each gap from the dropdown."

```json
{
  "type": "multipleChoiceCloze",
  "globalId": "550e8400-e29b-41d4-a716-446655440006",
  "prompt": "",
  "title": "Multiple Choice Cloze",
  "tags": ["vocabulary", "exam:fce", "level:B2"],
  "difficulty": 7.0,
  "points": 6.0,
  "passage": "The weather was @@@1 cold that we decided to stay indoors. We @@@2 a movie instead.",
  "gapOptions": {
    "1": ["so", "such", "very", "too"],
    "2": ["watched", "saw", "looked", "viewed"]
  },
  "correctAnswers": {
    "1": 0,
    "2": 0
  },
  "gapOptionFeedback": {
    "1": {
      "0": "Correct! 'so' is used before adjectives",
      "1": "'such' is used before nouns",
      "2": "'very' doesn't fit with 'that'",
      "3": "'too' suggests excess"
    }
  },
  "allowPartialCredit": true,
  "shuffleOptions": false
}
```

**Type-Specific Properties:**

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `passage` | string | ✅ Yes | `""` | Text with numbered `@@@1`, `@@@2`, etc. marking gaps (1-based) |
| `gapOptions` | object | ✅ Yes | `{}` | Dictionary: gap number (1-based) → array of options |
| `correctAnswers` | object | ✅ Yes | `{}` | Dictionary: gap number (1-based) → correct option index (0-based) |
| `gapOptionFeedback` | object | ❌ No | `null` | Dictionary: gap number → option index → feedback |
| `allowPartialCredit` | boolean | ❌ No | `true` | Award partial credit for some correct answers |
| `shuffleOptions` | boolean | ❌ No | `false` | Randomize option order within each gap |

---

## Phase 3: Text Entry

### 7. ShortAnswer

**Description:** Free text response with multiple acceptable answers and case sensitivity options.

**Use Case:** Short answer questions, name/term identification.

**Example:** "What is the largest planet in our solar system?"

```json
{
  "type": "shortAnswer",
  "globalId": "550e8400-e29b-41d4-a716-446655440007",
  "prompt": "What is the largest planet in our solar system?",
  "title": "Largest Planet",
  "tags": ["science:astronomy", "stage:lower-secondary"],
  "difficulty": 2.0,
  "points": 1.0,
  "acceptedAnswers": ["Jupiter"],
  "caseSensitive": false
}
```

**Type-Specific Properties:**

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `acceptedAnswers` | string[] | ✅ Yes | `[]` | All acceptable answers. The first entry is treated as the canonical form shown in solutions and feedback. |
| `caseSensitive` | boolean | ❌ No | `false` | Whether answer matching is case-sensitive |

---

### 8. Essay

**Description:** Long-form text response with optional word limits and grading rubric.

**Use Case:** Essay questions, extended writing tasks.

**Example:** "Write a 250-word essay about climate change."

```json
{
  "type": "essay",
  "globalId": "550e8400-e29b-41d4-a716-446655440008",
  "prompt": "Write an essay discussing the impact of climate change on global ecosystems.",
  "title": "Climate Change Essay",
  "tags": ["writing", "exam:ielts", "level:C1"],
  "difficulty": 8.0,
  "points": 20.0,
  "expectedAnswer": "Sample model answer...",
  "expectedLines": 15,
  "minWords": 200,
  "maxWords": 300,
  "rubricText": "## Grading Criteria\n- Task Response (25%)\n- Coherence & Cohesion (25%)\n- Lexical Resource (25%)\n- Grammatical Range (25%)"
}
```

**Type-Specific Properties:**

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `expectedAnswer` | string | ❌ No | `""` | Model answer / sample response |
| `expectedLines` | integer | ❌ No | `0` | Suggested number of lines in text area |
| `minWords` | integer | ❌ No | `0` | Minimum word count (0 = no limit) |
| `maxWords` | integer | ❌ No | `0` | Maximum word count (0 = no limit) |
| `rubricText` | string | ❌ No | `null` | Markdown-formatted grading rubric |

---

## Phase 4: Structured Tasks (Implemented)

### 9. Matching

**Description:** Match items to their corresponding match (1:1) or classify items into categories (many-to-one). The shape branches by an explicit `matchingMode` discriminator: `"pairs"` for 1:1 matching where each item has one correct match, and `"classification"` for many-to-one where each item belongs to one category and multiple items may share a category. `distractors` carries decoys in either mode (extra match values in pairs mode; extra category labels in classification mode).

**Use Cases:**

- **`pairs`** — Vocabulary ↔ definition, country ↔ capital, author ↔ work, thinker ↔ idea, cause ↔ effect. Any 1:1 association where the pedagogical meaning lives in the pairing.
- **`classification`** — Time expressions ↔ tense, foods ↔ food group, animals ↔ habitat, sentences ↔ register, examples ↔ argument-role. Any sort where multiple items share each category.

#### Common properties (both modes)

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `matchingMode` | string (`"pairs"` \| `"classification"`) | ✅ Yes | Selects the sub-shape. No default — the schema can't validate the shape without it. |
| `distractors` | string[] | ❌ No | Pairs mode: extra match values with no correct item. Classification mode: extra category labels that don't own any item. Default `[]`. |
| `allowPartialCredit` | boolean | ❌ No | If `true` (default), score per correct row; if `false`, all-or-nothing. |

#### `pairs` mode — properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `pairs` | object[] | ✅ Yes | Each entry is one item-and-match row: `{ "item": string, "match": string }`. Both fields required, `minLength: 1`. Minimum 2 pairs. |

#### `classification` mode — properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `categories` | object[] | ✅ Yes | Each entry is one category: `{ "label": string, "items": string[] }`. `label` required, `minLength: 1`. `items` required, `minItems: 1` (an empty category is meaningless — list it as a `distractors[]` entry instead). Minimum 2 categories. Consumers MUST randomize the row order at render time per [NORMATIVE §5.6](NORMATIVE.md) — source order is grouped by category and would directly expose the answer. |

A document that mixes shapes (both `pairs` and `categories` present, or `matchingMode` omitted) fails validation.

#### Example — `pairs` mode

```json
{
  "type": "matching",
  "globalId": "550e8400-e29b-41d4-a716-446655441502",
  "title": "Roots of Democracy — Match the Thinker",
  "tags": ["politics:enlightenment", "philosophy:political"],
  "points": 8.0,
  "difficulty": 5.0,
  "prompt": "",
  "matchingMode": "pairs",
  "pairs": [
    { "item": "John Locke",         "match": "Government derives its authority from the consent of the governed." },
    { "item": "Jean-Jacques Rousseau", "match": "Citizens form a 'social contract' that creates the legitimate state." },
    { "item": "Baron de Montesquieu", "match": "Power should be divided across separate branches of government." },
    { "item": "John Stuart Mill",   "match": "Liberty is the freedom to act, limited only by harm to others." }
  ],
  "distractors": [
    "The state should own the means of production.",
    "Tradition is the safest guide to political reform."
  ]
}
```

**See `examples/15-matching.json` for the full canonical pairs example.**

#### Example — `classification` mode

```json
{
  "type": "matching",
  "globalId": "550e8400-e29b-41d4-a716-446655441550",
  "title": "Time Expressions — Classify by Tense",
  "tags": ["grammar:tenses:past-simple", "grammar:tenses:present-perfect", "level:B1"],
  "points": 6.0,
  "difficulty": 4.0,
  "prompt": "",
  "matchingMode": "classification",
  "categories": [
    { "label": "past simple",     "items": ["a year ago", "yesterday", "in May 2019"] },
    { "label": "present perfect", "items": ["all my life", "never", "since 2020"] }
  ],
  "distractors": ["future continuous"]
}
```

**See `examples/15b-matching-classification.json` for the full canonical classification example.**

#### Renderer expectation

In `pairs` mode, consumers MAY render two columns with drag-and-drop pairing (or a per-row dropdown of choosable matches). In `classification` mode, consumers MAY render the items as draggable chips and the category labels (plus distractors) as drop zones. Both presentations are consumer-defined; the wire format describes the structural relationship and hints at the affordance.

#### Scoring

Per-row scoring. In `pairs` mode, each row is one item↔match comparison. In `classification` mode, each item is compared against its category's label (the row is correct if the learner placed the item under the correct label). `allowPartialCredit: true` (default) awards partial credit per correct row; `false` requires every row correct for any credit.

---

### 10. Ordering

**Description:** Sequence items correctly. Students arrange shuffled tiles into the teacher-defined correct order.

**Use Case:** Sentence word-order unscrambling, ordering process steps in a paragraph, ordering paragraphs of an essay, chronological ordering — any task where pedagogical meaning lives in the sequence.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `sourceText` | string | Yes | The original sentence or passage shown for context (the correct ordering when items are joined) |
| `items` | string[] | Yes | Tiles in correct order. `items[i]` is the correct tile at position `i` |
| `distractors` | string[] | No | Extra tiles that do not belong in the sequence (mixed into the tile bank as decoys) |
| `scoringMode` | string | No | Scoring policy hint: `"strict"` = all-or-nothing exact match; `"kendall"` = partial credit via Kendall tau distance. When omitted, the recommended default is `"strict"` for `orderingUnit: "word"` and `"kendall"` for `"sentence"` / `"paragraph"`. See Scoring below |
| `orderingUnit` | string | No | Display granularity hint: `"word"` (default), `"sentence"`, or `"paragraph"`. See variants below |

#### Display variants (`orderingUnit`)

`orderingUnit` is an advisory hint — the same `ordering` discriminator covers all three variants and consumers MAY render uniformly. The hint lets a consumer choose layout that fits the chunk size:

| `orderingUnit` | Typical chunk size | Typical layout | Example use |
|---|---|---|---|
| `"word"` | one word or short phrase | inline draggable tokens on one line | Unscramble a sentence — see [`16-ordering.json`](https://lc-json.org/examples/16-ordering.json) |
| `"sentence"` | one sentence (10–30 words) | stacked card blocks, vertical | Order steps of a process, narrative beats — see [`16b-sentence-ordering.json`](https://lc-json.org/examples/16b-sentence-ordering.json) |
| `"paragraph"` | one paragraph (50–100 words) | stacked block cards, vertical, larger | Order paragraphs of an essay — see [`16c-paragraph-ordering.json`](https://lc-json.org/examples/16c-paragraph-ordering.json) |

#### Word-level example

```json
{
  "type": "ordering",
  "globalId": "550e8400-e29b-41d4-a716-446655440010",
  "prompt": "",
  "title": "Word Order",
  "sourceText": "She went shopping yesterday.",
  "items": ["She", "went", "shopping", "yesterday"],
  "distractors": ["quickly"],
  "points": 1.0,
  "tags": ["grammar", "level:A2"]
}
```

(`orderingUnit` is omitted — the default `"word"` applies. `scoringMode` is also omitted; consumers default to `"strict"` for word-level — see Scoring below.)

#### Sentence-level example

```json
{
  "type": "ordering",
  "globalId": "550e8400-e29b-41d4-a716-446655441620",
  "prompt": "",
  "title": "Cellular Respiration — Order the Stages",
  "sourceText": "Glucose enters the cell and is split into two pyruvate molecules… (full passage)",
  "items": [
    "Glucose enters the cell and is split into two pyruvate molecules in the cytoplasm during glycolysis…",
    "Each pyruvate is then transported into the mitochondrion and converted to acetyl-CoA…",
    "…"
  ],
  "scoringMode": "kendall",
  "orderingUnit": "sentence",
  "points": 4.0,
  "tags": ["biology:cell-biology:respiration"]
}
```

See [`16b-sentence-ordering.json`](https://lc-json.org/examples/16b-sentence-ordering.json) for the full example.

#### Paragraph-level example

Same shape, with `orderingUnit: "paragraph"` and longer items. See [`16c-paragraph-ordering.json`](https://lc-json.org/examples/16c-paragraph-ordering.json) — a four-paragraph essay-structure reorder.

#### Scoring

Two modes selected by `scoringMode`:

- **`"strict"`** — all items must be in their correct positions AND no distractors placed in the answer area. Any deviation = 0 points.
- **`"kendall"`** — partial credit by Kendall tau distance over the learner's permutation: each discordant pair (one item placed before another that should follow it) reduces the score. With *N* items and *k* discordant pairs, the score is `points × (1 − k / (N × (N−1) / 2))`. Useful when the chunks have a single defensible order but partial credit reflects partial understanding (e.g., process narratives, essay structure).

When `scoringMode` is omitted, the recommended default is `"strict"` for `orderingUnit: "word"` (where pairwise inversions don't have pedagogical meaning — a sentence either reads correctly or it doesn't) and `"kendall"` for `orderingUnit: "sentence"` and `"paragraph"` (where partial credit reflects partial understanding of the discourse structure). Consumers that don't support partial credit MAY collapse `"kendall"` to `"strict"`.

---

### 11. Placement

**Description:** Place items into anchored gaps in a structured passage. Each placement entry pairs a 1-based gap-marker number (`@@@N` in the passage) with the item that belongs in that gap. Distractors are extra items with no correct gap; passage gap-markers without a corresponding placement entry are decoy positions — a TOEFL-style variant where one item must be placed into one of several candidate positions. The shape mirrors the matching-redesign principle: for structured tasks where the relationship between items and slots is the data, the relationship is encoded explicitly per row.

**Use Cases:**

- **Cambridge B2 First Part 6** — sentence-level "missing sentences" tasks where 6 short sentences must be placed back into a 6-gap article. Use `placementUnit: "sentence"`. See `examples/17a-sentence-placement.json`.
- **Cambridge C1 Advanced Part 7** — paragraph-level reordering of a 6-gap essay. Use `placementUnit: "paragraph"`. See `examples/17b-paragraph-placement.json`.
- **IELTS Matching Headings** — short headings labeled to sections of a passage. Use `placementUnit: "sectionLabel"`. The same shape covers analytical meta-labels (e.g., labeling each paragraph 'thesis', 'counter-argument', 'evidence') — both real headings and analytical labels share the wire format. See `examples/17c-section-label-placement.json`.
- **TOEFL Sentence Insertion** — a single missing sentence with multiple candidate positions; only one is correct. Author 4 `@@@N` markers in `passage` and a single `placements[]` entry whose `gap` is the correct position. The unanswered markers are decoy gaps. Use `placementUnit: "sentence"` and `allowPartialCredit: false` (single-gap → all-or-nothing). See `examples/17d-toefl-insertion-placement.json`.

**Word-level placement** is covered by [`wordBankCloze`](#5-wordbankcloze) — placement does not include `"word"` in the `placementUnit` enum.

**Symbolic-type `prompt` convention.** On the eight symbolic question types (the gap-fill family, sentence transformation, matching, ordering, placement) the structured fields carry the question's meaning, so `prompt` is **non-authoritative**. It remains required but **MAY be empty** (`""`); equally, a producer MAY populate it with a brief human-readable summary derived from the question's content — a readable preview, not authored framing. See `examples/01b-simple-gap-fill-readable-prompt.json`, which shows `"I saw ___ elephant at the zoo yesterday."` as one valid form, with `""` (as in `examples/01-simple-gap-fill.json`) equally valid. Consumers MUST NOT rely on a symbolic `prompt`'s content for scoring, rendering, equality, or deduplication.

**Framing instructions** for the exercise (e.g., *"Place these sentences in the gaps where they best fit. Some markers are decoys."*) belong on the parent `exerciseItem.instructions` (or `quizItem.instructions`) field, not duplicated into each question's `prompt`. Consumers typically render the parent item's `instructions` once at the top of the exercise — above all its questions — so per-question framing would be redundant. This applies symmetrically to all eight symbolic question types.

#### Properties

| Property | Type | Required | Description |
|---|---|---|---|
| `placementUnit` | string | ✅ Yes | Display granularity hint: `"sentence"`, `"paragraph"`, or `"sectionLabel"`. Default `"sentence"`. Each value carries a different marker-placement convention — see the table below. |
| `passage` | string | ✅ Yes | Structured text with `@@@1`, `@@@2`, … gap markers (1-based). Must contain at least one marker (the schema's `pattern` keyword enforces this). Plain text only — no HTML. |
| `placements` | object[] | ✅ Yes | Each entry: `{ "gap": int, "item": string }`. Both required; `gap` ≥ 1; `item.minLength` 1. Order is author-free. `minItems: 1` — permits the TOEFL variant (1 item, multiple candidate gaps). |
| `distractors` | string[] | ❌ No | Extra **items** with no correct gap. Default `[]`. Distinct from decoy gaps (extra `@@@N` markers without a corresponding `placements[].gap` entry). |
| `allowPartialCredit` | boolean | ❌ No | Award partial credit per correct gap instead of all-or-nothing. Default `true`. |

#### Display variants (`placementUnit`)

`placementUnit` is an advisory hint and a marker-placement convention. The same `placement` discriminator covers all three variants and consumers MAY render uniformly.

| `placementUnit` | Typical render | Marker-placement convention | Example use |
|---|---|---|---|
| `"sentence"` | Inline drop slot at each marker | Marker appears mid-prose; surrounding whitespace and punctuation are the author's choice. | Cambridge B2 missing-sentences (17a) and TOEFL Sentence Insertion (17d). |
| `"paragraph"` | Block-level drop slot between paragraphs | Marker is the entire content of its paragraph — surrounded by `\n\n` or at start/end of passage. | Cambridge C1 paragraph-reordering (17b). |
| `"sectionLabel"` | Label slot above / leading edge of a paragraph | Marker at the start of the section it labels (first non-whitespace token of a paragraph), followed by a space and then the section's content. | IELTS Matching Headings and analytical meta-labels (17c). |

#### Marker-placement conventions

`passage` is plain text. Consumers detect paragraph boundaries by `\n\n` (double newline). The conventions above are documented in the schema's `placementUnit` description and given side-by-side here:

```text
sentence:
  "The experiment began with a simple question. @@@1 The results surprised the team."

paragraph:
  "Coined money had served European trade for centuries.\n\n@@@1\n\nWhat converted private bills into public currency was the cost of seventeenth-century war."

sectionLabel:
  "@@@1 Paper currency did not spread simply because it was convenient.\n\n@@@2 Before paper notes, European trade depended mainly on metal coin."
```

#### Decoy gaps (TOEFL Sentence Insertion variant)

A `passage` with N `@@@N` markers and fewer than N `placements[]` entries is valid: the unanswered markers are **decoy gaps** — candidate positions where the missing item could plausibly fit but doesn't. This natively expresses TOEFL Sentence Insertion: 4 candidate positions, 1 correct placement. See `examples/17d-toefl-insertion-placement.json`.

This is distinct from **decoy items** (`distractors[]`) — extra content the learner has but should not place anywhere.

#### Validator policy

Hard errors (validation fails):

- Every `placements[].gap` MUST reference a `@@@N` marker present in `passage`. Orphan placement entries fail.
- No duplicate `gap` values within `placements[]`.
- `gap` must be a positive integer (≥ 1).
- `passage` MUST contain at least one `@@@N` marker (enforced by the schema's `pattern` keyword).

Soft warnings (NOTE-tier, not blocking):

- `@@@N` markers SHOULD be sequential starting at 1 (`1, 2, 3, …`). Inherits the `wordBankCloze` convention.
- Per-`placementUnit` marker-placement convention violations: `paragraph` markers that sit mid-prose alongside other text rather than alone on a paragraph; `sectionLabel` markers that don't appear at the start of a paragraph. `sentence` mode has no positional rule.
- A `@@@N` marker without a corresponding `placements[].gap` entry is **not** a warning — it is a valid decoy gap. The validator distinguishes intentional decoys from authoring errors only by inference.

#### Scoring

Per-gap scoring against the authored `placements[]`. With `allowPartialCredit: true` (default), each gap whose chosen item matches the authored item is worth `points / placements.length`; remaining gaps contribute zero. With `allowPartialCredit: false`, every gap must be correct for any credit. Decoy gaps (markers without a `placements[]` entry) are unscored — placing an item into one is a "wrong gap" event whose treatment is consumer-defined; placing nothing into one is the expected case.

---

### 12. SentenceTransformation

**Description:** Cambridge exam-style controlled paraphrase tasks.

**Use Case:** Cambridge FCE/CAE Use of English Part 4 (Key Word Transformation).

**Example:** Transform sentence using given keyword.

```json
{
  "type": "sentenceTransformation",
  "globalId": "550e8400-e29b-41d4-a716-446655440018",
  "prompt": "",
  "title": "Key Word Transformation",
  "tags": ["grammar", "exam:fce", "level:B2"],
  "difficulty": 8.0,
  "points": 2.0,
  "promptSentence": "I haven't seen John for three weeks.",
  "keyword": "LAST",
  "targetSentence": "The @@@ was three weeks ago.",
  "allOrNothing": false,
  "acceptedChunks": {
    "1": ["last time"],
    "2": ["I saw John"]
  },
  "chunkFeedback": {
    "1": "Use 'LAST' + 'time'. The fixed phrase is 'the last time'.",
    "2": "Past simple 'saw' is needed here, not present perfect 'have seen'."
  }
}
```

**Type-Specific Properties:**

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `promptSentence` | string | ✅ Yes | `""` | Original sentence to transform |
| `keyword` | string | ✅ Yes | `""` | Word that MUST be used (uppercase) |
| `targetSentence` | string | ✅ Yes | `""` | Template with `@@@` for answer chunks |
| `allOrNothing` | boolean | ❌ No | `false` | All chunks correct or zero points |
| `acceptedChunks` | object | ✅ Yes | `{}` | Dictionary: chunk index → array of accepted answers |
| `chunkCaseSensitive` | object | ❌ No | `null` | Dictionary: chunk index → boolean (default: false) |
| `chunkFeedback` | object | ❌ No | `null` | Dictionary: chunk index → feedback string |

---

## Reserved Types

The seven question types in this section are reserved in the `question-base.schema.json` discriminator enum but do not yet have per-type schemas; full implementation is targeted for 2027. Per [`NORMATIVE.md`](NORMATIVE.md) §6, conforming consumers MUST preserve them in full across read/write cycles (every field, value, and nested structure — per §6.2/§6.4), MUST treat earned points as 0, and SHOULD render a non-interactive placeholder. Producers SHOULD NOT emit reserved types in cross-implementation distribution.

### 13. Association

**Description:** Group items into categories (Categorization).

**Use Case:** Classify items, group by category.

**Status:** 🔒 Reserved (per `NORMATIVE.md` §6) — discriminator name is reserved in 1.0; per-type schema is targeted for 2027. Producers SHOULD NOT emit reserved types in cross-implementation distribution; consumers MUST preserve them in full across read/write cycles (every field, value, and nested structure — per §6.2/§6.4), MUST treat earned points as 0, and SHOULD render a non-interactive placeholder. The example below shows only the `question-base` fields any reserved-type instance must carry.

```json
{
  "type": "association",
  "globalId": "550e8400-e29b-41d4-a716-446655440011",
  "prompt": "Group these words by part of speech",
  "title": "Parts of Speech",
  "tags": ["grammar", "level:B1"],
  "difficulty": 5.0,
  "points": 4.0
}
```

**Note:** Per-type properties are not defined in 1.0; tool-specific extension fields MAY be carried (consumers MUST preserve them per `NORMATIVE.md` §6.4 round-trip preservation).

---

### 14. Hotspot

**Description:** Click regions on image (HotspotImage).

**Use Case:** Image-based identification, anatomy diagrams.

**Status:** 🔒 Reserved (per `NORMATIVE.md` §6) — discriminator name is reserved in 1.0; per-type schema is targeted for 2027. Producers SHOULD NOT emit reserved types in cross-implementation distribution; consumers MUST preserve them in full across read/write cycles (every field, value, and nested structure — per §6.2/§6.4), MUST treat earned points as 0, and SHOULD render a non-interactive placeholder. The example below shows only the `question-base` fields any reserved-type instance must carry.

```json
{
  "type": "hotspot",
  "globalId": "550e8400-e29b-41d4-a716-446655440012",
  "prompt": "Click on the heart in the diagram",
  "title": "Anatomy Hotspot",
  "tags": ["science:biology", "level:B1"],
  "difficulty": 4.0,
  "points": 2.0
}
```

**Note:** Per-type properties are not defined in 1.0; tool-specific extension fields MAY be carried (consumers MUST preserve them per `NORMATIVE.md` §6.4 round-trip preservation).

---

### 15. GraphicGapMatch

**Description:** Visual arrangement (DragAndDrop).

**Use Case:** Drag-and-drop activities, visual matching.

**Status:** 🔒 Reserved (per `NORMATIVE.md` §6) — discriminator name is reserved in 1.0; per-type schema is targeted for 2027. Producers SHOULD NOT emit reserved types in cross-implementation distribution; consumers MUST preserve them in full across read/write cycles (every field, value, and nested structure — per §6.2/§6.4), MUST treat earned points as 0, and SHOULD render a non-interactive placeholder. The example below shows only the `question-base` fields any reserved-type instance must carry.

```json
{
  "type": "graphicGapMatch",
  "globalId": "550e8400-e29b-41d4-a716-446655440013",
  "prompt": "Drag the labels to the correct positions on the diagram",
  "title": "Label Diagram",
  "tags": ["science", "level:B2"],
  "difficulty": 6.0,
  "points": 5.0
}
```

**Note:** Per-type properties are not defined in 1.0; tool-specific extension fields MAY be carried (consumers MUST preserve them per `NORMATIVE.md` §6.4 round-trip preservation).

---

### 16. GraphicAssociate

**Description:** Associate items with images.

**Use Case:** Match text with images.

**Status:** 🔒 Reserved (per `NORMATIVE.md` §6) — discriminator name is reserved in 1.0; per-type schema is targeted for 2027. Producers SHOULD NOT emit reserved types in cross-implementation distribution; consumers MUST preserve them in full across read/write cycles (every field, value, and nested structure — per §6.2/§6.4), MUST treat earned points as 0, and SHOULD render a non-interactive placeholder. The example below shows only the `question-base` fields any reserved-type instance must carry.

```json
{
  "type": "graphicAssociate",
  "globalId": "550e8400-e29b-41d4-a716-446655440014",
  "prompt": "Match each animal with its habitat",
  "title": "Animal Habitats",
  "tags": ["science:biology", "level:A2"],
  "difficulty": 4.0,
  "points": 3.0
}
```

**Note:** Per-type properties are not defined in 1.0; tool-specific extension fields MAY be carried (consumers MUST preserve them per `NORMATIVE.md` §6.4 round-trip preservation).

---

### 17. GraphicOrder

**Description:** Order items based on images.

**Use Case:** Sequence images, visual ordering.

**Status:** 🔒 Reserved (per `NORMATIVE.md` §6) — discriminator name is reserved in 1.0; per-type schema is targeted for 2027. Producers SHOULD NOT emit reserved types in cross-implementation distribution; consumers MUST preserve them in full across read/write cycles (every field, value, and nested structure — per §6.2/§6.4), MUST treat earned points as 0, and SHOULD render a non-interactive placeholder. The example below shows only the `question-base` fields any reserved-type instance must carry.

```json
{
  "type": "graphicOrder",
  "globalId": "550e8400-e29b-41d4-a716-446655440015",
  "prompt": "Put these images in the correct order to show the life cycle",
  "title": "Life Cycle Order",
  "tags": ["science:biology", "level:B1"],
  "difficulty": 5.0,
  "points": 4.0
}
```

**Note:** Per-type properties are not defined in 1.0; tool-specific extension fields MAY be carried (consumers MUST preserve them per `NORMATIVE.md` §6.4 round-trip preservation).

---

### 18. FileUpload

**Description:** Submit documents.

**Use Case:** Assignment submission, file uploads.

**Status:** 🔒 Reserved (per `NORMATIVE.md` §6) — discriminator name is reserved in 1.0; per-type schema is targeted for 2027. Producers SHOULD NOT emit reserved types in cross-implementation distribution; consumers MUST preserve them in full across read/write cycles (every field, value, and nested structure — per §6.2/§6.4), MUST treat earned points as 0, and SHOULD render a non-interactive placeholder. The example below shows only the `question-base` fields any reserved-type instance must carry.

```json
{
  "type": "fileUpload",
  "globalId": "550e8400-e29b-41d4-a716-446655440016",
  "prompt": "Upload your completed assignment (PDF format)",
  "title": "Assignment Submission",
  "tags": ["assignment", "level:C1"],
  "difficulty": 0.0,
  "points": 50.0
}
```

**Note:** Per-type properties are not defined in 1.0; tool-specific extension fields MAY be carried (consumers MUST preserve them per `NORMATIVE.md` §6.4 round-trip preservation).

---

### 19. MediaPromptedEssay

**Description:** Record audio/video answer.

**Use Case:** Speaking tasks, oral presentations.

**Status:** 🔒 Reserved (per `NORMATIVE.md` §6) — discriminator name is reserved in 1.0; per-type schema is targeted for 2027. Producers SHOULD NOT emit reserved types in cross-implementation distribution; consumers MUST preserve them in full across read/write cycles (every field, value, and nested structure — per §6.2/§6.4), MUST treat earned points as 0, and SHOULD render a non-interactive placeholder. The example below shows only the `question-base` fields any reserved-type instance must carry.

```json
{
  "type": "mediaPromptedEssay",
  "globalId": "550e8400-e29b-41d4-a716-446655440017",
  "prompt": "Record a 2-minute audio response describing your favorite place",
  "title": "Speaking Task",
  "tags": ["speaking", "exam:ielts", "level:B2"],
  "difficulty": 7.0,
  "points": 10.0
}
```

**Note:** Per-type properties are not defined in 1.0; tool-specific extension fields MAY be carried (consumers MUST preserve them per `NORMATIVE.md` §6.4 round-trip preservation).

---

## Validation Rules

### Type Discriminator
- ✅ `"type"` value MUST match one of the supported types in canonical **camelCase**: `simpleGapFill`, `multipleChoice`, `trueFalseQuestion`, etc.
- ❌ Non-conforming: `"type": "SimpleGapFill"` (pre-1.0 PascalCase). Conforming consumers MUST reject per `NORMATIVE.md` §5.3.
- ❌ Non-conforming: `"type": "simplegapfill"` (wrong case). Conforming consumers MUST reject.
- ❌ Invalid: `"type": "GapFill"` — not a recognized discriminator.

### Common Properties
- ✅ `globalId` must be a valid RFC 4122 UUID (any version; shape-only validation against the 8-4-4-4-12 hex pattern); required per `NORMATIVE.md` §4.4.
- ✅ `difficulty` must be 0.0 to 10.0.
- ✅ `points` must be a non-negative number (minimum `0.0`); MAY be `null` to inherit a consumer-default scoring weight. Use `0` for ungraded questions; positive values for graded.
- ✅ `tags` must be array of strings (can be empty; per the empty-default-strip rule in spec examples, omit when empty).

### Type-Specific Validation

**SimpleGapFill:**
- ✅ `sentence` must contain exactly one `@@@` marker
- ✅ `acceptedAnswers` must have at least one answer

**TrueFalseQuestion:**
- ✅ `correctAnswer` must be a boolean (`true` or `false`)
- ✅ `displayStyle` if present must be one of: "TrueFalse", "CorrectIncorrect", "CheckmarkX"

**MultipleChoice:**
- ✅ `options` must have at least 2 items
- ✅ `optionsAndPoints` must have entries for all options
- ✅ At least one option must have points > 0

**WordBankCloze / MultiGapCloze:**
- ✅ Numbered `@@@1`, `@@@2`, etc. in `passage` must match `gapAcceptedAnswers` count
- ✅ Gap numbers must be sequential starting at 1 (1, 2, 3, ...)
- ✅ Each gap must have at least one accepted answer

**MultipleChoiceCloze:**
- ✅ Numbered `@@@1`, `@@@2`, etc. in `passage` must match `gapOptions` and `correctAnswers` count
- ✅ `correctAnswers` indices must be valid (within option array bounds)

**SentenceTransformation:**
- ✅ `keyword` must appear in student's answer (validated by renderer)
- ✅ `targetSentence` must contain **exactly one** `@@@` placeholder — chunks are sequential answer pieces typed at that single position, not separate gaps. Multiple `@@@` markers are ambiguous and non-conforming.
- ✅ Chunk indices in `acceptedChunks` must be sequential starting from 1 (`"1"`, `"2"`, `"3"`, …)

---

## Complete Example: ExerciseItem with Mixed Questions

```json
{
  "type": "exercise",
  "globalId": "550e8400-e29b-41d4-a716-446655440100",
  "title": "Grammar Practice Exercise",
  "sequence": 0,
  "instructions": "Complete all questions to the best of your ability.",
  "suggestedTime": 15,
  "isOptional": false,
  "isGraded": true,
  "points": 10.0,
  "passMarkPercent": 70.0,
  "questions": [
    {
      "type": "simpleGapFill",
      "globalId": "550e8400-e29b-41d4-a716-446655440101",
      "prompt": "",
      "title": "Articles",
      "tags": ["grammar:articles"],
      "difficulty": 3.0,
      "points": 2.0,
      "sentence": "I saw @@@ elephant at the zoo.",
      "acceptedAnswers": ["an"],
      "caseSensitive": false
    },
    {
      "type": "multipleChoice",
      "globalId": "550e8400-e29b-41d4-a716-446655440102",
      "prompt": "Which sentence is grammatically correct?",
      "title": "Correct Sentence",
      "tags": ["grammar:tenses"],
      "difficulty": 5.0,
      "points": 3.0,
      "options": [
        "She go to school every day.",
        "She goes to school every day.",
        "She going to school every day.",
        "She is go to school every day."
      ],
      "optionsAndPoints": {
        "She go to school every day.": 0.0,
        "She goes to school every day.": 1.0,
        "She going to school every day.": 0.0,
        "She is go to school every day.": 0.0
      },
      "allowMultipleCorrect": false,
      "allowPartialCredit": false,
      "penalizeIncorrect": false,
      "shuffleOptions": true,
      "showLetterLabels": true
    },
    {
      "type": "trueFalseQuestion",
      "globalId": "550e8400-e29b-41d4-a716-446655440103",
      "prompt": "The past tense of 'go' is 'went'.",
      "title": "Past Tense",
      "tags": ["grammar:irregular-verbs"],
      "difficulty": 2.0,
      "points": 1.0,
      "correctAnswer": true,
      "displayStyle": "TrueFalse",
      "penalizeIncorrect": false,
      "incorrectPenaltyPercent": 0.0
    }
  ]
}
```

---

## Related Documentation

- [`NORMATIVE.md`](NORMATIVE.md) — Conformance requirements (RFC 2119 keywords, producer/consumer roles).
- [`README.md`](README-spec.md) — Specification overview.
- [`schemas/`](https://github.com/lc-json/specification/tree/main/schemas) — JSON Schema files (the contract for each type).
- [`examples/`](https://github.com/lc-json/specification/tree/main/examples) — Per-type example files (`01-simple-gap-fill.json` … `16c-paragraph-ordering.json`).
- [`tests/`](tests/) — Conformance test corpus.

---

**Version history:**
- 1.0-rc.1 (2026-05-25) — initial release candidate; internal, never publicly announced.
- 1.0-rc.2 (2026-05-30) — first publicly announced release candidate; `prompt`-field correction.
- 1.0-rc.3 (2026-06-13) — localization model, corpus expansion; `sentenceTransformation` schema drops two prototype-era fields.
- 1.0 (target 2026-06-30) — final release.
