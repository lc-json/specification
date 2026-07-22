#!/usr/bin/env python3
"""
assemble_pack_bundle.py - manifest -> bundle packaging for LC-JSON curriculumPack
documents.

A bundle is a PACKAGING of the same pack, never a different document:
this tool resolves the manifest's collectionRefs[] and
contentRefs[] against a set of search directories and embeds the referenced
documents VERBATIM into an `embedded` block:

    "packMode": "bundle",
    "embedded": {
        "collections": [ <full subjectCollection documents> ],
        "content":     [ <full course / questionSet / glossary documents> ]
    }

Everything else — refs, sequence, coverage — is preserved unchanged from the
manifest: the refs stay the bill of materials, `embedded` carries the
payloads. Identity discipline: embedding copies documents whole; each document's
type-directed identity (a course/questionSet's sourceCourseId/sourceQuestionSetId,
else root globalId), member ids and node globalIds are never re-minted or rewritten. `--strip`
performs the inverse (drop `embedded`, flip packMode), so
manifest -> bundle -> strip round-trips to a SEMANTICALLY identical manifest.
Preservation is at the JSON-value level, not the byte level: the tool parses
and re-serializes with its own formatting, so whitespace, key order, and
trailing-newline details are not guaranteed to survive the round trip.

Version pinning: a ref that pins a version resolves only to a document of
that version; with --allow-version-drift a differing version is accepted and
surfaced as a warning instead (the consumer posture: surface, never silently
substitute).

The result is validated with lc_pack.py before writing (bundle closure,
selector resolution into embedded courses, coverage against the embedded
collection). Unresolvable refs are all listed, then the tool exits 1.

Usage:
    python assemble_pack_bundle.py --pack manifest.pack.json \
        --search path/to/collections \
        --search path/to/content \
        --out bundle.pack.json [--allow-version-drift]

    python assemble_pack_bundle.py --pack bundle.pack.json --strip \
        --out manifest.pack.json
"""

import argparse
import json
import os
import sys

import lc_pack as lp
import _lcjson_schema

EMBEDDABLE_TYPES = {"subjectCollection", "course", "questionSet", "glossary"}


def index_search_dirs(dirs):
    """(documentType, identity) -> (doc, path) over every LC-JSON document found.

    Identity is type-directed (NORMATIVE §4.4): a course/questionSet is keyed by
    its sourceCourseId/sourceQuestionSetId, a collection/glossary by its root
    globalId. A document that does not carry the identity its type resolves against
    (e.g. a course with no sourceCourseId) is not indexable and is skipped — a pack
    cannot reference it."""
    index = {}
    for root_dir in dirs:
        for dirpath, _dirnames, filenames in os.walk(root_dir):
            for name in sorted(filenames):
                if not name.endswith(".json"):
                    continue
                path = os.path.join(dirpath, name)
                try:
                    with open(path, encoding="utf-8") as f:
                        doc = json.load(f)
                except (OSError, json.JSONDecodeError):
                    continue
                if not isinstance(doc, dict):
                    continue
                dtype, ident = doc.get("documentType"), lp.document_identity(doc)
                if dtype in EMBEDDABLE_TYPES and ident:
                    key = (dtype, ident)
                    if key in index:
                        print(f"  note: {key[0]} '{ident}' found in both "
                              f"{index[key][1]} and {path}; using the first")
                    else:
                        index[key] = (doc, path)
    return index


def resolve(ref, dtype, index, allow_drift, problems, warnings):
    """Resolve one ref; returns the document or None (problem recorded).

    Collection refs carry `globalId`; content refs carry the type-directed `id`."""
    ref_ident = ref.get("id") if "id" in ref else ref.get("globalId")
    key = (dtype, ref_ident)
    hit = index.get(key)
    if hit is None:
        problems.append(f"{dtype} '{ref_ident}' not found in the search dirs")
        return None
    doc, path = hit
    pinned = ref.get("version")
    if pinned and doc.get("version") != pinned:
        msg = (f"{dtype} '{ref_ident}': pack pins version {pinned}, "
               f"found {doc.get('version')} at {path}")
        if allow_drift:
            warnings.append(msg + " (accepted; --allow-version-drift)")
        else:
            problems.append(msg + " (pass --allow-version-drift to accept)")
            return None
    return doc


def assemble(pack, index, allow_drift=False):
    """Returns (bundle, problems, warnings). Bundle is None when problems exist."""
    problems, warnings = [], []
    if pack.get("packMode") != "manifest":
        problems.append(f"input packMode is '{pack.get('packMode')}', expected 'manifest'")
        return None, problems, warnings

    collections, content, seen = [], [], set()
    for ref in pack.get("collectionRefs") or []:
        doc = resolve(ref, "subjectCollection", index, allow_drift, problems, warnings)
        if doc is not None and ("subjectCollection", doc["globalId"]) not in seen:
            seen.add(("subjectCollection", doc["globalId"]))
            collections.append(doc)
    for ref in pack.get("contentRefs") or []:
        doc = resolve(ref, ref.get("type"), index, allow_drift, problems, warnings)
        if doc is not None:
            doc_key = (ref.get("type"), lp.document_identity(doc))
            if doc_key not in seen:
                seen.add(doc_key)
                content.append(doc)
    if problems:
        return None, problems, warnings

    bundle = dict(pack)  # shallow: every untouched field is carried verbatim
    bundle["packMode"] = "bundle"
    bundle["embedded"] = {"collections": collections, "content": content}
    return bundle, problems, warnings


def validate_embedded(bundle):
    """Schema AND domain problems for every document embedded in a bundle.

    Delegates to the shared emission gate so this is the same check every other
    writer runs. It previously ran a schema-only pass, which let a schema-valid
    but domain-invalid artifact (a Glossary violating GL-4, say) be packaged.

    Note this is deliberately NOT called from assemble(): that function is a pure
    transform, and the harness exercises it with intentionally schema-incomplete
    stubs. Validation gates the *writer*, which is where a nonconforming document
    would actually escape.
    """
    return _lcjson_schema.embedded_problems(bundle)


def strip(pack):
    """The exact inverse of assemble()."""
    problems = []
    if pack.get("packMode") != "bundle":
        problems.append(f"input packMode is '{pack.get('packMode')}', expected 'bundle'")
        return None, problems
    manifest = dict(pack)
    manifest["packMode"] = "manifest"
    manifest.pop("embedded", None)
    return manifest, problems


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", required=True, metavar="FILE",
                        help="the manifest to assemble (or, with --strip, the bundle)")
    parser.add_argument("--search", action="append", default=[], metavar="DIR",
                        help="directory to resolve referenced documents from (repeatable)")
    parser.add_argument("--out", required=True, metavar="FILE")
    parser.add_argument("--allow-version-drift", action="store_true",
                        help="accept (and surface) refs whose pinned version differs "
                             "from the found document")
    parser.add_argument("--strip", action="store_true",
                        help="inverse operation: bundle -> manifest")
    args = parser.parse_args()

    with open(args.pack, encoding="utf-8") as f:
        pack = json.load(f)

    if args.strip:
        result, problems = strip(pack)
        warnings = []
    else:
        if not args.search:
            parser.error("--search is required when assembling (where do the "
                         "referenced documents live?)")
        index = index_search_dirs(args.search)
        result, problems, warnings = assemble(pack, index, args.allow_version_drift)

    for w in warnings:
        print(f"  WARNING: {w}")
    if problems:
        print(f"FAILED — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    _, val_warnings = lp.validate(result)
    for w in val_warnings:
        print(f"  WARNING: {w}")

    # The emission gate: the pack's own schema + canonical $schema identity + pack
    # domain rules, then schema AND domain rules for every embedded document. This
    # is the same gate lc_pack.save() and lc_collection.save() run, so the writer
    # cannot emit something the validators would reject.
    errors = _lcjson_schema.validate_for_emission(result)
    if errors:
        print(f"RESULT INVALID — {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")

    emb = result.get("embedded") or {}
    print(f"Wrote {args.out}: packMode {result['packMode']}, "
          f"{len(emb.get('collections', []))} collection(s) + "
          f"{len(emb.get('content', []))} content document(s) embedded, "
          f"{os.path.getsize(args.out)} bytes")


if __name__ == "__main__":
    main()
