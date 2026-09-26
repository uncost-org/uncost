# type_audit fixtures

Inputs for `python3 tools/type_audit.py --selftest`. Nothing here is a site
source and the selftest never runs against `website/dist` or any tracked page.

Each `bad-*` file carries exactly ONE defect, and the selftest asserts both
that the audit fails on it and that it fails for the INTENDED reason — the
error kind is checked, not just the exit code. A fixture that failed for an
incidental reason would otherwise look like a working audit.

| fixture | must | why |
| --- | --- | --- |
| `good-consistent.html` | PASS | baseline: one headline size, one wrap point per band |
| `good-hero-larger.html` | PASS | the page hero is 96px against 60px section headlines, and its own headline and body wrap at different points. Heroes are excluded from both invariants, so this is clean. It is the counterpart to `bad-headline-larger.html`, which applies the same 96px step to a band that is not the hero and must be caught — together they prove the hero is *excluded* rather than size differences *ignored*. |
| `good-components.html` | PASS | component headings that come FIRST in their band: a card grid whose two `<h2>` are 28px and is a band's entire content, and a `<nav>` table of contents whose `<h2>` is 12px, ahead of the band's real headline. That ordering is the point — "the first `<h2>` in the band" reports both as section headlines against a 60px modal. Neither is one. |
| `bad-headline-smaller.html` | FAIL `HEADLINE-SIZE` | the real defect: "Working harder, still falling behind." renders smaller than its peers |
| `bad-headline-larger.html` | FAIL `HEADLINE-SIZE` | one section headline renders larger than its peers |
| `bad-measure-split.html` | FAIL `MEASURE` | a prose band whose headline keeps a narrower measure than its body |
| `bad-measure-body-uncapped.html` | FAIL `MEASURE` | a prose band whose body has no measure at all while the headline has one |
| (no file) | FAIL `LOAD` | a route that will not load is an error, never a skipped line |
| `good-card-step.html` | PASS | C19.3 (V6): boxed repeated cards whose heading sits one step below the section headline in the page's own `--fs-*` scale; an unboxed list beside them has 18px row headings that must NOT be measured |
| `bad-card-at-section-size.html` | FAIL `COMPONENT-SIZE` | the /treasury/ and project-card defect: card headings at the section headline's size |
| `bad-card-too-small.html` | FAIL `COMPONENT-SIZE` | card headings below the step |
| `bad-card-no-scale.html` | FAIL `UNRESOLVED` | cards but no type scale to measure them against: a failure, not a skip |

The measure fixtures fail at 1440 and are clean at 390, which is correct: at
390 a 728px cap and no cap at all wrap at the same place, because the viewport
is the binding constraint. The audit judges the WRAP POINT — min(max-width,
containing block width) — not the declared max-width, so it does not invent a
defect at narrow widths.

No expected pixel value is written down anywhere in the audit or in these
fixtures. The expected headline size is the modal size of whatever the page
renders, and the expected body measure is whatever that band's own headline
wraps at, so the tool keeps working when the measure moves from 728px to
min(66vw, 960px) and when the headline scale moves with it.
