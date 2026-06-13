---
name: Bug report
about: Report a problem with a schema, the reference validator, the spec text, or a fixture
title: ""
labels: bug
assignees: ""
---

**Spec version**
<!-- e.g. 1.0-rc.2, 1.0 -->

**Bug class**
<!-- One of: schema / validator / spec text / fixture.
     "Schema doesn't enforce X", "validator crashes on Y", and
     "spec text is ambiguous about Z" are different bugs — naming
     the class routes the report to the right place. -->

**Reproduction**
<!-- The smallest LC-JSON document (or fragment) that shows the
     problem. Paste it here or attach a file. For spec-text bugs,
     quote the passage and link the section instead. -->

**Expected vs actual**
<!-- What the spec/schema/validator should do, and what it does. -->

**Validator output (if any)**
<!-- Output of `python tools/validate_course.py --course-path <file> --strict`
     or your JSON Schema validator's error. -->
