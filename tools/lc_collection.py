#!/usr/bin/env python3
"""
lc_collection.py - Reference library and validator for LC-JSON subjectCollection documents.

This validator implements the subjectCollection rules in the LC-JSON
specification (see VALIDATION.md §15, rule ids SC-1…SC-14). Identity rules:
  - every member carries a stable, immutable `id` (mint once, never re-mint);
  - `slug`/`name`/`label` are display, never identity;
  - documents MUST be self-contained (closure): categories cover every tag's
    categoryId; every objective tagId resolves within the document;
  - generated JSON carries no comments (strict parsers).

Usage:
    python lc_collection.py --validate path/to/collection.json
"""

import argparse
import json
import sys
import uuid

import _lcjson_schema


DIFFICULTY_BANDS = {"Recall", "Understand", "Apply", "Analyze", None}

# Typed alignment claims recognized by the subjectCollection artifact type.
# "assesses"/"verifiedBy" are reserved for a future revision and rejected here.
ALIGNMENT_CLAIMS = {"references", "alignedTo", "covers"}


def new_document(global_id, title, subject_id, subject_label, version="1.0.0",
                 license_="unspecified", description=None):
    return {
        "$schema": "https://lc-json.org/1.1-rc.1/subject-collection.schema.json",
        "documentType": "subjectCollection",
        "specVersion": "1.1",
        "globalId": global_id,
        "version": version,
        "title": title,
        "description": description,
        "scope": {
            "subject": {"scheme": None, "id": subject_id, "label": subject_label},
            "level": None,
            "audience": [],
            "purpose": [],
            "jurisdiction": None,
        },
        "license": license_,
        "authors": [],
        "canonicalUrl": None,
        "derivedFrom": [],
        "externalAlignments": [],
        "categories": [],
        "tags": [],
        "objectives": [],
    }


def category(cat_id, name, sort_order=0, description=None, icon=None):
    return {"id": cat_id, "name": name, "description": description,
            "sortOrder": sort_order, "icon": icon}


def tag(member_id, slug, name, category_id, parent_id=None, level=0,
        sort_order=0, description=None, aliases=None, color=None, icon=None,
        is_active=True):
    return {"id": member_id, "slug": slug, "name": name, "description": description,
            "categoryId": category_id, "parentId": parent_id, "level": level,
            "sortOrder": sort_order, "aliases": aliases, "color": color,
            "icon": icon, "isActive": is_active}


def objective(member_id, text, band=None, tag_ids=None):
    return {"id": member_id, "text": text, "difficultyBand": band,
            "tagIds": list(tag_ids or [])}


def alignment(claim, scheme, external_id, label=None):
    """Typed alignment claim against an external scheme — the external
    registry is referenced, never re-implemented."""
    return {"claim": claim, "scheme": scheme, "id": external_id, "label": label}


class IdMap:
    """Mint-once member-id registry: the map file SHOULD be retained so
    regenerating a collection keeps ids for members that persist."""

    def __init__(self, path):
        self.path = path
        try:
            with open(path, encoding="utf-8") as f:
                self.ids = json.load(f)
        except FileNotFoundError:
            self.ids = {}
        self._dirty = False

    def id_for(self, stable_key):
        if stable_key not in self.ids:
            self.ids[stable_key] = str(uuid.uuid4())
            self._dirty = True
        return self.ids[stable_key]

    def save(self):
        if self._dirty:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.ids, f, indent=2, sort_keys=True, ensure_ascii=False)
                f.write("\n")


def validate(doc):
    """Returns a list of problems; empty list = valid."""
    problems = []

    if doc.get("documentType") != "subjectCollection":
        problems.append(f"documentType is '{doc.get('documentType')}', expected 'subjectCollection'")
    if not doc.get("globalId"):
        problems.append("globalId is required (portable identity)")
    if not (doc.get("scope") or {}).get("subject", {}).get("id"):
        problems.append("scope.subject.id is required")

    category_ids = set()
    for cat in doc.get("categories", []):
        if not cat.get("id"):
            problems.append("a category has no id")
        elif cat["id"] in category_ids:
            problems.append(f"duplicate category id '{cat['id']}'")
        else:
            category_ids.add(cat["id"])

    tag_ids, slugs = set(), set()
    for t in doc.get("tags", []):
        label = t.get("slug") or t.get("name") or "?"
        if not t.get("id"):
            problems.append(f"tag '{label}' has no member id (identity is not optional)")
            continue
        if t["id"] in tag_ids:
            problems.append(f"duplicate tag member id '{t['id']}'")
        tag_ids.add(t["id"])
        if not t.get("slug"):
            problems.append(f"tag '{t['id']}' has no slug")
        elif t["slug"] in slugs:
            problems.append(f"duplicate slug '{t['slug']}'")
        else:
            slugs.add(t["slug"])
        if t.get("categoryId") not in category_ids:
            problems.append(f"tag '{label}' references category '{t.get('categoryId')}' "
                            "not carried in categories[] (closure)")
        if t.get("aliases") is not None and not isinstance(t["aliases"], list):
            problems.append(f"tag '{label}' aliases must be an array or null, "
                            f"got {type(t['aliases']).__name__}")

    parent_of = {}
    for t in doc.get("tags", []):
        if t.get("parentId") and t["parentId"] not in tag_ids:
            problems.append(f"tag '{t.get('slug')}' parentId '{t['parentId']}' is not a member id "
                            "(parents are member ids, never slugs)")
        elif t.get("parentId"):
            parent_of[t["id"]] = t["parentId"]

    # SC-7 acyclicity: the parent relation MUST form a hierarchy (a forest),
    # so no tag may be its own ancestor. Walk each tag's parent chain and flag
    # the first repeat — this catches self-parenting and longer cycles alike.
    for start in list(parent_of):
        seen, cur = set(), start
        while cur in parent_of:
            if cur in seen:
                problems.append(f"tag member id '{cur}' is part of a parentId cycle "
                                "(a tag may not be its own ancestor)")
                break
            seen.add(cur)
            cur = parent_of[cur]

    for a in doc.get("externalAlignments", []):
        if a.get("claim") not in ALIGNMENT_CLAIMS:
            problems.append(f"externalAlignment claim '{a.get('claim')}' is not a recognized claim "
                            f"({'/'.join(sorted(ALIGNMENT_CLAIMS))}; assesses/verifiedBy are reserved)")
        if not a.get("scheme") or not a.get("id"):
            problems.append(f"externalAlignment '{a.get('label') or a.get('id') or '?'}' "
                            "needs both scheme and id")

    obj_ids = set()
    for o in doc.get("objectives", []):
        text = (o.get("text") or "?")[:40]
        if not o.get("id"):
            problems.append(f'objective "{text}" has no member id')
            continue
        if o["id"] in obj_ids:
            problems.append(f"duplicate objective member id '{o['id']}'")
        obj_ids.add(o["id"])
        if o.get("difficultyBand") not in DIFFICULTY_BANDS:
            problems.append(f'objective "{text}" has invalid difficultyBand \'{o.get("difficultyBand")}\'')
        for tid in o.get("tagIds", []):
            if tid not in tag_ids:
                problems.append(f'objective "{text}" links tagId \'{tid}\' not in tags[] (closure)')

    return problems


def save(doc, path):
    # The emission gate, not validate() alone: a writer must not emit a document
    # that passes the domain rules but fails its schema or declares the wrong
    # canonical $schema.
    problems = _lcjson_schema.validate_for_emission(doc)
    if problems:
        raise ValueError("Collection is not valid:\n  " + "\n  ".join(problems))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--validate", metavar="FILE", help="validate a collection document")
    parser.add_argument("--domain-only", action="store_true",
                        help="run the domain rules without schema validation. NOT a "
                             "conformance check — reports DOMAIN-ONLY OK, never VALID")
    args = parser.parse_args()

    if args.validate:
        # Exits EXIT_VALIDATION_UNAVAILABLE if the schema pass cannot run and
        # --domain-only was not given, so a schema-invalid document can never
        # reach exit 0.
        full = _lcjson_schema.cli_preflight(args.domain_only,
                                           doctype="subjectCollection")
        with open(args.validate, encoding="utf-8") as f:
            doc = json.load(f)
        schema_errors = []
        if full:
            schema_errors, unavailable = _lcjson_schema.schema_stage(
                doc, "subjectCollection")
            if unavailable:
                _lcjson_schema.exit_unavailable(unavailable)
        problems = schema_errors + validate(doc)
        if problems:
            print(f"INVALID — {len(problems)} problem(s):")
            for p in problems:
                print(f"  - {p}")
            sys.exit(1)
        verdict = "VALID" if full else "DOMAIN-ONLY OK (not a conformance check)"
        print(f"{verdict}: {doc['title']} ({doc['globalId']} v{doc['version']}) — "
              f"{len(doc.get('categories', []))} categories, {len(doc.get('tags', []))} tags, "
              f"{len(doc.get('objectives', []))} objectives")
        sys.exit(0)

    parser.print_help()


if __name__ == "__main__":
    main()
