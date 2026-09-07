# Implementations

**Status:** Informative.
**Spec version:** 1.1
**Last updated:** 2026-09-07

Tools that produce, consume, or validate LC-JSON (Learning Content JSON).

To list a new implementation, open a PR adding an entry below. Implementations are listed in alphabetical order within each section. Inclusion does not imply endorsement.

---

## Producers

Tools that emit LC-JSON documents.

- **Lesson Commons®** — Authoring and delivery platform for structured learning content. Emits all five LC-JSON 1.1 artifact types — courses, question sets, glossaries, subject collections, and curriculum packs. <https://lessoncommons.com>

## Consumers

Tools that ingest LC-JSON documents.

- **Lesson Commons** — Imports LC-JSON 1.0 and 1.1, all five artifact types. Extension-preserving consumer per NORMATIVE §7 (unknown `x-*` members round-trip through a load/save cycle), §6.4 (reserved-type questions preserve their type-specific bodies), and §12.1 (accessibility-preservation floor). <https://lessoncommons.com>

## Reference tools

Distributed alongside the specification in this repository. They are
**non-authoritative reference implementations**: they implement the contract stated
in [`NORMATIVE.md`](NORMATIVE.md), the companion normative documents, and the schema
constraints — they do not define it. Where a validator and a normative source
disagree, the source governs and the validator is a defect.

### Exit-status contract

All four validators share one exit contract:

| Exit | Meaning |
|---|---|
| `0` | The document was fully checked (schema **and** domain) **against the publication it declares**, and conforms to it. |
| `1` | The document does **not** conform. Normally established by the full check; a definitive canonical-`$schema` identity or RD-1 failure is also reported as `1` even when the Draft-07 pass could not run, because that verdict does not depend on the pass that was missing. The reported problem list may then be partial. |
| `3` | **Validation unavailable / indeterminate** — the check could not be completed *and* no definitive failure had already been established, so nothing is claimed about the document either way. |

**Exit `0` is always a statement about the declared publication.** §8.4 makes a
document's `$schema` URL the binding validation target, so a document declaring an
earlier publication is validated against *that* publication's schemas — which the
published tree carries for every release it has ever served. The validators will not
check a 1.0 document against 1.1 schemas and then exit `0`; that would assert a
conformance nobody established.

Exit `3` covers every case where the tool cannot complete the check:

- the `jsonschema` dependency is missing (install with `pip install -r tools/requirements.txt`);
- a schema required for the document's artifact type — including one reachable through
  `$ref` — is absent from the publication. A missing schema is an *infrastructure*
  failure; reporting it as exit `1` would blame the document for the tool's problem;
- the document declares a publication this tree does not carry. The result is then
  **indeterminate**: use a validator built for that publication.

The validators deliberately do **not** fall back to a reduced pass and exit `0` in any
of these cases. A note on stdout saying the schema pass was skipped is invisible to the
CI job or script reading the exit status, which would then treat an unchecked document
as conforming.

Domain-only operation is available as an explicit opt-in, `--domain-only`. It runs the
hand-written domain rules alone, skips **every** schema stage, reports `DOMAIN-ONLY OK`
rather than `VALID`, and is **not** a conformance check — a conformance claim under
[`NORMATIVE.md`](NORMATIVE.md) §10 requires the schema pass to have run. The flag is an
explicit request, so it takes precedence over schema availability: it behaves the same
way whether or not the schemas could have loaded.

- **`validate_course.py`** — Python reference validator. Runs documents through the published JSON Schemas (`jsonschema` ≥ 4.18) plus a hand-written domain pass for rules JSON Schema cannot easily express (HTML allowlist, gap-marker counts, points consistency). Default mode is lenient — pre-1.0 document shapes (wrapped envelopes, bare payloads) are tolerated with warnings so legacy/pre-1.0 documents can still be ingested during migration. The `--strict` flag is the public-conformance mode: those shapes become fatal errors, and the full set of `NORMATIVE.md` §3.2 / §4.1 rejections is enforced. **Public conformance claims under `NORMATIVE.md` §10 are evaluated in `--strict` mode.**
- **`lc_collection.py`** — Reference validator for `subjectCollection` documents. Checks member identity, category/tag/objective closure, and alignment-claim vocabulary (the SC-\* rules cataloged in [`VALIDATION.md`](VALIDATION.md) §15). `--validate FILE`; exits `0` when the document conforms, `1` on a violation, `3` when no conformance statement could be made.
- **`lc_pack.py`** — Reference validator for `curriculumPack` documents. Checks step/pacing/checkpoint shape, taught-before-used sequencing, term capacity, and — given `--collection FILE` — coverage against the referenced Subject Collection (the CP-\* rules in [`VALIDATION.md`](VALIDATION.md) §16). Separates errors (exit `1`) from advisory warnings (surfaced, exit `0`).
- **`lc_glossary.py`** — Reference validator for `glossary` documents. Checks the gloss rule and the declared translation-inventory rules (the GL-\* rules in [`VALIDATION.md`](VALIDATION.md) §17); `--validate FILE`.
- **`assemble_pack_bundle.py`** — Packages a Curriculum Pack manifest into a self-contained bundle (embedding referenced documents identity-verbatim) and back (`--strip`), so bundle round-trips are reproducible by third parties. Before writing, it runs the shared emission gate: the pack's own schema and domain rules, plus the schema **and** domain rules of every embedded document, dispatched on that document's `documentType`.
- **`run_corpus.py`** — Conformance corpus harness for **spec maintainers and contributors**. Reads `tests/manifest.json` and runs every fixture through the reference validator matching its `documentType` (`--strict` for course/questionSet), asserting that valid fixtures exit `0` and invalid fixtures are adjudicated as definitively non-conforming (exit `1`). An indeterminate exit `3` fails the harness: the fixture's rule was never checked, so counting it as a correct rejection would overstate the result. The spec repo's CI runs it as a gating step on every push and PR — a corpus regression blocks deployment. Contributors SHOULD run it locally before opening a PR that touches the spec. LC-JSON **consumers** (tools that read/write LC-JSON documents in their own applications) do not need it; they can ignore it and treat `tests/manifest.json` plus the fixture files as the canonical test set for their own implementation tests.

---

## Conformance claims

Implementations may state conformance per `NORMATIVE.md` §10:

- *Conforms to LC-JSON 1.1 as a producer*
- *Conforms to LC-JSON 1.1 as a consumer*
- *Conforms to LC-JSON 1.1* (both producer and consumer)

The version names the contract a tool implements; a tool implementing only the 1.0 artifact types states 1.0. Conformance is scoped per artifact type (NORMATIVE §5.1) — a tool that reads only courses claims only that.

The conformance test corpus at [`tests/`](tests/) lets implementations self-verify.

---

## Extension namespaces

Registered `x-`-namespaced extension prefixes (NORMATIVE §7). Listing a namespace here documents its owner and intent so other tools can interoperate or avoid collision; it does not make the extension part of the core format.

- **`x-lessoncommons`** — Lesson Commons. Carries tool-specific authoring metadata that has no place in the interchange core; member details are documented in the Lesson Commons developer docs. Consumers outside Lesson Commons MUST ignore these members (NORMATIVE §7.4) but are encouraged to preserve them across round trips so authoring provenance survives a transfer through third-party tools.
