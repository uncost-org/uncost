#!/usr/bin/env python3
"""Uptime check for the live site — what .github/workflows/uptime.yml runs.

Standard library only; no secrets. Every check is read-only, and the one POST
cannot send an email (see CONTACT below).

  HOME        https://uncost.org/ answers 200 and its <title> is the site's.
  WWW         https://www.uncost.org/ redirects (301 or 308) to https://uncost.org/.
  ROBOTS      /robots.txt answers 200.
  SITEMAP     /sitemap.xml answers 200.
  CONTACT     POST /api/contact from a foreign Origin, with Accept:
              application/json and no body. The live handler
              (website/functions/api/contact.js) checks the origin FIRST and
              answers 200 {"ok":false} without reading the body, so this never
              reaches the mailer and can never send an email. With the form
              switched off the handler answers 404; set
              UPTIME_CONTACT_FORM=off to expect that instead.
  SECURITY    /.well-known/security.txt answers 200 and its Expires date is
              more than 30 days away (renew it before then; prod_check fails
              the build once it has passed).

A failing check is retried once, after --retry-delay seconds, before the run
fails.

    python3 scripts/uptime_check.py                 # https://uncost.org
    python3 scripts/uptime_check.py --selftest      # canned responses

Exit 0 when every check passes, 1 when any fails after its retry.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ORIGIN = "https://uncost.org"
WWW = "https://www.uncost.org"
SITE_TITLE = "Uncost — Living should not have a price tag."
EXPIRES_MARGIN_DAYS = 30
UA = "uncost-uptime-check (+https://github.com/uncost-org/uncost/blob/main/.github/workflows/uptime.yml)"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):
        return None


def fetch(url: str, method: str = "GET", headers: dict | None = None, follow: bool = True):
    """(status, headers, body) — an HTTP error status is a result, not an exception."""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, **(headers or {})},
                                 data=b"" if method == "POST" else None)
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    try:
        with opener.open(req, timeout=20) as r:
            return r.status, dict(r.headers), r.read(200_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers or {}), (e.read(200_000) or b"").decode("utf-8", "replace")


# Each judge takes (status, headers, body) and returns None when fine, or why not.
def judge_home(st, hd, body):
    if st != 200:
        return f"HTTP {st}"
    m = re.search(r"<title>(.*?)</title>", body, re.S)
    got = m.group(1).strip() if m else None
    return None if got == SITE_TITLE else f"title is {got!r}"


def judge_www(st, hd, body):
    loc = {k.lower(): v for k, v in hd.items()}.get("location", "")
    if st not in (301, 308):
        return f"HTTP {st}, not a permanent redirect"
    return None if loc.rstrip("/") == ORIGIN else f"redirects to {loc!r}"


def judge_ok(st, hd, body):
    return None if st == 200 else f"HTTP {st}"


def judge_contact(expect_on: bool):
    def judge(st, hd, body):
        if not expect_on:
            return None if st == 404 else f"HTTP {st}; expected 404 with the form off"
        if st != 200:
            return f"HTTP {st}; expected 200 {{\"ok\":false}}"
        try:
            ok = json.loads(body).get("ok")
        except ValueError:
            return f"body is not JSON: {body[:60]!r}"
        return None if ok is False else f"answered {body[:60]!r}; expected {{\"ok\":false}}"
    return judge


def judge_security(now: datetime.datetime):
    def judge(st, hd, body):
        if st != 200:
            return f"HTTP {st}"
        m = re.search(r"^Expires:\s*(\S+)\s*$", body, re.M | re.I)
        if not m:
            return "no Expires field"
        try:
            when = datetime.datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
        except ValueError:
            return f"Expires {m.group(1)!r} is not a date-time"
        days = (when - now).days
        return None if days > EXPIRES_MARGIN_DAYS else f"Expires {m.group(1)} is {days} days away (renew it)"
    return judge


def checks(expect_contact_on: bool, now: datetime.datetime):
    return [
        ("HOME", lambda: fetch(ORIGIN + "/"), judge_home),
        ("WWW", lambda: fetch(WWW + "/", follow=False), judge_www),
        ("ROBOTS", lambda: fetch(ORIGIN + "/robots.txt"), judge_ok),
        ("SITEMAP", lambda: fetch(ORIGIN + "/sitemap.xml"), judge_ok),
        ("CONTACT", lambda: fetch(ORIGIN + "/api/contact", method="POST",
                                  headers={"Origin": "https://uptime-check.invalid", "Accept": "application/json"}),
         judge_contact(expect_contact_on)),
        ("SECURITY", lambda: fetch(ORIGIN + "/.well-known/security.txt"), judge_security(now)),
    ]


def run(retry_delay: float) -> dict:
    now = datetime.datetime.now(datetime.timezone.utc)
    expect_on = os.environ.get("UPTIME_CONTACT_FORM", "on") != "off"
    results = {}
    for name, get, judge in checks(expect_on, now):
        for attempt in (1, 2):
            try:
                why = judge(*get())
            except Exception as e:  # network failure, timeout, TLS
                why = f"{e.__class__.__name__}: {e}"
            if why is None or attempt == 2:
                break
            time.sleep(retry_delay)
        results[name] = {"ok": why is None, "attempts": attempt, **({"why": why} if why else {})}
    return {"ok": all(r["ok"] for r in results.values()), "checked_at": now.isoformat(timespec="seconds"),
            "contact_form_expected": "on" if expect_on else "off", "checks": results}


def selftest() -> int:
    now = datetime.datetime(2026, 10, 20, tzinfo=datetime.timezone.utc)
    page = f"<html><head><title>{SITE_TITLE}</title></head></html>"
    cases = [
        ("home ok", judge_home(200, {}, page), True),
        ("home 500", judge_home(500, {}, ""), False),
        ("home other title", judge_home(200, {}, "<title>About · Uncost</title>"), False),
        ("www 301", judge_www(301, {"Location": "https://uncost.org/"}, ""), True),
        ("www 200", judge_www(200, {}, page), False),
        ("www elsewhere", judge_www(301, {"Location": "https://example.com/"}, ""), False),
        ("contact rejects", judge_contact(True)(200, {}, '{"ok":false}'), True),
        ("contact accepted?!", judge_contact(True)(200, {}, '{"ok":true}'), False),
        ("contact 404 while on", judge_contact(True)(404, {}, "Not found"), False),
        ("contact 404 while off", judge_contact(False)(404, {}, "Not found"), True),
        ("security ok", judge_security(now)(200, {}, "Contact: x\nExpires: 2027-10-20T00:00:00Z\n"), True),
        ("security soon", judge_security(now)(200, {}, "Expires: 2026-11-10T00:00:00Z\n"), False),
        ("security missing", judge_security(now)(404, {}, ""), False),
    ]
    failures = [name for name, why, want in cases if (why is None) != want]
    print(json.dumps({"ok": not failures, "selftest_cases": len(cases), "failures": failures}, indent=1))
    return 0 if not failures else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--retry-delay", type=float, default=60.0)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    result = run(a.retry_delay)
    print(json.dumps(result, indent=1))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("### Uptime check\n\n| Check | Result |\n|---|---|\n")
            for name, r in result["checks"].items():
                f.write(f"| {name} | {'ok' if r['ok'] else 'FAIL: ' + r['why']} |\n")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
