# contrast_audit fixtures

Inputs for `python3 tools/contrast_audit.py --selftest`. Each `bad-*`
file carries one real defect class this repository has actually
shipped or nearly shipped; the audit must FAIL on every one of them
and PASS every `good-*` file.

`good-nested-gap.html` is the important pass: a grid container paints
ink only so a 2px gap draws a divider, while each cell repaints cream.
An audit that takes the nearest ancestor with a background reports
these echo spans as ink-grounded failures. They are cream-grounded and
fine.

These files are fixtures, never site sources. The selftest never runs
against website/dist or any tracked source.
