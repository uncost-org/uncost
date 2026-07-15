#!/usr/bin/env python3
from pathlib import Path
import re, sys, json
root=Path(__file__).resolve().parents[1]
errors=[]; warnings=[]
expected=['README.md','OPEN_LETTER.md','IMAGINE.md','PRINCIPLES.md','NEEDS.md','GOVERNANCE.md','ASSEMBLY.md','FUNDING.md','FAQ.md','CLAUDE.md','REVIEW_STATUS.md','CONTRIBUTING.md','CODE_OF_CONDUCT.md','SECURITY.md','docs/CONTROL.md','docs/MOVEMENT_PLAN.md','docs/ROADMAP.md','policies/README.md','projects/README.md','sectors/README.md','sources/register.csv','website/README.md']
for f in expected:
    if not (root/f).is_file(): errors.append(f'MISSING:{f}')
policy=list((root/'policies').glob('POL-[0-9][0-9][0-9]-*.md'))
project=list((root/'projects').glob('PRJ-[0-9][0-9][0-9]-*.md'))
sector=list((root/'sectors').glob('SEC-[0-9][0-9][0-9]-*.md'))
if len(policy)!=10: errors.append(f'POLICY_COUNT:{len(policy)}')
if len(project)!=7: errors.append(f'PROJECT_COUNT:{len(project)}')
if len(sector)!=15: errors.append(f'SECTOR_COUNT:{len(sector)}')
for p in policy+project:
    s=p.read_text(encoding='utf-8')
    if 'status: draft' not in s: errors.append(f'DRAFT_STATUS_MISSING:{p.relative_to(root)}')
    if 'review_status: independent-claude-review-pending' not in s: errors.append(f'REVIEW_STATUS_MISSING:{p.relative_to(root)}')
    if 'privacy: public' not in s: errors.append(f'PUBLIC_BOUNDARY_MISSING:{p.relative_to(root)}')
    if p in project and '- **Roadmap:**' not in s: errors.append(f'ROADMAP_FIELD_MISSING:{p.relative_to(root)}')
    if re.search(r'Plan Section [A-Z]|the plan\'s Section [A-Z]|v3\.2|founder operates from Vietnam|already designed into|faceless',s,re.I): errors.append(f'PRIVATE_OR_STALE_REMNANT:{p.relative_to(root)}')
for p in root.rglob('*'):
    if not p.is_file() or '.git' in p.parts or p.suffix.lower() not in {'.md','.py','.yml','.yaml','.csv',''}: continue
    try:s=p.read_text(encoding='utf-8')
    except UnicodeDecodeError: errors.append(f'NON_UTF8:{p.relative_to(root)}'); continue
    if s and not s.endswith('\n'): errors.append(f'NO_FINAL_NEWLINE:{p.relative_to(root)}')
    for n,line in enumerate(s.splitlines(),1):
        if line.rstrip()!=line: errors.append(f'TRAILING_WS:{p.relative_to(root)}:{n}')
    rel=p.relative_to(root)
    if re.search(r'/Users/[A-Za-z0-9._-]+/',s): errors.append(f'LOCAL_PATH:{rel}')
    if rel not in {Path('.gitignore'),Path('scripts/audit_repository.py')} and re.search(r'(?i)(github_pat_|ghp_[A-Za-z0-9]{20,}|CLOUDFLARE_API_TOKEN|postgres(?:ql)?://[^\s]+:[^\s]+@|\.wrangler/)',s): errors.append(f'SECRET_OR_PRIVATE_MARKER:{rel}')
    if rel != Path('scripts/audit_repository.py'):
        for phrase in ['14 sectors','fourteen sectors','post-monetary','beyond money','#UncostTheWorld','Start with $1','DAO donation','Money is broken. Here']:
            if phrase.lower() in s.lower(): errors.append(f'STALE_PHRASE:{rel}:{phrase}')
# Relative markdown links must resolve; ignore anchors and web/mail.
link_re=re.compile(r'\[[^\]]*\]\(([^)]+)\)')
for p in root.rglob('*.md'):
    s=p.read_text(encoding='utf-8')
    for target in link_re.findall(s):
        t=target.split('#',1)[0]
        if not t or re.match(r'^[a-z]+://',t) or t.startswith('mailto:'): continue
        dest=(p.parent/t).resolve()
        try: dest.relative_to(root.resolve())
        except ValueError: errors.append(f'LINK_ESCAPE:{p.relative_to(root)}:{target}'); continue
        if not dest.exists(): errors.append(f'BROKEN_LINK:{p.relative_to(root)}:{target}')
road=(root/'docs/ROADMAP.md').read_text()
for d in ['2026-07-15','2026-10-13','2027-01-15','2027-04-15','2027-07-15']:
    if d not in road: errors.append(f'ROADMAP_DATE_MISSING:{d}')
result={'ok':not errors,'errors':errors,'warnings':warnings,'counts':{'policies':len(policy),'projects':len(project),'sectors':len(sector)}}
print(json.dumps(result,indent=2))
sys.exit(0 if not errors else 1)
