# LC-JSON Conformance Test Corpus

A curated set of test documents for verifying that an implementation conforms to **LC-JSON 1.0** (Learning Content JSON) as described in [`../NORMATIVE.md`](../NORMATIVE.md).

## Structure

```
tests/
├── README.md          ← you are here
├── manifest.json      ← machine-readable index of every test case
├── valid/             ← documents that MUST validate
└── invalid/           ← documents that MUST fail validation
```

## How to use the corpus

A conforming consumer self-tests against the corpus as follows:

1. For every file under `valid/`, run the implementation's validator. It MUST report success.
2. For every file under `invalid/`, run the validator. It MUST report a failure. The failure SHOULD identify the violated clause matching `manifest.json`.

A **producer** does not validate the corpus directly. Instead, a producer's emitted output is fed through any conforming consumer (its own or a third party's) and MUST pass validation. The corpus is for consumer/validator self-test.

## Behavioral conformance (informative)

The required self-test above (validate `valid/` cases as passing, `invalid/` cases as failing) verifies *document validity*. Some normative obligations are *behavioral* — they concern what a conforming consumer does WITH the data after import — and cannot be tested by validation alone:

- **§6.4 Round-trip preservation** for reserved and unknown question types (`type` values not in the consumer's implemented enum).
- **§7 Extension preservation** for `x-`-namespaced fields the consumer does not recognize.
- **§12.1 Accessibility-preservation floor** for `alt`, `<track>`, `lang`/`dir`, and `x-`-namespaced accessibility metadata.

Several fixtures in this corpus are tagged in `manifest.json` as demonstrating these behaviors (look for `"§6.4"`, `"§12.1"`, or "preservation" / "round-trip" in `demonstrates`). A consumer MAY exercise them as a behavioral self-test:

1. Load the fixture.
2. Re-emit the document via the consumer's export path.
3. Diff the input and output for the byte-level preservation the cited clause requires (reserved-type question objects, `x-`-namespaced fields, accessibility metadata).

Formal behavioral conformance fixtures and a reference round-trip runner are an open direction for future versions, subject to implementer feedback.

## Manifest schema

`manifest.json` enumerates every test file:

```json
{
  "specVersion": "1.0",
  "valid": [
    { "file": "01-course-minimal.json", "schema": "course.schema.json", "demonstrates": ["§..."] },
    ...
  ],
  "invalid": [
    { "file": "01-missing-document-type.json", "violatedClause": "§3.2", "violation": "..." },
    ...
  ]
}
```

## Adding a test case

1. Add a new file to `valid/` or `invalid/`, numbered to extend the existing sequence.
2. Append a corresponding entry to `manifest.json`.
3. For invalid cases, choose the most specific clause violated. If a document violates multiple clauses, use the earliest one in document order.
4. Keep each test case as small as possible — ideally exercising exactly one clause. Larger documents are harder to debug when an implementation fails them.

## Reference validator

The reference implementation in `../../tools/validate_course.py` runs the corpus as part of its own test suite. CI for the public spec repository will run a strict validator over the corpus as a gate.

The reference validator retains lenient handling of pre-1.0 document shapes (wrapped envelope `{"course": {...}}`, bare payload `{"units": [...]}` with no `documentType`) for backward compatibility with legacy content during migration. This lenient handling is a migration aid, not a feature of LC-JSON 1.0. The `--strict` flag — which the conformance harness `tools/run_corpus.py` always passes — disables the lenient paths and evaluates the published conformance contract.
