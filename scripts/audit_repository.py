#!/usr/bin/env python3
from pathlib import Path
import re, sys, json, subprocess
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
for p in project:
    s=p.read_text(encoding='utf-8')
    if 'status: draft' not in s: errors.append(f'DRAFT_STATUS_MISSING:{p.relative_to(root)}')
    if 'review_status: independent-claude-review-pending' not in s: errors.append(f'REVIEW_STATUS_MISSING:{p.relative_to(root)}')
    if 'privacy: public' not in s: errors.append(f'PUBLIC_BOUNDARY_MISSING:{p.relative_to(root)}')
    if '- **Roadmap:**' not in s: errors.append(f'ROADMAP_FIELD_MISSING:{p.relative_to(root)}')
    if re.search(r'Plan Section [A-Z]|the plan\'s Section [A-Z]|v3\.2|founder operates from Vietnam|already designed into|faceless',s,re.I): errors.append(f'PRIVATE_OR_STALE_REMNANT:{p.relative_to(root)}')
policy_banner='> **Draft — not in force; pending required review/adoption.**'
source_hash='5b99100ecbeeb068b89c7f5a19d38e5382b01ee79f991d35df98106764d48670'
for p in policy:
    s=p.read_text(encoding='utf-8')
    required=['status: draft','canonical_status: public-review-draft-not-in-force','visibility: public','adoption_status: not-adopted','review_status: pending-required-review-and-adoption','independent_claude_review: pending-post-publication',f'source_sha256: {source_hash}',policy_banner]
    for marker in required:
        if marker not in s: errors.append(f'POLICY_METADATA_MISSING:{p.relative_to(root)}:{marker}')
    for pattern in [r'\$250',r'\$1,000',r'interim: US\$50',r'operates internationally from day one',r'Pledge page commitments are binding',r'founder operates separate commercial ventures']:
        if re.search(pattern,s,re.I): errors.append(f'POLICY_PRIVATE_OR_PLACEHOLDER:{p.relative_to(root)}:{pattern}')
    if re.search(r'Plan Section [A-Z]|the plan\'s Section [A-Z]|v3\.2|founder operates from Vietnam|already designed into|faceless',s,re.I): errors.append(f'PRIVATE_OR_STALE_REMNANT:{p.relative_to(root)}')
# Source-controlled policy assertions.
checks={
 'POL-004-financial-controls-and-donations.md':['does not take equity or investment positions','No v1.2 placeholder amount'],
 'POL-006-assembly-governance-and-voting.md':['one person, one vote','prior explicit written lawful delegation','subject to legal and fiduciary approval','at least two trained human moderators'],
 'POL-008-safeguarding-and-pilot-safety.md':['sufficient funding','qualified local operator','permits and site permission','insurance','operational expertise'],
 'POL-010-in-kind-gift-acceptance.md':['documented provenance','may not conceal a conflict'],
}
for filename,markers in checks.items():
    s=(root/'policies'/filename).read_text(encoding='utf-8')
    for marker in markers:
        if marker.lower() not in s.lower(): errors.append(f'POLICY_CONTROL_MARKER_MISSING:{filename}:{marker}')
master=(root/'policies/POLICY-PACK-v1.3.md').read_text(encoding='utf-8')
for marker in ['canonical_status: public-review-draft-not-in-force','adoption_status: not-adopted','independent_claude_review: pending-post-publication',f'source_sha256: {source_hash}',policy_banner]:
    if marker not in master: errors.append(f'MASTER_METADATA_MISSING:{marker}')
for p in policy:
    text=p.read_text(encoding='utf-8')
    heading=re.search(r'(?m)^# (POL-\d{3} .+)$',text)
    if not heading: errors.append(f'SPLIT_POLICY_HEADING_MISSING:{p.name}'); continue
    body=text[text.index('# '+heading.group(1)):].strip()
    if master.count(body)!=1: errors.append(f'MASTER_POLICY_BODY_MISMATCH:{p.name}:{master.count(body)}')
index=(root/'policies/README.md').read_text(encoding='utf-8')
for marker in [source_hash,policy_banner,'Publication does not satisfy any gate or authorize implementation.']:
    if marker not in index: errors.append(f'POLICY_INDEX_CONTROL_MISSING:{marker}')
for source_file in [root/'docs/CONTROL.md',root/'sources/register.csv',root/'policies/POLICY-PACK-v1.3.md']:
    if source_hash not in source_file.read_text(encoding='utf-8'): errors.append(f'SOURCE_HASH_MISSING:{source_file.relative_to(root)}')
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

design_script = root/'scripts/audit_design_handoff.py'
if design_script.exists():
    design_audit = subprocess.run(
        [sys.executable, str(design_script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if design_audit.returncode != 0:
        errors.append(f'DESIGN_HANDOFF_AUDIT_FAILED')
        warnings.append(design_audit.stdout.strip())

result={'ok':not errors,'errors':errors,'warnings':warnings,'counts':{'policies':len(policy),'projects':len(project),'sectors':len(sector)}}
print(json.dumps(result,indent=2))
sys.exit(0 if not errors else 1)
