# CHG-003 — Homepage hero line changes; former line becomes the intro's underlined phrase

**Date:** 2026-09-19 · **Branch:** `feat/design-v2-integration` · **Status:** founder decision, recorded

## The decision

The homepage hero line changes from:

> Living should not have a price tag.

to:

> Technology should make living cheaper, not billionaires richer.

with **"not billionaires richer"** carrying the hero accent.

The former line is not retired. It moves into the homepage intro paragraph as
the underlined phrase:

> Uncost is a nonprofit, nonpartisan movement that believes <u>living should
> not have a price tag</u>. We aim to significantly reduce the cost of living
> by putting AI and robotics to work for humanity.

Underline exactly that phrase; size and colour unchanged.

## What this supersedes

This **supersedes the hero line in `uncost/canon/brief.md`.** The canon change
is a separate pull request in a separate repository and is not this repository's
job. Until that PR lands, `canon/brief.md` and this site disagree about the hero
line, and this record is the reason why: the site is correct and the canon is
stale, not the other way round.

The line "Living should not have a price tag." continues to appear unchanged in
the site footer and in the movement materials. It is demoted from headline to
supporting phrase on the homepage only.

## Affected public surfaces

- `website/src/index.njk` (hero, intro) — and, after the content-layer
  migration, the homepage entry in the `_data` content layer
- The "A nonprofit, nonpartisan movement" eyebrow tag above the hero is removed;
  the same fact now reads in the intro sentence, so the tag was saying it twice.

## Provenance

Founder instruction, Sweep 3 of preview `27d92249`, 2026-09-19. No AI authorship
of the line; recorded verbatim as given.
