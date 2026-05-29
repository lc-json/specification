#!/usr/bin/env python3
"""
validate_course.py - Validate course.json / question-set.json structure.

Usage:
    python validate_course.py
    python validate_course.py --course-path "path/to/course.json"
    python validate_course.py --verbose
    python validate_course.py --strict       # public-conformance mode (TD-155)
    python validate_course.py --no-schema    # skip jsonschema, run domain checks only

Public-conformance mode (TD-155, 2026-05-04):

    By default the validator is lenient: pre-1.0 document shapes from
    internal Lesson Commons content (wrapped envelopes `{"course":{...}}`,
    bare payloads `{"units":[...]}` with no documentType) emit a warning
    and fall through with reduced schema enforcement. This is intentional
    — the Lesson Commons Editor's migration paths still ingest these
    shapes, and failing them outright would block the upgrade. Third-party
    producers and consumers should treat the lenient path as a
    Lesson-Commons-internal migration aid, not a published affordance.

    `--strict` disables that tolerance. Pre-1.0 shapes become FATAL ERRORS
    in strict mode. Conformance-corpus runs MUST use --strict so that the
    NORMATIVE.md §3.2 / §4.1 rejections promised by the spec are actually
    enforced. The conformance corpus harness (tools/run_corpus.py) always
    invokes validate_course.py with --strict.

    Public conformance claims under NORMATIVE.md §10 are evaluated in
    --strict mode.

Two-pass validation (TD-109, 2026-04-28):

    1. PRIMARY — JSON Schema: every document is run through the published
       schemas in LC.JSON/specification/schemas/ via the `jsonschema` package
       (>=4.18, modern `referencing` API). This catches required-field
       omissions, enum violations, UUID format drift, type mismatches, and
       any other contract that the schemas already declare. Per-question
       schema dispatch happens in a second jsonschema pass keyed off the
       `type` discriminator (matching/ordering fall back to question-base
       until Phase 5 adds their schemas).

    2. SECONDARY — Domain rules: things JSON Schema can't easily express:
       HTML-tag allowlist + anchor scheme allowlist, gap-marker / accepted-
       answer count consistency, sequence integrity, points consistency
       (item.points == sum of question.points), SentenceTransformation
       chunk numbering and keyword case, MultiGapCloze comma/colon ban,
       ContentSequence cross-reference resolution, signpost-without-
       objectives warning.

If `jsonschema` is not installed the validator emits a startup warning and
runs only the secondary pass. Install with `pip install -r LC.JSON/requirements.txt`.
"""

import json
import re
import sys
from pathlib import Path
import argparse


# ---------------------------------------------------------------------------
# JSON Schema integration (TD-109, 2026-04-28; Phase 5, 2026-04-28)
# ---------------------------------------------------------------------------
#
# We load every *.schema.json file from LC.JSON/specification/schemas/ into
# a Registry once at startup. Each schema is registered under both its bare
# filename and its declared canonical $id (`lc-json.org/1.0-rc.2/` for the
# current rc.2 publication; `lc-json.org/1.0/` once 1.0 final ships) so
# $ref resolution works whether a schema $refs a peer by filename or by
# absolute URL.
#
# Phase 5 (2026-04-28) migrated every schema $id to the canonical
# `lc-json.org/<version>/` host. The version path tracks the publication
# being shipped (NORMATIVE.md §3.1 + §8.3): rc.N publications are at
# `/1.0-rc.N/`; the `/1.0/` path is reserved for 1.0 final.

_HERE = Path(__file__).resolve().parent

# The publication this validator ships with. The bundled reference validator
# tracks a single publication (the development head, currently 1.0-rc.2); it is
# NOT a dual-version validator — a document pins its version via $schema, and an
# rc.1 document is validated with the rc.1-tagged validator. Bump this when
# cutting the next publication (e.g. "1.0" at final). Drives both the public-repo
# schema-dir selection and the canonical $id registered for $ref resolution.
_CURRENT_PUBLICATION = "1.0-rc.2"


def _detect_schemas_dir():
    """Resolve the schemas directory for the current layout.

    Lesson Commons monorepo (source):  LC.JSON/tools/ → ../specification/schemas/
    Public spec repo (published):      tools/         → ../schemas/<X.Y(-rc.N)>/

    Tries the source-layout path first. In the public-repo layout, multiple
    immutable versioned dirs may coexist (e.g. a frozen schemas/1.0-rc.1/
    alongside schemas/1.0-rc.2/), so this MUST load the dir for THIS validator's
    own publication (_CURRENT_PUBLICATION) — never whichever sorts first, which
    would validate one publication's documents against another's schemas.
    """
    dev_path = _HERE.parent / "specification" / "schemas"
    if dev_path.is_dir():
        return dev_path
    pub_schemas_root = _HERE.parent / "schemas"
    if pub_schemas_root.is_dir():
        # Prefer this validator's own publication.
        preferred = pub_schemas_root / _CURRENT_PUBLICATION
        if (preferred / "course.schema.json").exists():
            return preferred
        # Fallback: a single-version deployment published under a different name.
        for candidate in sorted(pub_schemas_root.iterdir()):
            if candidate.is_dir() and (candidate / "course.schema.json").exists():
                return candidate
    return dev_path  # fallback; downstream errors will be clearer than a misleading path


SCHEMAS_DIR = _detect_schemas_dir()

# Map question type discriminator (camelCase) → schema filename.
# matching/ordering have no per-type schemas yet (Phase 5 task) — fall back
# to question-base.schema.json.
_QUESTION_TYPE_SCHEMA = {
    "simpleGapFill": "simple-gap-fill.schema.json",
    "trueFalseQuestion": "true-false-question.schema.json",
    "multipleChoice": "multiple-choice.schema.json",
    "wordBankCloze": "word-bank-cloze.schema.json",
    "multiGapCloze": "multi-gap-cloze.schema.json",
    "multipleChoiceCloze": "multiple-choice-cloze.schema.json",
    "shortAnswer": "short-answer.schema.json",
    "essay": "essay.schema.json",
    "sentenceTransformation": "sentence-transformation.schema.json",
    "matching": "matching.schema.json",
    "ordering": "ordering.schema.json",
    "placement": "placement.schema.json",
    # Reserved-for-2027 question types (FF-102) — declared in question-base
    # enum but with no per-type schema yet. Validate against base only.
    "association": "question-base.schema.json",
    "hotspot": "question-base.schema.json",
    "graphicGapMatch": "question-base.schema.json",
    "graphicAssociate": "question-base.schema.json",
    "graphicOrder": "question-base.schema.json",
    "fileUpload": "question-base.schema.json",
    "mediaPromptedEssay": "question-base.schema.json",
}

try:
    from jsonschema import Draft7Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT7
    _JSONSCHEMA_AVAILABLE = True
except ImportError as _ie:
    _JSONSCHEMA_IMPORT_ERROR = str(_ie)
    _JSONSCHEMA_AVAILABLE = False


def _load_schema_registry():
    """Load every *.schema.json into a Registry keyed by multiple URIs.

    Returns (registry, schemas_by_filename). Registry is None if jsonschema
    is unavailable.
    """
    if not _JSONSCHEMA_AVAILABLE:
        return None, {}

    if not SCHEMAS_DIR.is_dir():
        return None, {}

    schemas_by_filename = {}
    pairs = []
    for path in sorted(SCHEMAS_DIR.glob("*.schema.json")):
        with path.open("r", encoding="utf-8") as f:
            contents = json.load(f)

        fname = path.name
        schemas_by_filename[fname] = contents

        resource = DRAFT7.create_resource(contents)
        declared_id = contents.get("$id", "") or ""
        canonical = f"https://lc-json.org/{_CURRENT_PUBLICATION}/{fname}"

        # De-dup so we don't register the same URI twice with the same resource.
        for uri in {fname, declared_id, canonical}:
            if uri:
                pairs.append((uri, resource))

    registry = Registry().with_resources(pairs)
    return registry, schemas_by_filename


_SCHEMA_REGISTRY, _SCHEMAS = _load_schema_registry()


def _format_schema_path(path_iter, ref_prefix=""):
    """Render a jsonschema absolute_path deque as 'ref_prefix > a > b > c'."""
    segments = [ref_prefix] if ref_prefix else []
    segments.extend(str(p) for p in path_iter)
    return " > ".join(segments) if segments else "<root>"


def _validate_against_schema(payload, schema_filename, ref_prefix=""):
    """Run a payload through the named schema. Returns list of error strings.

    If jsonschema isn't available, returns an empty list — caller relies on
    the secondary domain-rule pass.
    """
    if not _JSONSCHEMA_AVAILABLE:
        return []

    schema = _SCHEMAS.get(schema_filename)
    if schema is None:
        return [f"INTERNAL: schema '{schema_filename}' not found in registry"]

    validator = Draft7Validator(schema, registry=_SCHEMA_REGISTRY)
    errors = []
    for err in validator.iter_errors(payload):
        path = _format_schema_path(err.absolute_path, ref_prefix)
        # Trim verbose `instance` repr from the message — jsonschema tends to
        # echo the full offending value. Keep just the short reason.
        msg = err.message.split("\n", 1)[0]
        if len(msg) > 240:
            # `oneOf` failures dump the full instance dict into the message;
            # truncate so the report stays scannable. The path locates the
            # error; the per-element details show up in subsequent errors.
            msg = msg[:240].rsplit(" ", 1)[0] + "… (truncated)"
        errors.append(f"[SCHEMA] {path}: {msg}")
    return errors


def _validate_questions_per_type(questions, parent_ref):
    """Run each question through its per-type schema (TD-109 secondary pass).

    Yields error strings. The parent's `course`/`question-set` schema only
    validates against question-base for items in a questions[] array, so
    type-specific properties (options on multipleChoice, acceptedChunks on
    sentenceTransformation, etc.) need a per-question pass to be enforced.
    """
    errors = []
    if not _JSONSCHEMA_AVAILABLE:
        return errors

    for idx, question in enumerate(questions or []):
        if not isinstance(question, dict):
            continue
        qtype = question.get("type")
        schema_name = _QUESTION_TYPE_SCHEMA.get(qtype)
        ref = f"{parent_ref} > Q{idx + 1} ({qtype})"
        if schema_name is None:
            # Surface a clean error for unknown question types so the user
            # doesn't have to parse the noisy oneOf failure from the parent.
            errors.append(
                f"[SCHEMA] {ref} > type: '{qtype}' is not a recognised question "
                f"discriminator. Allowed: {', '.join(sorted(_QUESTION_TYPE_SCHEMA.keys()))}."
            )
            continue
        errors.extend(_validate_against_schema(question, schema_name, ref))
    return errors


def _walk_and_validate_all_questions(course):
    """Walk Course → Units → Lessons → Items, validate each item's questions
    against its per-type schema. Returns list of error strings."""
    errors = []
    units = course.get("units") or []
    for u_idx, unit in enumerate(units):
        if not isinstance(unit, dict):
            continue
        unit_ref = f"units > {u_idx}"
        for l_idx, lesson in enumerate(unit.get("lessons") or []):
            if not isinstance(lesson, dict):
                continue
            lesson_ref = f"{unit_ref} > lessons > {l_idx}"
            for i_idx, item in enumerate(lesson.get("items") or []):
                if not isinstance(item, dict):
                    continue
                item_ref = f"{lesson_ref} > items > {i_idx}"
                if isinstance(item.get("questions"), list):
                    errors.extend(_validate_questions_per_type(item["questions"], item_ref))
    return errors


def _collect_weighted_points_notes(course):
    """TD-122: emit informational notes when an Exercise/Quiz item's `points`
    field differs from the sum of its question points. This is intentional —
    teachers weight an item to a fixed score (e.g. 10) regardless of question
    count or per-question values — so the mismatch is a NOTE, not a WARN.
    """
    notes = []
    units = course.get("units") or []
    for u_idx, unit in enumerate(units):
        if not isinstance(unit, dict):
            continue
        for l_idx, lesson in enumerate(unit.get("lessons") or []):
            if not isinstance(lesson, dict):
                continue
            for i_idx, item in enumerate(lesson.get("items") or []):
                if not isinstance(item, dict):
                    continue
                if normalize_item_type(item.get("type")) not in ("exercise", "quiz"):
                    continue
                if "points" not in item or not isinstance(item.get("questions"), list):
                    continue
                declared = item["points"]
                calculated = sum(q.get("points", 0) for q in item["questions"] if isinstance(q, dict))
                if declared != calculated:
                    item_ref = (
                        f"Unit {u_idx} ({unit.get('title', 'Untitled')}) > "
                        f"Lesson {l_idx} ({lesson.get('title', 'Untitled')}) > "
                        f"Item {i_idx} ({item.get('type')}: {item.get('title', 'Untitled')})"
                    )
                    notes.append(
                        f"{item_ref}: weighted points ({declared}) differ from "
                        f"sum of question points ({calculated}) — intentional "
                        f"if you're weighting this item to a fixed score."
                    )
    return notes


def _collect_objective_id_violations(course):
    """KG-6: referential integrity for objectiveIds at every structural level.

    Every entry in courseObjectiveIds[], unit.objectiveIds[], and
    lesson.objectiveIds[] MUST reference an id declared in
    course.objectives[].id. Unresolved references break the signpost-
    auto-rendering contract (a signpost with an unresolved objective id
    renders nothing for that id).

    Returns a list of WARN-tier violation strings (warning-tier per the
    TD-145 framing of integrity checks — does not block import, but
    surfaces authoring errors).
    """
    warnings = []
    objectives = course.get('objectives') or []
    if not isinstance(objectives, list):
        return warnings  # schema-level error; let it surface elsewhere

    valid_ids = {
        obj.get('id') for obj in objectives
        if isinstance(obj, dict) and isinstance(obj.get('id'), str)
    }

    def _check(scope_ref, ids_field, container):
        ref_ids = container.get(ids_field)
        if not isinstance(ref_ids, list):
            return
        for ref_id in ref_ids:
            if not isinstance(ref_id, str):
                continue
            if ref_id not in valid_ids:
                warnings.append(
                    f"{scope_ref}: '{ids_field}' references '{ref_id}', which is not "
                    f"declared in course.objectives[]. Signposts that try to render "
                    f"this objective will show nothing for it."
                )

    _check(f"Course ({course.get('title', 'Untitled')})", 'courseObjectiveIds', course)

    for u_idx, unit in enumerate(course.get('units') or []):
        if not isinstance(unit, dict):
            continue
        unit_ref = f"Unit {u_idx} ({unit.get('title', 'Untitled')})"
        _check(unit_ref, 'objectiveIds', unit)
        for l_idx, lesson in enumerate(unit.get('lessons') or []):
            if not isinstance(lesson, dict):
                continue
            lesson_ref = f"{unit_ref} > Lesson {l_idx} ({lesson.get('title', 'Untitled')})"
            _check(lesson_ref, 'objectiveIds', lesson)

    return warnings


# UUID v4 regex pattern
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', re.IGNORECASE)

BOOLEANISH_TRUE = {"true", "1", "correct", "yes", "tick"}
BOOLEANISH_FALSE = {"false", "0", "incorrect", "no", "cross"}
TF_DISPLAY_STYLES = {"TrueFalse", "CorrectIncorrect", "CheckmarkX"}

# ---------------------------------------------------------------------------
# HTML safety profile (TD-130) — mirrors LC.JSON/specification/HTML_SAFETY.md.
#
# Severity policy:
#   ERROR   — XSS-class. Forbidden elements (§2.4), event handlers (`on*`),
#             `javascript:` / `vbscript:` URLs.
#   WARN    — sanitizable. Unknown elements, unknown attributes, CSS properties
#             outside the §3.4 allowlist, `tel:` URLs (consumer-policy gated),
#             `data:` URLs, missing `rel="noopener noreferrer"` on
#             target="_blank", missing `alt` on <img>.
#
# Spec authority: HTML_SAFETY.md is the source of truth. If this validator and
# the spec disagree, the spec wins; update this file.
# ---------------------------------------------------------------------------

# §2.1–§2.3 allowed elements
HTML_ALLOWED_TAGS = {
    # Block (§2.1)
    "p", "div",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "blockquote", "pre", "hr",
    "table", "thead", "tbody", "tr", "th", "td",
    "figure", "figcaption",
    # Inline (§2.2)
    "a", "strong", "em", "b", "i", "u", "mark", "small", "sub", "sup",
    "code", "br", "span", "abbr", "q", "time",
    # Media (§2.3)
    "img", "video", "audio", "source", "track",
}

# §2.4 forbidden elements — presence is an ERROR.
HTML_FORBIDDEN_TAGS = {
    "script", "iframe", "object", "embed",
    "form", "input", "button", "select", "textarea",
    "style", "link", "meta", "base",
    "svg", "math",
    "applet", "frame", "frameset", "noframes",
}

# §4.1 allowed URL schemes
HTML_ALLOWED_LINK_SCHEMES = {"http", "https", "mailto", "tel"}

# §4.2 explicitly-forbidden URL schemes that aren't javascript/vbscript
# (those two are separate ERROR-level checks)
HTML_FORBIDDEN_URL_SCHEMES = {
    "data", "blob", "file", "chrome", "chrome-extension",
    "ftp", "ws", "wss", "gopher", "view-source",
}

# §3.4 inline-style CSS-property allowlist
HTML_ALLOWED_CSS_PROPERTIES = {
    # Sizing
    "max-width", "min-width", "width",
    "max-height", "min-height", "height",
    # Spacing
    "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
    "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
    # Borders
    "border", "border-top", "border-right", "border-bottom", "border-left",
    "border-collapse", "border-spacing",
    "border-style", "border-width", "border-color",
    # Alignment
    "text-align", "vertical-align",
}

# Universal attributes that may appear on any allowed element (§3.1)
HTML_UNIVERSAL_ATTRS = {"id", "class", "title", "lang", "dir", "style"}

# Per-element attribute additions (§3.3) — universal set is added on top.
HTML_PER_TAG_ATTRS = {
    "a":          {"href", "target", "rel"},
    "img":        {"src", "alt", "width", "height"},
    "video":      {"src", "poster", "controls", "width", "height", "preload"},
    "audio":      {"src", "controls", "preload"},
    "source":     {"src", "type"},
    "track":      {"src", "kind", "srclang", "label", "default"},
    "table":      {"border"},
    "th":         {"colspan", "rowspan", "headers", "scope"},
    "td":         {"colspan", "rowspan", "headers", "scope"},
    "ol":         {"start", "reversed", "type"},
    "li":         {"value"},
    "blockquote": {"cite"},
    "q":          {"cite"},
    "time":       {"datetime"},
}

# URL-bearing attributes per element (for §4 scheme checks)
HTML_URL_ATTRS = {
    "a":          ("href",),
    "img":        ("src",),
    "video":      ("src", "poster"),
    "audio":      ("src",),
    "source":     ("src",),
    "track":      ("src",),
    "blockquote": ("cite",),
    "q":          ("cite",),
}

HTML_OPEN_TAG_PATTERN = re.compile(
    r'<\s*([A-Za-z][A-Za-z0-9]*)\b([^>]*)>', re.IGNORECASE
)
HTML_CLOSE_TAG_PATTERN = re.compile(
    r'<\s*/\s*([A-Za-z][A-Za-z0-9]*)\b[^>]*>', re.IGNORECASE
)
HTML_ATTR_PATTERN = re.compile(
    r'([A-Za-z_:][A-Za-z0-9_:.\-]*)\s*(?:=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s"\'>]+)))?',
)
CSS_DECL_PATTERN = re.compile(r'([A-Za-z\-]+)\s*:\s*([^;]+?)(?:;|$)')


def _extract_attributes(attr_string):
    """Parse an HTML tag's attribute string into [(name_lower, value)] pairs.

    Bare attributes (`controls`, `default`) yield (name, "").
    """
    pairs = []
    for match in HTML_ATTR_PATTERN.finditer(attr_string):
        name = match.group(1)
        value = match.group(2) or match.group(3) or match.group(4) or ""
        pairs.append((name.lower(), value))
    return pairs


def _classify_url_scheme(url):
    """Return the lowercased scheme, or '' for relative URLs."""
    url = (url or "").strip()
    if not url:
        return ""
    if ":" not in url:
        return ""
    # Schemes are letters / digits / +-. up to the first colon.
    scheme = url.split(":", 1)[0].lower()
    # Sanity check: schemes are ASCII alphanumerics + + - .
    if not re.fullmatch(r'[a-z][a-z0-9+\-.]*', scheme):
        return ""
    return scheme


def validate_html_content(html, ref, field_name):
    """Validate an HTML block against LC-JSON's HTML safety profile (TD-130).

    Returns (errors, warnings). See HTML_SAFETY.md §8 for the severity policy.
    """
    errors = []
    warnings = []

    if not html or not isinstance(html, str):
        return errors, warnings

    # Track open tags so we can recognise things like <a target="_blank">
    # without rel attributes — that's a warning per §6.1, normalised by the
    # consumer at render time. The full HTML5 parsing model isn't needed; we
    # only need to inspect open tags one-by-one.
    for match in HTML_OPEN_TAG_PATTERN.finditer(html):
        tag = match.group(1).lower()
        attrs_string = match.group(2) or ""
        attrs = _extract_attributes(attrs_string)

        # ----- Tag classification -----
        if tag in HTML_FORBIDDEN_TAGS:
            errors.append(
                f"{ref}: {field_name} contains forbidden element <{tag}> "
                f"(HTML_SAFETY.md §2.4). Consumer MUST reject the document."
            )
            # Don't bother checking attributes on a forbidden element.
            continue

        if tag not in HTML_ALLOWED_TAGS:
            warnings.append(
                f"{ref}: {field_name} contains unknown element <{tag}>. "
                f"Consumers will strip the tag and preserve its inner text "
                f"(HTML_SAFETY.md §6.2)."
            )
            # Still scan attrs for event handlers / unsafe URLs — XSS doesn't
            # care that the carrying element is unknown.

        # ----- Attribute classification -----
        allowed_for_tag = HTML_UNIVERSAL_ATTRS | HTML_PER_TAG_ATTRS.get(tag, set())

        for attr_name, attr_value in attrs:
            # Event handlers (§3.5) — ERROR.
            if attr_name.startswith("on"):
                errors.append(
                    f"{ref}: {field_name} contains event-handler attribute "
                    f"'{attr_name}' on <{tag}> (HTML_SAFETY.md §3.5). "
                    f"Consumer MUST reject the document."
                )
                continue

            # Universal forbidden form-related attributes
            if attr_name in {"srcdoc", "formaction", "formenctype",
                             "formmethod", "formnovalidate", "formtarget"}:
                errors.append(
                    f"{ref}: {field_name} contains forbidden attribute "
                    f"'{attr_name}' on <{tag}> (HTML_SAFETY.md §3.5)."
                )
                continue

            if tag in HTML_ALLOWED_TAGS and attr_name not in allowed_for_tag:
                warnings.append(
                    f"{ref}: {field_name} attribute '{attr_name}' on <{tag}> "
                    f"is not in the allowlist (HTML_SAFETY.md §3). Consumers "
                    f"will strip it."
                )
                # Continue scanning; even unknown attributes can carry unsafe URLs
                # if they happen to be URL-shaped, but the consumer strips them.
                continue

            # ----- URL-bearing attribute scheme checks (§4) -----
            url_attrs_for_tag = HTML_URL_ATTRS.get(tag, ())
            if attr_name in url_attrs_for_tag and attr_value:
                scheme = _classify_url_scheme(attr_value)
                if scheme in {"javascript", "vbscript"}:
                    errors.append(
                        f"{ref}: {field_name} contains <{tag} {attr_name}=\"{attr_value[:60]}\"> "
                        f"with scheme '{scheme}:' (HTML_SAFETY.md §4.2). "
                        f"Consumer MUST reject the document."
                    )
                elif scheme == "data":
                    warnings.append(
                        f"{ref}: {field_name} contains <{tag} {attr_name}=...> "
                        f"with a data: URL. Forbidden per HTML_SAFETY.md §4.2; "
                        f"consumers will strip on render."
                    )
                elif scheme in HTML_FORBIDDEN_URL_SCHEMES:
                    warnings.append(
                        f"{ref}: {field_name} contains <{tag} {attr_name}=...> "
                        f"with forbidden scheme '{scheme}:' (HTML_SAFETY.md §4.2). "
                        f"Consumers will strip on render."
                    )
                elif scheme == "tel":
                    warnings.append(
                        f"{ref}: {field_name} contains a tel: link. Permitted "
                        f"per HTML_SAFETY.md §7, but consumer policy varies "
                        f"by audience — some consumers (Lesson Commons Learn "
                        f"is one example) gate tel: links via a config flag "
                        f"and default to off for school-age audiences."
                    )
                elif scheme and scheme not in HTML_ALLOWED_LINK_SCHEMES:
                    warnings.append(
                        f"{ref}: {field_name} contains <{tag} {attr_name}=...> "
                        f"with non-allowlisted scheme '{scheme}:' "
                        f"(HTML_SAFETY.md §4.1). Consumers will strip on render."
                    )
                # Empty/relative URLs are fine.

            # ----- Inline style allowlist (§3.4) -----
            if attr_name == "style" and attr_value:
                for css_match in CSS_DECL_PATTERN.finditer(attr_value):
                    prop = css_match.group(1).strip().lower()
                    val = css_match.group(2).strip()
                    if prop not in HTML_ALLOWED_CSS_PROPERTIES:
                        warnings.append(
                            f"{ref}: {field_name} <{tag} style=...> contains "
                            f"CSS property '{prop}' outside the allowlist "
                            f"(HTML_SAFETY.md §3.4). Consumers will strip the "
                            f"property and preserve the others."
                        )
                    # Reject obvious JS-in-CSS tricks at WARN level — no consumer
                    # should be running these but we surface them.
                    val_lower = val.lower()
                    if "expression(" in val_lower or "javascript:" in val_lower:
                        errors.append(
                            f"{ref}: {field_name} <{tag} style=...> CSS value "
                            f"for '{prop}' contains a JS-injection pattern "
                            f"(HTML_SAFETY.md §3.4). Consumer MUST reject."
                        )

        # ----- Per-tag domain rules -----
        attr_dict = {n: v for n, v in attrs}

        if tag == "a" and attr_dict.get("target") == "_blank":
            rel = attr_dict.get("rel", "")
            rel_tokens = set(rel.lower().split())
            if not ({"noopener", "noreferrer"} & rel_tokens):
                warnings.append(
                    f"{ref}: {field_name} <a target=\"_blank\"> without "
                    f"rel=\"noopener noreferrer\" (HTML_SAFETY.md §6.1). "
                    f"Producers SHOULD emit; consumers MUST normalize."
                )

        if tag == "img" and "alt" not in attr_dict:
            warnings.append(
                f"{ref}: {field_name} <img> missing required 'alt' attribute "
                f"(HTML_SAFETY.md §3.3). Empty alt=\"\" is permitted for "
                f"decorative images."
            )

        if tag in {"video", "audio"}:
            if "autoplay" in attr_dict:
                warnings.append(
                    f"{ref}: {field_name} <{tag}> uses 'autoplay' which "
                    f"producers MUST NOT emit (HTML_SAFETY.md §7). Consumers "
                    f"SHOULD ignore."
                )
            if "loop" in attr_dict:
                warnings.append(
                    f"{ref}: {field_name} <{tag}> uses 'loop' which "
                    f"producers MUST NOT emit (HTML_SAFETY.md §7)."
                )

    # Accessibility post-pass: each <video> block SHOULD carry a
    # <track kind="captions"> or <track kind="subtitles"> element when the
    # video contains speech (ACCESSIBILITY.md §3.1 / WCAG 1.2.2). The rc.1
    # validator emits this as a WARN; the --accessibility flag in 1.0 final
    # (TD-138 deepenings) will promote it to ERROR for tooling that wants to
    # fail-build on the accessibility-profile claim.
    for video_match in re.finditer(
        r'<\s*video\b[^>]*>(.*?)<\s*/\s*video\s*>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        inner = video_match.group(1)
        # Look for <track kind="captions"|"subtitles"> inside the block.
        has_caption_track = False
        for track_match in re.finditer(r'<\s*track\b([^>]*)>', inner, re.IGNORECASE):
            track_attrs = {n: v for n, v in _extract_attributes(track_match.group(1))}
            kind = (track_attrs.get('kind') or '').lower()
            if kind in {'captions', 'subtitles'}:
                has_caption_track = True
                break
        if not has_caption_track:
            warnings.append(
                f"{ref}: {field_name} contains a <video> block with no "
                f"<track kind=\"captions\"> or <track kind=\"subtitles\"> element "
                f"(ACCESSIBILITY.md §3.1 / WCAG 1.2.2). Prerecorded instructional "
                f"video with speech MUST carry captions when claiming Accessibility "
                f"Profile conformance (NORMATIVE §12.2)."
            )

    return errors, warnings


def normalize_item_type(raw_type):
    """Normalize item type strings to the import/export model (lowercase)."""
    if not raw_type:
        return ""
    value = str(raw_type).strip().lower()
    mapping = {
        "contentitem": "content",
        "exerciseitem": "exercise",
        "quizitem": "quiz",
        "contentsequence": "contentsequence",
        "contentsequenceitem": "contentsequence",
        "signpost": "signpost",
        "signpostitem": "signpost",
    }
    return mapping.get(value, value)


def load_course(course_path):
    """Load and parse course.json."""
    try:
        with open(course_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}"
    except Exception as e:
        return None, f"Error loading file: {e}"


# ---------------------------------------------------------------------------
# FF-101 Option D shape dispatch
# ---------------------------------------------------------------------------

def _canonicalise_doc_type(value):
    """Strip separators and lowercase for case-insensitive documentType compare.
    Matches the .NET dispatcher's tolerance — accepts "Course", "COURSE",
    "questionSet", "Question-Set", "question_set", etc."""
    if not isinstance(value, str):
        return ""
    return ''.join(c.lower() for c in value if c not in '-_ \t\n')


_QUESTION_TYPES = set(_QUESTION_TYPE_SCHEMA.keys())
_ITEM_TYPES = {"content", "exercise", "quiz", "contentsequence", "signpost"}


def dispatch_document_shape(doc):
    """Inspect the document and return (shape, payload).

    Document shapes (importable by .NET dispatcher):
        'option-d-course'        — Option D root with documentType:"course"
        'option-d-question-set'  — Option D root with documentType:"questionSet"
        'legacy-wrapped'         — {"course": {...}} envelope (pre-FF-101)
        'legacy-bare'            — {"units": [...]} at root (pre-FF-101)

    Fragment shapes (documentation-only; not importable as standalone files
    but valid against their per-type schema — TD-109 widens the validator
    so the spec examples 01-16 + minimal fragments validate cleanly):
        'fragment-question'      — single question with `type` discriminator
        'fragment-item'          — single lesson item with `type` discriminator
        'fragment-unit'          — single unit (no documentType, has lessons[])
        'fragment-lesson'        — single lesson (no documentType, has items[])

        'unknown'                — nothing matched
    """
    if not isinstance(doc, dict):
        return 'unknown', None

    # Option D path
    raw_doc_type = doc.get('documentType')
    if isinstance(raw_doc_type, str) and raw_doc_type:
        canonical = _canonicalise_doc_type(raw_doc_type)
        if canonical == 'course':
            return 'option-d-course', doc
        if canonical == 'questionset':
            return 'option-d-question-set', doc
        return 'unknown', None

    # Fragment dispatch — fragment files have a `type` discriminator at root.
    raw_type = doc.get('type')
    if isinstance(raw_type, str):
        if raw_type in _QUESTION_TYPES:
            return 'fragment-question', doc
        if raw_type in _ITEM_TYPES:
            return 'fragment-item', doc

    # Legacy wrapped: {"course": {...}}
    if isinstance(doc.get('course'), dict):
        return 'legacy-wrapped', doc['course']

    # Fragment unit/lesson dispatch — no documentType, no `type` discriminator,
    # but has the structural arrays of a unit or lesson. Order matters:
    # check unit (lessons[]) before lesson (items[]) before legacy-bare (units[]).
    if 'lessons' in doc and 'units' not in doc:
        return 'fragment-unit', doc
    if 'items' in doc and 'lessons' not in doc and 'units' not in doc:
        return 'fragment-lesson', doc

    # Legacy bare: {"units": [...]}
    if 'units' in doc:
        return 'legacy-bare', doc

    return 'unknown', None


def check_spec_version(doc):
    """FF-101 forward-compat guard. Returns (errors, warnings).

    Accepts any 1.x specVersion, rejects 2.x+ cleanly. Missing specVersion
    is tolerated (Option D documents should declare it, but legacy paths
    won't have it).
    """
    errors = []
    warnings = []
    spec_version = doc.get('specVersion')
    if spec_version is None:
        return errors, warnings
    if not isinstance(spec_version, str):
        errors.append(f"specVersion must be a string (got {type(spec_version).__name__})")
        return errors, warnings
    if not spec_version.startswith('1.'):
        errors.append(
            f"Unsupported specVersion '{spec_version}'. This validator accepts 1.x documents only. "
            f"Upgrade your tooling to read 2.x+ documents."
        )
    return errors, warnings


def validate_question_set_flat(doc, verbose=False):
    """Validate an Option D question-set document.

    Flat artifact: required fields are documentType, specVersion, title,
    questions[]. Each question is validated using the same per-question
    rules as the course path. No units/lessons/items in this shape.
    """
    all_errors = []
    all_warnings = []

    # PRIMARY PASS — JSON Schema validation against question-set.schema.json.
    # Per-question type-specific validation runs as a secondary jsonschema
    # pass below.
    all_errors.extend(_validate_against_schema(doc, "question-set.schema.json", "questionSet"))

    questions = doc.get('questions') or []
    if not isinstance(questions, list):
        # Schema would have caught this, but the rest of this function assumes
        # a list. Fall back to empty.
        questions = []

    # Per-question type-specific schema validation.
    all_errors.extend(_validate_questions_per_type(questions, "questionSet"))

    # specVersion forward-compat (rejects 2.x cleanly with a hard error;
    # the schema's pattern catches 0.x but not >=2.x).
    sv_errors, sv_warnings = check_spec_version(doc)
    all_errors.extend(sv_errors)
    all_warnings.extend(sv_warnings)

    # supportLanguage WARN — should be a 2-letter ISO 639-1 code (or omitted).
    # Mirrors the course-level check in validate_course_level so the QuestionSet
    # path doesn't silently accept malformed locale codes.
    support_lang = doc.get('supportLanguage')
    if support_lang is not None:
        if not isinstance(support_lang, str) or len(support_lang) != 2 or not support_lang.isalpha():
            all_warnings.append(
                f"Question Set: 'supportLanguage' should be a 2-letter ISO 639-1 code: '{support_lang}'"
            )

    # Domain-rule pass: per-question domain checks (HTML allowlist,
    # gap-marker counts, ST chunk numbering, etc.).
    qs_ref = f"Question Set ({doc.get('title', 'Untitled')})"
    for q_index, question in enumerate(questions):
        errors, warnings = validate_question(question, qs_ref, q_index, verbose)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    # Print summary
    print(f"\nValidation complete:")
    print(f"  Artifact: Question Set")
    print(f"  Title: {doc.get('title', 'Untitled')}")
    print(f"  documentType: {doc.get('documentType')}")
    print(f"  specVersion: {doc.get('specVersion')}")
    if doc.get('sourceQuestionSetId'):
        print(f"  sourceQuestionSetId: {doc.get('sourceQuestionSetId')}")
    print(f"  Questions: {len(questions)}")
    print(f"  Errors: {len(all_errors)}")
    print(f"  Warnings: {len(all_warnings)}")
    print()

    if all_errors:
        print("ERRORS:")
        for error in all_errors:
            print(f"  [ERROR] {error}")
        print()

    if all_warnings:
        print("WARNINGS:")
        for warning in all_warnings:
            print(f"  [WARN] {warning}")
        print()

    if not all_errors and not all_warnings:
        print("All checks passed!")
        return True
    elif not all_errors:
        print("Validation passed with warnings.")
        return True
    else:
        print("Validation FAILED with errors.")
        return False


def is_valid_uuid(value):
    """Check if a string is a valid UUID v4."""
    if not isinstance(value, str):
        return False
    return UUID_PATTERN.match(value) is not None


def validate_sequence_order(items, parent_ref, entity_label="item"):
    """Validate sequence properties within a list of sibling entities.

    Accepts both 0-based (0,1,2...) and 1-based (1,2,3...) numbering.
    Warns on gaps, duplicates, or mismatches with array position.
    NOTE: Import uses array position, not sequence values — these are advisory only.
    """
    warnings = []

    sequences = [item.get('sequence') for item in items if 'sequence' in item]
    if not sequences:
        return warnings  # No sequence properties to validate

    # Check for duplicates
    seen = {}
    for idx, item in enumerate(items):
        seq = item.get('sequence')
        if seq is None:
            continue
        if seq in seen:
            prev_title = items[seen[seq]].get('title', 'Untitled')
            curr_title = item.get('title', 'Untitled')
            warnings.append(
                f"{parent_ref}: Duplicate sequence {seq} on {entity_label}s "
                f"[{seen[seq]}] '{prev_title}' and [{idx}] '{curr_title}' "
                f"(import uses array position, not sequence values)"
            )
        else:
            seen[seq] = idx

    # Check if sequences match array position (0-based or 1-based)
    is_zero_based = all(
        items[i].get('sequence') == i
        for i in range(len(items))
        if 'sequence' in items[i]
    )
    is_one_based = all(
        items[i].get('sequence') == i + 1
        for i in range(len(items))
        if 'sequence' in items[i]
    )

    if not is_zero_based and not is_one_based and len(sequences) > 1:
        seq_list = [items[i].get('sequence', '?') for i in range(min(6, len(items)))]
        suffix = "..." if len(items) > 6 else ""
        warnings.append(
            f"{parent_ref}: {entity_label.capitalize()} sequence values {seq_list}{suffix} "
            f"don't match array positions — import will use array order instead"
        )

    return warnings


def validate_unit(unit, unit_index, verbose=False):
    """Validate a single unit structure."""
    errors = []
    warnings = []

    unit_ref = f"Unit {unit_index} ({unit.get('title', 'Untitled')})"

    # Check required properties
    # NOTE: 'id' property removed in v1.9.0 - system uses only globalId (GUID)
    if 'globalId' not in unit:
        errors.append(f"{unit_ref}: Missing 'globalId' property (REQUIRED)")
    elif not is_valid_uuid(unit['globalId']):
        warnings.append(f"{unit_ref}: 'globalId' is not a valid UUID")

    if 'title' not in unit:
        errors.append(f"{unit_ref}: Missing 'title' property")

    if 'sequence' not in unit:
        warnings.append(f"{unit_ref}: Missing 'sequence' property")

    if 'lessons' not in unit:
        errors.append(f"{unit_ref}: Missing 'lessons' array")
    elif not isinstance(unit['lessons'], list):
        errors.append(f"{unit_ref}: 'lessons' must be an array")
    else:
        # Validate lesson sequence order within this unit
        warnings.extend(validate_sequence_order(unit['lessons'], unit_ref, "lesson"))

        # Validate each lesson
        for lesson_index, lesson in enumerate(unit['lessons']):
            lesson_errors, lesson_warnings = validate_lesson(lesson, unit_ref, lesson_index, verbose)
            errors.extend(lesson_errors)
            warnings.extend(lesson_warnings)

    return errors, warnings


def validate_lesson(lesson, unit_ref, lesson_index, verbose=False):
    """Validate a single lesson structure."""
    errors = []
    warnings = []

    lesson_ref = f"{unit_ref} > Lesson {lesson_index} ({lesson.get('title', 'Untitled')})"

    # Check required properties
    # NOTE: 'id' property removed in v1.9.0 - system uses only globalId (GUID)
    if 'globalId' not in lesson:
        errors.append(f"{lesson_ref}: Missing 'globalId' property (REQUIRED)")
    elif not is_valid_uuid(lesson['globalId']):
        warnings.append(f"{lesson_ref}: 'globalId' is not a valid UUID")

    if 'title' not in lesson:
        errors.append(f"{lesson_ref}: Missing 'title' property")

    if 'items' not in lesson:
        warnings.append(f"{lesson_ref}: Missing 'items' array (empty lesson)")
    elif not isinstance(lesson['items'], list):
        errors.append(f"{lesson_ref}: 'items' must be an array")
    else:
        # Validate item sequence order within this lesson
        warnings.extend(validate_sequence_order(lesson['items'], lesson_ref, "item"))

        # Validate each item
        for item_index, item in enumerate(lesson['items']):
            item_errors, item_warnings = validate_item(
                item,
                lesson_ref,
                item_index,
                lesson['items'],
                verbose
            )
            errors.extend(item_errors)
            warnings.extend(item_warnings)

    return errors, warnings


def validate_item(item, lesson_ref, item_index, lesson_items, verbose=False):
    """Validate a single item (ContentItem or ExerciseItem)."""
    errors = []
    warnings = []

    item_type = item.get('type', 'Unknown')
    normalized_type = normalize_item_type(item_type)
    item_ref = f"{lesson_ref} > Item {item_index} ({item_type}: {item.get('title', 'Untitled')})"

    if item_type != normalized_type and any(ch.isupper() for ch in str(item_type)):
        warnings.append(f"{item_ref}: Uses deprecated PascalCase type '{item_type}' (should be '{normalized_type}')")

    # Check required properties
    if 'type' not in item:
        errors.append(f"{item_ref}: Missing 'type' property")

    if 'globalId' not in item:
        errors.append(f"{item_ref}: Missing 'globalId' property (REQUIRED for items)")
    elif not is_valid_uuid(item['globalId']):
        warnings.append(f"{item_ref}: 'globalId' is not a valid UUID")

    if 'title' not in item:
        warnings.append(f"{item_ref}: Missing 'title' property")

    # Validate based on item type
    if normalized_type == 'content':
        if 'html' not in item:
            errors.append(f"{item_ref}: Content item missing 'html' property")
        if 'body' in item:
            warnings.append(f"{item_ref}: Content item uses deprecated 'body' property (should be 'html')")
        # Check HTML whitelist + anchor schemes (Tier 1 link support).
        html_errors, html_warnings = validate_html_content(
            item.get('html', ''), item_ref, "'html'")
        errors.extend(html_errors)
        warnings.extend(html_warnings)

    elif normalized_type in ['exercise', 'quiz']:
        # Check for correct property name (camelCase 'instructions')
        if 'Instructions' in item:
            warnings.append(f"{item_ref}: Exercise item uses deprecated PascalCase 'Instructions' (should be camelCase 'instructions')")
        if 'instructions' not in item:
            errors.append(f"{item_ref}: Exercise item missing 'instructions' property")

        if 'questions' not in item:
            errors.append(f"{item_ref}: Exercise item missing 'questions' array")
        elif not isinstance(item['questions'], list):
            errors.append(f"{item_ref}: 'questions' must be an array (not nested in 'set' object)")
        else:
            # Check for old nested structure
            if len(item['questions']) > 0 and isinstance(item['questions'][0], dict):
                if 'set' in item['questions'][0]:
                    errors.append(f"{item_ref}: Questions nested in 'set' object (should be direct array)")

            # TD-122: item.points is "weighted points" — an intentional
            # override of the question-points sum (e.g. weight a 3-question
            # exercise to 10 points regardless of per-question values). The
            # sum-mismatch check has been lifted to a separate walker that
            # emits an informational [NOTE], not a [WARN] — see
            # _collect_weighted_points_notes().

            # Validate each question
            for question_index, question in enumerate(item['questions']):
                question_errors, question_warnings = validate_question(question, item_ref, question_index, verbose)
                errors.extend(question_errors)
                warnings.extend(question_warnings)

    elif normalized_type == 'contentsequence':
        content_item_id = item.get('contentItemId')
        related_item_ids = item.get('relatedItemIds')
        layout = item.get('layout')

        if not content_item_id:
            errors.append(f"{item_ref}: ContentSequence item missing 'contentItemId'")
        elif not is_valid_uuid(content_item_id):
            warnings.append(f"{item_ref}: 'contentItemId' is not a valid UUID")

        if related_item_ids is None:
            errors.append(f"{item_ref}: ContentSequence item missing 'relatedItemIds'")
        elif not isinstance(related_item_ids, list) or not related_item_ids:
            errors.append(f"{item_ref}: 'relatedItemIds' must be a non-empty array")
        else:
            for related_id in related_item_ids:
                if not is_valid_uuid(related_id):
                    warnings.append(f"{item_ref}: Related item id '{related_id}' is not a valid UUID")

        if layout is None:
            warnings.append(f"{item_ref}: ContentSequence item missing 'layout' (defaults to Auto)")
        elif layout not in {"Auto", "Split", "Vertical"}:
            warnings.append(f"{item_ref}: 'layout' should be Auto, Split, or Vertical")

        def find_index_by_id(target_id):
            for idx, candidate in enumerate(lesson_items):
                if candidate.get('globalId') == target_id:
                    return idx, candidate
            return None, None

        if content_item_id:
            content_index, content_item = find_index_by_id(content_item_id)
            if content_index is None:
                errors.append(f"{item_ref}: contentItemId '{content_item_id}' not found in lesson")
            else:
                if content_index > item_index:
                    errors.append(f"{item_ref}: contentItemId must be declared before ContentSequence item")
                content_type = normalize_item_type(content_item.get('type'))
                if content_type != 'content':
                    errors.append(f"{item_ref}: contentItemId references non-content type '{content_item.get('type')}'")

        if isinstance(related_item_ids, list):
            for related_id in related_item_ids:
                related_index, related_item = find_index_by_id(related_id)
                if related_index is None:
                    errors.append(f"{item_ref}: relatedItemId '{related_id}' not found in lesson")
                    continue
                if related_index > item_index:
                    errors.append(f"{item_ref}: relatedItemId '{related_id}' must be declared before ContentSequence item")
                related_type = normalize_item_type(related_item.get('type'))
                if related_type not in ['exercise', 'quiz']:
                    errors.append(f"{item_ref}: relatedItemId '{related_id}' references non-exercise/quiz type '{related_item.get('type')}'")

    elif normalized_type == 'signpost':
        # Signpost items display intro/summary messages with objectives and stats
        signpost_type = item.get('signpostType')
        scope = item.get('scope')

        if not signpost_type:
            errors.append(f"{item_ref}: Signpost item missing 'signpostType' property")
        elif signpost_type not in ['intro', 'summary']:
            errors.append(f"{item_ref}: 'signpostType' must be 'intro' or 'summary' (got '{signpost_type}')")

        if not scope:
            errors.append(f"{item_ref}: Signpost item missing 'scope' property")
        elif scope not in ['course', 'unit', 'lesson']:
            errors.append(f"{item_ref}: 'scope' must be 'course', 'unit', or 'lesson' (got '{scope}')")

        # Signposts should not have questions
        if 'questions' in item:
            errors.append(f"{item_ref}: Signpost items cannot contain questions")

        # customHtml is optional; validate tags/links if present.
        if item.get('customHtml'):
            html_errors, html_warnings = validate_html_content(
                item['customHtml'], item_ref, "'customHtml'")
            errors.extend(html_errors)
            warnings.extend(html_warnings)

    return errors, warnings


def validate_question(question, item_ref, question_index, verbose=False):
    """Validate a single question."""
    errors = []
    warnings = []

    question_type = question.get('type', 'Unknown')
    question_ref = f"{item_ref} > Q{question_index + 1} ({question_type})"

    # Check for deprecated 'questionType' property
    if 'questionType' in question:
        errors.append(f"{question_ref}: Uses deprecated 'questionType' property (should be 'type')")

    if 'type' not in question:
        errors.append(f"{question_ref}: Missing 'type' property")

    if 'globalId' not in question:
        errors.append(f"{question_ref}: Missing 'globalId' property")
    elif not is_valid_uuid(question['globalId']):
        warnings.append(f"{question_ref}: 'globalId' is not a valid UUID")

    if 'prompt' not in question:
        warnings.append(f"{question_ref}: Missing 'prompt' property")

    if 'points' not in question:
        warnings.append(f"{question_ref}: Missing 'points' property")

    # Domain-rule dispatch — accept both canonical camelCase (TD-108, post-2026-04-27)
    # and the legacy PascalCase form so pre-TD-108 exports keep getting checked.
    qt_lower = (question_type or "").lower()

    # rc.2 domain rule (TD-212): the schema now allows an empty `prompt` (minLength 0),
    # so emptiness must be caught here where it is a genuine error. For the four
    # REAL-CONTENT types the prompt *is* the question, so an empty/whitespace prompt
    # is an authoring error. The eight symbolic types carry their meaning in structured
    # fields — an empty prompt is valid there. The seven reserved types get no rule
    # (deferred to v1.1, when they gain per-type schemas). minLength stays in the JSON
    # Schema; this rule only covers the real-content emptiness the schema can no longer
    # see. See docs/architecture/decisions/2026-05-29_LC-JSON_prompt_field_decision.md.
    REAL_CONTENT_TYPES = {'truefalsequestion', 'multiplechoice', 'shortanswer', 'essay'}
    if qt_lower in REAL_CONTENT_TYPES:
        prompt_val = question.get('prompt')
        if isinstance(prompt_val, str) and prompt_val.strip() == "":
            errors.append(
                f"{question_ref}: '{question_type}' has an empty 'prompt' — "
                f"for this question type the prompt is the question and MUST be non-empty"
            )

    if qt_lower == 'sentencetransformation':
        st_errors, st_warnings = validate_sentence_transformation(question, question_ref, verbose)
        errors.extend(st_errors)
        warnings.extend(st_warnings)

    if qt_lower == 'truefalsequestion':
        tf_errors, tf_warnings = validate_true_false_question(question, question_ref, verbose)
        errors.extend(tf_errors)
        warnings.extend(tf_warnings)

    if qt_lower == 'multigapcloze':
        mgc_errors, mgc_warnings = validate_multi_gap_cloze(question, question_ref, verbose)
        errors.extend(mgc_errors)
        warnings.extend(mgc_warnings)

    if qt_lower == 'placement':
        pl_errors, pl_warnings = validate_placement(question, question_ref, verbose)
        errors.extend(pl_errors)
        warnings.extend(pl_warnings)

    if qt_lower == 'multiplechoice':
        mc_errors, mc_warnings = validate_multiple_choice(question, question_ref, verbose)
        errors.extend(mc_errors)
        warnings.extend(mc_warnings)

    if qt_lower == 'wordbankcloze':
        wbc_errors, wbc_warnings = validate_word_bank_cloze(question, question_ref, verbose)
        errors.extend(wbc_errors)
        warnings.extend(wbc_warnings)

    if qt_lower == 'multiplechoicecloze':
        mcc_errors, mcc_warnings = validate_multiple_choice_cloze(question, question_ref, verbose)
        errors.extend(mcc_errors)
        warnings.extend(mcc_warnings)

    if qt_lower == 'essay':
        es_errors, es_warnings = validate_essay(question, question_ref, verbose)
        errors.extend(es_errors)
        warnings.extend(es_warnings)

    return errors, warnings


def _gap_marker_numbers(passage):
    """Return the list of @@@N marker numbers found in a passage (preserves duplicates).

    Shared by placement, wordBankCloze, multiGapCloze, and multipleChoiceCloze —
    every cloze-family question type uses the same @@@N marker convention.
    """
    if not isinstance(passage, str):
        return []
    return [int(m.group(1)) for m in re.finditer(r"@@@(\d+)", passage)]


def _check_cloze_gap_consistency(passage, dict_keys, question_ref, dict_field_name):
    """Shared gap-count + sequentiality checks for cloze passages.

    Used by wordBankCloze (gapAcceptedAnswers), multiGapCloze (gapAcceptedAnswers),
    and multipleChoiceCloze (gapOptions / correctAnswers). Returns (errors, warnings).

    Rules enforced:
      ERROR: the set of @@@N marker numbers in the passage MUST equal the set of
             integer keys in the answer/option dictionary.
      WARN:  marker numbers SHOULD be sequential starting at 1 (1, 2, 3, …).
    """
    errors = []
    warnings = []

    if not isinstance(passage, str) or not passage:
        return errors, warnings

    marker_numbers = _gap_marker_numbers(passage)
    if not marker_numbers:
        return errors, warnings  # schema's @@@\d+ pattern already catches this

    marker_set = set(marker_numbers)

    # Normalise dict keys to integers (schema enforces ^[0-9]+$ key pattern)
    try:
        key_set = {int(k) for k in (dict_keys or [])}
    except (TypeError, ValueError):
        return errors, warnings  # schema-level error; let it surface elsewhere

    if marker_set != key_set:
        only_in_passage = sorted(marker_set - key_set)
        only_in_dict = sorted(key_set - marker_set)
        detail_parts = []
        if only_in_passage:
            detail_parts.append(
                f"@@@{only_in_passage} marker(s) in passage have no entry in '{dict_field_name}'"
            )
        if only_in_dict:
            detail_parts.append(
                f"'{dict_field_name}' key(s) {only_in_dict} have no @@@N marker in passage"
            )
        errors.append(
            f"{question_ref}: gap-marker / '{dict_field_name}' mismatch — "
            + "; ".join(detail_parts)
            + "."
        )

    # Sequentiality WARN — markers SHOULD be 1, 2, 3, … in some order.
    unique_sorted = sorted(marker_set)
    expected = list(range(1, len(unique_sorted) + 1))
    if unique_sorted != expected:
        warnings.append(
            f"{question_ref}: @@@N marker numbers {unique_sorted} are not "
            f"sequential starting at 1 (expected {expected}); non-sequential "
            f"numbering is permitted but flagged."
        )

    return errors, warnings


def validate_placement(question, question_ref, verbose=False):
    """Domain rules for placement questions (LC-JSON 1.0-rc.2).

    Hard errors:
      - Every placements[].gap MUST reference a @@@N marker present in passage.
      - No duplicate `gap` values within placements[].
    Soft warnings (NOTE-tier):
      - @@@N markers SHOULD be sequential starting at 1 (inherits wordBankCloze convention).
      - Per-placementUnit marker-placement convention violations:
          paragraph: marker should be alone on its paragraph;
          sectionLabel: marker should be at the start of a paragraph followed by a space.
        sentence mode has no positional rule.
    """
    errors = []
    warnings = []

    passage = question.get('passage', '')
    placements = question.get('placements', [])
    placement_unit = question.get('placementUnit', 'sentence')

    if not isinstance(passage, str) or not passage:
        # Schema enforces passage required + minLength; skip domain checks.
        return errors, warnings

    marker_numbers = _gap_marker_numbers(passage)
    marker_set = set(marker_numbers)

    # Hard error: every placements[].gap must reference an @@@N marker in passage.
    if isinstance(placements, list):
        seen_gaps = set()
        for idx, p in enumerate(placements):
            if not isinstance(p, dict):
                continue
            gap = p.get('gap')
            if not isinstance(gap, int):
                continue  # schema-level error
            if gap not in marker_set:
                errors.append(
                    f"{question_ref}: placements[{idx}].gap = {gap} but no @@@{gap} marker is present in passage"
                )
            if gap in seen_gaps:
                errors.append(
                    f"{question_ref}: duplicate gap value {gap} in placements[]"
                )
            seen_gaps.add(gap)

    # Soft warning: @@@N markers SHOULD be sequential starting at 1.
    if marker_numbers:
        unique_sorted = sorted(set(marker_numbers))
        expected = list(range(1, len(unique_sorted) + 1))
        if unique_sorted != expected:
            warnings.append(
                f"{question_ref}: @@@N marker numbers {unique_sorted} are not sequential starting at 1 "
                f"(expected {expected}); non-sequential numbering is permitted but flagged."
            )

    # Soft warning: per-placementUnit marker-placement convention.
    if placement_unit == 'paragraph':
        # Each @@@N should be the entire content of its paragraph (surrounded by \n\n
        # or at start/end of passage). Detect markers that appear mid-prose.
        # Split by double-newline and check whether each marker stands alone.
        for m in re.finditer(r"@@@(\d+)", passage):
            start, end = m.span()
            line_before = passage[:start]
            line_after = passage[end:]
            # Find the nearest \n\n boundaries (or start/end).
            prev_break = max(line_before.rfind('\n\n'), -2)
            next_break = line_after.find('\n\n')
            seg_start = prev_break + 2 if prev_break >= 0 else 0
            seg_end = end + next_break if next_break >= 0 else len(passage)
            segment = passage[seg_start:seg_end].strip()
            if segment != m.group(0):
                warnings.append(
                    f"{question_ref}: placementUnit='paragraph' but {m.group(0)} is not alone "
                    f"on its paragraph (expected the marker to stand alone between blank lines)."
                )
    elif placement_unit == 'sectionLabel':
        # Each @@@N should be at the start of a paragraph (immediately preceded by
        # \n\n or start-of-passage; immediately followed by a space).
        for m in re.finditer(r"@@@(\d+)", passage):
            start, end = m.span()
            preceded_ok = start == 0 or passage[max(0, start - 2):start] == '\n\n'
            followed_ok = end < len(passage) and passage[end] == ' '
            if not (preceded_ok and followed_ok):
                warnings.append(
                    f"{question_ref}: placementUnit='sectionLabel' but {m.group(0)} is not at the "
                    f"start of a paragraph followed by a space (expected '\\n\\n@@@N <section content>' "
                    f"or '@@@N <section content>' at start of passage)."
                )

    return errors, warnings


def validate_multi_gap_cloze(question, question_ref, verbose=False):
    """Validate MultiGapCloze-specific properties.

    Key constraint: accepted answers must not contain commas (,) or colons (:).
    Some consuming applications (Lesson Commons Learn is one) encode multi-gap
    student submissions as "gap:answer,gap:answer" for transmission to the
    scoring engine; commas or colons inside an answer can be silently truncated
    during parsing, so a student typing the exact accepted answer would be
    marked wrong. MultiGapCloze is a vocabulary/grammar exercise — single words
    or short phrases only. Apostrophes (don't) and hyphens (well-known) are
    fine; other punctuation is discouraged.
    """
    errors = []
    warnings = []

    gap_accepted = question.get('gapAcceptedAnswers', {})
    if not isinstance(gap_accepted, dict):
        errors.append(f"{question_ref}: 'gapAcceptedAnswers' must be a dictionary")
        return errors, warnings

    # Gap-count + sequentiality (KG-1, KG-2): passage @@@N marker set MUST
    # match gapAcceptedAnswers key set; markers SHOULD be sequential from 1.
    consistency_errors, consistency_warnings = _check_cloze_gap_consistency(
        question.get('passage', ''), gap_accepted.keys(), question_ref, 'gapAcceptedAnswers'
    )
    errors.extend(consistency_errors)
    warnings.extend(consistency_warnings)

    # Allowed punctuation in answers: apostrophes (straight + curly) and hyphens
    # (ASCII hyphen, non-breaking hyphen, en/em dashes).
    allowed_punct = {"'", "\u2018", "\u2019", "-", "\u2010", "\u2011", "\u2013", "\u2014"}

    for gap_key, answers in gap_accepted.items():
        if not isinstance(answers, list):
            continue
        for answer in answers:
            if not isinstance(answer, str):
                continue

            # Hard error: commas or colons break the submission wire format
            if ',' in answer or ':' in answer:
                errors.append(
                    f"{question_ref}: Gap {gap_key} accepted answer '{answer}' contains "
                    f"a comma or colon. These characters break the scoring engine's "
                    f"submission parser and will cause students to be marked wrong even "
                    f"when they type the correct answer."
                )
                continue

            # Warning: other punctuation is discouraged
            offending = [
                ch for ch in answer
                if not ch.isalnum() and not ch.isspace() and ch not in allowed_punct
            ]
            if offending:
                warnings.append(
                    f"{question_ref}: Gap {gap_key} accepted answer '{answer}' contains "
                    f"punctuation ({''.join(sorted(set(offending)))}). MultiGapCloze is "
                    f"typically a vocabulary/grammar exercise — consider single words or "
                    f"short phrases. Only apostrophes and hyphens are recommended."
                )

    return errors, warnings


def validate_word_bank_cloze(question, question_ref, verbose=False):
    """Domain rules for wordBankCloze (KG-1, KG-2).

    Hard errors:
      - passage @@@N marker set MUST equal gapAcceptedAnswers key set.
    Soft warnings:
      - marker numbers SHOULD be sequential starting at 1.
    """
    errors = []
    warnings = []

    gap_accepted = question.get('gapAcceptedAnswers', {})
    if not isinstance(gap_accepted, dict):
        # Schema already catches this; bail out to avoid noise.
        return errors, warnings

    consistency_errors, consistency_warnings = _check_cloze_gap_consistency(
        question.get('passage', ''), gap_accepted.keys(), question_ref, 'gapAcceptedAnswers'
    )
    errors.extend(consistency_errors)
    warnings.extend(consistency_warnings)

    return errors, warnings


def validate_multiple_choice_cloze(question, question_ref, verbose=False):
    """Domain rules for multipleChoiceCloze (KG-1, KG-2, KG-5).

    Hard errors:
      - passage @@@N marker set MUST equal gapOptions key set.
      - passage @@@N marker set MUST equal correctAnswers key set.
      - each correctAnswers[N] MUST be a valid index into gapOptions[N].
    Soft warnings:
      - marker numbers SHOULD be sequential starting at 1.
    """
    errors = []
    warnings = []

    gap_options = question.get('gapOptions', {})
    correct_answers = question.get('correctAnswers', {})

    if not isinstance(gap_options, dict) or not isinstance(correct_answers, dict):
        return errors, warnings  # schema already catches type errors

    # Gap-count consistency against the passage (KG-1) — check against gapOptions;
    # also fire a separate ERROR if correctAnswers keys diverge from gapOptions.
    consistency_errors, consistency_warnings = _check_cloze_gap_consistency(
        question.get('passage', ''), gap_options.keys(), question_ref, 'gapOptions'
    )
    errors.extend(consistency_errors)
    warnings.extend(consistency_warnings)

    try:
        gap_option_keys = {int(k) for k in gap_options.keys()}
        correct_keys = {int(k) for k in correct_answers.keys()}
    except (TypeError, ValueError):
        return errors, warnings

    if gap_option_keys != correct_keys:
        only_in_options = sorted(gap_option_keys - correct_keys)
        only_in_correct = sorted(correct_keys - gap_option_keys)
        detail_parts = []
        if only_in_options:
            detail_parts.append(
                f"'gapOptions' has gap(s) {only_in_options} with no entry in 'correctAnswers'"
            )
        if only_in_correct:
            detail_parts.append(
                f"'correctAnswers' has gap(s) {only_in_correct} with no entry in 'gapOptions'"
            )
        errors.append(
            f"{question_ref}: 'gapOptions' / 'correctAnswers' key mismatch — "
            + "; ".join(detail_parts)
            + "."
        )

    # Index-bounds check (KG-5): each correctAnswers[N] MUST be < len(gapOptions[N]).
    for gap_key, idx in correct_answers.items():
        if not isinstance(idx, int):
            continue  # schema already enforces integer type
        options = gap_options.get(gap_key)
        if not isinstance(options, list):
            continue
        if idx < 0 or idx >= len(options):
            errors.append(
                f"{question_ref}: correctAnswers[{gap_key}] = {idx} is out of bounds for "
                f"gapOptions[{gap_key}] (length {len(options)}; valid indices 0..{len(options) - 1})."
            )

    return errors, warnings


def validate_multiple_choice(question, question_ref, verbose=False):
    """Domain rules for multipleChoice (KG-3, KG-4).

    Hard errors:
      - 'optionsAndPoints' MUST contain an entry for every value in 'options'.
      - 'optionsAndPoints' MUST have at least one entry with a positive value
        (otherwise no answer can earn credit — an MCQ with no correct answer).
    """
    errors = []
    warnings = []

    options = question.get('options')
    options_and_points = question.get('optionsAndPoints')

    if not isinstance(options, list) or not isinstance(options_and_points, dict):
        return errors, warnings  # schema-level errors surface elsewhere

    # KG-4: every option MUST have a corresponding optionsAndPoints entry.
    missing = [o for o in options if o not in options_and_points]
    if missing:
        errors.append(
            f"{question_ref}: 'optionsAndPoints' is missing entries for option(s) {missing} "
            f"declared in 'options'. Every option MUST appear as a key in 'optionsAndPoints' "
            f"so the consumer knows how to score it (0 for incorrect, > 0 for correct)."
        )

    # Extra entries in optionsAndPoints that don't correspond to any option —
    # flag as WARN (less harmful than missing entries, but still suspect).
    extras = [k for k in options_and_points.keys() if k not in options]
    if extras:
        warnings.append(
            f"{question_ref}: 'optionsAndPoints' has entries {extras} that don't match any "
            f"value in 'options'. Authors typically keep the two in sync; orphan entries are ignored."
        )

    # KG-3: at least one positive-points entry (otherwise no answer is correct).
    positive_count = sum(
        1 for k in options if isinstance(options_and_points.get(k), (int, float)) and options_and_points[k] > 0
    )
    if positive_count == 0:
        errors.append(
            f"{question_ref}: 'optionsAndPoints' has no option with points > 0. An MCQ MUST "
            f"have at least one correct answer; otherwise no learner submission can earn credit."
        )

    return errors, warnings


def validate_essay(question, question_ref, verbose=False):
    """Domain rules for essay (KG-bonus: maxWords >= minWords when both > 0)."""
    errors = []
    warnings = []

    min_words = question.get('minWords', 0)
    max_words = question.get('maxWords', 0)
    if (
        isinstance(min_words, int)
        and isinstance(max_words, int)
        and min_words > 0
        and max_words > 0
        and max_words < min_words
    ):
        warnings.append(
            f"{question_ref}: 'maxWords' ({max_words}) is less than 'minWords' ({min_words}); "
            f"the word-count window is empty and no submission can satisfy both limits."
        )

    return errors, warnings


def validate_sentence_transformation(question, question_ref, verbose=False):
    """Validate SentenceTransformation-specific properties."""
    errors = []
    warnings = []

    # Check for deprecated PascalCase properties
    deprecated_props = {
        'PromptSentence': 'promptSentence',
        'Keyword': 'keyword',
        'TargetSentence': 'targetSentence',
        'AcceptedChunks': 'acceptedChunks',
        'AllOrNothing': 'allOrNothing',
        'ChunkCaseSensitive': 'chunkCaseSensitive',
        'ChunkFeedback': 'chunkFeedback'
    }

    for old_prop, new_prop in deprecated_props.items():
        if old_prop in question:
            warnings.append(f"{question_ref}: Uses deprecated PascalCase '{old_prop}' (should be camelCase '{new_prop}')")

    required_props = ['promptSentence', 'keyword', 'targetSentence', 'acceptedChunks']
    for prop in required_props:
        if prop not in question:
            errors.append(f"{question_ref}: Missing required property '{prop}'")

    # Check allOrNothing property
    if 'allOrNothing' not in question:
        warnings.append(f"{question_ref}: Missing 'allOrNothing' property (defaults to false)")

    # Validate acceptedChunks structure
    if 'acceptedChunks' in question:
        chunks = question['acceptedChunks']
        if not isinstance(chunks, dict):
            errors.append(f"{question_ref}: 'acceptedChunks' must be a dictionary")
        else:
            # Check chunk numbering
            chunk_numbers = sorted([int(k) for k in chunks.keys()])
            if chunk_numbers != list(range(1, len(chunk_numbers) + 1)):
                warnings.append(f"{question_ref}: Chunk numbers should be sequential starting from 1")

            # Check each chunk has answers
            for chunk_num, answers in chunks.items():
                if not isinstance(answers, list):
                    errors.append(f"{question_ref}: Chunk {chunk_num} answers must be a list")
                elif len(answers) == 0:
                    warnings.append(f"{question_ref}: Chunk {chunk_num} has no accepted answers")

    # Check chunkFeedback structure (if present)
    if 'chunkFeedback' in question:
        feedback = question['chunkFeedback']
        if not isinstance(feedback, dict):
            errors.append(f"{question_ref}: 'chunkFeedback' must be a dictionary")

    # Check chunkCaseSensitive structure (if present)
    if 'chunkCaseSensitive' in question:
        case_sensitive = question['chunkCaseSensitive']
        if not isinstance(case_sensitive, dict):
            errors.append(f"{question_ref}: 'chunkCaseSensitive' must be a dictionary")
        else:
            for chunk_num, value in case_sensitive.items():
                if not isinstance(value, bool):
                    warnings.append(f"{question_ref}: chunkCaseSensitive[{chunk_num}] should be boolean")

    # Verify targetSentence contains exactly one @@@ placeholder.
    # SentenceTransformation uses a SINGLE @@@ regardless of acceptedChunks
    # count — chunks are sequential answer pieces typed at that one position,
    # not separate gaps (unlike the cloze types which use @@@N per gap).
    # Multiple @@@ markers are ambiguous (which chunk goes where?) and reject.
    if 'targetSentence' in question:
        marker_count = question['targetSentence'].count('@@@')
        if marker_count == 0:
            warnings.append(
                f"{question_ref}: targetSentence should contain a '@@@' placeholder for the answer"
            )
        elif marker_count > 1:
            errors.append(
                f"{question_ref}: targetSentence contains {marker_count} '@@@' markers — "
                f"SentenceTransformation uses exactly one '@@@' regardless of acceptedChunks count "
                f"(chunks are sequential answer pieces typed at the single position, not separate "
                f"gaps). Multiple markers are ambiguous and will not score."
            )

    # Verify keyword is uppercase
    if 'keyword' in question:
        keyword = question['keyword']
        if keyword != keyword.upper():
            warnings.append(f"{question_ref}: keyword should be uppercase ('{keyword}' -> '{keyword.upper()}')")

    return errors, warnings


def is_booleanish(value):
    """Return True if value is a boolean or a common boolean-like literal."""
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)) and value in (0, 1):
        return True
    if isinstance(value, str):
        lowered = value.strip().lower()
        return lowered in BOOLEANISH_TRUE or lowered in BOOLEANISH_FALSE
    return False


def validate_true_false_question(question, question_ref, verbose=False):
    """Validate TrueFalseQuestion-specific properties."""
    errors = []
    warnings = []

    has_correct_answer = "correctAnswer" in question
    has_options = "options" in question
    has_options_and_points = "optionsAndPoints" in question

    if not has_correct_answer and not has_options_and_points:
        errors.append(f"{question_ref}: Missing 'correctAnswer' (v2) and no legacy 'optionsAndPoints' (v1)")

    if has_correct_answer:
        value = question.get("correctAnswer")
        if not isinstance(value, bool):
            if is_booleanish(value):
                warnings.append(f"{question_ref}: 'correctAnswer' should be a JSON boolean (true/false)")
            else:
                errors.append(f"{question_ref}: 'correctAnswer' must be a boolean")

    if has_options or has_options_and_points:
        warnings.append(f"{question_ref}: Uses deprecated v1 TrueFalse schema ('options'/'optionsAndPoints')")

    if has_options and not isinstance(question.get("options"), list):
        errors.append(f"{question_ref}: 'options' must be an array when present")

    if has_options_and_points:
        options_and_points = question.get("optionsAndPoints")
        if not isinstance(options_and_points, dict):
            errors.append(f"{question_ref}: 'optionsAndPoints' must be a dictionary when present")
        else:
            positive = [k for k, v in options_and_points.items() if isinstance(v, (int, float)) and v > 0]
            if len(positive) == 0:
                warnings.append(f"{question_ref}: 'optionsAndPoints' has no positive points option")
            elif len(positive) > 1:
                warnings.append(f"{question_ref}: 'optionsAndPoints' has multiple positive points options")

    if "displayStyle" in question:
        display_style = question.get("displayStyle")
        if not isinstance(display_style, str):
            warnings.append(f"{question_ref}: 'displayStyle' should be a string when present")
        elif display_style not in TF_DISPLAY_STYLES:
            warnings.append(f"{question_ref}: 'displayStyle' should be one of {sorted(TF_DISPLAY_STYLES)}")

    if "penalizeIncorrect" in question and not isinstance(question.get("penalizeIncorrect"), bool):
        warnings.append(f"{question_ref}: 'penalizeIncorrect' should be a boolean when present")

    if "incorrectPenaltyPercent" in question:
        percent = question.get("incorrectPenaltyPercent")
        if not isinstance(percent, (int, float)):
            warnings.append(f"{question_ref}: 'incorrectPenaltyPercent' should be a number when present")
        elif percent < 0 or percent > 100:
            warnings.append(f"{question_ref}: 'incorrectPenaltyPercent' should be between 0 and 100")

    feedback = question.get("feedback")
    if feedback is None:
        warnings.append(f"{question_ref}: Missing 'feedback' object for TrueFalseQuestion")
    elif not isinstance(feedback, dict):
        errors.append(f"{question_ref}: 'feedback' must be an object")
    else:
        missing_keys = [key for key in ("correct", "incorrect") if key not in feedback]
        if missing_keys:
            warnings.append(f"{question_ref}: feedback missing {', '.join(missing_keys)}")
        non_string = [key for key in ("correct", "incorrect")
                      if key in feedback and not isinstance(feedback.get(key), str)]
        if non_string:
            warnings.append(f"{question_ref}: feedback fields should be strings ({', '.join(non_string)})")
        if "choiceFeedback" in feedback:
            warnings.append(f"{question_ref}: 'feedback.choiceFeedback' is deprecated for TrueFalseQuestion")

    return errors, warnings


def validate_course_level(course, verbose=False):
    """Validate course-level properties (title, sourceCourseId, version)."""
    errors = []
    warnings = []

    # Check title (required)
    if 'title' not in course or not course.get('title'):
        errors.append("Course: Missing 'title' property (REQUIRED)")

    # TD-116 / ADR-018: sourceCourseId is the canonical course-identity
    # field. Course-level globalId was dropped from the wire (auto-
    # generated by consumers; not a portable identifier).
    source_course_id = course.get('sourceCourseId')

    if source_course_id is not None:
        if not is_valid_uuid(source_course_id):
            warnings.append(f"Course: 'sourceCourseId' is not a valid UUID: {source_course_id}")
        if verbose:
            print(f"  sourceCourseId: {source_course_id}")
    else:
        if verbose:
            warnings.append("Course: no 'sourceCourseId' — re-import detection will not be available for this course")

    # Legacy field detection: emit a clear migration warning if pre-1.0
    # field names are present.
    legacy_fields = [f for f in ('authorId', 'authorCourseId') if course.get(f) is not None]
    if legacy_fields:
        warnings.append(
            f"Course: legacy identity field(s) present ({', '.join(legacy_fields)}). "
            f"LC-JSON 1.0 uses 'sourceCourseId' as the canonical course-identity field. "
            f"Migrate by renaming the field; values can be preserved as-is."
        )

    # Check version (optional but recommended when sourceCourseId is present).
    # Pattern accepts an optional pre-release suffix to match the schema and
    # the dual-track versioning scheme (e.g., '0.9.44-Beta'). Schema runs the
    # primary pattern check; this hand-written warning fires only when the
    # jsonschema package is missing.
    if 'version' in course and course['version'] is not None:
        version = course['version']
        version_pattern = re.compile(r'^[0-9]+(\.[0-9]+){0,2}$')
        if not version_pattern.match(version):
            warnings.append(f"Course: 'version' must be numeric, dotted, 1-3 segments (e.g., '1', '1.0', '1.2.3', '4'): {version}")
        if verbose:
            print(f"  version: {version}")

    # Check supportLanguage (optional, must be valid ISO 639-1 if present)
    support_lang = course.get('supportLanguage')
    if support_lang is not None:
        if not isinstance(support_lang, str) or len(support_lang) != 2 or not support_lang.isalpha():
            warnings.append(f"Course: 'supportLanguage' should be a 2-letter ISO 639-1 code: '{support_lang}'")
        elif verbose:
            print(f"  supportLanguage: {support_lang}")

    # Warn if sourceCourseId present without version (or vice versa)
    has_source_course_id = source_course_id is not None
    has_version = course.get('version') is not None
    if has_source_course_id and not has_version:
        warnings.append("Course: 'sourceCourseId' present but no 'version' — consider adding version for tracking")
    if has_version and not has_source_course_id:
        warnings.append("Course: 'version' present but no 'sourceCourseId' — consider adding sourceCourseId for re-import tracking")

    return errors, warnings


_ITEM_TYPE_SCHEMA = {
    "content": "content-item.schema.json",
    "exercise": "exercise-item.schema.json",
    "quiz": "quiz-item.schema.json",
    "contentsequence": "content-sequence-item.schema.json",
    "signpost": "signpost-item.schema.json",
}


def validate_fragment(doc, shape, verbose=False):
    """Validate a single-entity fragment file against the appropriate schema.

    Fragment files (LC.JSON/specification/examples/01-*.json,
    lesson-minimal.json, unit-minimal.json) are documentation fragments —
    single questions, items, units, or lessons without a course/questionSet
    wrapper. They aren't importable as standalone documents, but they ARE
    valid against their per-type schema, so the validator should give a
    clean pass when they're correct.
    """
    all_errors = []
    all_warnings = []
    summary_label = ""

    if shape == 'fragment-question':
        qtype = doc.get('type', 'unknown')
        schema_name = _QUESTION_TYPE_SCHEMA.get(qtype, "question-base.schema.json")
        ref = f"question[{qtype}]"
        all_errors.extend(_validate_against_schema(doc, schema_name, ref))
        # Domain rules: per-question domain checks (HTML, gap markers, etc.).
        q_errors, q_warnings = validate_question(doc, "Fragment", 0, verbose)
        all_errors.extend(q_errors)
        all_warnings.extend(q_warnings)
        summary_label = f"Question fragment ({qtype})"

    elif shape == 'fragment-item':
        itype = normalize_item_type(doc.get('type'))
        schema_name = _ITEM_TYPE_SCHEMA.get(itype)
        ref = f"item[{itype}]"
        if schema_name:
            all_errors.extend(_validate_against_schema(doc, schema_name, ref))
        else:
            all_warnings.append(f"Fragment: unknown item type '{doc.get('type')}'")
        # Per-question schema dispatch for items that hold questions.
        if isinstance(doc.get('questions'), list):
            all_errors.extend(_validate_questions_per_type(doc['questions'], ref))
        # Domain rules: HTML allowlist on content/signpost items, etc.
        if itype == 'content' and doc.get('html'):
            html_errors, html_warnings = validate_html_content(doc['html'], "Fragment", "'html'")
            all_errors.extend(html_errors)
            all_warnings.extend(html_warnings)
        if itype == 'signpost' and doc.get('customHtml'):
            html_errors, html_warnings = validate_html_content(doc['customHtml'], "Fragment", "'customHtml'")
            all_errors.extend(html_errors)
            all_warnings.extend(html_warnings)
        # Domain rules: per-question for exercise/quiz items.
        if itype in ('exercise', 'quiz') and isinstance(doc.get('questions'), list):
            for idx, q in enumerate(doc['questions']):
                q_errors, q_warnings = validate_question(q, "Fragment", idx, verbose)
                all_errors.extend(q_errors)
                all_warnings.extend(q_warnings)
        summary_label = f"Item fragment ({itype})"

    elif shape == 'fragment-unit':
        all_errors.extend(_validate_against_schema(doc, "unit.schema.json", "unit"))
        # Walk lessons → items → questions for per-question-type schema dispatch.
        for l_idx, lesson in enumerate(doc.get('lessons') or []):
            for i_idx, item in enumerate(lesson.get('items') or []):
                if isinstance(item.get('questions'), list):
                    ref = f"unit > lessons > {l_idx} > items > {i_idx}"
                    all_errors.extend(_validate_questions_per_type(item['questions'], ref))
        summary_label = f"Unit fragment ({doc.get('title', 'Untitled')})"

    elif shape == 'fragment-lesson':
        all_errors.extend(_validate_against_schema(doc, "lesson.schema.json", "lesson"))
        for i_idx, item in enumerate(doc.get('items') or []):
            if isinstance(item.get('questions'), list):
                ref = f"lesson > items > {i_idx}"
                all_errors.extend(_validate_questions_per_type(item['questions'], ref))
        summary_label = f"Lesson fragment ({doc.get('title', 'Untitled')})"

    else:
        all_errors.append(f"INTERNAL: validate_fragment dispatched on unknown shape '{shape}'")

    # Print summary
    print(f"\nValidation complete:")
    print(f"  Shape: {shape}")
    if summary_label:
        print(f"  {summary_label}")
    print(f"  Errors: {len(all_errors)}")
    print(f"  Warnings: {len(all_warnings)}")
    print()

    if all_errors:
        print("ERRORS:")
        for error in all_errors:
            print(f"  [ERROR] {error}")
        print()
    if all_warnings:
        print("WARNINGS:")
        for warning in all_warnings:
            print(f"  [WARN] {warning}")
        print()

    if not all_errors and not all_warnings:
        print("All checks passed!")
        return True
    if not all_errors:
        print("Validation passed with warnings.")
        return True
    print("Validation FAILED with errors.")
    return False


def validate_course(course_path, verbose=False, strict=False):
    """Validate a course.json or question-set.json file.

    FF-101: dispatches by document shape. Option D documentType:"questionSet"
    routes to validate_question_set_flat(); everything else (Option D
    documentType:"course", legacy wrapped, legacy bare) routes to the
    course path below.

    TD-155: when strict=True, legacy shapes ('legacy-wrapped', 'legacy-bare')
    are fatal errors instead of tolerated-with-warning. Used by the
    conformance corpus harness so NORMATIVE §3.2 / §4.1 rejections are
    actually enforced.
    """
    print(f"Validating: {course_path}")
    if strict:
        print("Mode: --strict (public conformance — pre-1.0 shapes rejected)")
    print("=" * 80)

    result = load_course(course_path)
    if isinstance(result, tuple):
        course, error = result
        print(f"FATAL ERROR: {error}")
        return False

    doc = result

    # FF-101 shape dispatch
    shape, payload = dispatch_document_shape(doc)
    if shape == 'unknown':
        print(
            "FATAL ERROR: Unrecognised document shape. Expected one of: "
            "canonical flat-root form with documentType:\"course\"|\"questionSet\" "
            "(per NORMATIVE.md §3.2 / §4.1), pre-1.0 wrapped envelope "
            "{\"course\":{...}}, pre-1.0 bare payload {\"units\":[...]}, "
            "or a fragment (single question / item / unit / lesson)."
        )
        return False

    # TD-155: strict mode rejects legacy shapes that the lenient default
    # tolerates with a warning. The 3 conformance fixtures
    # invalid/01-missing-document-type, invalid/10-wrapped-envelope,
    # invalid/11-bare-payload all dispatch to legacy-bare or legacy-wrapped
    # and would otherwise pass with warnings.
    if strict and shape in ('legacy-wrapped', 'legacy-bare'):
        print(
            f"FATAL ERROR: Pre-1.0 document shape '{shape}' rejected under --strict mode "
            f"(NORMATIVE.md §3.2 / §4.1: producers MUST emit the canonical flat-root form "
            f"with $schema, documentType, specVersion). Re-export against the canonical "
            f"flat-root form, or remove --strict for pre-1.0 migration tolerance."
        )
        return False

    if verbose:
        print(f"  Detected shape: {shape}")
    if not _JSONSCHEMA_AVAILABLE:
        print(
            "  [WARN] jsonschema package not installed — running domain-rule pass only. "
            "Install with: pip install -r LC.JSON/requirements.txt"
        )

    # Question Set path (Option D only)
    if shape == 'option-d-question-set':
        return validate_question_set_flat(payload, verbose)

    # Fragment paths — TD-109 widens the validator so spec example fragments
    # validate against their per-type schema. These shapes are not importable
    # as standalone files; they're documentation fragments meant to be pasted
    # into a full course.
    if shape.startswith('fragment-'):
        return validate_fragment(payload, shape, verbose)

    # Course path
    course = payload

    # Option D specVersion forward-compat guard (no-op for legacy shapes)
    sv_errors, sv_warnings = check_spec_version(course)
    if sv_errors:
        for err in sv_errors:
            print(f"FATAL ERROR: {err}")
        return False

    if 'units' not in course:
        print("FATAL ERROR: Missing 'units' array at root level")
        return False

    if not isinstance(course['units'], list):
        print("FATAL ERROR: 'units' must be an array")
        return False

    all_errors = []
    all_warnings = []
    all_notes = []
    all_warnings.extend(sv_warnings)

    # PRIMARY PASS — JSON Schema validation against course.schema.json.
    # Only run for Option D documents; legacy shapes don't have $schema/
    # documentType at root and the schema would reject them outright.
    if shape == 'option-d-course':
        all_errors.extend(_validate_against_schema(course, "course.schema.json", "course"))
        # Per-question type-specific schema dispatch (course.schema.json
        # only validates questions[] against question-base).
        all_errors.extend(_walk_and_validate_all_questions(course))
    elif shape in ('legacy-wrapped', 'legacy-bare'):
        all_warnings.append(
            f"Schema validation skipped for pre-1.0 shape '{shape}'. "
            f"Re-export against the canonical flat-root form for full schema enforcement."
        )

    # Domain rules: course-level properties (title, sourceCourseId, version)
    course_errors, course_warnings = validate_course_level(course, verbose)
    all_errors.extend(course_errors)
    all_warnings.extend(course_warnings)

    # Validate unit sequence order within the course
    course_ref = f"Course ({course.get('title', 'Untitled')})"
    all_warnings.extend(validate_sequence_order(course['units'], course_ref, "unit"))

    # Validate each unit
    for unit_index, unit in enumerate(course['units']):
        errors, warnings = validate_unit(unit, unit_index, verbose)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    # TD-122: weighted-points notes (informational, not warnings)
    all_notes.extend(_collect_weighted_points_notes(course))

    # KG-6 (TD-141 / partial TD-145): objectiveIds referential integrity.
    # Warning-tier — unresolved references don't block import but break
    # signpost auto-rendering of objectives.
    all_warnings.extend(_collect_objective_id_violations(course))

    # Print results
    print(f"\nValidation complete:")
    print(f"  Course: {course.get('title', 'Untitled')}")
    if course.get('sourceCourseId'):
        print(f"  sourceCourseId: {course.get('sourceCourseId')}")
    if course.get('version'):
        print(f"  Version: {course.get('version')}")
    print(f"  Units: {len(course['units'])}")
    print(f"  Errors: {len(all_errors)}")
    print(f"  Warnings: {len(all_warnings)}")
    print(f"  Notes: {len(all_notes)}")
    print()

    if all_errors:
        print("ERRORS:")
        for error in all_errors:
            print(f"  [ERROR] {error}")
        print()

    if all_warnings:
        print("WARNINGS:")
        for warning in all_warnings:
            print(f"  [WARN] {warning}")
        print()

    if all_notes:
        print("NOTES:")
        for note in all_notes:
            print(f"  [NOTE] {note}")
        print()

    if not all_errors and not all_warnings and not all_notes:
        print("All checks passed!")
        return True
    elif not all_errors:
        print("Validation passed.")
        return True
    else:
        print("Validation FAILED with errors.")
        return False


def main():
    # Force UTF-8 stdout so Unicode characters (→, ✓, etc.) print cleanly on
    # Windows without requiring users to set PYTHONIOENCODING. reconfigure()
    # is Python 3.7+; some embedded builds don't expose it, hence the guard.
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        pass

    parser = argparse.ArgumentParser(description='Validate course.json structure')
    parser.add_argument('--course-path', type=str,
                        default=r'C:\Users\PC\OneDrive\@MY_CODE\CourseGenieSolution\CourseGenie.Runner\content\course.json',
                        help='Path to course.json')
    parser.add_argument('--verbose', action='store_true',
                        help='Show detailed validation information')
    parser.add_argument('--strict', action='store_true',
                        help='Public-conformance mode (TD-155): reject legacy '
                             'document shapes (wrapped envelope, bare payload, '
                             'documentType-less roots). Required for '
                             'conformance-corpus enforcement.')

    args = parser.parse_args()

    success = validate_course(args.course_path, args.verbose, strict=args.strict)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
