#!/usr/bin/env python3
"""
run_corpus.py - Run the LC-JSON conformance corpus through the reference validator.

Reads `specification/tests/manifest.json`, runs every valid/* fixture and every
invalid/* fixture through the reference validator matching its `documentType`,
and reports pass/fail counts. Exits 0 only when the entire corpus behaves as the
manifest says it should (all valid pass, all invalid fail).

Validator dispatch by `documentType`:
    course, questionSet   → validate_course.py --strict --course-path FILE
    subjectCollection     → lc_collection.py --validate FILE
    curriculumPack        → lc_pack.py --validate FILE
    glossary              → lc_glossary.py --validate FILE
All four share the same exit contract: 0 = conforming, non-zero = a violation.
A manifest entry MAY set "validator" explicitly to override the documentType
dispatch (e.g. to run a curriculumPack fixture with a --collection argument);
see the manifest's "validatorArgs" field.

This is the script CI runs (CONTRIBUTING.md). It is also the script developers
should run locally before opening a PR that touches the spec.

Usage:
    python run_corpus.py
    python run_corpus.py --verbose
    python run_corpus.py --tests-dir path/to/tests   # default: ../specification/tests
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent


def _detect_tests_dir():
    """Resolve the tests directory for the current layout.

    Source layout:            tools/ alongside a sibling specification/tests/
    Public spec repo layout:  tools/ → ../tests/
    """
    dev_path = THIS_DIR.parent / "specification" / "tests"
    if dev_path.is_dir():
        return dev_path
    pub_path = THIS_DIR.parent / "tests"
    if pub_path.is_dir():
        return pub_path
    return dev_path  # fallback; downstream errors will be clearer than a misleading path


DEFAULT_TESTS_DIR = _detect_tests_dir()
VALIDATOR = THIS_DIR / "validate_course.py"

# documentType → (validator script, argv builder taking the fixture path).
# All four validators exit 0 on a conforming document and non-zero on a violation.
_DISPATCH = {
    "course":            (THIS_DIR / "validate_course.py", lambda p: ["--course-path", str(p), "--strict"]),
    "questionSet":       (THIS_DIR / "validate_course.py", lambda p: ["--course-path", str(p), "--strict"]),
    "subjectCollection": (THIS_DIR / "lc_collection.py",   lambda p: ["--validate", str(p)]),
    "curriculumPack":    (THIS_DIR / "lc_pack.py",         lambda p: ["--validate", str(p)]),
    "glossary":          (THIS_DIR / "lc_glossary.py",     lambda p: ["--validate", str(p)]),
}


def _document_type(fixture_path):
    """Read the fixture's root documentType (None if unreadable / absent)."""
    try:
        with open(fixture_path, encoding="utf-8") as f:
            return json.load(f).get("documentType")
    except (OSError, ValueError):
        return None


def run_validator(fixture_path, entry, verbose):
    """Dispatch a fixture to the validator matching its documentType.

    A manifest entry MAY override dispatch with "validator" (a script basename)
    and "validatorArgs" (extra argv appended after the fixture argument) — used
    for the curriculumPack + --collection cross-validation fixture.

    Returns (exit_code, output).
    """
    doc_type = _document_type(fixture_path)
    override = entry.get("validator") if isinstance(entry, dict) else None
    if override:
        script = THIS_DIR / override
        argv = ["--validate", str(fixture_path)] + list(entry.get("validatorArgs", []))
    else:
        script, argv_builder = _DISPATCH.get(
            doc_type, _DISPATCH["course"]  # legacy/fragment fixtures fall back to validate_course.py
        )
        argv = argv_builder(fixture_path)

    proc = subprocess.run(
        [sys.executable, str(script)] + argv,
        capture_output=True,
        text=True,
        cwd=str(fixture_path.parent),  # so relative --collection args resolve against the fixture dir
    )
    if verbose:
        print(proc.stdout)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
    return proc.returncode, proc.stdout + proc.stderr


# The warning-class line prefixes the reference validators emit. validate_course.py
# uses "[WARN] "; lc_pack.py, lc_glossary.py, and assemble_pack_bundle.py use
# "WARNING: ".
_WARNING_PREFIXES = ("[WARN]", "WARNING:")


def _warning_asserted(expect, output):
    """True when `expect` appears on a WARNING-class line of the validator output.

    A bare substring search over combined stdout+stderr proves nothing: the fixture
    path, its title, a NOTE, or even an ERROR message could satisfy it, so a warning
    fixture could pass while the warning it names never fired. Requiring the match
    to land on a warning-prefixed line makes the assertion mean what it says.
    """
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith(_WARNING_PREFIXES) and expect in stripped:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Run the LC-JSON conformance corpus")
    parser.add_argument("--tests-dir", type=Path, default=DEFAULT_TESTS_DIR,
                        help="Path to the tests/ directory containing manifest.json")
    parser.add_argument("--verbose", action="store_true",
                        help="Show validator output for every fixture")
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, Exception):
        pass

    manifest_path = args.tests_dir / "manifest.json"
    if not manifest_path.is_file():
        print(f"FATAL: manifest not found at {manifest_path}", file=sys.stderr)
        sys.exit(2)

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    valid_entries = manifest.get("valid", [])
    invalid_entries = manifest.get("invalid", [])
    compat_entries = manifest.get("compatibility", [])
    examples_dir = args.tests_dir.parent / "examples"
    example_files = sorted(examples_dir.glob("*.json"))

    print("LC-JSON conformance corpus harness")
    print("=" * 80)
    print(f"  manifest:        {manifest_path}")
    print(f"  validator:       {VALIDATOR}")
    print(f"  valid fixtures:  {len(valid_entries)}")
    print(f"  invalid fixtures:{len(invalid_entries)}")
    if compat_entries:
        print(f"  compatibility:   {len(compat_entries)}")
    if example_files:
        print(f"  shipped examples:{len(example_files)}")
    print()

    failures = []  # list of (kind, file, reason)

    # Valid fixtures MUST pass under --strict. A fixture MAY additionally declare
    # "expectWarning": "<substring>" to assert that a specific advisory surfaces
    # in the validator output (a valid-with-surfaced-warning case) — exit stays 0,
    # but the warning text must be present.
    print(f"Valid fixtures (expecting exit 0):")
    for entry in valid_entries:
        rel = entry["file"]
        path = args.tests_dir / rel
        rc, output = run_validator(path, entry, args.verbose)
        expect = entry.get("expectWarning") if isinstance(entry, dict) else None
        warning_ok = (expect is None) or _warning_asserted(expect, output)
        status = "PASS" if (rc == 0 and warning_ok) else "FAIL"
        suffix = f"  (expects warning: {expect!r})" if expect else ""
        print(f"  [{status}] {rel}  (exit {rc}){suffix}")
        if rc != 0:
            failures.append(("valid-but-failed", rel, output.strip().splitlines()[-1] if output.strip() else "no output"))
        elif not warning_ok:
            failures.append(("valid-but-warning-missing", rel, f"expected warning substring not found: {expect!r}"))

    print()

    # Invalid fixtures MUST fail under --strict.
    print(f"Invalid fixtures (expecting exit non-zero):")
    for entry in invalid_entries:
        rel = entry["file"]
        path = args.tests_dir / rel
        rc, output = run_validator(path, entry, args.verbose)
        status = "PASS" if rc != 0 else "FAIL"
        print(f"  [{status}] {rel}  (exit {rc})  -- {entry.get('violatedClause', '?')}")
        if rc == 0:
            failures.append(("invalid-but-passed", rel, entry.get("violation", "")))

    print()

    # Compatibility fixtures assert only that a document from an EARLIER
    # publication is never REJECTED (exit != 1). They deliberately do not assert
    # exit 0, because the honest answer depends on the layout: the published tree
    # carries every prior publication, so the declared schemas load and the result
    # is a real conformance statement (exit 0); the source tree carries one flat
    # publication, so the same document is indeterminate (exit 3). Asserting
    # "never rejected" is true in both, which keeps the corpus layout-agnostic
    # without pretending the two layouts do the same work.
    if compat_entries:
        print("Compatibility fixtures (expecting exit != 1 — never rejected):")
        for entry in compat_entries:
            rel = entry["file"]
            path = args.tests_dir / rel
            rc, output = run_validator(path, entry, args.verbose)
            verdict = {0: "conforming", 3: "indeterminate"}.get(rc, f"exit {rc}")
            status = "PASS" if rc != 1 else "FAIL"
            print(f"  [{status}] {rel}  (exit {rc} — {verdict})")
            if rc == 1:
                failures.append(("compat-but-rejected", rel,
                                 "a document from an earlier publication was "
                                 "REJECTED; compatibility requires exit != 1"))
        print()

    # Shipped examples: every examples/*.json is a template implementers COPY, so
    # it must validate clean. They are NOT in the manifest (they carry no declared
    # pass/fail — all must pass) and were historically ungated; a broken example
    # is a broken template that propagates. Dispatched exactly like a valid
    # fixture: by documentType, with fragments (single questions/items/units/
    # lessons — no documentType) falling back to validate_course.py --strict.
    if example_files:
        print("Shipped examples (expecting exit 0 — every template must validate clean):")
        for path in example_files:
            rc, output = run_validator(path, {}, args.verbose)
            status = "PASS" if rc == 0 else "FAIL"
            print(f"  [{status}] examples/{path.name}  (exit {rc})")
            if rc != 0:
                failures.append(("example-invalid", f"examples/{path.name}",
                                 output.strip().splitlines()[-1] if output.strip() else "no output"))
        print()

    print("=" * 80)
    total = (len(valid_entries) + len(invalid_entries) + len(compat_entries)
             + len(example_files))
    passed = total - len(failures)
    print(f"Corpus result: {passed}/{total} checks behaved as expected "
          f"({len(valid_entries) + len(invalid_entries) + len(compat_entries)} "
          f"fixtures + {len(example_files)} examples)")
    print()

    if failures:
        print("FAILURES:")
        for kind, rel, detail in failures:
            print(f"  - [{kind}] {rel}")
            if detail:
                print(f"      {detail}")
        sys.exit(1)
    else:
        print("All corpus expectations met.")
        sys.exit(0)


if __name__ == "__main__":
    main()
