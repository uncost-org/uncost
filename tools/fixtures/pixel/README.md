# pixel_validator fixtures

Inputs for `python3 tools/pixel_validator.py --selftest`. Fixtures
only — the selftest never runs against website/dist or any tracked
source.

Each `bad-*` file reproduces a defect this repository actually
shipped past a DOM-only check:

- `bad-double-rule` — both the upper band's bottom edge and the lower
  band's top edge draw, so the boundary carries two rules.
- `bad-rule-thicker-than-declared` — 8px renders where 4px is
  declared (`/treasury/`).
- `bad-frame-stacked-on-band-rule` — a component's frame edge sits on
  top of the band rule (`/join/`, `/policies/`).
- `bad-undeclared-rule` — a child's background draws a rule no border
  declares, so the DOM reports the boundary as bare.
