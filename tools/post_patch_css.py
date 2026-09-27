#!/usr/bin/env python3
"""Re-apply the standing CSS corrections after adopting a fresh export.

Every re-export overwrites these, and they are not cosmetic: without them the
site fails its own WCAG gate and html-validate. Run after copying the export's
stylesheets into website/design-system/.
"""
import pathlib, sys

T = pathlib.Path("website/design-system/tokens.css")
S = pathlib.Path("website/design-system/site.css")
SEC = pathlib.Path("website/design-system/sections.css")

def sub(path, old, new, label, required=True, marker=None):
    """Apply one correction, idempotently.

    `marker` is the smallest string that proves the correction is already in
    place. Without it the check compared whole replacement blocks, so a comment
    reworded by hand read as "not applied": the script re-applied it and then
    aborted on the next patch whose anchor had already been consumed, leaving a
    half-patched stylesheet. These run after every re-export, so a partial run
    is worse than no run.
    """
    t = path.read_text(encoding="utf-8")
    probe = marker if marker is not None else new
    if probe in t:
        print(f"  = {label} (already applied)"); return
    if old not in t:
        if required:
            print(f"  ! {label}: ANCHOR NOT FOUND and target absent"); sys.exit(1)
        print(f"  - {label} (anchor absent, skipped)"); return
    path.write_text(t.replace(old, new, 1), encoding="utf-8")
    print(f"  + {label}")

def sub_all(path, old, new, label, marker=None):
    """Like sub(), but every occurrence. Used where the export repeats a raw
    literal — the ink hex appears nine times in site.css alone, and a
    first-occurrence-only replace would leave the rest at the old value and
    ship two different inks."""
    t = path.read_text(encoding="utf-8")
    probe = marker if marker is not None else new
    if probe in t and old not in t:
        print(f"  = {label} (already applied)"); return
    n = t.count(old)
    if not n:
        print(f"  - {label} (anchor absent, skipped)"); return
    path.write_text(t.replace(old, new), encoding="utf-8")
    print(f"  + {label} ({n} occurrence(s))")


print("WCAG 2.2 AA corrections (AUTHORITY.md; founder-approved divergence):")
# C1, 2026-09-25 — ink is #0A0A0A. Runs FIRST: the --ink-on-coral correction
# below anchors on the --ink line, so the value it looks for has to be the
# post-C1 one. On #0A0A0A, --coral is 4.58:1 and ink-on-coral is 4.58:1, so
# both clear 4.5 at every size; on the export's #0E0E0C both were 4.47:1.
sub(T, "  --ink:          #0E0E0C;", "  --ink:          #0A0A0A;",
    "--ink -> #0A0A0A (C1)", marker="  --ink:          #0A0A0A;")
sub(T, "  --rule:         #0E0E0C;", "  --rule:         #0A0A0A;",
    "--rule follows ink (C1)", marker="  --rule:         #0A0A0A;")
sub(T, "  --rule-soft:    rgba(14,14,12,0.18);", "  --rule-soft:    rgba(10,10,10,0.18);",
    "--rule-soft follows ink (C1)", marker="rgba(10,10,10,0.18)")
sub(T, "  --rule-hair:    rgba(14,14,12,0.08);", "  --rule-hair:    rgba(10,10,10,0.08);",
    "--rule-hair follows ink (C1)", marker="rgba(10,10,10,0.08)")
# The export also writes the ink hex as a raw literal, which no token change
# reaches: nine times in site.css (the .ft-updates footer block) and once in
# sections.css (.u-105's ink background). Left behind they render a second,
# slightly different ink beside the token one.
sub_all(S, "#0E0E0C", "#0A0A0A", "site.css raw ink literals (C1)")
sub_all(SEC, "#0E0E0C", "#0A0A0A", "sections.css raw ink literal (C1)")
sub(T, "  --ink:          #0A0A0A;",
    "  --ink:          #0A0A0A;\n"
    "  /* ink-on-coral — AA correction applied on adoption. The export puts --ink\n"
    "     (4.47:1) or #FFFFFF (4.32:1) on brand coral; both miss the 4.5 floor for\n"
    "     normal text. #0A0A0A measures 4.58:1 and is visually indistinguishable. */\n"
    "  --ink-on-coral: #0A0A0A;",
    "--ink-on-coral token", marker="--ink-on-coral:")
sub(T, "  --link:         var(--coral);",
    "  --link:         var(--coral-deep);   /* AA: coral is 4.04:1 on cream */",
    "--link -> coral-deep", marker="--link:         var(--coral-deep)")
sub(T, ".u-block--coral  { background: var(--coral); color: var(--ink); }",
    ".u-block--coral  { background: var(--coral); color: var(--ink-on-coral); }",
    ".u-block--coral text", required=False)
sub(T, ".u-btn--primary { background: var(--coral); color: var(--ink); }",
    ".u-btn--primary { background: var(--coral); color: var(--ink-on-coral); }",
    ".u-btn--primary text", required=False)
sub(S, ".blk--coral{background:var(--coral);color:var(--ink);",
    ".blk--coral{background:var(--coral);color:var(--ink-on-coral);",
    ".blk--coral text", marker=".blk--coral{background:var(--coral);color:var(--ink-on-coral)")
sub(S, ".hd .cta-btn{background:var(--coral);color:#FFFFFF;",
    ".hd .cta-btn{background:var(--coral);color:var(--ink-on-coral);",
    "header CTA text", marker=".hd .cta-btn{background:var(--coral);color:var(--ink-on-coral)")
sub(S, ".hd .cta-btn:hover{background:var(--coral-deep);color:var(--ink)}",
    ".hd .cta-btn:hover{background:var(--coral-deep);color:var(--cream)}",
    "header CTA hover", required=False)
sub(S, ".hd-mega .mg-num{font-family:var(--font-display);font-weight:900;font-size:12px;letter-spacing:.14em;color:var(--coral);",
    ".hd-mega .mg-num{font-family:var(--font-display);font-weight:900;font-size:12px;letter-spacing:.14em;color:var(--coral-deep);",
    "mega-panel number", required=False)
sub(S, ".hd-mega .mg-go a .ar{font-size:17px;color:var(--coral)}",
    ".hd-mega .mg-go a .ar{font-size:17px;color:var(--coral-deep)}",
    "mega-panel arrow", required=False)
sub(S, ".drawer-acc>button .pm{font-family:var(--font-body);font-size:20px;color:var(--coral);",
    ".drawer-acc>button .pm{font-family:var(--font-body);font-size:20px;color:var(--coral-deep);",
    "drawer plus/minus", required=False)
sub(S, ".drawer-acc .in a .ar{color:var(--coral)}",
    ".drawer-acc .in a .ar{color:var(--coral-deep)}", "drawer arrow", required=False)
sub(S, ".ft-updates .chk{color:var(--fg-3)}",
    ".ft-updates .chk{color:var(--fg-2)}", "updates checkbox on wheat", required=False)
sub(S, ".ft-form button:hover{background:var(--coral);border-color:var(--cream);color:var(--ink)}",
    ".ft-form button:hover{background:var(--coral);border-color:var(--cream);color:var(--ink-on-coral)}",
    "footer form button hover", required=False)

C = pathlib.Path("website/design-system/components.css")
sub(C, ".rcpt-conf--needs-refresh { background: var(--coral); color: var(--ink); }",
    ".rcpt-conf--needs-refresh { background: var(--coral); color: var(--ink-on-coral); }",
    "needs-refresh pill", required=False)
sub(C, ".status--focus  { background: var(--coral); color: var(--ink); }",
    ".status--focus  { background: var(--coral); color: var(--ink-on-coral); }",
    "focus pill", required=False)
sub(C, ".site-hdr nav a:hover { color: var(--coral); }",
    ".site-hdr nav a:hover { color: var(--coral-deep); }", "legacy hdr hover", required=False)
sub(C, ".site-hdr nav a.here { color: var(--coral); }",
    ".site-hdr nav a.here { color: var(--coral-deep); }", "legacy hdr here", required=False)
sub(C, ".site-hdr .cta-btn { background: var(--coral); color: var(--ink);",
    ".site-hdr .cta-btn { background: var(--coral); color: var(--ink-on-coral);",
    "legacy hdr CTA", required=False)
sub(C, ".site-foot .foot-col a:hover { color: var(--coral); }",
    ".site-foot .foot-col a:hover { color: var(--coral-on-ink); }", "legacy foot hover", required=False)
# v4.2 hardcodes #5B574F here; on the wheat band that is 3.68:1.
sub(S, ".ft-updates .chk{color:#5B574F}",
    ".ft-updates .chk{color:var(--fg-2)}", "updates checkbox on wheat", required=False)
sub(S, ".ft-updates .ft-form button:hover{background:var(--coral);color:#0A0A0A;border-color:#0A0A0A}",
    ".ft-updates .ft-form button:hover{background:var(--coral);color:var(--ink-on-coral);border-color:var(--ink-on-coral)}",
    "updates form button hover", required=False)

t = S.read_text(encoding="utf-8")
if ":focus-visible { outline-color: var(--ink); }" not in t:
    S.write_text(t.rstrip("\n") + """

/* AA correction on adoption — focus-ring visibility on saturated fills.
   sections.css switches the ring to --coral-on-ink for ink blocks; on a coral,
   wheat or sage fill a --coral ring measures ~1:1 against its own background.
   --ink clears the 3.0:1 non-text floor on those; --cream clears it on the deep
   fills. Carry back to the design canvas. */
.blk--coral :focus-visible,
.blk--wheat :focus-visible,
.blk--sage :focus-visible,
.u-block--coral :focus-visible,
.hd .cta-btn:focus-visible,
.pledgebar :focus-visible { outline-color: var(--ink); }
.bg-clay :focus-visible,
.bg-ink-blue :focus-visible { outline-color: var(--cream); }
""", encoding="utf-8")
    print("  + focus-ring overrides")

print("Heading-level aliases (declaration-identical; no visual change):")
sec = SEC.read_text(encoding="utf-8")
for sel in (".step h4", ".prin h4", ".prin h4 i", ".grid3 h3", ".grid3 h3 i", ".polrow h4"):
    alias = sel.replace("h4", "h3") if "h4" in sel else sel.replace("h3", "h2")
    if sel + "{" in sec and alias + "," + sel + "{" not in sec:
        sec = sec.replace(sel + "{", f"{alias},{sel}{{", 1); print(f"  + {alias},{sel}")
SEC.write_text(sec, encoding="utf-8")
s2 = S.read_text(encoding="utf-8")
for sel in (".ft-updates h3", ".ft-col h4"):
    alias = sel.replace("h3", "h2") if sel.endswith("h3") else sel.replace("h4", "h3")
    if sel + "{" in s2 and alias + "," + sel + "{" not in s2:
        s2 = s2.replace(sel + "{", f"{alias},{sel}{{", 1); print(f"  + {alias},{sel}")
S.write_text(s2, encoding="utf-8")
print("done")
