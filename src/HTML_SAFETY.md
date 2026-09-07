# LC-JSON HTML Safety Profile

**Status:** Normative. Referenced from [NORMATIVE.md](NORMATIVE.md) §11.
**Spec version:** 1.0
**Last updated:** 2026-05-03

This document defines the HTML subset that LC-JSON (Learning Content JSON) 1.0 documents MAY carry in HTML-bearing fields, the obligations consumers MUST satisfy when rendering it, and the URL-scheme allowlist for embedded references.

The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, **MAY**, and **RECOMMENDED** are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174).

---

## 1. Scope

### 1.1 HTML-bearing fields

HTML is permitted in the following fields:

| Field | Carrier | Schema reference |
|---|---|---|
| `html` | `ContentItem` | [`schemas/content-item.schema.json`](https://lc-json.org/1.1/content-item.schema.json) |
| `customHtml` | `SignpostItem` | [`schemas/signpost-item.schema.json`](https://lc-json.org/1.1/signpost-item.schema.json) |

No other LC-JSON 1.0 field carries HTML. Question prompts, hints, choice text, feedback strings, and similar author-visible prose are plain text. A producer MUST NOT embed HTML in plain-text fields; a consumer MUST treat HTML in plain-text fields as literal text.

### 1.2 Why this profile exists

Without a portable allowlist, every consumer would sanitize against its own subset, and the same document would render differently — sometimes unsafely — across implementations. This profile fixes the contract:

- Producers know what they MAY emit and have rendered consistently.
- Consumers know what they MUST accept, what they MUST sanitize away, and where the line falls between "render-time stripping" and "reject the document."
- Third-party implementers have a single reference for `<script>`, event handlers, `<iframe>`, `target="_blank"`, `data:` URLs, and the rest of the long tail.

The profile is deliberately strict-enough-to-be-safe, lenient-enough-to-author. Decisions throughout favor producer flexibility (any class, an inline-style allowlist that covers real authoring patterns, `tel:` for adult/corporate audiences) while binding consumer sanitization tightly enough that no conforming consumer can be coerced into XSS by a conforming document.

---

## 2. Allowed elements

A conforming consumer MUST render the following HTML elements when they appear in HTML-bearing fields, subject to the attribute allowlist in §3 and the URL-scheme allowlist in §4.

### 2.1 Block

`<p>`, `<div>`, `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, `<h6>`, `<ul>`, `<ol>`, `<li>`, `<blockquote>`, `<pre>`, `<hr>`, `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>`, `<figure>`, `<figcaption>`

### 2.2 Inline

`<a>`, `<strong>`, `<em>`, `<b>`, `<i>`, `<u>`, `<mark>`, `<small>`, `<sub>`, `<sup>`, `<code>`, `<br>`, `<span>`, `<abbr>`, `<q>`, `<time>`

### 2.3 Media

`<img>`, `<video>`, `<audio>`, `<source>`, `<track>`

### 2.4 Forbidden elements

The following elements MUST NOT be emitted by producers and MUST be stripped (along with their entire subtree) by consumers:

`<script>`, `<iframe>`, `<object>`, `<embed>`, `<form>`, `<input>`, `<button>`, `<select>`, `<textarea>`, `<style>`, `<link>`, `<meta>`, `<base>`, `<svg>`, `<math>`, `<applet>`, `<frame>`, `<frameset>`, `<noframes>`

`<svg>` and `<math>` are forbidden inline (the surface for XSS via SVG sanitization is wide and inconsistently understood across libraries). SVG raster equivalents are permitted via `<img src="...">` per §4.1; consumers SHOULD NOT inline-render the contents of an SVG fetched this way (the standard `<img>` rendering pipeline is sufficient and isolates script).

### 2.5 Unknown elements

When a consumer encounters an element name not listed in §2.1–§2.3 and not in the forbidden list of §2.4, the consumer MUST handle it per §6 (Unknown-element handling). Consumers MUST NOT reject a document on the basis of unknown elements alone.

---

## 3. Allowed attributes

### 3.1 Universal attributes

The following attributes MAY appear on every element listed in §2.1–§2.3:

| Attribute | Purpose | Notes |
|---|---|---|
| `id` | Anchor target | SHOULD be document-unique; consumers MAY rewrite to namespace within their UI |
| `class` | Author-defined CSS hooks | See §3.2 |
| `title` | Tooltip / accessible name | |
| `lang` | Language override (BCP 47) | |
| `dir` | Text direction (`ltr`, `rtl`, `auto`) | |

### 3.2 The `class` attribute

The `class` attribute is permitted on all allowed elements. Values are author-defined; the spec does not constrain or interpret them. Consumers MUST preserve the `class` attribute across read/write cycles (§6.4 round-trip preservation in NORMATIVE applies). Consumers MAY style classes they recognize; consumers MUST ignore (without stripping) classes they do not recognize.

This is intentional. Different consumers ship different stylesheets — `img-medium` matters to one consumer, `lc-callout` matters to another, generic Tailwind classes might appear in a third. The wire format does not arbitrate which class system wins; it preserves the author's intent and lets each consumer apply its own visual policy.

### 3.3 Per-element attribute table

In addition to the universal attributes, the following per-element attributes are allowed.

| Element | Attributes | URL-scheme constrained? |
|---|---|---|
| `<a>` | `href`, `target`, `rel` | `href` per §4.1 |
| `<img>` | `src`, `alt` (REQUIRED), `width`, `height` | `src` per §4.1 |
| `<video>` | `src`, `poster`, `controls`, `width`, `height`, `preload` | `src`, `poster` per §4.1 |
| `<audio>` | `src`, `controls`, `preload` | `src` per §4.1 |
| `<source>` | `src`, `type` | `src` per §4.1 |
| `<track>` | `src`, `kind`, `srclang`, `label`, `default` | `src` per §4.1 |
| `<table>` | `border` (`"1"` or absent only) | — |
| `<th>`, `<td>` | `colspan`, `rowspan`, `headers`, `scope` | — |
| `<ol>` | `start`, `reversed`, `type` | — |
| `<li>` | `value` | — |
| `<blockquote>` | `cite` | URL per §4.1 |
| `<q>` | `cite` | URL per §4.1 |
| `<abbr>` | (universal only) | — |
| `<time>` | `datetime` | — |

**`<img alt>` is REQUIRED.** Empty `alt=""` is permitted (and indicates a decorative image — see [`ACCESSIBILITY.md`](ACCESSIBILITY.md) §2). Producers MUST emit `alt`; consumers SHOULD treat a missing `alt` as a domain-validation warning and render the image.

### 3.4 Inline `style` attribute

The `style` attribute MAY appear on any element listed in §2.1–§2.3. Consumers MUST sanitize CSS properties against the allowlist below; properties outside the allowlist MUST be stripped (the property only — the element and other style properties are preserved).

**Allowed CSS properties:**

| Category | Properties |
|---|---|
| Sizing | `max-width`, `min-width`, `width`, `max-height`, `min-height`, `height` |
| Spacing | `margin`, `margin-top`, `margin-right`, `margin-bottom`, `margin-left`, `padding`, `padding-top`, `padding-right`, `padding-bottom`, `padding-left` |
| Borders | `border`, `border-top`, `border-right`, `border-bottom`, `border-left`, `border-collapse`, `border-spacing`, `border-style`, `border-width`, `border-color` |
| Alignment | `text-align`, `vertical-align` |

**Property values:**

- Lengths in `px`, `em`, `rem`, `%`, or unitless `0`. Negative values permitted where the property allows them. `vh`/`vw`/`vmin`/`vmax` MAY be permitted at consumer discretion; producers SHOULD NOT emit them.
- Color values for `border-color`: hex (`#abc`, `#aabbcc`), `rgb()`, `rgba()`, named CSS colors. `currentColor` permitted.
- `auto` is permitted for sizing properties.

Consumers MUST NOT execute CSS expressions, `url()` references to remote stylesheets, `@import` directives, or any value that resembles a JavaScript expression (`expression(...)`, `behavior:`, `-moz-binding`, etc.). Consumers MUST strip any value that doesn't lex as a simple length, color, or keyword token.

The narrow allowlist exists because authors need to size images, set table borders, and align cell content — pragmatic affordances that semantic markup alone doesn't cover. Anything beyond layout (colors, fonts, animations, positioning, transforms) is consumer-skin territory and belongs on a class hook (§3.2).

### 3.5 Forbidden attributes

The following attributes MUST NOT appear on any element. Consumers MUST strip them on render:

- All event handler attributes: any attribute matching `on*` (e.g., `onclick`, `onload`, `onmouseover`, `onerror`, `onfocus`, `onblur`).
- `srcdoc` (on any element).
- `formaction`, `formenctype`, `formmethod`, `formnovalidate`, `formtarget` (form submission attributes).

`data:` and other forbidden URL schemes are governed by §4.2; this section does not duplicate that rule.

---

## 4. URL scheme allowlist

### 4.1 Allowed schemes

For URL-bearing attributes (`href`, `src`, `poster`, `cite`, `<source>.src`, `<track>.src`):

| Scheme | Where allowed | Notes |
|---|---|---|
| `https:` | All URL-bearing attributes | Always allowed. |
| `http:` | All URL-bearing attributes | Allowed but discouraged. Mixed-content rendering on HTTPS pages is consumer-defined; consumers SHOULD warn or upgrade. |
| `mailto:` | `<a href>` only | Standard mail-link behavior. |
| `tel:` | `<a href>` only | See §7. Consumer policy varies by audience. |
| Relative URLs | All URL-bearing attributes | Resolved against the consumer's content base for the document. Producers MAY use relative paths to reference media bundled alongside the LC-JSON file (e.g., `media/images/foo.jpg`). |

### 4.2 Forbidden schemes

The following schemes MUST NOT appear in any URL-bearing attribute. Consumers MUST reject the URL (either by stripping the attribute or by replacing the attribute with a safe placeholder, e.g., `href="#"`):

`javascript:`, `vbscript:`, `data:`, `blob:`, `file:`, `chrome:`, `chrome-extension:`, `ftp:`, `ws:`, `wss:`, `gopher:`, `view-source:`

`data:` is forbidden globally — including for `<img src>`. The XSS surface (SVG-via-data, HTML-via-data, type-confusion attacks via mixed content sniffing) is wider than the authoring convenience justifies. Consumers MUST strip `data:` URIs even on `<img>`.

`blob:` and `file:` are forbidden because they reference consumer-local memory or filesystem state; their meaning is not portable.

### 4.3 URL validation

Consumers SHOULD validate URLs against [RFC 3986](https://www.rfc-editor.org/rfc/rfc3986) before rendering. Malformed URLs (whitespace in the middle, control characters, embedded null bytes) MUST be treated as invalid and stripped.

---

## 5. Sanitization obligation

A consumer MUST sanitize HTML from LC-JSON documents before rendering. The HTML in an LC-JSON document is untrusted input from the consumer's perspective, regardless of the document source.

A producer's claim of LC-JSON conformance does NOT exempt the consumer from sanitization. Producers can be misconfigured, compromised, or simply buggy; consumers stand alone as the last line of defense.

### 5.1 Sanitization rules summary

A conforming consumer MUST:

- Strip every element not listed in §2.1–§2.3, preserving its inner text content per §6.
- Strip every attribute not listed in §3, preserving the element.
- Strip every event handler attribute (`on*`).
- Strip every URL with a scheme outside §4.1.
- Strip every CSS property in inline `style` outside the §3.4 allowlist.
- Normalize `<a target="_blank">` to include `rel="noopener noreferrer"` per §6.1, even when the producer omitted it.
- Reject the entire document if it contains any element from the §2.4 forbidden list (`<script>`, `<iframe>`, etc.) **or** any `on*` event-handler attribute **or** any `javascript:` / `vbscript:` URL. See §8 for validator severity.

### 5.2 Reference implementations (informative)

The following sanitizer configurations are known to align with this profile:

- [DOMPurify](https://github.com/cure53/DOMPurify) (JavaScript) — configure `ALLOWED_TAGS` and `ALLOWED_ATTR` from §2.1–§2.3 and §3.
- [Bleach](https://github.com/mozilla/bleach) (Python) — `bleach.clean(text, tags=..., attributes=..., protocols=['http','https','mailto','tel'])`.
- [HtmlSanitizer](https://github.com/mganss/HtmlSanitizer) (.NET) — equivalent allowlist configuration.

These are reference points only. Conformance is judged against the rules in this document, not against any specific library's defaults.

---

## 6. Link safety, link normalization, and unknown-element handling

### 6.1 `target="_blank"` rel-normalization

A producer that emits `<a target="_blank">` SHOULD also emit `rel="noopener noreferrer"`.

A consumer MUST normalize `<a target="_blank">` to include `rel="noopener noreferrer"` on render, adding the tokens if the producer omitted them. This applies even to documents that otherwise satisfy producer conformance — the consumer has the last word on render.

The reverse-tabnabbing risk that this mitigates is well-documented; the cost of producing `rel="noopener noreferrer"` is zero. Producers SHOULD save consumers the work, but consumers cannot rely on producers to do so.

### 6.2 Unknown-element handling

When a consumer encounters an HTML element whose name is not in §2.1–§2.3 and not in the §2.4 forbidden list, the consumer:

- **MUST** strip the element while preserving its text content. `<unknown>hello world</unknown>` becomes `hello world`.
- **SHOULD** log a warning (form is consumer-defined).
- **MUST NOT** reject the document for unknown elements alone. Forward-compatibility for HTML extensions is preserved by graceful degradation, not by strict rejection.

This mirrors NORMATIVE §6's handling of reserved/unknown question types: degrade gracefully, never fail-closed on names you don't recognize. The contract is symmetrical across both surfaces.

### 6.3 Unknown-attribute handling

When a consumer encounters an attribute not listed in §3, the consumer MUST strip the attribute while preserving the element. Unknown attributes are not grounds for rejecting the document.

### 6.4 Unknown CSS properties

When a consumer encounters a CSS property in `style="..."` not listed in §3.4, the consumer MUST strip the property while preserving the element and the other (allowed) properties. Unknown properties are not grounds for rejecting the document.

---

## 7. Media handling

### 7.1 `<video>`

- `src` MUST be `https:`, `http:`, or relative.
- Consumers MUST NOT auto-play. Producers MUST NOT emit `autoplay` or `loop`. Consumers SHOULD ignore these attributes if a non-conforming producer emits them.
- `controls` SHOULD be present (consumer policy MAY hide them, but the wire intent is "user-driven playback").
- Inner `<source>` elements MAY appear; consumers MUST process them per the same URL-scheme allowlist (§4.1).
- Inner `<track>` elements with `kind="captions"` or `kind="subtitles"` SHOULD be present for video content. Accessibility requirements for captions are codified separately in [`ACCESSIBILITY.md`](ACCESSIBILITY.md) §3.
- `poster` URL MUST satisfy §4.1.

### 7.2 `<audio>`

- `src` MUST be `https:`, `http:`, or relative.
- Consumers MUST NOT auto-play. Producers MUST NOT emit `autoplay` or `loop`.
- `controls` SHOULD be present.
- Inner `<source>` elements MAY appear.

### 7.3 Bandwidth and preload

`preload` accepts `"none"`, `"metadata"`, `"auto"`. Consumers SHOULD respect the producer's `preload` hint but MAY override for bandwidth, storage, or accessibility reasons.

### 7.4 Format compatibility

LC-JSON does not mandate specific media codecs. Producers SHOULD use widely-compatible formats (H.264 + AAC in MP4 for video; MP3, AAC, or Opus for audio) and SHOULD provide multiple `<source>` fallbacks where format compatibility matters.

### 7.5 `<track>` for captions and subtitles

`<track src>` MUST satisfy §4.1. `kind` accepts `"subtitles"`, `"captions"`, `"descriptions"`, `"chapters"`, `"metadata"`. `srclang` is a BCP 47 language tag (RECOMMENDED for `subtitles` and `captions`).

---

## 8. Validator severity

A reference validator (or any consumer's pre-render validation pass) SHOULD classify HTML profile violations as follows.

### 8.1 Errors (validator MUST reject)

These violations indicate a security-critical XSS surface or a structural violation that no consumer can render safely:

- Any forbidden element listed in §2.4.
- Any event handler attribute (`onclick`, `onload`, `onmouseover`, etc.).
- Any URL with scheme `javascript:` or `vbscript:`.

### 8.2 Warnings (validator MAY accept; consumer SHOULD strip)

These violations are sanitizable and not security-critical. The validator reports them so producers can fix their output, but the document is still useful:

- Unknown elements (per §2.5, §6.2).
- Unknown attributes (per §3.5, §6.3).
- CSS properties outside the §3.4 allowlist (per §6.4).
- URL schemes outside §4.1 but not listed in §4.2 (rare; mostly relative-URL edge cases).
- `tel:` URLs (per §7 — consumer-policy gated; some audiences disable them).
- Missing `rel="noopener noreferrer"` on `<a target="_blank">` (per §6.1 — consumer auto-normalizes).
- Missing `alt` on `<img>` (cross-references [`ACCESSIBILITY.md`](ACCESSIBILITY.md) §2).
- `data:` URLs (forbidden per §4.2, but a warning rather than an error because the consumer-side mitigation — strip the `data:` URL before rendering — degrades gracefully to a broken image, not an XSS surface. The forbidden-scheme rule still binds; the validator severity choice is "tell the author the image won't render anywhere," not "reject this otherwise-fine document.")

### 8.3 Why this split

Errors fail the build. Warnings notify the author but don't break interop. The line between them is "could a consumer render this document safely if it tried?" — yes for warnings, no for errors. Producers SHOULD treat warnings as actionable; consumers MUST sanitize regardless.

---

## 9. Round-trip preservation

NORMATIVE §6.4 requires consumers to preserve every member of reserved-type questions across read/write cycles (semantic preservation; key order is producer-discretion per §6.2). The same principle applies to HTML content with one important softening: a consumer that re-exports an LC-JSON document MAY emit the *sanitized* HTML rather than the input HTML, provided that:

- No allowed elements, attributes, or CSS properties (per §2 and §3) are lost.
- Element classes (per §3.2) are preserved verbatim.
- Authored text content is preserved.
- Semantic structure (heading levels, list nesting, table rows/cells) is preserved.

In other words: consumers MAY drop content the spec requires them to strip anyway (`<script>`, `onclick`, `data:` URLs). Consumers MUST NOT drop content they're not required to strip. This protects authors from silent edit-on-import without forcing consumers to round-trip security-critical violations.

A consumer that imports a document containing forbidden content under §8.1 MUST report the violation to the user; the consumer MAY refuse to round-trip such a document at all.

---

## 10. Examples

### 10.1 Minimal conforming HTML

```json
{
  "type": "content",
  "globalId": "...",
  "title": "Reading",
  "html": "<h2>Section 1</h2>\n<p>Some text with <strong>emphasis</strong> and <a href=\"https://example.org\">a link</a>.</p>"
}
```

### 10.2 Image with class hook

```json
{
  "html": "<p>The diagram below shows the cycle:</p>\n<img src=\"media/cycle.png\" alt=\"Carbon cycle diagram\" class=\"img-medium\" />"
}
```

### 10.3 Video with captions

```json
{
  "html": "<video src=\"media/lecture.mp4\" controls poster=\"media/lecture-thumb.jpg\" preload=\"metadata\" width=\"640\">\n  <track src=\"media/lecture.vtt\" kind=\"captions\" srclang=\"en\" label=\"English\" default />\n</video>"
}
```

### 10.4 Table with allowed inline styles

```json
{
  "html": "<table border=\"1\" style=\"border-collapse: collapse; width: 100%;\">\n  <thead>\n    <tr><th style=\"padding: 8px; text-align: left;\">Country</th><th style=\"padding: 8px;\">Capital</th></tr>\n  </thead>\n  <tbody>\n    <tr><td style=\"padding: 8px;\">France</td><td style=\"padding: 8px;\">Paris</td></tr>\n  </tbody>\n</table>"
}
```

### 10.5 Link with `target="_blank"` and `rel`

```json
{
  "html": "<p>Read more on <a href=\"https://en.wikipedia.org/wiki/Photosynthesis\" target=\"_blank\" rel=\"noopener noreferrer\">Wikipedia</a>.</p>"
}
```

### 10.6 What to avoid

```html
<!-- ✗ <script> is forbidden — validator MUST reject -->
<script>alert("hi")</script>

<!-- ✗ event handler — validator MUST reject -->
<a href="https://example.com" onclick="track()">click</a>

<!-- ✗ javascript: URL — validator MUST reject -->
<a href="javascript:void(0)">click</a>

<!-- ✗ data: URL — consumer strips, validator warns -->
<img src="data:image/png;base64,..." alt="..." />

<!-- ✗ inline-rendered SVG — element forbidden -->
<svg><circle cx="50" cy="50" r="40" /></svg>

<!-- ✓ SVG raster reference is fine -->
<img src="https://example.org/logo.svg" alt="Example logo" />
```

---

## 11. Cross-references

- [`NORMATIVE.md`](NORMATIVE.md) §11 — normative reference to this document
- [`ITEM_PATTERNS.md`](ITEM_PATTERNS.md) §3 — `tel:` consumer policy as one example of consumer plurality
- [`schemas/content-item.schema.json`](https://lc-json.org/1.1/content-item.schema.json) — `html` field
- [`schemas/signpost-item.schema.json`](https://lc-json.org/1.1/signpost-item.schema.json) — `customHtml` field
- [`ACCESSIBILITY.md`](ACCESSIBILITY.md) — `alt`, captions, keyboard alternatives, language/direction, placeholder accessibility for reserved types, WCAG 2.1 AA cross-references, recommended ARIA patterns (rc.1 release; additive deepenings — per-criterion normative table, expanded ARIA patterns, conformance fixtures — land in 1.0 final)
- [`tests/`](tests/) — conformance fixtures including `valid/06-html-with-video-track.json` and `invalid/13-html-with-script.json`

---

## 12. Summary table

| Category | Producer MUST | Producer SHOULD | Consumer MUST | Consumer SHOULD |
|---|---|---|---|---|
| Allowed elements | Stay within §2.1–§2.3 | Use semantic markup | Render allowed elements; strip forbidden (§2.4); strip-while-preserving-text for unknown (§6.2) | Log warnings on unknown |
| Forbidden elements | Not emit `<script>`, `<iframe>`, `<form>`, etc. | — | Reject document if forbidden present (§8.1) | Surface error to user |
| Attributes | Stay within §3 | Use semantic attributes | Strip unknown attributes (§6.3); strip event handlers always | — |
| Inline `style` | Stay within §3.4 allowlist | Prefer class hooks | Strip out-of-allowlist properties (§6.4) | — |
| URL schemes | Use `https:`, `http:`, `mailto:`, `tel:`, or relative | Prefer `https:` | Reject `javascript:`/`vbscript:`; strip `data:`/`blob:`/`file:`/etc. | Warn on `http:`, `tel:` |
| `target="_blank"` | Emit `rel="noopener noreferrer"` | — | Normalize to add `rel="noopener noreferrer"` if missing (§6.1) | — |
| `<img alt>` | Emit `alt` | Use empty `alt=""` for decorative | — | Treat missing `alt` as warning |
| `<video>`, `<audio>` autoplay | Not emit `autoplay`, `loop` | — | Not auto-play | Ignore `autoplay` if a non-conforming producer emits it |
| Sanitization | — | — | Sanitize before render, every time | Use a vetted reference implementation (§5.2) |
