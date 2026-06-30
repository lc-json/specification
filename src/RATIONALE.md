# LC-JSON Rationale and Positioning

**Status:** Informative  
**Spec version context:** LC-JSON 1.0  
**Audience:** teachers, curriculum designers, institutional reviewers, educational software developers, and implementers evaluating LC-JSON for adoption.

This document is **informative**, not normative. It explains the design rationale and positioning behind LC-JSON. Conformance requirements remain in [`NORMATIVE.md`](NORMATIVE.md).

LC-JSON describes itself as an **open learning-content interchange specification** rather than an "industry standard." That word is reserved for formats whose acceptance has been ratified by a recognized body or by long ecosystem use. LC-JSON has neither yet, and overclaiming would invite reasonable skepticism.

## The Problem

Teachers and institutions create large amounts of learning content: courses, lessons, readings, exercises, quizzes, feedback, and assessments. Too often, that content becomes tied to the tool that created it.

Common problems include:

- A course can be exported, but the export is difficult for another tool to understand.
- Question banks lose feedback, scoring intent, tags, or structure during transfer.
- Teachers cannot inspect their own course files without proprietary tooling.
- Institutions cannot easily preserve or migrate teacher-authored content across platforms.
- Accessibility metadata can be lost when content is exported, imported, edited, or repackaged.

LC-JSON exists to make learning content portable in a way that is both technically reliable and inspectable by the people who own the content.

## What LC-JSON Is

LC-JSON is an **open learning-content interchange specification**.

For teachers, it can be understood as a **portable course file format**: a way to store courses, lessons, questions, answers, feedback, and related teaching material in a file that compatible tools can read.

For developers, LC-JSON defines a schema-validated JSON wire format plus producer/consumer conformance rules for exchanging learning content.

LC-JSON 1.0 defines two artifact types:

- **Course** — hierarchical learning content: Course -> Units -> Lessons -> Items -> Questions.
- **QuestionSet** — a flat list of questions for question-bank exchange and packaged delivery.

The practical goal is to preserve teacher-authored instructional intent: sequence, explanations, questions, distractors, feedback, objectives, tags, rubrics, and grading intent.

## Design Principles

### Machine-Validatable, Human-Inspectable

LC-JSON documents validate against published JSON Schemas, but they are also designed so that authored content remains visible in the file.

A teacher, curriculum designer, or teacher-developer should be able to open a course JSON file and recognize courses, units, lessons, items, prompts, choices, answers, and feedback without proprietary tooling.

This is a deliberate stance against formats whose meaning only emerges through tooling. It is offered without promise of zero technical fields — portability requires some, and `$schema`, `specVersion`, and `globalId` exist for that reason. The promise is that the pedagogical structure stays inspectable to the people who authored it. Where field-naming or structural trade-offs arise during spec evolution, the spec favors the form that keeps pedagogical content recognizable.

### Hierarchy Follows Pedagogy

LC-JSON uses the structure teachers already recognize:

```text
Course -> Unit -> Lesson -> Item -> Question
```

This is not a database-first shape. It is a teaching-content shape.

### Plain Property Names

LC-JSON favors readable property names where technically possible:

- `prompt`, not `p`.
- `acceptedAnswers`, not `accAns`.
- `passMarkPercent`, not `pmp`.
- `feedback`, not an opaque metadata bundle.

The goal is not to remove every technical term. The goal is to keep teaching intent visible.

### No Envelope Tricks

LC-JSON uses a flat document root with `$schema`, `documentType`, and `specVersion` as root-level siblings. The course or question-set payload lives beside those fields, not hidden inside an extra wrapper.

This keeps schema dispatch explicit while avoiding unnecessary nesting.

### Accessibility Metadata Must Survive Transformation

Learning content often moves through multiple tools before it reaches learners. LC-JSON therefore treats accessibility metadata as something that must survive import/export cycles.

Base LC-JSON consumer conformance includes a preservation floor for accessibility-relevant data such as image `alt`, media `<track>`, `lang`, `dir`, `language`, `supportLanguage`, and reserved-type accessibility metadata. Tools that additionally claim the LC-JSON Accessibility Profile take on the rendering obligations defined in [`ACCESSIBILITY.md`](ACCESSIBILITY.md).

## Where LC-JSON Fits

LC-JSON is not trying to replace every educational specification or format.

It focuses on a specific problem: portable teacher-authored courses and questions in a JSON-native format that tools can validate, exchange, preserve, and inspect.

LC-JSON is most useful when a team needs:

- portable course files,
- question-bank exchange,
- schema validation before import,
- preservation of feedback and scoring intent,
- round-trip preservation of unsupported future question types,
- a format that teacher-developers and technical curriculum teams can inspect directly.

Runtime delivery, gradebook integration, learner analytics, roster sync, and LMS-specific workflows remain implementation concerns unless a future LC-JSON version explicitly adds a portable contract for them.

A typical adoption path is to author or preserve content in LC-JSON, then export or map selected surfaces to delivery, package, or analytics layers such as QTI, Common Cartridge, H5P, xAPI, or Caliper where needed.

## Landscape

LC-JSON is one of several specifications that touch learning content. It sits at a specific layer — **content interchange** — and is intended to be used alongside, not instead of, the formats that handle adjacent concerns.

| Format | Layer | Relation to LC-JSON |
|---|---|---|
| **LTI 1.3 / Advantage** | Tool launch, deep linking, roster, grade passback | Different layer. LTI is how an LMS launches and integrates with an external tool; LC-JSON is the content that tool may have authored or consumed. Complementary. |
| **xAPI / cmi5** | Learning activity records | Different layer. xAPI describes what a learner did; LC-JSON describes the content they did it with. Complementary. |
| **SCORM 2004** | Packaged courseware delivery and runtime API | Older, XML-based, designed for self-paced corporate compliance training and bound to a runtime API. LC-JSON is editable interchange, not a delivery wrapper. |
| **IMS Common Cartridge** | Multi-format content package | Bundles QTI, SCORM, web links, and a manifest into a single archive. LC-JSON is a single JSON-native artifact rather than a package format. |
| **QTI 2.x / 3.0** | Question and assessment interchange | Closest peer. QTI was conceived as XML; 3.0 added a JSON binding but the conceptual model remains XML-shaped and the surface area is broad. LC-JSON is JSON-native from the start, course-shaped as well as question-bank-shaped, narrower in surface, and designed for direct human inspection. |
| **OneRoster** | Roster, enrollment, grade exchange | Different layer; orthogonal to content. |
| **CASE** | Competency and academic-standards framework | Different layer. CASE describes the competencies a course might address; LC-JSON describes the course content itself. Complementary. |
| **H5P** | Interactive content packages and runtimes | Different layer. H5P provides executable interaction types and player/runtime semantics; LC-JSON is a neutral editable source/interchange format that could generate or map to selected runtime targets. |
| **Caliper** | Learning analytics event model | Different layer. Like xAPI, Caliper describes learner activity events; LC-JSON describes the content those events may refer to. Complementary. |

This is a high-level map, not an exhaustive comparison. LC-JSON's intended combination — JSON-native, human-inspectable, and covering hierarchical course structure as well as flat question sets — is uncommon among established educational interchange formats.

The question of whether such a format needs to exist resolves as follows: QTI is mature and deep for assessment exchange, and LC-JSON deliberately targets a narrower, JSON-native course-and-question authoring source rather than competing on assessment surface area; SCORM and Common Cartridge are package-and-delivery formats from an earlier era, not editable JSON; xAPI, Caliper, LTI, OneRoster, and CASE are oriented at other layers. LC-JSON exists to occupy the JSON-native, teacher-readable, course-and-question interchange slot.

## How LC-JSON Differs

The same comparison, expressed as field-level stances:

| Need | LC-JSON stance | Typical peer behavior |
|---|---|---|
| Teacher-readable interchange files | First-class design principle | Many established interchange formats prioritize machine/tool processing over direct human inspection |
| JSON-native validation | Published JSON Schemas (Draft 7) | QTI is XML-shaped (3.0 added a JSON binding); SCORM and Common Cartridge are XML and package-based |
| Course + question portability in one family | Separate `course` and `questionSet` artifacts under a common flat root | QTI covers questions; SCORM and Common Cartridge package courses; few formats cover both as editable JSON |
| Accessibility metadata preservation across import/export | Base consumer-conformance preservation floor for `alt`, `<track>`, `lang`, `dir`, `language`, `supportLanguage`, reserved-type accessibility metadata | Accessibility metadata can be dropped or normalized away during transformation |
| Accessible delivery claims | Opt-in Accessibility Profile binding (see [`ACCESSIBILITY.md`](ACCESSIBILITY.md)) | Accessibility-conformance claims are typically made about the delivery platform, not the interchange file |
| Unsupported future question types | Preserve verbatim and report; never silently drop | Fallback behavior varies by implementation; without an explicit preservation contract, data loss is a practical risk |
| Tool-specific data | Namespaced `x-` extensions; other consumers ignore unknown namespaces and extension-preserving consumers round-trip them where possible (see [`NORMATIVE.md`](NORMATIVE.md) §7) | Custom-extension mechanisms exist (e.g. QTI custom interactions) but are often tightly coupled to one tool |
| Version stability | Immutable schema URL paths per spec version | URL stability practices vary by specification |
| LMS / runtime integration | Out of scope unless a future LC-JSON version adds a portable contract | SCORM defines a runtime API; LTI defines launch and grade integration |

## Adoption Positioning

For teachers:

> LC-JSON is a portable course file format for moving teaching materials between compatible platforms.

For institutions:

> LC-JSON is an open JSON-based interchange format designed to make teacher-authored learning content portable between compatible tools and platforms.

For developers:

> LC-JSON defines a schema-validated JSON wire format plus producer/consumer conformance rules for learning-content interchange.

For standards reviewers:

> LC-JSON is an emerging open learning-content interchange specification with a stable 1.0 release-candidate contract, published schemas, conformance fixtures, and explicit producer/consumer obligations.

## Scope and Limits

LC-JSON is a focused, open, schema-validated interchange specification for portable learning content. It is not — on its own — any of the following:

- A WCAG conformance claim. LC-JSON's Accessibility Profile binds preservation and rendering obligations on conforming consumers, but WCAG conformance is established by the delivery platform under test, not by the interchange file.
- An LMS interoperability format. Tool launch, deep linking, and grade passback are LTI's domain.
- A roster, enrollment, or grade-exchange format. That is OneRoster's domain.
- A learning-analytics or activity-record format. That is xAPI / cmi5's domain.
- A runtime delivery wrapper. SCORM 2004 defines a runtime API; LC-JSON does not.
- An established industry standard. LC-JSON is an emerging open specification at 1.0-rc.3, with published schemas, conformance fixtures, and explicit producer/consumer obligations. Whether it becomes widely adopted will be determined by implementers and time, not by self-description.

Within those limits, LC-JSON aims to be exactly one thing well: a JSON-native, human-inspectable interchange format for hierarchical courses and flat question sets, with extension-preserving round-trips, a base accessibility-preservation floor, and an opt-in Accessibility Profile for delivery obligations.

