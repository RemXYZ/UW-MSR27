#!/usr/bin/env python3
"""Create a reproducible stratified review sample and an HTML diff report."""
import csv
import difflib
import html
import random
import sqlite3
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'lsh_results'
DB=ROOT.parent/'gitskills-sample-main/agent_skills_sample/agent_skills_sample.db'
rng=random.Random(2026)
with (OUT/'lsh_pairs.csv').open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
groups=defaultdict(list)
for r in rows:
    score=max(float(r.get('full_jaccard') or 0),float(r.get('body_jaccard') or 0))
    category='0.90–1.00' if score>=.9 else '0.75–0.90' if score>=.75 else '0.50–0.75' if score>=.5 else 'pokrycie krótszego'
    groups[category].append(r)
selected=[]
for category, group in sorted(groups.items()):
    for row in rng.sample(group,min(10,len(group))):
        selected.append((category,row))
db=sqlite3.connect(DB.resolve().as_uri()+'?mode=ro',uri=True)
content={sha:text for sha,text in db.execute('select file_sha,content from artifacts where dedup_primary=1')}
e=html.escape
parts=['<!doctype html><html lang="pl"><meta charset="utf-8"><title>Przegląd par</title><style>body{font:15px system-ui;max-width:1100px;margin:auto;padding:1em}section{border-top:2px solid #bbb;padding:1em 0}pre{background:#f5f5f5;padding:1em;white-space:pre-wrap;overflow-wrap:anywhere}.add{color:green}.del{color:#b00}</style><h1>Próbka par do ręcznej oceny</h1><p>Losowo maksymalnie 10 par z każdego przedziału; seed 2026. Diff jest skrócony do 200 linii. Wyniki tej próbki nie są oszacowaniem jakości całej metody.</p>']
review_path = OUT/'lsh_labels.csv'
if not review_path.exists():
    with review_path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['id','warstwa','sha_a','sha_b','ocena','uwagi'])
        for index,(category,r) in enumerate(selected,1):
            w.writerow([index,category,r['sha_a'],r['sha_b'],'',''])
else:
    print('Zachowuję istniejący plik lsh_labels.csv; usuń go lub zmień jego nazwę, aby utworzyć nowy.')
for index,(category,r) in enumerate(selected,1):
    parts.append(f'<section><h2>{index}. {e(category)}</h2>')
    for side in ('a','b'):
        repo=r['repo_'+side]; path=r['path_'+side]
        url='https://github.com/'+quote(repo,safe='/')+'/blob/HEAD/'+quote(path,safe='/')
        parts.append(f'<p>{side.upper()}: <a href="{e(url,quote=True)}">{e(repo)} / {e(path)}</a> — {e(r["name_"+side])}; wystąpienia: {r["copies_"+side]}, repozytoria: {r["repos_"+side]}</p>')
    parts.append('<p>Jaccard pełny/body: '+e(r['full_jaccard'])+' / '+e(r['body_jaccard'])+'; pokrycie krótszego pełny/body: '+e(r['full_containment'])+' / '+e(r['body_containment'])+'</p>')
    diff=list(difflib.unified_diff(content[r['sha_a']].splitlines(),content[r['sha_b']].splitlines(),fromfile='A',tofile='B',lineterm=''))
    parts.append('<pre>'+ '\n'.join(('<span class="add">'+e(line)+'</span>' if line.startswith('+') else '<span class="del">'+e(line)+'</span>' if line.startswith('-') else e(line)) for line in diff[:200])+ ('\n… dalszy diff pominięty' if len(diff)>200 else '')+'</pre></section>')
parts.append('</html>');(OUT/'lsh_review.html').write_text('\n'.join(parts),encoding='utf-8')
print('Pary do oceny:',len(selected),'warstwy:',{k:len(v) for k,v in groups.items()})
