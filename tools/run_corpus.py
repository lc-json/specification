#!/usr/bin/env python3
"""
run_corpus.py - Run the LC-JSON conformance corpus through the reference validator.

Reads `specification/tests/manifest.json`, runs every valid/* fixture and every
invalid/* fixture through `validate_course.py --strict`, and reports pass/fail
counts. Exits 0 only when the entire corpus behaves as the manifest says it
should (all valid pass, all invalid fail).

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

    Lesson Commons monorepo (source):  LC.JSON/tools/ → ../specification/tests/
    Public spec repo (published):      tools/         → ../tests/
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


def run_validator(fixture_path, verbose):
    """Run validate_course.py --strict on a fixture. Returns (exit_code, output)."""
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), "--course-path", str(fixture_path), "--strict"],
        capture_output=True,
        text=True,
    )
    if verbose:
        print(proc.stdout)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
    return proc.returncode, proc.stdout + proc.stderr


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

    print("LC-JSON conformance corpus harness")
    print("=" * 80)
    print(f"  manifest:        {manifest_path}")
    print(f"  validator:       {VALIDATOR}")
    print(f"  valid fixtures:  {len(valid_entries)}")
    print(f"  invalid fixtures:{len(invalid_entries)}")
    print()

    failures = []  # list of (kind, file, reason)

    # Valid fixtures MUST pass under --strict.
    print(f"Valid fixtures (expecting exit 0):")
    for entry in valid_entries:
        rel = entry["file"]
        path = args.tests_dir / rel
        rc, output = run_validator(path, args.verbose)
        status = "PASS" if rc == 0 else "FAIL"
        print(f"  [{status}] {rel}  (exit {rc})")
        if rc != 0:
            failures.append(("valid-but-failed", rel, output.strip().splitlines()[-1] if output.strip() else "no output"))

    print()

    # Invalid fixtures MUST fail under --strict.
    print(f"Invalid fixtures (expecting exit non-zero):")
    for entry in invalid_entries:
        rel = entry["file"]
        path = args.tests_dir / rel
        rc, output = run_validator(path, args.verbose)
        status = "PASS" if rc != 0 else "FAIL"
        print(f"  [{status}] {rel}  (exit {rc})  -- {entry.get('violatedClause', '?')}")
        if rc == 0:
            failures.append(("invalid-but-passed", rel, entry.get("violation", "")))

    print()
    print("=" * 80)
    total = len(valid_entries) + len(invalid_entries)
    passed = total - len(failures)
    print(f"Corpus result: {passed}/{total} fixtures behaved as expected")
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
