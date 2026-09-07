#!/usr/bin/env python3
"""
lc_pack.py - Shared library + validator for LC-JSON curriculumPack documents.

This validator implements the curriculumPack rules in the LC-JSON
specification (see VALIDATION.md §16, rule ids CP-1…CP-17). It is the
executable form of the sequence[]/pacing/checkpoint model: the specification
describes intent, the check list below is the set of rules this reference
validator implements. It is NOT normative: the normative prose (NORMATIVE.md and
the companion normative documents) and the schema constraints govern, and where
this validator diverges from them the validator is the defect. A curriculumPack lays a subjectCollection's objectives out across a
teaching calendar (years, terms, weeks) as an ordered sequence[] of steps.

Identity rules:
  - packs reference Collection member ids and content by each document's
    type-directed portable identity (NORMATIVE §4.4): a course's sourceCourseId,
    a questionSet's sourceQuestionSetId, else the root globalId — carried in the
    contentRef `id` field. They never mint, re-mint, or restate identity;
  - step ids are document-local plan labels, not member ids;
  - generated JSON carries NO comments (strict parsers).

Check list — the rules implemented here (E = error -> exit 1, W = warning ->
report only). Non-authoritative; see the note above:
  E01 documentType == "curriculumPack"; globalId/version/title non-empty;
      packMode in {manifest, bundle}; collectionRefs/contentRefs/sequence arrays
  E02 pacing present when sequence[] is non-empty; years/lessonsPerWeek int >= 1;
      termsPerYear int >= 1 (default 3); weeksPerTerm (when present) an int>=1
      array of length termsPerYear; teachingWeeksPerYear == sum(weeksPerTerm)
      when both present
  E03 step ids non-empty and unique; kind in {teaching, review, assessment,
      mock, buffer}; label non-empty; year/term/weekOfTerm/durationLessons
      int >= 1; objectiveIds/tagIds/dependsOn arrays; contentRef null or
      {type, id[, version, selector]}; selector (when present) uses the
      node-globalId-bearing grammar "unit:<id>" | "lesson:<id>" | "item:<id>"
  E04 year <= pacing.years; term <= termsPerYear; weekOfTerm within the term;
      a step's week span stays inside its term (when weeksPerTerm is known)
  E05 term capacity: sum(durationLessons) per (year, term) <=
      weeksPerTerm[term-1] * lessonsPerWeek (when weeksPerTerm is known)
  E06 dependsOn: ids exist, no self-reference, and every dependency is
      STRICTLY earlier in the (year, term, weekOfTerm) timeline, OR in the
      SAME week and earlier in sequence[] document order (within a week,
      document order is the schedule). Acyclicity stays free: (sort key,
      document position) is a
      strict total order and every valid edge points backward in it
  E07 checkpoint present IFF kind in {assessment, mock}
  E08 checkpoint shape: kind in {formative, summative} (mock => summative);
      format non-empty; scope in {listed, allTaughtToDate};
      listed => assessesObjectiveIds non-empty; allTaughtToDate => == []
  E09 checkpoints assess only objectives first taught strictly earlier
  E10 review steps list only objectives first taught strictly earlier
  E11 bill of materials (both modes): every non-null step contentRef appears
      in root contentRefs[] with a matching type
  E12 coverage block: collectionGlobalId non-empty and present in
      collectionRefs; assertions subset of {everyObjectiveTaughtAtLeastOnce,
      everyObjectiveAssessedAtLeastOnce}
  E13 (with --collection) coverage.collectionGlobalId == collection.globalId;
      every objectiveId/tagId used anywhere resolves to a collection member;
      exemptObjectiveIds resolve too
  E14 (with --collection) declared coverage assertions hold:
      taught    = objective appears on a teaching step
      assessed  = objective is in some checkpoint's effective assessed set
      (effective set for scope allTaughtToDate = everything first taught
       strictly before that step); exemptObjectiveIds are excluded
  W01 teaching step with empty objectiveIds
  W02 week occupancy: modeling each step as ceil(duration/lessonsPerWeek)
      weeks from its start week, a week whose lessons exceed lessonsPerWeek
  W03 sequence[] not serialized in timeline order
  W04 unauthored slot (contentRef null) without an authoringNote (buffer
      steps excluded)
  W05 formative-before-summative: an objective reaches a summative checkpoint
      never having been formatively assessed earlier
  W06 dead checkpoint: effective assessed set is empty
  W07 immediate revisit: a review step revisits an objective first taught
      fewer than recyclingPolicy.minSpacingWeeks (default 2) absolute weeks
      earlier (absolute weeks need term lengths; approximated from
      teachingWeeksPerYear when weeksPerTerm is absent)
  E15 bundle mode: the pack carries an embedded block
      {collections: [docs], content: [docs]}; manifests must NOT carry one;
      every collectionRef resolves to an embedded subjectCollection, every
      contentRef and non-null step contentRef resolves to an embedded content
      document of the matching documentType; embedded docs carry
      documentType + their type-directed identity (course/questionSet by
      sourceCourseId/sourceQuestionSetId, else root globalId; embedded verbatim,
      never re-minted);
      a course selector (unit:/lesson:/item:<globalId>) resolves to a node of
      that kind inside the embedded course
  W08 stowaway: an embedded document nothing in the pack references
  W09 version drift: a ref pins a version that differs from the embedded
      document's version (bundling SHOULD surface, not silently substitute)
  W10 a collectionRef/contentRef does not pin a version at all (CP-17: refs
      SHOULD pin so a consumer surfaces a mismatch rather than substituting)

In bundle mode, when --collection is not supplied, coverage/member checks run
against the embedded collection targeted by coverage.collectionGlobalId.

Usage:
    python lc_pack.py --validate pack.json [--collection collection.json]
"""

import argparse
import json
import math
import sys

import _lcjson_schema

STEP_KINDS = {"teaching", "review", "assessment", "mock", "buffer"}
CHECKPOINT_KINDS = {"formative", "summative"}
CHECKPOINT_SCOPES = {"listed", "allTaughtToDate"}
COVERAGE_ASSERTIONS = {"everyObjectiveTaughtAtLeastOnce",
                       "everyObjectiveAssessedAtLeastOnce"}
SELECTOR_PREFIXES = ("unit:", "lesson:", "item:")
DEFAULT_MIN_SPACING_WEEKS = 2


# --------------------------------------------------------------------------
# Builders (used by pack generators; mirror lc_collection.py's helpers)
# --------------------------------------------------------------------------

def new_pack(global_id, title, version="1.0.0", pack_mode="manifest",
             license_="unspecified", description=None):
    return {
        "$schema": "https://lc-json.org/1.1/curriculum-pack.schema.json",
        "documentType": "curriculumPack",
        "specVersion": "1.1",
        "globalId": global_id,
        "version": version,
        "title": title,
        "description": description,
        "packMode": pack_mode,
        "license": license_,
        "authors": [],
        "canonicalUrl": None,
        "derivedFrom": [],
        "pacing": None,
        "collectionRefs": [],
        "contentRefs": [],
        "coverage": None,
        "recyclingPolicy": None,
        "sequence": [],
    }


def pacing(years, lessons_per_week, terms_per_year=3, weeks_per_term=None,
           teaching_weeks_per_year=None, note=None):
    return {"years": years, "termsPerYear": terms_per_year,
            "weeksPerTerm": weeks_per_term, "lessonsPerWeek": lessons_per_week,
            "teachingWeeksPerYear": teaching_weeks_per_year, "note": note}


def coverage(collection_global_id, assertions, exempt_objective_ids=None, note=None):
    return {"collectionGlobalId": collection_global_id,
            "assertions": list(assertions),
            "exemptObjectiveIds": list(exempt_objective_ids or []),
            "note": note}


def step(step_id, kind, label, year, term, week_of_term, duration_lessons,
         objective_ids=None, tag_ids=None, content_ref=None,
         authoring_note=None, depends_on=None, checkpoint=None):
    return {"id": step_id, "kind": kind, "label": label,
            "year": year, "term": term, "weekOfTerm": week_of_term,
            "durationLessons": duration_lessons,
            "objectiveIds": list(objective_ids or []),
            "tagIds": list(tag_ids or []),
            "contentRef": content_ref,
            "authoringNote": authoring_note,
            "dependsOn": list(depends_on or []),
            "checkpoint": checkpoint}


def checkpoint(kind, format_, assesses_objective_ids=None, scope="listed"):
    return {"kind": kind, "format": format_,
            "assessesObjectiveIds": list(assesses_objective_ids or []),
            "scope": scope}


# Portable document identity is type-directed (NORMATIVE §4.4, "Document identity
# by artifact type"): a course/questionSet identifies itself by its source-side id,
# the 1.1 artifact types by their root globalId. A pack contentRef carries that value
# in its `id` field, resolved against the referenced document by its documentType.
_IDENTITY_FIELD = {
    "course": "sourceCourseId",
    "questionSet": "sourceQuestionSetId",
}

# The producer-closed contentRef target vocabulary (NORMATIVE §4.4). A producer
# MUST emit one of these; anything else is a producer error. The wire schema
# leaves `type` an open string (§5.8) so a consumer never rejects an unknown
# future type — this closed set binds producers, enforced here, exactly like the
# externalAlignments[].claim vocabulary.
_CONTENT_REF_TYPES = ("course", "questionSet", "glossary")


def _content_ref_type_error(ref_type, ident, step=None):
    where = (f"step '{step}' contentRef" if step
             else f"contentRef {ref_type}:{ident}")
    if ref_type == "curriculumPack":
        why = ("a Curriculum Pack MUST NOT reference another Curriculum Pack "
               "(NORMATIVE §4.4) — a pack is an arrangement, not embeddable content")
    elif ref_type == "subjectCollection":
        why = ("a SubjectCollection is referenced through collectionRefs, not "
               "contentRefs (NORMATIVE §4.4)")
    else:
        why = (f"'{ref_type}' is not a content type — a contentRef targets one of "
               f"{'/'.join(_CONTENT_REF_TYPES)} (NORMATIVE §4.4; producer-closed "
               "vocabulary)")
    return f"{where} is not permitted: {why}"


def document_identity(doc):
    """The portable identity value of an embeddable document, per its documentType.

    course -> sourceCourseId, questionSet -> sourceQuestionSetId, else root globalId.
    Returns None when the document does not carry the field its type resolves against
    (e.g. a course with no sourceCourseId) — such a document cannot be referenced by a
    pack (NORMATIVE §4.4)."""
    if not isinstance(doc, dict):
        return None
    field = _IDENTITY_FIELD.get(doc.get("documentType"), "globalId")
    return doc.get(field)


def content_ref(type_, id_, version=None, selector=None):
    return {"type": type_, "id": id_,
            "version": version, "selector": selector}


# --------------------------------------------------------------------------
# Timeline helpers
# --------------------------------------------------------------------------

def sort_key(s):
    return (s.get("year", 0), s.get("term", 0), s.get("weekOfTerm", 0))


def _term_weeks(pac):
    """weeksPerTerm if present, else a documented approximation (W07/E04 use
    the exact table only; the approximation feeds absolute-week spacing)."""
    wpt = pac.get("weeksPerTerm")
    if wpt:
        return list(wpt)
    terms = pac.get("termsPerYear") or 3
    twpy = pac.get("teachingWeeksPerYear") or 12 * terms
    return [math.ceil(twpy / terms)] * terms


def absolute_week(s, pac):
    """1-based week index on the whole-pack week line (spacing checks)."""
    weeks = _term_weeks(pac)
    per_year = sum(weeks)
    return ((s["year"] - 1) * per_year
            + sum(weeks[:s["term"] - 1])
            + s["weekOfTerm"])


def _weeks_span(s, pac):
    lpw = pac.get("lessonsPerWeek") or 1
    return math.ceil(s.get("durationLessons", 1) / lpw)


def _first_taught(steps):
    """objective id -> sort key of its earliest teaching step."""
    first = {}
    for s in steps:
        if s.get("kind") != "teaching":
            continue
        for oid in s.get("objectiveIds", []):
            if oid not in first or sort_key(s) < first[oid]:
                first[oid] = sort_key(s)
    return first


def effective_assessed(s, steps):
    """The checkpoint's effective assessed set."""
    ck = s.get("checkpoint") or {}
    if ck.get("scope", "listed") == "allTaughtToDate":
        first = _first_taught(steps)
        return {oid for oid, k in first.items() if k < sort_key(s)}
    return set(ck.get("assessesObjectiveIds", []))


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def _is_pos_int(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 1


def validate(doc, collection=None):
    """Returns (errors, warnings) lists; empty errors = valid."""
    errors, warnings = [], []

    # ---- E01 root envelope ------------------------------------------------
    if doc.get("documentType") != "curriculumPack":
        errors.append(f"documentType is '{doc.get('documentType')}', expected 'curriculumPack'")
    for field in ("globalId", "version", "title"):
        if not doc.get(field):
            errors.append(f"{field} is required")
    if doc.get("packMode") not in ("manifest", "bundle"):
        errors.append(f"packMode '{doc.get('packMode')}' must be 'manifest' or 'bundle'")
    for field in ("collectionRefs", "contentRefs", "sequence"):
        if not isinstance(doc.get(field), list):
            errors.append(f"{field} must be an array")
    steps = [s for s in doc.get("sequence") or [] if isinstance(s, dict)]
    for i, s in enumerate(doc.get("sequence") or []):
        if not isinstance(s, dict):
            errors.append(f"sequence[{i}] is not an object")

    # ---- W10 refs SHOULD pin a version (CP-17 hygiene) ---------------------
    # A ref without a `version` leaves the consumer free to substitute any
    # version silently. Advisory only: pinning is a SHOULD, not a MUST.
    for r in doc.get("collectionRefs") or []:
        if isinstance(r, dict) and r.get("globalId") and not r.get("version"):
            warnings.append(f"collectionRef '{r['globalId']}' does not pin a version "
                            "(SHOULD pin so a consumer surfaces a mismatch rather than "
                            "silently substituting)")
    for r in doc.get("contentRefs") or []:
        if isinstance(r, dict) and r.get("id") and not r.get("version"):
            warnings.append(f"contentRef {r.get('type')}:{r['id']} does not pin a "
                            "version (SHOULD pin so a consumer surfaces a mismatch rather "
                            "than silently substituting)")

    # ---- E02 pacing --------------------------------------------------------
    pac = doc.get("pacing")
    if steps and not isinstance(pac, dict):
        errors.append("pacing block is required when sequence[] is non-empty")
        pac = None
    if isinstance(pac, dict):
        for field in ("years", "lessonsPerWeek"):
            if not _is_pos_int(pac.get(field)):
                errors.append(f"pacing.{field} must be an integer >= 1")
        terms_per_year = pac.get("termsPerYear", 3)
        if not _is_pos_int(terms_per_year):
            errors.append("pacing.termsPerYear must be an integer >= 1")
            terms_per_year = 3
        wpt = pac.get("weeksPerTerm")
        if wpt is not None:
            if (not isinstance(wpt, list) or len(wpt) != terms_per_year
                    or not all(_is_pos_int(w) for w in wpt)):
                errors.append(f"pacing.weeksPerTerm must be an array of {terms_per_year} "
                              "integers >= 1 (one per term)")
                wpt = None
        twpy = pac.get("teachingWeeksPerYear")
        if twpy is not None and not _is_pos_int(twpy):
            errors.append("pacing.teachingWeeksPerYear must be an integer >= 1")
        if wpt and _is_pos_int(twpy) and sum(wpt) != twpy:
            errors.append(f"pacing.teachingWeeksPerYear ({twpy}) != sum(weeksPerTerm) ({sum(wpt)})")
    else:
        pac = None

    # ---- E03 step shape ----------------------------------------------------
    ids_seen, dup = set(), set()
    for s in steps:
        sid = s.get("id") or "?"
        if not s.get("id"):
            errors.append("a step has no id")
        elif s["id"] in ids_seen:
            dup.add(s["id"])
        else:
            ids_seen.add(s["id"])
        if s.get("kind") not in STEP_KINDS:
            errors.append(f"step '{sid}' kind '{s.get('kind')}' is not one of "
                          f"{'/'.join(sorted(STEP_KINDS))}")
        if not s.get("label"):
            errors.append(f"step '{sid}' has no label")
        for field in ("year", "term", "weekOfTerm", "durationLessons"):
            if not _is_pos_int(s.get(field)):
                errors.append(f"step '{sid}' {field} must be an integer >= 1")
        for field in ("objectiveIds", "tagIds", "dependsOn"):
            if field in s and not isinstance(s[field], list):
                errors.append(f"step '{sid}' {field} must be an array")
        if "contentRef" not in s:
            errors.append(f"step '{sid}' is missing contentRef (null = unauthored slot)")
        cr = s.get("contentRef")
        if cr is not None:
            if not isinstance(cr, dict) or not cr.get("type") or not cr.get("id"):
                errors.append(f"step '{sid}' contentRef must be null or carry type + id")
            else:
                sel = cr.get("selector")
                if sel is not None and not (isinstance(sel, str)
                                            and sel.startswith(SELECTOR_PREFIXES)
                                            and sel.split(":", 1)[1]):
                    errors.append(f"step '{sid}' contentRef.selector '{sel}' must use the "
                                  "globalId-bearing grammar unit:<id> | lesson:<id> | item:<id>")
    for d in sorted(dup):
        errors.append(f"duplicate step id '{d}'")

    # Steps that are shape-complete enough for timeline math:
    placed = [s for s in steps
              if all(_is_pos_int(s.get(f)) for f in ("year", "term", "weekOfTerm", "durationLessons"))]

    # ---- E04 ranges / span; E05 term capacity ------------------------------
    if pac:
        years = pac.get("years")
        terms_per_year = pac.get("termsPerYear", 3)
        wpt = pac.get("weeksPerTerm") if isinstance(pac.get("weeksPerTerm"), list) else None
        lpw = pac.get("lessonsPerWeek")
        for s in placed:
            sid = s["id"]
            if _is_pos_int(years) and s["year"] > years:
                errors.append(f"step '{sid}' year {s['year']} exceeds pacing.years {years}")
            if _is_pos_int(terms_per_year) and s["term"] > terms_per_year:
                errors.append(f"step '{sid}' term {s['term']} exceeds pacing.termsPerYear {terms_per_year}")
            if wpt and s["term"] <= len(wpt):
                term_len = wpt[s["term"] - 1]
                if s["weekOfTerm"] > term_len:
                    errors.append(f"step '{sid}' weekOfTerm {s['weekOfTerm']} exceeds "
                                  f"term {s['term']}'s {term_len} weeks")
                elif _is_pos_int(lpw) and s["weekOfTerm"] + _weeks_span(s, pac) - 1 > term_len:
                    errors.append(f"step '{sid}' ({s['durationLessons']} lessons from week "
                                  f"{s['weekOfTerm']}) runs past the end of term {s['term']} "
                                  f"({term_len} weeks)")
        if wpt and _is_pos_int(lpw):
            per_term = {}
            for s in placed:
                per_term.setdefault((s["year"], s["term"]), 0)
                per_term[(s["year"], s["term"])] += s["durationLessons"]
            for (y, t), total in sorted(per_term.items()):
                if t <= len(wpt):
                    cap = wpt[t - 1] * lpw
                    if total > cap:
                        errors.append(f"year {y} term {t} is over capacity: {total} lessons "
                                      f"planned, {cap} available ({wpt[t-1]} weeks x {lpw})")
            # ---- W02 week occupancy (greedy spread) -------------------------
            occupancy = {}
            for s in placed:
                remaining = s["durationLessons"]
                week = s["weekOfTerm"]
                while remaining > 0:
                    take = min(lpw, remaining)
                    key = (s["year"], s["term"], week)
                    occupancy[key] = occupancy.get(key, 0) + take
                    remaining -= take
                    week += 1
            for (y, t, w), total in sorted(occupancy.items()):
                if total > lpw:
                    warnings.append(f"year {y} term {t} week {w} is overloaded: {total} lessons "
                                    f"against {lpw}/week (parallel steps colliding)")

    # ---- E06 dependencies (R3': same-week edges resolve by document order) ---
    by_id = {s["id"]: s for s in placed if s.get("id")}
    doc_pos = {s["id"]: i for i, s in enumerate(steps) if s.get("id")}
    for s in placed:
        for dep in s.get("dependsOn", []):
            if dep == s["id"]:
                errors.append(f"step '{s['id']}' depends on itself")
            elif dep not in ids_seen:
                errors.append(f"step '{s['id']}' dependsOn '{dep}' which does not exist")
            elif dep in by_id:
                if sort_key(by_id[dep]) > sort_key(s):
                    errors.append(f"step '{s['id']}' dependsOn '{dep}' which is not strictly "
                                  "earlier in the timeline")
                elif (sort_key(by_id[dep]) == sort_key(s)
                        and doc_pos.get(dep, 0) >= doc_pos.get(s["id"], 0)):
                    errors.append(f"step '{s['id']}' dependsOn '{dep}' which is in the same "
                                  "week but not earlier in document order (within a "
                                  "week, document order is the schedule)")

    # ---- E07/E08 checkpoint presence + shape --------------------------------
    for s in steps:
        sid = s.get("id") or "?"
        ck = s.get("checkpoint")
        if s.get("kind") in ("assessment", "mock"):
            if not isinstance(ck, dict):
                errors.append(f"step '{sid}' is kind '{s.get('kind')}' and must carry a checkpoint")
                continue
            if ck.get("kind") not in CHECKPOINT_KINDS:
                errors.append(f"step '{sid}' checkpoint kind '{ck.get('kind')}' must be "
                              "formative or summative")
            if s.get("kind") == "mock" and ck.get("kind") != "summative":
                errors.append(f"step '{sid}' is a mock; its checkpoint must be summative")
            if not ck.get("format"):
                errors.append(f"step '{sid}' checkpoint has no format")
            scope = ck.get("scope", "listed")
            if scope not in CHECKPOINT_SCOPES:
                errors.append(f"step '{sid}' checkpoint scope '{scope}' must be "
                              "listed or allTaughtToDate")
            assessed = ck.get("assessesObjectiveIds")
            if not isinstance(assessed, list):
                errors.append(f"step '{sid}' checkpoint assessesObjectiveIds must be an array")
            elif scope == "listed" and not assessed:
                errors.append(f"step '{sid}' checkpoint scope 'listed' requires a non-empty "
                              "assessesObjectiveIds")
            elif scope == "allTaughtToDate" and assessed:
                errors.append(f"step '{sid}' checkpoint scope 'allTaughtToDate' requires "
                              "assessesObjectiveIds to be [] (the set is computed, never stated)")
        elif ck is not None:
            errors.append(f"step '{sid}' is kind '{s.get('kind')}' and must not carry a "
                          "checkpoint (use kind assessment/mock)")

    # ---- E09/E10 taught-before-used; W05/W06/W07 ---------------------------
    first = _first_taught(placed)
    formatively_assessed = set()
    for s in sorted(placed, key=sort_key):
        sid = s["id"]
        if s.get("kind") == "review":
            for oid in s.get("objectiveIds", []):
                if oid not in first or not first[oid] < sort_key(s):
                    errors.append(f"review step '{sid}' revisits objective '{oid}' which has "
                                  "no earlier teaching step")
                elif pac:
                    gap = absolute_week(s, pac) - _abs_week_of_key(first[oid], placed, pac)
                    min_gap = ((doc.get("recyclingPolicy") or {}).get("minSpacingWeeks")
                               or DEFAULT_MIN_SPACING_WEEKS)
                    if gap < min_gap:
                        warnings.append(f"review step '{sid}' revisits objective '{oid}' only "
                                        f"{gap} week(s) after first teach (< {min_gap}; spacing "
                                        "is the point of spiral recycling)")
        ck = s.get("checkpoint")
        if isinstance(ck, dict) and s.get("kind") in ("assessment", "mock"):
            eff = effective_assessed(s, placed)
            if ck.get("scope", "listed") == "listed":
                for oid in sorted(eff):
                    if oid not in first or not first[oid] < sort_key(s):
                        errors.append(f"checkpoint on step '{sid}' assesses objective '{oid}' "
                                      "which has no earlier teaching step")
            if not eff:
                warnings.append(f"checkpoint on step '{sid}' assesses nothing (dead checkpoint)")
            if ck.get("kind") == "summative":
                never_formative = sorted(oid for oid in eff
                                         if oid in first and first[oid] < sort_key(s)
                                         and oid not in formatively_assessed)
                if never_formative:
                    shown = ", ".join(never_formative[:3])
                    more = f" (+{len(never_formative)-3} more)" if len(never_formative) > 3 else ""
                    warnings.append(f"summative checkpoint on step '{sid}' assesses "
                                    f"{len(never_formative)} objective(s) never formatively "
                                    f"assessed earlier: {shown}{more}")
            if ck.get("kind") == "formative":
                formatively_assessed |= eff

    # ---- W01/W03/W04 --------------------------------------------------------
    for s in steps:
        if s.get("kind") == "teaching" and not s.get("objectiveIds"):
            warnings.append(f"teaching step '{s.get('id') or '?'}' teaches no objectives")
        if (s.get("kind") != "buffer" and s.get("contentRef") is None
                and not s.get("authoringNote")):
            warnings.append(f"step '{s.get('id') or '?'}' is an unauthored slot with no "
                            "authoringNote (say what belongs there)")
    keys = [sort_key(s) for s in placed]
    if keys != sorted(keys):
        warnings.append("sequence[] is not serialized in timeline order "
                        "(sort key is truth, but ordered files diff better)")

    # ---- CP-3 target type: the contentRef vocabulary is producer-closed -----
    # A producer MUST emit type ∈ {course, questionSet, glossary}. Anything else
    # — curriculumPack (no pack nesting), subjectCollection (wrong channel), or an
    # unknown type — is a producer error. The schema leaves `type` open (§5.8) so
    # a consumer never rejects an unknown future type; this closed set is enforced
    # here, at the producer/domain tier, like the alignment-claim vocabulary.
    def _bad(t):
        return isinstance(t, str) and t and t not in _CONTENT_REF_TYPES
    for r in doc.get("contentRefs") or []:
        if isinstance(r, dict) and _bad(r.get("type")):
            errors.append(_content_ref_type_error(r.get("type"), r.get("id")))
    for s in steps:
        cr = s.get("contentRef")
        if isinstance(cr, dict) and _bad(cr.get("type")):
            errors.append(_content_ref_type_error(
                cr.get("type"), cr.get("id"), step=s.get("id") or "?"))

    # ---- E11 bill of materials (both modes: contentRefs[] is the index) -----
    declared = {(r.get("type"), r.get("id"))
                for r in doc.get("contentRefs") or [] if isinstance(r, dict)}
    for s in steps:
        cr = s.get("contentRef")
        if isinstance(cr, dict) and cr.get("id"):
            if (cr.get("type"), cr.get("id")) not in declared:
                errors.append(f"step '{s.get('id') or '?'}' contentRef "
                              f"{cr.get('type')}:{cr.get('id')} is not listed in "
                              "contentRefs[] (the root array is the bill of materials)")

    # ---- E15 bundle embedded closure / W08 / W09 -----------------------------
    if doc.get("packMode") == "manifest" and doc.get("embedded") is not None:
        errors.append("a manifest must not carry an embedded block (that's what "
                      "packMode 'bundle' means)")
    emb_collections, emb_content = {}, {}
    if doc.get("packMode") == "bundle":
        emb = doc.get("embedded")
        if not isinstance(emb, dict):
            errors.append("a bundle must carry an embedded block "
                          "{collections: [...], content: [...]}")
        else:
            for d in emb.get("collections") or []:
                if not isinstance(d, dict) or not d.get("globalId"):
                    errors.append("an embedded collection has no globalId")
                elif d.get("documentType") != "subjectCollection":
                    errors.append(f"embedded collection '{d.get('globalId')}' has "
                                  f"documentType '{d.get('documentType')}'")
                else:
                    emb_collections[d["globalId"]] = d
            for d in emb.get("content") or []:
                if not isinstance(d, dict) or not d.get("documentType"):
                    errors.append("an embedded content document is missing documentType")
                    continue
                ident = document_identity(d)
                if not ident:
                    field = _IDENTITY_FIELD.get(d.get("documentType"), "globalId")
                    errors.append(f"an embedded {d.get('documentType')} content document "
                                  f"is missing its identity ({field})")
                    continue
                emb_content[(d["documentType"], ident)] = d
            referenced_cols, referenced_content = set(), set()
            for r in doc.get("collectionRefs") or []:
                if not isinstance(r, dict):
                    continue
                referenced_cols.add(r.get("globalId"))
                target = emb_collections.get(r.get("globalId"))
                if target is None:
                    errors.append(f"collectionRef '{r.get('globalId')}' is not embedded")
                elif r.get("version") and target.get("version") != r.get("version"):
                    warnings.append(f"collectionRef '{r.get('globalId')}' pins version "
                                    f"{r.get('version')} but the embedded document is "
                                    f"{target.get('version')} (surface, don't substitute)")
            for r in doc.get("contentRefs") or []:
                if not isinstance(r, dict):
                    continue
                key = (r.get("type"), r.get("id"))
                referenced_content.add(key)
                target = emb_content.get(key)
                if target is None:
                    errors.append(f"contentRef {key[0]}:{key[1]} is not embedded")
                elif r.get("version") and target.get("version") != r.get("version"):
                    warnings.append(f"contentRef '{r.get('id')}' pins version "
                                    f"{r.get('version')} but the embedded document is "
                                    f"{target.get('version')} (surface, don't substitute)")
            for s in steps:
                cr = s.get("contentRef")
                if isinstance(cr, dict) and cr.get("id"):
                    key = (cr.get("type"), cr.get("id"))
                    referenced_content.add(key)
                    target = emb_content.get(key)
                    if target is None:
                        errors.append(f"step '{s.get('id') or '?'}' contentRef "
                                      f"{key[0]}:{key[1]} is not embedded")
                    elif cr.get("selector") and target.get("documentType") == "course":
                        want_kind, want_id = cr["selector"].split(":", 1)
                        if (want_kind, want_id) not in _course_node_ids(target):
                            errors.append(f"step '{s.get('id') or '?'}' selector "
                                          f"'{cr['selector']}' does not resolve inside "
                                          f"embedded course '{cr.get('id')}'")
            for gid in sorted(set(emb_collections) - referenced_cols):
                warnings.append(f"embedded collection '{gid}' is referenced by nothing (stowaway)")
            for key in sorted(set(emb_content) - referenced_content):
                warnings.append(f"embedded {key[0]} '{key[1]}' is referenced by nothing (stowaway)")

    # ---- E12 coverage block --------------------------------------------------
    cov = doc.get("coverage")
    if cov is not None:
        if not isinstance(cov, dict) or not cov.get("collectionGlobalId"):
            errors.append("coverage block must carry collectionGlobalId")
            cov = None
        else:
            declared_cols = {r.get("globalId") for r in doc.get("collectionRefs") or []
                             if isinstance(r, dict)}
            if cov["collectionGlobalId"] not in declared_cols:
                errors.append(f"coverage.collectionGlobalId '{cov['collectionGlobalId']}' "
                              "is not in collectionRefs[]")
            for a in cov.get("assertions") or []:
                if a not in COVERAGE_ASSERTIONS:
                    errors.append(f"coverage assertion '{a}' is unknown "
                                  f"({'/'.join(sorted(COVERAGE_ASSERTIONS))})")

    # ---- E13/E14 against the Collection --------------------------------------
    if collection is None and cov and emb_collections:
        # Bundle self-containment: the embedded collection IS the vocabulary.
        collection = emb_collections.get(cov.get("collectionGlobalId"))
    if collection is not None:
        col_objectives = {o.get("id") for o in collection.get("objectives", []) if o.get("id")}
        col_tags = {t.get("id") for t in collection.get("tags", []) if t.get("id")}
        col_gid = collection.get("globalId")
        if cov and cov.get("collectionGlobalId") != col_gid:
            errors.append(f"coverage targets '{cov.get('collectionGlobalId')}' but the "
                          f"supplied Collection is '{col_gid}'")
        for s in steps:
            sid = s.get("id") or "?"
            for oid in s.get("objectiveIds", []):
                if oid not in col_objectives:
                    errors.append(f"step '{sid}' objectiveId '{oid}' does not resolve in "
                                  f"Collection '{col_gid}'")
            for tid in s.get("tagIds", []):
                if tid not in col_tags:
                    errors.append(f"step '{sid}' tagId '{tid}' does not resolve in "
                                  f"Collection '{col_gid}'")
            ck = s.get("checkpoint")
            if isinstance(ck, dict):
                for oid in ck.get("assessesObjectiveIds") or []:
                    if oid not in col_objectives:
                        errors.append(f"checkpoint on step '{sid}' assesses '{oid}' which "
                                      f"does not resolve in Collection '{col_gid}'")
        if cov:
            exempt = set(cov.get("exemptObjectiveIds") or [])
            for oid in sorted(exempt - col_objectives):
                errors.append(f"coverage.exemptObjectiveIds '{oid}' does not resolve in "
                              f"Collection '{col_gid}'")
            in_scope = col_objectives - exempt
            if "everyObjectiveTaughtAtLeastOnce" in (cov.get("assertions") or []):
                taught = set(_first_taught(placed))
                for oid in sorted(in_scope - taught):
                    errors.append(f"coverage: objective '{oid}' is never taught")
            if "everyObjectiveAssessedAtLeastOnce" in (cov.get("assertions") or []):
                assessed = set()
                for s in placed:
                    if s.get("kind") in ("assessment", "mock") and isinstance(s.get("checkpoint"), dict):
                        assessed |= effective_assessed(s, placed)
                for oid in sorted(in_scope - assessed):
                    errors.append(f"coverage: objective '{oid}' is never assessed by any checkpoint")

    return errors, warnings


def _abs_week_of_key(key, steps, pac):
    """Absolute week of a (year, term, weekOfTerm) sort key."""
    stub = {"year": key[0], "term": key[1], "weekOfTerm": key[2]}
    return absolute_week(stub, pac)


def _course_node_ids(course):
    """(kind, globalId) of every selector-addressable node in a course."""
    ids = set()
    for u in course.get("units") or []:
        ids.add(("unit", u.get("globalId")))
        for lesson in u.get("lessons") or []:
            ids.add(("lesson", lesson.get("globalId")))
            for item in lesson.get("items") or []:
                ids.add(("item", item.get("globalId")))
    return ids


# --------------------------------------------------------------------------
# Maturity report (informative)
# --------------------------------------------------------------------------

def maturity_report(doc, collection=None):
    lines = []
    steps = [s for s in doc.get("sequence") or [] if isinstance(s, dict)]
    by_kind = {}
    for s in steps:
        by_kind[s.get("kind", "?")] = by_kind.get(s.get("kind", "?"), 0) + 1
    lines.append("steps: " + ", ".join(f"{k} {v}" for k, v in sorted(by_kind.items())))
    slots = [s for s in steps if s.get("kind") != "buffer"]
    filled = [s for s in slots if s.get("contentRef")]
    lines.append(f"content slots filled: {len(filled)}/{len(slots)}"
                 + (" (pure blueprint)" if slots and not filled else ""))
    pac = doc.get("pacing") or {}
    wpt = pac.get("weeksPerTerm")
    lpw = pac.get("lessonsPerWeek")
    if wpt and lpw:
        per_term = {}
        for s in steps:
            if all(_is_pos_int(s.get(f)) for f in ("year", "term", "durationLessons")):
                per_term.setdefault((s["year"], s["term"]), 0)
                per_term[(s["year"], s["term"])] += s["durationLessons"]
        util = ", ".join(f"y{y}t{t} {total}/{wpt[t-1]*lpw}"
                         for (y, t), total in sorted(per_term.items()) if t <= len(wpt))
        lines.append(f"term utilization (lessons): {util}")
    if collection is not None:
        placed = [s for s in steps
                  if all(_is_pos_int(s.get(f)) for f in ("year", "term", "weekOfTerm", "durationLessons"))]
        first = _first_taught(placed)
        reviewed = set()
        for s in placed:
            if s.get("kind") == "review":
                reviewed |= set(s.get("objectiveIds", []))
        assessed_after = set()
        for s in placed:
            if s.get("kind") in ("assessment", "mock") and isinstance(s.get("checkpoint"), dict):
                assessed_after |= {oid for oid in effective_assessed(s, placed)
                                   if oid in first and sort_key(s)[:2] != first[oid][:2]}
        never_recycled = sorted(set(first) - reviewed - assessed_after)
        lines.append(f"objectives taught: {len(first)}/{len(collection.get('objectives', []))}; "
                     f"never revisited after their term: {len(never_recycled)}")
        if never_recycled:
            lines.append("  never-recycled ids: " + ", ".join(never_recycled[:5])
                         + (f" (+{len(never_recycled)-5} more)" if len(never_recycled) > 5 else ""))
    return lines


# --------------------------------------------------------------------------
# Save / CLI
# --------------------------------------------------------------------------

def save(doc, path, collection=None):
    # The emission gate, not validate() alone: this also covers the pack's schema,
    # its canonical $schema identity, and — for a bundle — the schema AND domain
    # rules of every embedded document.
    errors = _lcjson_schema.validate_for_emission(doc, collection)
    if errors:
        raise ValueError("Pack is not valid:\n  " + "\n  ".join(errors))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")


def _embedded_errors(doc):
    """Schema + domain problems for a bundle's embedded documents (none for a
    manifest)."""
    return _lcjson_schema.embedded_problems(doc)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--validate", metavar="FILE", help="validate a curriculumPack document")
    parser.add_argument("--collection", metavar="FILE",
                        help="the referenced subjectCollection artifact (enables member "
                             "resolution + coverage checks)")
    parser.add_argument("--domain-only", action="store_true",
                        help="run the domain rules without schema validation. NOT a "
                             "conformance check — reports DOMAIN-ONLY OK, never VALID")
    args = parser.parse_args()

    if not args.validate:
        parser.print_help()
        return

    full = _lcjson_schema.cli_preflight(args.domain_only,
                                       doctype="curriculumPack")

    with open(args.validate, encoding="utf-8") as f:
        doc = json.load(f)
    collection = None
    if args.collection:
        with open(args.collection, encoding="utf-8") as f:
            collection = json.load(f)

    schema_errors = []
    if full:
        schema_errors, unavailable = _lcjson_schema.schema_stage(
            doc, "curriculumPack")
        if unavailable:
            _lcjson_schema.exit_unavailable_unless_definitive(
                schema_errors, unavailable)
    errors, warnings = validate(doc, collection)
    # A bundle's embedded documents are part of what this pack asserts, so they
    # are checked here too — schema and domain, not schema alone. Skipped in
    # domain-only mode, which must not run any schema stage.
    errors = schema_errors + errors + (_embedded_errors(doc) if full else [])
    for w in warnings:
        print(f"  WARNING: {w}")
    if errors:
        print(f"INVALID — {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    verdict = "VALID" if full else "DOMAIN-ONLY OK (not a conformance check)"
    print(f"{verdict}: {doc.get('title')} ({doc.get('globalId')} v{doc.get('version')}, "
          f"{doc.get('packMode')})")
    if collection is None:
        print("  note: no --collection supplied; member resolution + coverage checks skipped")
    for line in maturity_report(doc, collection):
        print(f"  {line}")
    sys.exit(0)


if __name__ == "__main__":
    main()
