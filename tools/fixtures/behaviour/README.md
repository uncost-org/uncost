# behaviour_checks fixtures

Inputs for `python3 tools/behaviour_checks.py --selftest`. Fixtures
only — the selftest never runs against website/dist or any tracked
source.

`bad-hidden-attr-beaten-by-specificity.html` is the one that matters.
The control carries the `hidden` ATTRIBUTE and still renders, because
`[hidden]{display:none}` is (0,1,0) and a class rule beats it. A check
that reads `el.hidden` calls this page clean; this repository shipped
exactly that bug (CANVAS-SYNC 66). The tool must assert on
`offsetParent` and FAIL here.
