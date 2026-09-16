#!/usr/bin/env python3
"""Convert an export page's <main> into an Eleventy template body.

The export is the authoritative design. This does NOT re-author markup: it
takes the export's <main> verbatim and rewrites only the things that must
change for this repository — image references onto the manifest-pinned
{% image %} pipeline, hrefs onto the contractual routes, and the form blocks
onto the flag-gated partials.
"""
import os, re, sys, pathlib, json

EXPORT = pathlib.Path(os.environ.get("UNCOST_DESIGN_SOURCE", "../uncost-private/design-source"))

ROUTES = {
    "/later/case-dashboard/": "/case/dashboard/",
    "/later/case-tracker/": "/case/tracker/",
    "/later/community/": "/community/",
    "/later/events/": "/news/events/",
    "/later/press/": "/press/",
    "/later/quiz/": "/quiz/",
    "/later/share/": "/share/",
    "/pledge-check-email/": "/pledge/check-email/",
    "/pledge-resend/": "/pledge/resent/",
    "/pledge-thanks/": "/pledge/thanks/",
    "/pledge-verify/": "/pledge/verify/",
    "/policies/assembly-governance/": "/policies/assembly-governance-participation/",
    "/policies/financial-controls/": "/policies/financial-controls-donation/",
    "/policies/in-kind-gifts/": "/policies/in-kind-gift-acceptance/",
    "/policies/safeguarding/": "/policies/safeguarding-pilot-safety/",
    "/policies/corrections-source-integrity/": "/policies/corrections-and-source-integrity/",
    # The export also links some policies by FILENAME rather than contractual slug.
    "/policies/assembly-governance-and-voting/": "/policies/assembly-governance-participation/",
    "/policies/financial-controls-and-donations/": "/policies/financial-controls-donation/",
    "/policies/privacy-and-data-protection/": "/policies/privacy-data-protection/",
    "/policies/safeguarding-and-pilot-safety/": "/policies/safeguarding-pilot-safety/",
    "/policies/in-kind-gift-acceptance/": "/policies/in-kind-gift-acceptance/",
    # The Assembly dashboard is a React mock, explicitly not part of this build
    # (export README §8.10), so its link goes to the Assembly page instead.
    "/assembly-dashboard/index/": "/assembly/",
    "/assembly-dashboard/": "/assembly/",
}

def brand_path(src: str):
    """Map an export asset path onto its manifest-pinned brand counterpart."""
    if "/robots/" in src:
        return "robots/" + src.rsplit("/", 1)[1].replace(".png", "_transparent.png")
    if "/illustrations/" in src:
        return "sectors/" + src.rsplit("/", 1)[1]
    if "logo-tight-light" in src:
        return "logos/logo-tight-light.png"
    if "logo-tight-dark" in src:
        return "logos/logo-tight-dark.png"
    return None

def convert_images(html: str, notes: list):
    def repl(m):
        tag = m.group(0)
        src = re.search(r'src="([^"]*)"', tag)
        if not src:
            return tag
        bp = brand_path(src.group(1))
        if not bp:
            notes.append(f"UNMAPPED IMAGE {src.group(1)}")
            return tag
        alt = re.search(r'alt="([^"]*)"', tag)
        cls = re.search(r'class="([^"]*)"', tag)
        alt_v = (alt.group(1) if alt else "").replace('"', "&quot;")
        args = [f'"{bp}"', f'"{alt_v}"']
        if cls:
            args += ['"100vw"', "[320, 640, 960]", '"lazy"', f'"{cls.group(1)}"']
        return "{% image " + ", ".join(args) + " %}"
    return re.sub(r"<img\b[^>]*>", repl, html)

def convert_hrefs(html: str):
    for a, b in ROUTES.items():
        html = html.replace(f'href="{a}"', f'href="{b}"')
        html = html.replace(f'href="{a}#', f'href="{b}#')
    return html

def main_block(page: pathlib.Path):
    t = page.read_text(encoding="utf-8")
    m = re.search(r'<main([^>]*)>(.*?)</main>', t, re.S)
    attrs, body = m.group(1), m.group(2)
    cls = re.search(r'class="([^"]*)"', attrs)
    head = re.search(r"<title>(.*?)</title>", t, re.S).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)"', t)
    page_id = re.search(r'<body data-page="([^"]*)"', t).group(1)
    return (cls.group(1) if cls else None), body, head, (desc.group(1) if desc else ""), page_id

if __name__ == "__main__":
    rel = sys.argv[1]
    notes = []
    cls, body, title, desc, page_id = main_block(EXPORT / "pages" / rel)
    body = convert_hrefs(convert_images(body, notes))
    print(json.dumps({"mainClass": cls, "title": title, "description": desc,
                      "pageId": page_id, "notes": notes}))
    print(body)
