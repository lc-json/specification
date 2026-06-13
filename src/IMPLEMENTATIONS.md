# Implementations

**Status:** Informative.
**Spec version:** 1.0
**Last updated:** 2026-05-26

Tools that produce, consume, or validate LC-JSON (Learning Content JSON) 1.0.

To list a new implementation, open a PR adding an entry below. Implementations are listed in alphabetical order within each section. Inclusion does not imply endorsement.

---

## Producers

Tools that emit LC-JSON documents.

- **Lesson Commons** — Authoring and delivery platform for structured learning content. Emits courses and question sets in LC-JSON 1.0. <https://lessoncommons.com>

## Consumers

Tools that ingest LC-JSON documents.

- **Lesson Commons** — Imports LC-JSON 1.0. Extension-preserving consumer per NORMATIVE §7 (unknown `x-*` members round-trip through a load/save cycle), §6.4 (reserved-type questions preserve their type-specific bodies), and §12.1 (accessibility-preservation floor). <https://lessoncommons.com>

## Reference tools

Distributed alongside the specification in this repository.

- **`validate_course.py`** — Python reference validator. Runs documents through the published JSON Schemas (`jsonschema` ≥ 4.18) plus a hand-written domain pass for rules JSON Schema cannot easily express (HTML allowlist, gap-marker counts, points consistency). Default mode is lenient — pre-1.0 document shapes (wrapped envelopes, bare payloads) are tolerated with warnings so legacy/pre-1.0 documents can still be ingested during migration. The `--strict` flag is the public-conformance mode: those shapes become fatal errors, and the full set of `NORMATIVE.md` §3.2 / §4.1 rejections is enforced. **Public conformance claims under `NORMATIVE.md` §10 are evaluated in `--strict` mode.**
- **`run_corpus.py`** — Conformance corpus harness for **spec maintainers and contributors**. Reads `tests/manifest.json` and runs every fixture through `validate_course.py --strict`, asserting that valid fixtures pass and invalid fixtures fail with non-zero exit. The spec repo's CI runs it as a gating step on every push and PR — a corpus regression blocks deployment. Contributors SHOULD run it locally before opening a PR that touches the spec. LC-JSON **consumers** (tools that read/write LC-JSON documents in their own applications) do not need it; they can ignore it and treat `tests/manifest.json` plus the fixture files as the canonical test set for their own implementation tests.

---

## Conformance claims

Implementations may state conformance per `NORMATIVE.md` §10:

- *Conforms to LC-JSON 1.0 as a producer*
- *Conforms to LC-JSON 1.0 as a consumer*
- *Conforms to LC-JSON 1.0* (both producer and consumer)

The conformance test corpus at [`tests/`](tests/) lets implementations self-verify.

---

## Extension namespaces

Registered `x-`-namespaced extension prefixes (NORMATIVE §7). Listing a namespace here documents its owner and intent so other tools can interoperate or avoid collision; it does not make the extension part of the core format.

- **`x-lessoncommons`** — Lesson Commons. Carries tool-specific authoring metadata that has no place in the interchange core; member details are documented in the Lesson Commons developer docs. Consumers outside Lesson Commons MUST ignore these members (NORMATIVE §7.4) but are encouraged to preserve them across round trips so authoring provenance survives a transfer through third-party tools.
