"""Combine the two reviewed samples without fabricating missing goal/task analyses."""
import json
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
base = root.parent
items = json.loads((root/'analyses-1000.json').read_text(encoding='utf-8'))
assert [x['number'] for x in items]==list(range(1,1001))
assert len({x['sha'] for x in items})==1000
contents={}
import sqlite3
db=(base/'gitskills-sample-main/agent_skills_sample/agent_skills_sample.db').as_uri()+'?mode=ro'
with sqlite3.connect(db,uri=True) as c:
    need={x['sha'] for x in items}
    contents.update({sha:content for sha,content in c.execute('SELECT file_sha, content FROM artifacts WHERE dedup_primary=1 AND content IS NOT NULL') if sha in need})
assert all(x['sha'] in contents for x in items)
cards=[dict(x,content=contents[x['sha']]) for x in items]
template=(root/'english-template.html').read_text(encoding='utf-8')
template=template.replace('A sample of skill files, summarized in English. Review the goal, task, and domain for each skill. Domains use a fixed list of labels, with more detailed categories for IT.', 'Combined sample of 1,000 skills. The first 500 have goal and task summaries; the next 500 have a rationale for the assigned domain. All analyses are preliminary and based mainly on opening excerpts. This sample is not a random sample of the full dataset.')
template=template.replace("const link=el('a','View source on GitHub');", "const link=el('a','🔗 Open SKILL.md on GitHub');")
template=template.replace('<main id="cards"></main>', '<div class="tools"><label>Search <input id="search" type="search" placeholder="Name, repository, domain, text…"></label><label>Domain <select id="domain-filter"><option value="">All domains</option></select></label><strong id="visible-count"></strong><a href="../gitskills-pca-1000/wykres-3d.html">3D PCA plots</a></div><main id="cards"></main>')
template=template.replace('const fields=[[\'goal\',\'Goal\'],[\'task\',\'Task\'],[\'domain\',\'Domain\']];', "const fields=[['goal','Goal'],['task','Task'],['domain','Domain']];\nfunction fieldsFor(c){return c.analysis_source==='next-500'?[['domain','Domain']]:fields}")
oldload="try{reviews=JSON.parse(localStorage.getItem(storageKey)||'{}');if(!reviews||Array.isArray(reviews)||typeof reviews!=='object')reviews={};}catch(e){reviews={};status.textContent='Could not read saved reviews; you can import a backup.';}"
newload="""try{let saved=localStorage.getItem(storageKey);if(saved===null){const prefix='gitskills-review-en-v2-',oldSample=cards.slice(0,500).map(c=>c.sha).join(':');let previous=localStorage.getItem(prefix+oldSample);if(previous){reviews=JSON.parse(previous);status.textContent='Previous 500-skill reviews loaded; export a backup.'}else{const legacy=Object.keys(localStorage).find(k=>k.startsWith(prefix+oldSample+':'));if(legacy){const all=JSON.parse(localStorage.getItem(legacy)),ids=new Set(cards.map(c=>c.sha));reviews=Object.fromEntries(Object.entries(all).filter(([sha])=>ids.has(sha)));status.textContent='Previous reviews loaded; export a backup.'}}}else reviews=JSON.parse(saved);if(!reviews||Array.isArray(reviews)||typeof reviews!=='object')reviews={};}catch(e){reviews={};status.textContent='Could not read saved reviews; you can import a backup.';}"""
assert oldload in template
template=template.replace(oldload,newload)
template=template.replace("for(const [key,label] of fields)dl.append(el('dt',label),el('dd',c[key]));", "for(const [key,label] of fieldsFor(c))dl.append(el('dt',label),el('dd',c[key]));if(c.justification)dl.append(el('dt','Rationale'),el('dd',c.justification));")
template=template.replace("for(const [key,label] of fields){const fs=el('fieldset');", "for(const [key,label] of fieldsFor(c)){const fs=el('fieldset');")
template=template.replace("root.replaceChildren();for(const c of cards){", "root.replaceChildren();const q=document.getElementById('search').value.toLowerCase(), domain=document.getElementById('domain-filter').value;const shown=cards.filter(c=>(!domain||c.domain===domain)&&[c.number,c.path,c.repository,c.domain,c.goal,c.task,c.justification].join(' ').toLowerCase().includes(q));document.getElementById('visible-count').textContent=`Shown: ${shown.length} / ${cards.length}`;for(const c of shown){")
template=template.replace("data.sample!==sample", "!(data.sample===sample || (typeof data.sample==='string' && data.sample.split(':').length===500 && data.sample.split(':').every(sha=>cards.some(c=>c.sha===sha))))")
template=template.replace("if(!confirm('Replace the reviews saved for this sample?'))return;reviews=data.reviews;", "if(!confirm('Merge imported reviews? Entries for matching skills will be replaced.'))return;reviews={...reviews,...data.reviews};")
template=template.replace('render();\n</script>', "for(const d of domains){const option=el('option',d);option.value=d;document.getElementById('domain-filter').append(option)}document.getElementById('domain-filter').addEventListener('change',render);document.getElementById('search').addEventListener('input',render);render();\n</script>")
payload=json.dumps(cards,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
assert template.count('/*CARD_DATA*/')==1
(root/'review-1000.html').write_text(template.replace('/*CARD_DATA*/',payload),encoding='utf-8')
counts=Counter(x['domain'] for x in items)
lines=['# Domain statistics — 1,000 skills','','Preliminary AI-assigned labels, not independently verified. The two samples were selected differently and the combined sample is not a random sample of the database.','','| Domain | Skills | Share |','| --- | ---: | ---: |']
lines += [f'| {d} | {n} | {n/len(items):.1%} |' for d,n in sorted(counts.items(),key=lambda x:(-x[1],x[0]))]
lines += ['| **Total** | **1000** | **100.0%** |']
(root/'domain-statistics-1000.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Combined 1000 skills; unique SHA:',len({x['sha'] for x in items}))
