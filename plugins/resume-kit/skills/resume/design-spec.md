# design-spec.md: the measured geometry behind this renderer

Page geometry, colour, and type scale in §1-§5 are physical measurements
taken from a rendered PDF's own content streams and word positions, so they
are independent of which renderer draws them. §6 documents where Typst's own
box model needed different numbers than that "true" measurement, found by
iterating `components.typ` against the rendered page.

An earlier implementation of this same design, in HTML/CSS through headless
Chrome, is referred to below as the retired HTML pipeline. It is gone, but it
is worth naming in a few places: several numbers here exist specifically
because Chrome needed a compensation that Typst does not, or the reverse.

**You should not need to re-measure anything.** If you change the design,
change it here and in `template.typ`/`components.typ` together, and update
the snapshot baseline (§7) in the same commit.

---

## 1. Page

| Property | Value |
|---|---|
| Page size | A4, `595.28 x 841.89pt` |
| Left margin | `42pt` |
| Left column text right edge | `margin-left + col-width` (see §6 for `col-width`) |
| Navy sidebar left edge | `403.28pt` |
| Navy sidebar width | `193pt` (bleeds past the 595.28pt page edge) |
| Sidebar text left edge | `437.28pt` → padding-left `34pt` |

The navy band is **full bleed**: `sidebar-band()` in `components.typ` paints
it via `place()` at the true page edge, sized to the full page height,
independent of `page(margin: ...)`. It repeats on every page automatically
(Typst re-evaluates the page `background` for each page in the flow), with no
equivalent of the HTML pipeline's repeating-`<thead>` trick required. See §6
point 1.

## 2. Colour

| Role | Hex |
|---|---|
| Navy sidebar | `#082A4D` |
| Body text, headings | `#0D111A` |
| Date lines | `#959BA6` |
| Name | `#000000` |
| Sidebar text | `#FFFFFF` |

## 3. Type

Two families, copied into this skill's own `fonts/` so a build never depends
on what the host has installed:

* **Oswald Medium** (500): name, section headings, sidebar headings
* **Lato** Regular (400) + Bold (700): everything else

| Element | Font | Size | Notes |
|---|---|---|---|
| Name | Oswald Medium | 22pt | |
| Subtitle | Lato Regular | 6pt | uppercase, no letter-spacing (see §7e) |
| Section headings | Oswald Medium | 14pt | Professional Summary / Employment History / Education |
| Body + bullets | Lato Regular | 9pt | line pitch `12.825pt` (see §6 point 2) |
| Job title / degree | Lato **Bold** | 10pt | |
| Date lines / year | Lato Regular | 6pt | uppercase, no letter-spacing (see §7e), `#959BA6` |
| Sidebar headings | Oswald Medium | 9pt | |
| Sidebar items | Lato Regular | 8pt | pure white |

Bullets: glyph `•` (U+2022) at `x=55pt`, text at `x=64pt` (13pt / 22pt from
the 42pt margin). See §6 point 3 for how Typst's `list()` reaches that x
position.

**The separator in a date range is a plain hyphen**, `geo.date-sep` in
`components.typ`: "JUN 2025 - PRESENT". The design this template was measured
against used an em dash (U+2014); this renderer emits no em or en dashes at
all, in date lines or anywhere else. A word separator ("to") was tried first
and rejected: it changes the rendered width of every date line, which is a
type decision rather than a punctuation one.

## 4. Sidebar rhythm

`sidebar-top` (the Details heading's ink-top) and the per-block
`(heading→item, item→item, item→next-heading)` triple are in
`components.typ`'s `geo.sidebar-top` / `geo.sb-rhythm`. All of it was
calibrated against a real rendered resume with populated, multi-item Skills
(8 items) and Hobbies (5 items) blocks (see §7a); the values are measured,
not placeholders, for every block that content exercised.

* `gap-edu-edu` (the gap between a later education entry and the one before
  it) is still a placeholder, copied from `gap-bullets-job`'s calibrated
  value (`15.73pt`), because no content calibrated against has had two or
  more education entries to isolate its own true value. It is a *guess that
  reuses a job-specific number*, not a measurement of education-specific
  rhythm. Recalibrate it the next time a two-or-more-entry education list is
  built, and regenerate the §7 baseline with it.
* **`edu-entry` pagination gap:** the same theoretical heading-to-content
  page-break gap `job-entry` had (a degree/school heading could in
  principle get stranded from its year line). Fixed the same way
  `job-entry` was: `edu-entry` merges the degree/school heading and its
  year line into one `block(breakable: false)` unit.

## 5. Content source

Whichever content file is passed at build time. This skill owns no content of
its own: the only YAML it ships is `examples/sample-resume.yaml`, which is a
layout fixture for the test in §7 and not a resume anybody should send.

## 6. Where Typst's box model deviates from the measured numbers, and why

Typst has none of Chrome's print-CSS bugs (no margin-clipping bug, no
sub-pixel `@page size` rounding, no CSS `line-height` px-rounding), so the
HTML pipeline's four Chrome compensations do not apply here. Typst has
different quirks of its own, found by iterating `components.typ` and
measuring the resulting page:

1. **No margin-0/spacer-table workaround needed.** `place()` positions
   relative to the true page edge regardless of `page(margin: ...)`, and
   Typst re-paints a `page(background: ...)` on every page in the flow
   automatically. The HTML pipeline's `@page margin: 0` + `.frame`
   `<thead>`/`<tfoot>` spacer-table hack (working around Chrome clipping all
   painting to the page area) has no Typst equivalent to reproduce.

2. **Column width is `336.3pt`, not the measured `329.28pt`.** Like
   Chrome's Lato, Typst's own text shaping wraps one word early at the true
   width. Every line matched against real content (see §7a) reproduces its
   target break anywhere in `[336.15, 336.5]pt`, a plateau almost identical
   to the HTML version's own `[335, 338]pt` one, landing on nearly the same
   number for an unrelated reason (independent text-shaping engines
   converging on the same font file's metrics). `336.3pt` is the middle.

3. **`list()`'s `body-indent` is measured from the marker's own right edge,
   not from the paragraph left.** CSS's `padding-left: 22pt` on `.bullets li`
   is a single absolute offset from the text box. Typst's `body-indent`
   parameter stacks on top of the marker's own rendered width (`•` at 9pt
   Lato is ~5.22pt wide), so `bullet-body-indent` is set to `3.78pt`
   (`22 - 13 - 5.22`), not `9pt` (`22 - 13`), to land text at the same
   `x=64pt`.

4. **`par.leading` is added on top of the font's own natural line height,
   not the total pitch.** CSS `line-height: 12.825pt` *is* the total
   baseline-to-baseline distance. Typst's `par.leading` is extra space added
   on top of Lato 9pt's own natural single-line metric, empirically
   `6.448pt` at this font/size, found by rendering two different `leading`
   values, measuring the resulting on-page pitch for each, and solving the
   resulting linear relationship. `body-line-const` in `components.typ`
   holds that `6.448pt`; every place body-leading is set uses
   `body-leading - body-line-const`, not `body-leading` directly.

5. **Every block-level gap needed re-measuring, not just line-height.**
   Typst's default block/paragraph spacing (roughly `1.2em`, scaled to
   whichever text size is locally active) stacks on top of every explicit
   `v()` gap unless zeroed. `template.typ` sets `block(spacing: 0pt)` /
   `par(spacing: 0pt)` globally so `v()` is the only source of vertical
   rhythm, matching the pattern `bullet-list` already used locally for its
   own list par. Once that was zeroed, every main-column gap
   (`gap-name-subtitle` through `gap-edu-year`) and the sidebar's
   heading→item gap needed its own correction, found the same way as
   `body-line-const`: the retired HTML pipeline's tuned CSS custom properties
   (its `:root` block) were the starting hypothesis for the main column (the
   best available approximation of the true rhythm, since Typst has no
   "true" measurement of its own, see the values and the CSS source in
   `components.typ`'s comments), then each was corrected against the
   position measured in the rendered page. A page's first line also sits
   above its own nominal box top by a roughly constant amount that differs
   by which text starts the page: `7.95pt` for the 22pt Oswald name (page 1)
   vs `2.06pt` for 9pt Lato body text (later pages, which open mid-bullet).
   `margin-top` (`46.06pt`) is calibrated for the body-text case since it
   applies to every page; `pad-top` (`5.89pt`) adds the extra space the name
   specifically needs, once, before it, the same split the retired HTML
   pipeline made for the analogous Chrome quirk (`--pad-top` on top of a
   `42.88pt` spacer).

6. **A bullet's own gap to the next bullet isn't free.** Each bullet is
   wrapped in its own single-item `list()` (so `block(breakable: false)`
   can keep a bullet from splitting across a page break, per §6a below).
   Typst's `list.spacing` parameter governs the gap *within* one `list()`
   between its items, so it has no effect between two separate `list()`
   instances stacked in the flow. `gap-bullet-bullet` (`6.4pt`) inserts
   that gap explicitly between bullets in `bullet-list`.

7. **YAML parses a bare `year: 2015` as an integer, not a string.**
   Discovered the first time a real `education` entry was built (previously
   always `education: []`, so `edu-entry()` had never been exercised):
   Typst's `upper()` requires a string and throws on an integer. `edu-entry`
   now does `str(edu.at("year", default: ""))` before comparing/uppercasing
   it. The retired HTML pipeline's Python/Jinja2 templating never hit this
   because Python coerces both types the same way when interpolated into a
   template string.

8. **A wrapped `edu-entry` degree/school line needs explicit `par.leading`.**
   Typst's default paragraph leading (~`0.65em`) produced a `13.73pt` wrap
   pitch for a two-line degree name; the reference measures `14.25pt`
   (§4). Set explicitly to `7.02pt` (found the same way as
   `body-line-const` in point 4: solve the linear relationship between a
   changed `leading` value and the resulting on-page pitch) rather than
   left at the Typst default.

## 6a. Pagination rules

| Rule | `components.typ` / `template.typ` mechanism |
|---|---|
| A bullet is never split across a page break | each bullet is its own `block(breakable: false, list(item))` via `bullet-item()` |
| A job heading keeps its first bullet | `job-entry()` merges heading (title+date) and first bullet into one `block(breakable: false)` unit; remaining bullets (2+) still render through normal breakable `bullet-list` |
| A job is allowed to split between two bullets | heading + first bullet is non-breakable, but bullets 2+ are independent blocks and may break across pages |
| An education heading keeps its year line | `edu-entry()` merges degree/school and its year line into one `block(breakable: false)` unit, mirroring `job-entry()`'s fix |

Verified with a synthetic stress fixture (every job's bullets tripled, to
force multiple page breaks): every page break falls between two bullets,
no job or education heading is ever stranded from what must follow it, and
the sidebar band stayed full-bleed on every page. Re-run that check after any
change to `bullet-item`, `job-entry`, or `edu-entry`: copy a content file,
triple every job's bullet list in the copy, build it, and read every page
break in the result. It is a manual check, deliberately: it asks whether a
page break lands somewhere a reader would forgive, which is not a question
the snapshot test in §7 can answer.

## 7. The snapshot test

`tools/check-fidelity.sh` is the only check in this kit that looks at the
rendered page rather than the source. Run it after any change to
`template.typ` or `components.typ`; it exits non-zero on any deviation.

| Piece | Path |
|---|---|
| Fixture | `examples/sample-resume.yaml` |
| Baseline | `examples/sample-resume.baseline.json` |
| Check | `tools/check-fidelity.sh` |
| Comparison | `tools/snapshot.py` |

It is a **self-snapshot**, not a comparison against another renderer's
output. `check-fidelity.sh` renders the fixture through `bin/build` into a
temporary directory, extracts every line's page, column, x and y with
`pdftotext -bbox`, and compares that list elementwise against the committed
baseline: same number of lines, same text on the same page in the same
column in the same order, and every line within `TOL = 1.0pt` of where it
was in both x and y.

Elementwise is the point. Both sides come from the same renderer on the same
content, sorted the same way, so line N of one is line N of the other and
there is no need to find a line by its text. Matching by text answers the
weaker question "does this line exist somewhere in the document", which a
page overflow, a whole column shifting sideways, and a stray extra line all
survive. Nothing in the check is a hand-maintained constant that can drift
out of agreement with reality: the baseline's own contents are the
expectation.

**`TOL = 1.0pt` is a floor, not a dial.** Never raise it to quiet a
difference between hosts. A render that varies by host is a render depending
on the host's installed fonts, and the fix for that is `bin/build`'s
`--ignore-system-fonts`, which is already there because that regression
happened once.

**The baseline was generated on typst 0.15.1 and verified on 0.14.2 to
0.15.1.** Those versions render the fixture with identical geometry, so the
check runs on whatever typst is installed. When a typst release moves the
geometry the check fails; if the move is deliberate, regenerate:

```sh
tools/check-fidelity.sh --update    # rewrite the baseline from this render
```

Read the resulting diff before committing it. `--update` is how a deliberate
design change is recorded, and it is also how a real regression would be
papered over, so the diff is the only thing standing between those two.

## 7a. Where the geometry came from

Every value in §4 and §6 was calibrated against a real rendered resume
produced by the commercial template this design clones, with populated
multi-item sidebar blocks (8 skills, 5 hobbies) and a populated education
entry: sidebar content is what exposed a per-item drift that had reached
79pt by the last sidebar line, and education content is what surfaced the two
Typst quirks in §6 points 7-8. That reference is not shipped and is not
needed again: the snapshot test in §7 is what keeps these values honest now.

## 7b. One measurement worth keeping

For a period, two independent renderers consumed this same content format:
this Typst one and an HTML/CSS + headless-Chrome one. On identical content
they agreed at `matched 133/133` word positions, `dx = 0.00pt`, worst
`|dy| = 0.99pt`, two implementations, written separately, landing on the
same page to within a point.

The second implementation is gone, so that check cannot be re-run. What
replaces it is the snapshot test in §7, which asks a narrower question (has
*this* renderer moved) and answers it on every commit rather than once.

## 7c. Non-breaking hyphens, and what they cost

A hyphenated compound word ("e-commerce", "latency-breach",
"storefront-proxy") breaking across a line exactly at its own hyphen renders
correctly on the page but loses the hyphen when a parser or an applicant
tracking system extracts the text: `pdftotext` treats a line ending in "-" as
a soft line-wrap hyphenation and strips it, fusing the two halves
("ecommerce", "latencybreach", "storefrontproxy"). Several independent
screener reads against real postings found this same defect.

The fix (`components.typ`'s `nbh()`, applied to every body-text and heading
render path) replaces a mid-word "-" with a non-breaking hyphen (U+2011)
before layout, so the word is never split at that character; it moves to
the next line as a whole instead. This is correct and necessary; it is also
not free. Preventing a break at a hyphen changes where the line breaks,
which reflows everything after it in that paragraph.

Measured at the time against the original calibration reference, which came
from a renderer that did split words at hyphens: 16 of its 122 lines moved
their break on purpose, leaving `106/122` identical breaks, with worst
`|dy|` unchanged at `0.75pt` and `dx`, page count and page breaks
unaffected. A permanent, correct divergence from a reference that reproduces
the defect this fix removes, which is exactly why the baseline in §7 is a
render of this renderer rather than of any other.

## 7d. Per-content margins

`template.typ` reads an optional `layout:` block from the content file:
`margin-top` and `margin-bottom`, in points. Absent, `geo.margin-top` and
`geo.margin-bottom` apply, so the fixture and every content file without the
block are unchanged. The sidebar's absolute `sidebar-top` is honoured by
subtracting the effective top margin, as before.

Left margin and sidebar geometry are **not** overridable; they were
calibrated together. The intended use is squeezing a long draft onto a page
boundary without cutting a bullet: `40pt` top and bottom is a reasonable
floor to reach for, still above the `36pt` (0.5in) print-safe minimum.

## 7e. No letter-spacing on the subtitle and date lines

The subtitle and the date lines were set with `1pt` tracking, copied from
resume.io. At 6pt that gap is wide enough that `pdftotext` reads each letter
as its own word: the title extracted as "S E N I O R S O F T WA R E ..." and
dates as "A U G U S T 2 0 1 7 - M AY 2 0 1 9", so an applicant tracking
system could miss the title and every tenure. Screener reads against real
postings flagged it independently. Measured at 6pt, `0.6pt` still split and
`0.5pt` did not; the tracking is removed rather than set at that edge, since
other parsers draw the line elsewhere. `tests/test_text_layer.py` holds it.

## 8. Font provenance

`Lato-Regular.ttf` and `Lato-Bold.ttf` are the Google Fonts originals.
`Oswald-Medium.ttf` was instantiated from the Oswald variable font. The
retired HTML pipeline needed this because a variable font makes Chrome embed
headings as Type 3 outlines rather than real text, and the instantiated file
was carried over here unchanged rather than re-derived:

```sh
curl -LO 'https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/Oswald%5Bwght%5D.ttf'
python3 -c "
from fontTools import ttLib
from fontTools.varLib import instancer
f = ttLib.TTFont('Oswald[wght].ttf')
instancer.instantiateVariableFont(f, {'wght': 500}, updateFontNames=True).save('Oswald-Medium.ttf')"
```

Both families are SIL Open Font License; `fonts/OFL-Lato.txt` and
`fonts/OFL-Oswald.txt` are included as the licence requires.
