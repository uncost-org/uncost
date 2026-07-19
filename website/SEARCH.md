# Client-side search — index specification

Search at launch is a founder decision (client-side, no server round-trips,
no third-party service). The implementation is Pagefind, generated at build
time from the built output. This specification fixes the index scope now so
it is not decided under time pressure later.

## Binding schedule

Pagefind lands in the same pull request as the first real page content
(the governed design/content pass that replaces the placeholder templates),
not in an unscheduled follow-up. That PR must implement this specification
and cite it.

## What is indexed

Only pages that the site publishes for indexing: built pages that carry no
`noindex` robots directive. Concretely, at launch scope: `/`, `/movement`,
`/pledge`, `/join`, `/case`, `/sectors` and the fifteen sector pages,
`/receipts`, `/projects` and the seven project pages, `/assembly`,
`/roadmap`, `/news` and published news items, `/about`, `/faq`, `/policies`
and the ten policy pages, `/privacy`, `/contact`.

## What is excluded — explicitly

- Every page carrying a `noindex` robots directive, whatever its route.
  Search-index eligibility equals robots indexability — one rule, no
  second list to drift. That excludes today: `/pledge/thanks`, the three
  pledge-verification states, `/treasury` (until receipted figures),
  `/contribute` (until activation), and all roadmap-gated LATER routes
  (`/quiz`, `/share`, `/case/dashboard`, `/case/tracker`, `/news/events`,
  `/press`, `/community`).
- `404` and `500` states and the loading-state partial.
- The RSS feed and any non-HTML artifact.
- Anything under `design-system/` in the deploy artifact (stylesheets,
  fonts, icons — nothing there is a page).
- Draft, internal, gated, privacy-sensitive, or unpublished content of any
  kind: nothing enters the index that the site does not publish, and the
  shipped search bundle must not embed excerpts of excluded pages
  (Carlbot review point 3, 2026-07-19 decision record).

## Verification obligations for the implementing pull request

1. A CI assertion that no indexed record resolves to a `noindex` page.
2. A CI assertion that the search bundle contains no content from the
   excluded list above.
3. The content audit's built-output scan runs on the built site before
   the index is generated, so nothing prohibited can enter the index.
