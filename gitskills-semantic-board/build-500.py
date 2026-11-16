"""Rebuild the review and domain statistics for the 500 selected skills."""
from collections import Counter
import argparse
import json
import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description='Rebuild the 500-skill review and statistics.')
parser.add_argument('--db', type=Path, help='Path to the GitSkills sample SQLite database')
args = parser.parse_args()
candidates = [root.parent / 'gitskills-sample-main/agent_skills_sample/agent_skills_sample.db',
              root.parent.parent / 'gitskills-sample-main/agent_skills_sample/agent_skills_sample.db']
db = args.db if args.db else next((path for path in candidates if path.is_file()), candidates[0])
if not db.is_file():
    raise SystemExit('GitSkills sample database not found. Specify its path with --db.')
analyses = json.loads((root / 'analyses-500.json').read_text(encoding='utf-8'))
identities = json.loads((root / 'sample-500-identities.json').read_text(encoding='utf-8'))
assert len(analyses) == len(identities) == 500
assert [c['sha'] for c in analyses] == [c['sha'] for c in identities]
assert len({c['sha'] for c in analyses}) == 500
cards = []
with sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True) as conn:
    conn.row_factory = sqlite3.Row
    for item in analyses:
        row = conn.execute('SELECT repo_full_name, path, content FROM artifacts WHERE file_sha=? AND dedup_primary=1 AND content IS NOT NULL', (item['sha'],)).fetchone()
        assert row is not None and row['repo_full_name'] == item['repository'] and row['path'] == item['path'], item['sha']
        cards.append(dict(item, content=row['content']))

data = json.dumps(cards, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
template = (root / 'english-template.html').read_text(encoding='utf-8')
template = template.replace('A sample of skill files, summarized in English.',
    'A sample of 500 skill files with preliminary English analyses. All cards include their original source text.')
old_load = "try{reviews=JSON.parse(localStorage.getItem(storageKey)||'{}');if(!reviews||Array.isArray(reviews)||typeof reviews!=='object')reviews={};}catch(e){reviews={};status.textContent='Could not read saved reviews; you can import a backup.';}"
new_load = """try{
let saved=localStorage.getItem(storageKey);
if(saved===null){
 const prefix=storageKey+':';
 const legacy=Object.keys(localStorage).find(k=>k.startsWith(prefix)&&k.slice(prefix.length).split(':').length===500);
 if(legacy){const old=JSON.parse(localStorage.getItem(legacy));if(old&&typeof old==='object'&&!Array.isArray(old)){const allowed=new Set(cards.map(c=>c.sha));reviews=Object.fromEntries(Object.entries(old).filter(([sha])=>allowed.has(sha)));localStorage.setItem(storageKey,JSON.stringify(reviews));status.textContent='Imported saved reviews for the first 500 cards from the previous version.';}}
}else{reviews=JSON.parse(saved);}
if(!reviews||Array.isArray(reviews)||typeof reviews!=='object')reviews={};
}catch(e){reviews={};status.textContent='Could not read saved reviews; you can import a backup.';}"""
assert template.count(old_load) == 1
template = template.replace(old_load, new_load)
old_import = "if(data.format!=='gitskills-review-en-v2'||data.sample!==sample||!data.reviews||typeof data.reviews!=='object'||Array.isArray(data.reviews))throw Error('The file has a different format or sample.');const ids=new Set(cards.map(c=>c.sha));"
new_import = """const previousSample=typeof data.sample==='string'&&data.sample.startsWith(sample+':')&&data.sample.slice(sample.length+1).split(':').length===500;
if(data.format!=='gitskills-review-en-v2'||(data.sample!==sample&&!previousSample)||!data.reviews||typeof data.reviews!=='object'||Array.isArray(data.reviews))throw Error('The file has a different format or sample.');const ids=new Set(cards.map(c=>c.sha));
if(previousSample)data.reviews=Object.fromEntries(Object.entries(data.reviews).filter(([sha])=>ids.has(sha)));"""
assert template.count(old_import) == 1
template = template.replace(old_import, new_import)
assert template.count('/*CARD_DATA*/') == 1
output = template.replace('/*CARD_DATA*/', data)
(root / 'review-500-english.html').write_text(output, encoding='utf-8')
(root / 'sample-500-identities.json').write_text(json.dumps(
    [{k: c[k] for k in ('number', 'sha', 'repository', 'path')} for c in cards],
    ensure_ascii=False, indent=2), encoding='utf-8')
counts = Counter(c['domain'] for c in cards)
lines = ['# Domain statistics — 500 skills', '',
         'Counts use the preliminary domain assigned to each card; they do not include review corrections saved in a browser. Each skill has one domain.', '',
         '| Domain | Skills | Share |', '| --- | ---: | ---: |']
lines += [f'| {domain} | {count} | {count / len(cards):.1%} |' for domain, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
lines += [f'| **Total** | **{len(cards)}** | **100.0%** |', '',
          'These are preliminary classifications, mainly based on opening excerpts of the sampled files. They have not been independently validated and do not establish the distribution of the full dataset.', '']
(root / 'domain-statistics.md').write_text('\n'.join(lines), encoding='utf-8')
print('Prepared 500 unique analyzed cards and domain statistics.')
