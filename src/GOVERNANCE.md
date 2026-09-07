# Governance

**Status:** Informative.
**Spec version:** 1.1
**Last updated:** 2026-09-07

## Stewardship

LC-JSON (Learning Content JSON) is currently maintained by **Brent Miller**, the originator of the specification. The project operates under a benevolent-dictator model: substantive proposals are reviewed and accepted, modified, or rejected by the maintainer, with deliberations conducted publicly via GitHub Issues and Discussions on this repository.

This is a single-maintainer steward model. It is appropriate for a specification at its early stage — one originator, no working group, a small but growing community of implementers. It is not a permanent posture.

## How decisions are made

| Change type | Process |
|---|---|
| Typo, broken link, formatting | PR welcome directly. Merged quickly. |
| Schema or example bug fix | Open an issue describing the bug and a test case (positive or negative) demonstrating it. PR welcome alongside or after the issue. |
| New question type | Open an issue first describing the type, its scoring semantics, and the audience (which exam, which level, which subject). A reference schema, an example, and conformance test cases are required before merge. |
| Breaking change to existing schemas | Strongly discouraged within a major version (see `NORMATIVE.md` §8). Requires a new minor or major version with a new URL path. Open an issue to discuss before any PR. |
| Process or governance change | Open an issue. Substantial changes will be discussed publicly before being adopted. |

Substantive proposals (anything beyond a typo or non-normative fix) are documented in `proposals/` (added when the first such RFC lands) as one-page RFCs with a clear status line: `draft`, `accepted`, or `rejected`.

## Versioning and the living specification

The LC-JSON repository maintains a **single living specification source**. Published releases create **immutable versioned artifacts** — the per-version schema URLs (`lc-json.org/<version>/<name>.schema.json`). Backward compatibility and behavioral changes are documented through **versioned schema URLs, release notes, and the changelog**.

There is no separate, independently maintained prose source for a prior published version: the **git tag is the historical source**. The living specification (this repository's working tree) advances to the current version; prior versions persist as (a) their immutable published schema URLs and (b) git tags and commits. Every prior publication's schemas stay served and frozen at their own versioned path while the working tree moves on to the next; to read the specification exactly as a given version published it, read that version's git tag, not the current working tree.

## Release Candidate Policy

- RC releases MAY introduce backwards-compatible corrections.
- RC releases MAY clarify specification language.
- RC releases MUST NOT silently modify previously published artifacts — each RC publishes at its own immutable URL path (`/1.0-rc.1/`, `/1.0-rc.2/`, `/1.0-rc.3/`, …).
- Final v1.0 establishes the stable contract.

The rc.1 → rc.2 `prompt`-field correction is exactly this kind of sanctioned change: a backwards-compatible correction (`minLength: 1 → 0`) and a language clarification (defining `prompt` as non-authoritative for symbolic types), published at a new immutable `/1.0-rc.2/` path while `/1.0-rc.1/` stays frozen. The rc.2 → rc.3 cut follows the same pattern: it removes two prototype-era `sentenceTransformation` fields from the schema — which, because `/1.0-rc.2/` is immutable, must land at a new `/1.0-rc.3/` path — while rc.1 and rc.2 stay frozen, and every rc.2-valid document remains valid under rc.3.

## Working group

A formal working group will be considered when **at least two independent third-party implementations of LC-JSON exist and are in active use**. "Independent" means not built or maintained by the same organization that originated the specification.

Until that threshold is met, decisions remain with the maintainer. Forks are permitted under the Apache 2.0 license; community input is welcomed via Issues and Discussions, but accepted changes are at the maintainer's discretion.

Once the threshold is met, the maintainer will publish a transition plan: charter, working-group composition criteria, decision-making process, and (if appropriate) custodial handoff to a foundation or neutral steward.

## Trademark and naming

Lesson Commons® is a registered trademark of Brent Miller and is **not asserted** over the LC-JSON specification, the names "LC-JSON" or "Learning Content JSON", or any conforming implementation. Implementers may state conformance freely.

The canonical sources for the LC-JSON specification are this repository — [`github.com/lc-json/specification`](https://github.com/lc-json/specification) — and the published site at [`lc-json.org`](https://lc-json.org). Forks and mirrors are permitted under the Apache 2.0 license, but only the URLs above carry the canonical specification text. A forked or mirrored copy that materially differs from these sources is a derivative work and should be named accordingly — not "LC-JSON" without qualification.

The specification's name and canonical URL (`lc-json.org`) are not vendor-coupled by design. If stewardship of LC-JSON ever passes to a foundation, working group, or successor maintainer, the name and URL travel with the specification, not with any sponsoring organization.

## Contact

- **Issues and proposals:** open an issue on this repository.
- **Conformance questions:** consult [`NORMATIVE.md`](NORMATIVE.md); it is the authoritative source for implementer requirements.
- **Maintainer correspondence:** via GitHub.
