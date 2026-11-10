// The quiz page's tally requests must go with credentials: "same-origin"
// (CHG-019, 2026-11-09). A preview sits behind Cloudflare Access, which
// answers a request without its sign-in cookie with a redirect to its login:
// with "omit", the score POST never reached the Function and the reader just
// saw their own score. On uncost.org the site sets no cookies, so nothing
// changes there. This checks the source and, after a build, the shipped file.
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const WEB = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const FILES = [path.join(WEB, "src", "js", "quiz.js"), path.join(WEB, "dist", "js", "quiz.js")].filter((f) => existsSync(f));

test("the tally's fetches use same-origin credentials, never omit or include", () => {
  assert.ok(FILES.length >= 1, "js/quiz.js not found");
  for (const file of FILES) {
    // Code only: the header comment quotes the setting too.
    const src = readFileSync(file, "utf8").replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
    const modes = [...src.matchAll(/credentials\s*:\s*["']([a-z-]+)["']/g)].map((m) => m[1]);
    assert.deepEqual(modes, ["same-origin"], `${path.relative(WEB, file)}: one credentials setting, "same-origin" (found ${JSON.stringify(modes)})`);
    // The score POST and the stats GET both take that one init object.
    const tally = src.slice(src.indexOf("function tally("), src.indexOf("function compared("));
    assert.match(tally, /var init = \{ credentials: "same-origin"/, `${path.relative(WEB, file)}: the tally's init`);
    assert.match(tally, /getJson\("\/api\/quiz\/score", Object\.assign\(\{ method: "POST"[\s\S]*?\}, init\)\)/, `${path.relative(WEB, file)}: the score POST uses init`);
    assert.match(tally, /getJson\("\/api\/quiz\/stats\?version=" \+ encodeURIComponent\(version\), Object\.assign\(\{ method: "GET" \}, init\)\)/, `${path.relative(WEB, file)}: the stats GET uses init`);
  }
});
