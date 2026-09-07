#!/usr/bin/env python3
"""Shared schema stage and emission gate for the LC-JSON reference validators.

Two related jobs live here, in one module so the published tool set stays at seven
Python files:

  * the Draft-07 schema stage (schema_stage, validate_against_schema, the RD-1 and
    canonical-$schema identity checks) that every domain validator runs first;
  * the emission gate (validate_for_emission, embedded_problems) that every writer
    runs before putting a document on disk — see the section at the end of the file.


Loads the published JSON Schemas and validates a document against the schema for
its documentType, plus the RD-1 specVersion <-> $schema agreement check
(NORMATIVE.md Section 8.4). lc_collection.py, lc_pack.py, and lc_glossary.py call
schema_stage() ahead of their hand-written domain checks so a document that is
schema-invalid or RD-1-invalid is reported, not silently accepted.

Does NOT degrade to success. If `jsonschema` is not installed, or the published
schemas cannot be loaded, full validation is *unavailable* — a distinct state from
"valid". CLI entry points call cli_preflight(), which exits
EXIT_VALIDATION_UNAVAILABLE rather than letting a schema-invalid document reach a
zero exit. Domain-only operation remains available, but only as an explicit
opt-in (`--domain-only`) that never reports conformance.
"""

import contextlib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

# Exit status for "full validation could not run". Distinct from 0 (conforming)
# and 1 (non-conforming) so a caller can never mistake an unavailable check for
# a passing one.
EXIT_VALIDATION_UNAVAILABLE = 3

_HERE = Path(__file__).resolve().parent

# documentType -> the schema file that validates that artifact.
_SCHEMA_BY_DOCTYPE = {
    "course": "course.schema.json",
    "questionSet": "question-set.schema.json",
    "subjectCollection": "subject-collection.schema.json",
    "curriculumPack": "curriculum-pack.schema.json",
    "glossary": "glossary.schema.json",
}


def _version_key(publication):
    """Sort key for a publication segment: 1.0-rc.1 < 1.0-rc.3 < 1.0 < 1.1-rc.1 < 1.1.

    A final release sorts ABOVE its own release candidates (rc tier 0 vs 1) and
    below the next minor's candidates.
    """
    match = re.match(r"^(\d+)\.(\d+)(?:-rc\.(\d+))?$", publication or "")
    if not match:
        return (-1, -1, -1, -1)
    major, minor, rc = match.group(1), match.group(2), match.group(3)
    return (int(major), int(minor), 0 if rc else 1, int(rc) if rc else 0)


def detect_schemas_root():
    """Returns (root, layout) for the current tree.

    Source layout:            tools/ alongside a sibling specification/schemas/,
                              a FLAT directory holding one publication.
    Public spec repo layout:  tools/ -> ../schemas/<X.Y(-rc.N)>/, one directory
                              per publication, all of them served forever.
    """
    dev = _HERE.parent / "specification" / "schemas"
    if dev.is_dir():
        return dev, "flat"
    pub_root = _HERE.parent / "schemas"
    if pub_root.is_dir():
        return pub_root, "versioned"
    return dev, "flat"


def _publication_of_dir(directory):
    """The publication a schema directory belongs to, read from its own $id values.

    Never inferred from the directory name and never hardcoded, so it cannot drift
    from what the schemas actually declare.
    """
    for candidate in sorted(directory.glob("*.schema.json")):
        try:
            schema_id = json.loads(candidate.read_text(encoding="utf-8")).get("$id")
        except (OSError, ValueError):
            continue
        if isinstance(schema_id, str):
            match = _VERSIONED_URL.match(schema_id)
            if match:
                return match.group(0).rstrip("/").rsplit("/", 1)[-1]
    return None


def publication_dirs():
    """publication segment -> its schema directory, for every publication present.

    In the published layout that is all shipped publications; in the source
    layout it is the single publication under development.
    """
    root, layout = detect_schemas_root()
    result = {}
    if layout == "flat":
        if root.is_dir():
            pub = _publication_of_dir(root)
            if pub:
                result[pub] = root
        return result
    if not root.is_dir():
        return result
    for directory in sorted(root.iterdir()):
        if not directory.is_dir():
            continue
        pub = _publication_of_dir(directory)
        if pub:
            result[pub] = directory
    return result


def bundled_publication():
    """The publication this validator treats as its own — the newest present.

    Derived by version-sorting the publications actually in the tree, so it moves
    with the publication automatically, rather than naming a publication here.
    """
    pubs = publication_dirs()
    if not pubs:
        return None
    return max(pubs, key=_version_key)


try:
    from jsonschema import Draft7Validator
    from referencing import Registry
    from referencing.jsonschema import DRAFT7
    _HAVE_JSONSCHEMA = True
except ImportError:  # pragma: no cover - environment-dependent
    _HAVE_JSONSCHEMA = False

# publication -> {"schemas": {filename: doc}, "registry": Registry|None}
_PUBLICATION_CACHE = {}


def load_publication(publication):
    """Load one publication's schemas (and Registry). Returns the cache entry or None.

    The raw schema documents load even without `jsonschema`, because the identity
    checks read `$id` and must keep working well enough to report that the Draft-07
    pass is unavailable rather than silently skipping it.
    """
    if publication in _PUBLICATION_CACHE:
        return _PUBLICATION_CACHE[publication]
    directory = publication_dirs().get(publication)
    if directory is None:
        _PUBLICATION_CACHE[publication] = None
        return None

    schemas, pairs = {}, []
    for path in sorted(directory.glob("*.schema.json")):
        try:
            contents = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        schemas[path.name] = contents
        if not _HAVE_JSONSCHEMA:
            continue
        resource = DRAFT7.create_resource(contents)
        pairs.append((path.name, resource))
        schema_id = contents.get("$id")
        if schema_id:
            pairs.append((schema_id, resource))
    entry = {"schemas": schemas,
             "registry": Registry().with_resources(pairs) if _HAVE_JSONSCHEMA else None}
    _PUBLICATION_CACHE[publication] = entry
    return entry


def _bundled_schemas():
    entry = load_publication(bundled_publication())
    return (entry or {}).get("schemas", {})


def available():
    """True when jsonschema is installed and the bundled publication loaded."""
    return _HAVE_JSONSCHEMA and bool(_bundled_schemas())


def _ref_closure(schema_filename, schemas):
    """Every local schema file reachable from `schema_filename` through $ref.

    A missing $ref target is as fatal to the Draft-07 pass as a missing artifact
    schema, so the closure is what "required" has to mean.
    """
    needed, queue = set(), [schema_filename]
    while queue:
        current = queue.pop()
        if current in needed:
            continue
        needed.add(current)
        contents = schemas.get(current)
        if contents is None:
            continue
        stack = [contents]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                ref = node.get("$ref")
                if isinstance(ref, str) and not ref.startswith("#"):
                    target = ref.split("#", 1)[0]
                    if target.endswith(".schema.json"):
                        queue.append(target.rsplit("/", 1)[-1])
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    return needed


def missing_required_schemas(doctype, schemas):
    """Schema files needed to validate `doctype` that are absent from `schemas`."""
    filename = _SCHEMA_BY_DOCTYPE.get(doctype)
    if not filename:
        return []
    return sorted(f for f in _ref_closure(filename, schemas) if f not in schemas)


def unavailable_reason(doctype=None, publication=None):
    """None when the Draft-07 pass can run; otherwise why it cannot.

    Callers MUST treat a non-None result as "validation unavailable" — never as
    "no errors found". A partially loaded registry counts: a missing schema is an
    infrastructure failure, and reporting it as a document error would blame the
    document for the tool's problem.
    """
    if not _HAVE_JSONSCHEMA:
        return ("the 'jsonschema' package is not installed, so Draft-07 schema "
                "validation cannot run")
    publication = publication or bundled_publication()
    entry = load_publication(publication) if publication else None
    schemas = (entry or {}).get("schemas") or {}
    if not schemas:
        root, _layout = detect_schemas_root()
        return (f"no JSON Schemas could be loaded for publication "
                f"'{publication}' under {root}, so Draft-07 schema validation "
                "cannot run")
    if doctype:
        missing = missing_required_schemas(doctype, schemas)
        if missing:
            return (f"publication '{publication}' is missing "
                    f"{len(missing)} schema file(s) required to validate a "
                    f"'{doctype}' document ({', '.join(missing)}), so the Draft-07 "
                    "pass cannot be completed")
    return None


def resolve_publication_for(doc):
    """Which publication a document should be validated against, and whether it loaded.

    NORMATIVE Section 8.4 makes the declared `$schema` URL the binding validation
    target, so a document declaring an older publication is validated against THAT
    publication's schemas when this tree carries them — which the published clone
    does, for every release it has ever served. Validating a 1.0 document against
    1.1 schemas and then exiting 0 would assert a conformance the tool never checked.

    Returns (publication, entry, unavailable) — `unavailable` is a string when the
    declared publication cannot be loaded here, in which case the result is
    INDETERMINATE and callers must not report conformance.
    """
    declared = None
    schema_url = doc.get("$schema")
    if isinstance(schema_url, str):
        match = _VERSIONED_URL.match(schema_url)
        if match:
            declared = match.group(0).rstrip("/").rsplit("/", 1)[-1]

    publication = declared or bundled_publication()
    entry = load_publication(publication) if publication else None
    if entry is None or not entry.get("schemas"):
        return publication, None, (
            f"the document declares publication '{publication}', whose schemas are "
            "not carried in this tree, so it cannot be validated against the schema "
            "set NORMATIVE Section 8.4 makes binding. This is an INDETERMINATE "
            "result, not a conformance statement — use a validator built for that "
            "publication")
    return publication, entry, None


def cli_preflight(domain_only=False, stream=None, reason=None, doctype=None):
    """Gate a validator CLI on schema-validation availability.

    `--domain-only` is an EXPLICIT request for the reduced check, so it wins over
    availability: it returns False whether or not the schemas could load, and the
    caller must then skip every schema stage and report DOMAIN-ONLY OK rather than
    VALID. (Previously this returned True as soon as the dependency was present,
    so with `jsonschema` installed the flag did nothing at all and the tool still
    printed VALID.)

    `reason` lets a caller that loads schemas itself (validate_course.py has its
    own registry) supply its own unavailability reason. `doctype` narrows the
    availability question to the schemas that artifact actually needs.

    Returns True when full validation (schema + domain) will run.
    Returns False for domain-only mode — the caller MUST NOT report conformance.
    Exits EXIT_VALIDATION_UNAVAILABLE when validation cannot run and no explicit
    opt-in was given.
    """
    out = stream or sys.stderr
    if domain_only:
        print("  DOMAIN-ONLY: schema validation skipped at your request "
              "(--domain-only).", file=out)
        print("  Domain rules only. This is NOT a conformance check.", file=out)
        return False
    if reason is None:
        reason = unavailable_reason(doctype)
    if reason is None:
        return True
    print(f"VALIDATION UNAVAILABLE — {reason}.", file=out)
    print("This document was NOT checked for conformance. Install the dependency "
          "(pip install -r tools/requirements.txt), or pass --domain-only to run "
          "domain rules alone — which is not a conformance check.", file=out)
    sys.exit(EXIT_VALIDATION_UNAVAILABLE)


def exit_unavailable(reason, stream=None):
    """Report an indeterminate result and exit 3. Never reports on the document."""
    out = stream or sys.stderr
    print(f"VALIDATION UNAVAILABLE — {reason}.", file=out)
    sys.exit(EXIT_VALIDATION_UNAVAILABLE)


def exit_unavailable_unless_definitive(schema_errors, reason, stream=None):
    """Resolve an unrunnable Draft-07 pass into a truthful three-state result.

    Canonical-$schema identity and RD-1 are computed without jsonschema and without
    loading the publication the document declares, so when either has already failed,
    the document is definitively non-conforming and that verdict does not depend on
    the pass that could not run. Exiting 3 there discards a finding the tool already
    holds — and because a harness may read any non-zero exit as "correctly rejected",
    it can turn an unadjudicated fixture into a silent pass.

    This relies on an invariant upheld by the producer of `schema_errors`, not on
    inspecting them here: every error in that list is availability-independent. A
    condition that only means "this tree cannot check that" — above all, a declared
    publication absent locally — must arrive as `reason`, never as an error, or a 1.2
    document would be reported non-conforming by a 1.1 validator.

    Definitive errors present -> report them and exit 1, noting the list may be
    partial. No definitive error -> genuinely indeterminate, exit 3.
    """
    if not schema_errors:
        exit_unavailable(reason, stream)
    out = stream or sys.stdout
    print(f"INVALID — {len(schema_errors)} problem(s) established without the "
          f"Draft-07 pass:", file=out)
    for error in schema_errors:
        print(f"  - {error}", file=out)
    print(f"Note: the Draft-07 schema pass did not run ({reason}), so this list may "
          f"be incomplete; the document is non-conforming regardless.", file=out)
    sys.exit(1)


def validate_against_schema(doc, schema_filename, entry=None):
    """Validate `doc` against a named schema from `entry` (default: the bundled
    publication). Returns a list of error strings.

    A schema that is absent is NOT reported here as a document error — that is an
    infrastructure condition, surfaced by unavailable_reason() as exit 3. Blaming
    the document for the tool's missing file was exactly the partial-registry bug.
    """
    if not _HAVE_JSONSCHEMA:
        return []
    if entry is None:
        entry = load_publication(bundled_publication())
    if not entry:
        return []
    schema = entry["schemas"].get(schema_filename)
    if schema is None:
        return []
    validator = Draft7Validator(schema, registry=entry["registry"])
    errors = []
    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        location = "/".join(str(p) for p in err.absolute_path) or "(root)"
        errors.append(f"schema: {location}: {err.message}")
    return errors


_VERSIONED_URL = re.compile(r"https?://lc-json\.org/(\d+\.\d+)(?:-rc\.\d+)?/")


def rd1_error(doc):
    """RD-1 (NORMATIVE Section 8.4): when both `specVersion` and an lc-json.org
    versioned `$schema` URL are present, their major.minor MUST match. Absence of
    either field is governed by Section 3.2 and is not reported here. Returns an
    error string or None."""
    spec_version = doc.get("specVersion")
    schema_url = doc.get("$schema")
    if not isinstance(spec_version, str) or not isinstance(schema_url, str):
        return None
    url_match = _VERSIONED_URL.match(schema_url)
    if not url_match:
        return None
    sv_match = re.match(r"^(\d+\.\d+)", spec_version)
    if not sv_match:
        return None
    if url_match.group(1) != sv_match.group(1):
        return (f"RD-1: specVersion '{spec_version}' disagrees with the $schema "
                f"version path '{url_match.group(1)}' — the two MUST agree on "
                "major.minor (NORMATIVE Section 8.4)")
    return None


_CANONICAL_HOST = "https://lc-json.org/"


def schema_identity_errors(doc):
    """Canonical `$schema` identity (NORMATIVE Section 4.7 / Section 8.4).

    A producer MUST declare the canonical schema URL for its own `documentType`,
    and Section 8.4 makes the declared URL the binding validation target. Checking
    only the major/minor path (RD-1) lets a document declare, say, the Glossary
    schema while carrying a SubjectCollection — the two disagree and one of them
    is wrong.

    Verifies, when `$schema` is present:
      * the canonical host and a versioned publication path;
      * the schema filename matches the document's own `documentType`;
      * where the declared publication IS carried here, that it actually contains
        the named artifact schema.

    Every error returned is definitive and availability-independent: it condemns the
    document on evidence that does not depend on which publications this tree happens
    to carry. A publication simply being absent locally is an availability condition
    (exit 3), not an error, and is not reported here.

    Absence of `$schema` is governed by Section 3.2 and is not reported here.
    Returns a list of error strings.
    """
    schema_url = doc.get("$schema")
    if not isinstance(schema_url, str) or not schema_url:
        return []

    errors = []
    doctype = doc.get("documentType")
    if not schema_url.startswith(_CANONICAL_HOST):
        return [f"$schema '{schema_url}' is not a canonical LC-JSON schema URL — "
                f"producers MUST declare a '{_CANONICAL_HOST}<publication>/"
                "<artifact>.schema.json' URL (NORMATIVE Section 4.7)"]

    match = _VERSIONED_URL.match(schema_url)
    if not match:
        return [f"$schema '{schema_url}' has no versioned publication path — "
                f"expected '{_CANONICAL_HOST}<major>.<minor>[-rc.N]/"
                "<artifact>.schema.json' (NORMATIVE Section 8.3)"]

    declared_pub = match.group(0).rstrip("/").rsplit("/", 1)[-1]
    filename = schema_url[len(match.group(0)):]

    expected_filename = _SCHEMA_BY_DOCTYPE.get(doctype)
    if expected_filename and filename != expected_filename:
        errors.append(
            f"$schema declares '{filename}' but documentType is '{doctype}', whose "
            f"canonical schema is '{expected_filename}' — a producer MUST declare "
            "the canonical schema for its own documentType (NORMATIVE Section 4.7)")
    elif expected_filename is None and doctype is not None:
        errors.append(
            f"documentType '{doctype}' is not a known LC-JSON artifact type, so its "
            f"declared $schema '{filename}' cannot be checked (NORMATIVE Section 3.3)")

    # "This tree does not carry the declared publication" is deliberately NOT an
    # error here. It is a fact about this validator's environment, not about the
    # document: a 1.2 document is not non-conforming because a 1.1 validator cannot
    # reach 1.2's schemas. resolve_publication_for() carries that case as an
    # unavailable reason, which the CLI entry points turn into exit 3 — the
    # three-state contract in IMPLEMENTATIONS.md, and NORMATIVE Section 5.2's
    # forward-minor posture. Everything this function returns must be definitive
    # independently of what is present locally, because callers exit 1 on it.
    known = publication_dirs()
    if known and declared_pub in known:
        # The publication exists, but does the artifact schema exist WITHIN it?
        # Checking the directory alone let a SubjectCollection declare
        # /1.0/subject-collection.schema.json — a publication that predates the
        # artifact type entirely, so the URL resolves to nothing.
        entry = load_publication(declared_pub)
        if entry and filename not in entry["schemas"]:
            errors.append(
                f"$schema declares '{filename}' in publication '{declared_pub}', but "
                f"that publication carries no such schema — '{declared_pub}' predates "
                f"this artifact type or never published it. The declared URL resolves "
                "to nothing, so it cannot be the binding validation target "
                "(NORMATIVE Section 8.4).")
    return errors


def schema_stage(doc, expected_doctype):
    """Front-stage a domain validator runs before its own checks.

    Returns (errors, unavailable):
      errors      — canonical-$schema identity errors, RD-1 errors, and Draft-07
                    errors against the publication the document DECLARES.
      unavailable — a string when no conformance statement can be made (dependency
                    missing, required schemas absent, or the declared publication
                    not carried here). Callers MUST NOT report conformance then;
                    CLI entry points exit EXIT_VALIDATION_UNAVAILABLE.
    """
    errors = []
    # Identity and RD-1 need no jsonschema, so they run in every mode.
    errors.extend(schema_identity_errors(doc))
    rd1 = rd1_error(doc)
    if rd1:
        errors.append(rd1)

    if not _HAVE_JSONSCHEMA:
        return errors, unavailable_reason(expected_doctype)

    publication, entry, unavailable = resolve_publication_for(doc)
    if unavailable:
        return errors, unavailable
    reason = unavailable_reason(expected_doctype, publication)
    if reason:
        return errors, reason

    schema_filename = _SCHEMA_BY_DOCTYPE.get(expected_doctype)
    if schema_filename and schema_filename in entry["schemas"]:
        errors.extend(validate_against_schema(doc, schema_filename, entry))
    return errors, None


# ---------------------------------------------------------------------------
# The emission gate
# ---------------------------------------------------------------------------
#
# "Is this document fit to emit?" gets ONE answer, and every writer asks it here:
# assemble_pack_bundle (CLI), lc_pack.save(), lc_collection.save(), and the
# command-line entry points. Before this existed, the assembler ran a schema-only
# pass over embedded documents (so a schema-valid but domain-invalid Glossary could
# be packaged) and two writers ran no document validation at all.
#
# The gate checks, in order:
#   1. Availability. If the Draft-07 pass cannot run, emission is refused outright
#      — a writer must never emit on the strength of a check that did not happen.
#   2. The root document: canonical $schema identity, RD-1, its own schema, and its
#      own domain rules.
#   3. Every embedded document in a bundle: its own schema AND its own domain rules,
#      dispatched on that document's own documentType — so an embedded Glossary is
#      checked by the glossary validator, not merely against a schema.
#
# This lives in the same module as the schema stage rather than its own file so the
# published tool surface stays at the seven shipped Python files. The validator
# imports below are deliberately INSIDE the functions: lc_pack and lc_collection
# import this module, so importing them at module scope would be circular.

def _domain_problems(doc, doctype, collection=None):
    """Run the domain validator for `doctype` over `doc`. Returns error strings.

    Warnings are deliberately not returned: emission is gated on errors, and a
    writer that refused to emit over a warning would be stricter than the spec.
    """
    if doctype == "subjectCollection":
        import lc_collection
        return list(lc_collection.validate(doc))

    if doctype == "curriculumPack":
        import lc_pack
        errors, _warnings = lc_pack.validate(doc, collection)
        return list(errors)

    if doctype == "glossary":
        import lc_glossary
        errors, _warnings = lc_glossary.validate(doc)
        return list(errors)

    if doctype in ("course", "questionSet"):
        return _course_domain_problems(doc)

    return [f"documentType '{doctype}' has no known domain validator, so this "
            "document cannot be checked for emission (NORMATIVE Section 3.3)"]


def _course_domain_problems(doc):
    """Domain-validate an in-memory course/questionSet document.

    The course validator is path-based and reports by printing, so the document is
    written to a temporary file and its output captured. That keeps a single
    implementation of the course rules rather than a second, drifting copy.
    """
    import validate_course

    handle, path = tempfile.mkstemp(suffix=".json", prefix="lcjson-emit-")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            ok = validate_course.validate_course(path, verbose=False, strict=True)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

    if ok:
        return []
    detail = [line.strip() for line in buffer.getvalue().splitlines()
              if line.strip().startswith(("ERROR", "[SCHEMA]", "FATAL"))]
    if not detail:
        detail = ["see the course validator output for detail"]
    return [f"course validation failed: {d}" for d in detail]


def validate_for_emission(doc, collection=None):
    """Return the problems that make `doc` unfit to emit. Empty list == fit.

    `collection` is the referenced SubjectCollection for a Curriculum Pack, which
    enables member resolution and coverage checks; it is ignored for other types.
    """
    doctype = doc.get("documentType")
    if not doctype:
        return ["the document declares no documentType, so no schema or domain "
                "rules can be selected for it (NORMATIVE Section 3.2)"]

    problems = []
    schema_errors, unavailable = schema_stage(doc, doctype)
    if unavailable:
        return [f"cannot validate for emission — {unavailable}. Refusing to write a "
                "document that was never checked"]
    problems.extend(schema_errors)
    problems.extend(_domain_problems(doc, doctype, collection))

    problems.extend(embedded_problems(doc))
    return problems


def embedded_problems(doc):
    """Schema AND domain problems for every document embedded in a bundle.

    Only Curriculum Packs in `bundle` mode carry `embedded`; anything else has
    nothing to check here.
    """
    # Pack semantics apply only to a Curriculum Pack. On any other artifact a
    # root `embedded` field is just an unknown forward-compatible member, and
    # §5.4 forbids rejecting a document for one — so do not impose pack rules on
    # it. (A curriculumPack MANIFEST carrying `embedded` is caught separately by
    # the pack validator's own E15/CP-15 check, which is pack-scoped.)
    if doc.get("documentType") != "curriculumPack":
        return []
    embedded = doc.get("embedded")
    if not isinstance(embedded, dict):
        return []

    problems = []
    for group in ("collections", "content"):
        entries = embedded.get(group)
        if entries is None:
            continue
        if not isinstance(entries, list):
            problems.append(f"embedded.{group} is not an array")
            continue
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                problems.append(f"embedded.{group}[{index}] is not a JSON object")
                continue
            entry_type = entry.get("documentType")
            # Type-directed identity, not root globalId: a course/questionSet has no
            # root globalId, so the old label reported 'None' for them.
            _idf = {"course": "sourceCourseId",
                    "questionSet": "sourceQuestionSetId"}.get(entry_type, "globalId")
            label = (f"embedded {entry_type or '(no documentType)'} "
                     f"'{entry.get(_idf)}'")
            if not entry_type:
                problems.append(f"{label}: declares no documentType, so it cannot "
                                "be validated (NORMATIVE Section 3.2)")
                continue
            if entry_type == "curriculumPack":
                # A bundle MUST NOT embed a pack: 1.1 defines no pack-in-pack
                # nesting (NORMATIVE Section 4.4). Rejecting it here means no pack
                # can ever be embedded, so this validator never has to recurse into
                # a nested bundle's own embedded documents — there are none.
                problems.append(f"{label}: a bundle MUST NOT embed a curriculumPack "
                                "— 1.1 does not define pack-in-pack nesting "
                                "(NORMATIVE Section 4.4)")
                continue
            schema_errors, unavailable = schema_stage(entry, entry_type)
            if unavailable:
                problems.append(f"{label}: cannot be validated — {unavailable}")
                continue
            for err in schema_errors:
                problems.append(f"{label}: {err}")
            for err in _domain_problems(entry, entry_type):
                problems.append(f"{label}: {err}")
    return problems
