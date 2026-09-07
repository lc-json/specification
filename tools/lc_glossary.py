#!/usr/bin/env python3
"""lc_glossary.py - Reference validator (with in-memory builders) for LC-JSON glossary documents.

The `--validate` CLI is the tool's purpose: it implements the glossary rules in
the LC-JSON specification (see VALIDATION.md §17, rule ids GL-1…GL-11 /
GE01…GW04). It is the code-first, executable form of the glossary language
model — the specification describes intent, the check list below is the set of
rules this reference validator implements. It is NOT normative: the normative
prose and the schema constraints govern, and where this validator diverges from
them the validator is the defect.

The module also exposes small in-memory construction helpers (`new_glossary`,
`new_entry`) so tests and examples can build a document to validate without a
JSON fixture on disk. They write nothing and are not an exporter; the shipped
tool is validation-first.

Identity rules:
  - entry ids are mint-once, immutable member ids; display text is never identity;
  - one entry = one term IN ONE SENSE (multiple senses = multiple entries);
  - a foreign format never carries member ids: a round-trip out to another
    format and back is a NEW document, not a restore.

Language model:
  a glossary document is single-language (`language` = the language of terms,
  definitions, examples); per-entry `translations` / `definitionTranslations` /
  `examples[].translations` maps are CONTENT — data about the term, like its IPA —
  not field-level document localization. The root `translationLanguages` array is
  the document's DECLARED TRANSLATION INVENTORY: the exact set of language keys
  appearing anywhere in the document (a checkable claim — declared, not implied).
  Array order MAY be read as preference order by consumers that must pick one
  language. There is deliberately NO `supportLanguage` on glossaries: the
  "which one do I show" preference lives in the delivery context (the attached
  course's supportLanguage, or the user's L1), not on the portable artifact.

Severity principle: a FALSE claim is an ERROR; a MISSING claim is a WARN.
Declared-but-unused languages are false claims (GE05); translations present
without a declaration is a missing claim (GW02). Errors gate the interchange
boundary (export/publish), never mid-authoring working state.

Check list — the rules implemented here (GE = error -> exit 1, GW = warning ->
report only). Non-authoritative; see the note above:
  GE01 documentType == "glossary"; globalId/version/title/language non-empty;
       entries is an array; translationLanguages (when present) an array of
       unique, non-empty, BCP 47-shaped strings
  GE02 entry shape: id non-empty and unique; term non-empty; kind (when present)
       in {word, phrase}; partOfSpeech/definition/ipa/soundsLike/audioUrl/imageUrl/
       firstMention (when present) non-empty strings; linkAutomatically (when
       present) a bool; otherForms/tags (when present) arrays of non-empty strings;
       examples (when present) an array of {text[, translations]} with non-empty
       text; translations / definitionTranslations / example translations (when
       present) objects of language-tag keys (BCP 47-ish: 2-3 letter primary
       subtag, optional -subtags) to non-empty strings
  GE03 the gloss rule: every entry carries at least one of definition /
       translations / definitionTranslations (a term with none of these cannot
       be glossed, carded, or popovered). Interchange-boundary rule: producers
       MUST NOT emit a violating document; documents mid-authoring may fail it.
  GE04 declared-inventory membership: when translationLanguages is declared
       (non-empty), every translation key used anywhere (entry translations,
       definitionTranslations, example translations) is a member of it
  GE05 no false claims: every declared translationLanguages value is used by at
       least one translation value somewhere in the document
  GW01 duplicate matching surface: the same term/otherForm text (case-insensitive)
       appears on more than one entry — legal (senses), but auto-link needs
       disambiguation, so the author should know
  GW02 translations are present but the document declares no translationLanguages
       (missing claim — the nudge; fires on documents that carry translations but
       omit the translationLanguages declaration)
  GW03 an entry's otherForms repeats its own term (redundant surface)
  GW04 language-code lint: a declared translationLanguages value (or, when no
       declaration exists, a used key) whose 2-letter primary subtag is not
       ISO 639-1, or whose 2-letter region subtag is not ISO 3166-1 alpha-2.
       3-letter primary subtags and script/other subtags are shape-checked only
       (the 639-2/3 registry is too large to embed for a WARN-tier lint).

firstMention: optional lesson GlobalId on the entry —
the lesson where the term is introduced. Accepted + counted in the maturity report,
never an error: imported glossaries legitimately carry no lesson provenance, and a
firstMention naming a lesson the importer does not hold is treated as absent.
Importers that regenerate lesson ids MUST remap firstMention (consumer obligation;
see VALIDATION.md).

On success prints the maturity report: entry counts by kind, gloss coverage,
% with ipa / soundsLike / audio / image / examples / firstMention, translation
coverage per language key.

Usage:
    python lc_glossary.py --validate glossary.json
"""

import argparse
import json
import re
import sys
import unicodedata

import _lcjson_schema

ENTRY_KINDS = {"word", "phrase"}
LANG_KEY_RE = re.compile(r"^[a-zA-Z]{2,3}(-[a-zA-Z0-9]{1,8})*$")

# Frozen lookup sets for the GW04 lint (WARN-tier; registries are stable).
ISO_639_1 = frozenset("""
aa ab ae af ak am an ar as av ay az ba be bg bh bi bm bn bo br bs ca ce ch co
cr cs cu cv cy da de dv dz ee el en eo es et eu fa ff fi fj fo fr fy ga gd gl
gn gu gv ha he hi ho hr ht hu hy hz ia id ie ig ii ik io is it iu ja jv ka kg
ki kj kk kl km kn ko kr ks ku kv kw ky la lb lg li ln lo lt lu lv mg mh mi mk
ml mn mr ms mt my na nb nd ne ng nl nn no nr nv ny oc oj om or os pa pi pl ps
pt qu rm rn ro ru rw sa sc sd se sg si sk sl sm sn so sq sr ss st su sv sw ta
te tg th ti tk tl tn to tr ts tt tw ty ug uk ur uz ve vi vo wa wo xh yi yo za
zh zu
""".split())

ISO_3166_1_ALPHA2 = frozenset("""
AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL
BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV
CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD
GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM
IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK
LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW
MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR
PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS
ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY
UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW
""".split())

# ---------------------------------------------------------------------------
# Builders (generators mint immutable member ids)
# ---------------------------------------------------------------------------

def new_glossary(global_id, title, language, version="1.0.0",
                 translation_languages=None, description=None,
                 license_="unspecified"):
    return {
        "$schema": "https://lc-json.org/1.1/glossary.schema.json",
        "documentType": "glossary",
        "specVersion": "1.1",
        "globalId": global_id,
        "version": version,
        "title": title,
        "description": description,
        "language": language,
        "translationLanguages": list(translation_languages or []),
        "license": license_,
        "authors": [],
        "canonicalUrl": None,
        "derivedFrom": [],
        "entries": [],
    }


def new_entry(entry_id, term, **fields):
    entry = {"id": entry_id, "term": term}
    entry.update(fields)
    return entry


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _check_translations(owner, value, errors, where):
    if not isinstance(value, dict):
        errors.append(f"{owner} {where} must be an object of language-tag keys")
        return
    for key, text in value.items():
        if not LANG_KEY_RE.match(str(key)):
            errors.append(f"{owner} {where} key '{key}' is not a language tag "
                          "(use BCP 47, e.g. 'es', 'pt-BR')")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{owner} {where}['{key}'] must be a non-empty string")


def lang_key(tag):
    """Canonical comparison key for a BCP 47 language tag.

    BCP 47 section 2.1.1 makes tags case-insensitive: `es`, `ES` and `Es` are the
    same language, and `pt-BR` and `pt-br` are the same tag. Comparing raw strings
    made a Glossary declaring `es` and using the key `ES` fail twice over — GL-5
    (used but undeclared) *and* GL-6 (declared but unused) — for a document whose
    inventory actually matches. Original spelling is preserved for output; only
    comparison goes through this.
    """
    return str(tag).strip().casefold()


def surface_key(text):
    """Canonical comparison key for a matching surface (term / otherForms).

    Glossaries are explicitly multilingual, so `.lower()` is not enough: it leaves
    German `Straße` and `STRASSE` as different surfaces, and treats canonically
    equivalent compositions of the same accented character as distinct. NFC first
    (so one code point and its decomposed form agree), then `casefold()`, which is
    the Unicode caseless-matching operation and does expand the sharp s.
    """
    return unicodedata.normalize("NFC", str(text).strip()).casefold()


def _entry_language_keys(entry):
    """Every language key a well-shaped entry uses, across all three map sites.

    Returns {canonical key -> an original spelling}, so membership comparisons are
    case-insensitive while messages can still quote what the author actually wrote.
    """
    keys = {}
    def record(raw):
        keys.setdefault(lang_key(raw), str(raw))
    for site in ("translations", "definitionTranslations"):
        value = entry.get(site)
        if isinstance(value, dict):
            for k in value:
                record(k)
    examples = entry.get("examples")
    if isinstance(examples, list):
        for example in examples:
            if isinstance(example, dict) and isinstance(example.get("translations"), dict):
                for k in example["translations"]:
                    record(k)
    return keys


def _lint_language_code(tag, warnings, where):
    """GW04: primary/region subtag membership lint. Shape errors are GE01/GE02's job."""
    if not LANG_KEY_RE.match(str(tag)):
        return  # malformed shape already reported as an error
    subtags = str(tag).split("-")
    primary = subtags[0].lower()
    if len(primary) == 2 and primary not in ISO_639_1:
        warnings.append(f"{where} '{tag}': primary subtag '{primary}' is not an "
                        "ISO 639-1 code")
    for subtag in subtags[1:]:
        if len(subtag) == 2 and subtag.isalpha() and \
                subtag.upper() not in ISO_3166_1_ALPHA2:
            warnings.append(f"{where} '{tag}': region subtag '{subtag}' is not an "
                            "ISO 3166-1 code")


def validate(doc):
    """Returns (errors, warnings). Errors gate the interchange boundary (exit 1);
    warnings are advisory (exit 0)."""
    errors, warnings = [], []

    # ---- GE01 envelope ----------------------------------------------------
    if doc.get("documentType") != "glossary":
        errors.append(f"documentType is '{doc.get('documentType')}', expected 'glossary'")
    for field in ("globalId", "version", "title", "language"):
        if not str(doc.get(field) or "").strip():
            errors.append(f"{field} is required")
    declared = doc.get("translationLanguages")
    # canonical key -> the spelling the author used, so comparisons are
    # case-insensitive (BCP 47 section 2.1.1) while messages quote the original.
    declared_set = {}
    if declared is not None:
        if not isinstance(declared, list) or any(
                not isinstance(v, str) or not v.strip() for v in declared):
            errors.append("translationLanguages must be an array of non-empty strings")
            declared = None
        else:
            for tag in declared:
                if not LANG_KEY_RE.match(tag):
                    errors.append(f"translationLanguages '{tag}' is not a language tag "
                                  "(use BCP 47, e.g. 'es', 'pt-BR')")
                key = lang_key(tag)
                if key in declared_set:
                    first = declared_set[key]
                    same = " " if first == tag else (
                        f" (as '{first}' and '{tag}' — language tags are "
                        "case-insensitive) ")
                    errors.append(f"translationLanguages lists '{tag}'{same}more "
                                  "than once")
                else:
                    declared_set[key] = tag
    entries = doc.get("entries")
    if not isinstance(entries, list):
        errors.append("entries must be an array")
        entries = []

    # ---- GE02/GE03 entries --------------------------------------------------
    seen_ids = set()
    # canonical surface key -> [entry ids]; and canonical lang key -> spelling
    surface_owners = {}
    used_languages = {}
    surface_spellings = {}  # canonical surface key -> the spelling first seen
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append("every entry must be an object")
            continue
        eid = str(entry.get("id") or "").strip()
        label = eid or (str(entry.get("term") or "?")[:30])
        if not eid:
            errors.append(f"entry '{label}' has no id (member identity is not optional)")
        elif eid in seen_ids:
            errors.append(f"duplicate entry id '{eid}'")
        else:
            seen_ids.add(eid)

        term = entry.get("term")
        if not isinstance(term, str) or not term.strip():
            errors.append(f"entry '{label}' has no term")
            term = ""

        kind = entry.get("kind")
        if kind is not None and kind not in ENTRY_KINDS:
            errors.append(f"entry '{label}' kind '{kind}' is not one of "
                          + "/".join(sorted(ENTRY_KINDS)))

        for field in ("partOfSpeech", "definition", "ipa", "soundsLike",
                      "audioUrl", "imageUrl", "firstMention"):
            value = entry.get(field)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                errors.append(f"entry '{label}' {field} must be a non-empty string or omitted")

        link_auto = entry.get("linkAutomatically")
        if link_auto is not None and not isinstance(link_auto, bool):
            errors.append(f"entry '{label}' linkAutomatically must be true or false")

        for field in ("otherForms", "tags"):
            value = entry.get(field)
            if value is None:
                continue
            if not isinstance(value, list) or any(
                    not isinstance(v, str) or not v.strip() for v in value):
                errors.append(f"entry '{label}' {field} must be an array of non-empty strings")

        examples = entry.get("examples")
        if examples is not None:
            if not isinstance(examples, list):
                errors.append(f"entry '{label}' examples must be an array")
            else:
                for example in examples:
                    if not isinstance(example, dict) or not str(
                            example.get("text") or "").strip():
                        errors.append(f"entry '{label}' examples entries must be "
                                      "objects with a non-empty text")
                    elif example.get("translations") is not None:
                        _check_translations(f"entry '{label}'", example["translations"],
                                            errors, "example translations")

        translations = entry.get("translations")
        if translations is not None:
            _check_translations(f"entry '{label}'", translations, errors, "translations")

        definition_translations = entry.get("definitionTranslations")
        if definition_translations is not None:
            _check_translations(f"entry '{label}'", definition_translations,
                                errors, "definitionTranslations")

        # GE03 — the gloss rule (interchange-boundary error; see docstring)
        has_definition = isinstance(entry.get("definition"), str) and entry["definition"].strip()
        has_translation = any(
            isinstance(site, dict) and any(
                isinstance(v, str) and v.strip() for v in site.values())
            for site in (translations, definition_translations))
        if not has_definition and not has_translation:
            errors.append(f"entry '{label}' needs a definition or at least one "
                          "translation (the gloss rule)")

        # GE04 bookkeeping + declared-membership check
        entry_langs = _entry_language_keys(entry)
        for key, spelling in entry_langs.items():
            used_languages.setdefault(key, spelling)
        if declared_set:
            for key in sorted(set(entry_langs) - set(declared_set)):
                spelling = entry_langs[key]
                if LANG_KEY_RE.match(spelling):
                    errors.append(
                        f"entry '{label}' uses translation language '{spelling}' which "
                        "is not declared in translationLanguages")

        # matching-surface bookkeeping for GW01/GW03
        forms = entry.get("otherForms") if isinstance(entry.get("otherForms"), list) else []
        if term.strip():
            key = surface_key(term)
            surface_spellings.setdefault(key, term.strip())
            surface_owners.setdefault(key, []).append(label)
            if any(isinstance(f, str) and surface_key(f) == key for f in forms):
                warnings.append(f"entry '{label}' otherForms repeats its own term")
        for form in forms:
            if isinstance(form, str) and form.strip():
                key = surface_key(form)
                surface_spellings.setdefault(key, form.strip())
                surface_owners.setdefault(key, []).append(label)

    # ---- GE05 declared-but-unused (a false claim is an error) ----------------
    for tag in sorted(declared_set[k] for k in set(declared_set) - set(used_languages)):
        errors.append(f"translationLanguages declares '{tag}' but no entry carries "
                      "a translation in it (declared, not implied — remove it or "
                      "translate something)")

    # ---- GW01 duplicate matching surfaces ----------------------------------
    # Cross-entry only: dedupe owners per surface first, so an entry whose term
    # also appears in its own otherForms is not counted as colliding with itself
    # (that intra-entry repeat is GW03's job, above).
    for surface, owners in sorted(surface_owners.items()):
        distinct_owners = sorted(set(owners))
        if len(distinct_owners) > 1:
            warnings.append(f"matching surface '{surface_spellings.get(surface, surface)}' appears on entries "
                            f"{', '.join(distinct_owners)} — auto-link will need disambiguation")

    # ---- GW02 missing declaration (a missing claim is a warning) ------------
    if used_languages and not declared_set:
        warnings.append(
            "entries carry translations ("
            + ", ".join(sorted(used_languages.values()))
            + ") but the document declares no translationLanguages")

    # ---- GW04 language-code lint --------------------------------------------
    lint_targets = (sorted(declared_set.values()) if declared_set
                    else sorted(used_languages.values()))
    lint_where = "translationLanguages" if declared_set else "translation key"
    for tag in lint_targets:
        _lint_language_code(tag, warnings, lint_where)

    return errors, warnings


# ---------------------------------------------------------------------------
# Maturity report
# ---------------------------------------------------------------------------

def maturity_report(doc):
    entries = [e for e in doc.get("entries", []) if isinstance(e, dict)]
    total = len(entries)
    lines = []
    if not total:
        return ["entries: 0 (empty glossary — valid, but nothing to study yet)"]
    by_kind = {}
    for e in entries:
        by_kind[e.get("kind") or "(unset)"] = by_kind.get(e.get("kind") or "(unset)", 0) + 1
    lines.append("entries: " + ", ".join(f"{k} {v}" for k, v in sorted(by_kind.items()))
                 + f" (total {total})")

    def pct(field):
        n = sum(1 for e in entries if str(e.get(field) or "").strip())
        return f"{n}/{total}"

    lines.append(f"with definition {pct('definition')}, ipa {pct('ipa')}, "
                 f"soundsLike {pct('soundsLike')}, audio {pct('audioUrl')}, "
                 f"image {pct('imageUrl')}")
    lines.append("with examples "
                 + f"{sum(1 for e in entries if e.get('examples'))}/{total}"
                 + f", firstMention {pct('firstMention')}")
    langs = {}
    for e in entries:
        for key in _entry_language_keys(e):
            langs[key] = langs.get(key, 0) + 1
    if langs:
        lines.append("translations: " + ", ".join(
            f"{k} {v}/{total}" for k, v in sorted(langs.items())))
    return lines


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate an LC-JSON glossary document")
    parser.add_argument("--validate", metavar="GLOSSARY_JSON", required=True)
    parser.add_argument("--domain-only", action="store_true",
                        help="run the domain rules without schema validation. NOT a "
                             "conformance check — reports DOMAIN-ONLY OK, never VALID")
    args = parser.parse_args(argv)

    full = _lcjson_schema.cli_preflight(args.domain_only, doctype="glossary")

    with open(args.validate, encoding="utf-8") as f:
        doc = json.load(f)

    schema_errors = []
    if full:
        schema_errors, unavailable = _lcjson_schema.schema_stage(doc, "glossary")
        if unavailable:
            _lcjson_schema.exit_unavailable_unless_definitive(
                schema_errors, unavailable)
    errors, warnings = validate(doc)
    errors = schema_errors + errors
    for warning in warnings:
        print(f"  WARNING: {warning}")
    if errors:
        print(f"INVALID — {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        return 1

    declared = doc.get("translationLanguages") or []
    verdict = "VALID" if full else "DOMAIN-ONLY OK (not a conformance check)"
    print(f"{verdict}: {doc.get('title')} ({doc.get('globalId')} v{doc.get('version')}, "
          f"language {doc.get('language')}"
          + (f", translations {'/'.join(declared)}" if declared else "")
          + ")")
    for line in maturity_report(doc):
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
