from pathlib import Path
import csv, json, re, sqlite3, time
from collections import Counter
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, silhouette_score
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
items = json.loads((BASE/'gitskills-semantic-board/analyses-1000.json').read_text(encoding='utf-8'))
with sqlite3.connect((BASE/'gitskills-sample-main/agent_skills_sample/agent_skills_sample.db').as_uri()+'?mode=ro', uri=True) as db:
    ids = {item['sha'] for item in items}
    contents = {sha: content for sha, content in db.execute('SELECT file_sha, content FROM artifacts WHERE dedup_primary=1 AND content IS NOT NULL') if sha in ids}
    for item in items:
        if item['sha'] not in contents: raise ValueError(item['sha'])
        item['content'] = contents[item['sha']]

# Same input preparation as the original experiment. No label or generated analysis in model input.
def prepare(s):
    fm = re.match(r'^\s*---\s*\n(.*?)\n---\s*(?:\n|$)', s, re.S)
    head, body = (fm.group(1), s[fm.end():]) if fm else ('', s)
    return (head+'\n'+re.sub(r'```[\s\S]*?```', ' ', body)[:4000]).strip()

stop = set('a an the and or but if then than of in on at to for from by with as is are was were be been being this that these those it its which who whom what when where how can could should would may might will shall do does did have has had having i you your we our they their he she his her them us me my into about'.split())
# Do not alter words inside contractions or hyphenated technical identifiers.
word = re.compile(r"(?<![\w'’-])[A-Za-z]+(?![\w'’-])")
def remove_stop(s):
    return word.sub(lambda m: '' if m.group().lower() in stop else m.group(), s)

texts = [prepare(x['content']) for x in items]
variants = [texts, [remove_stop(x) for x in texts]]
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu', local_files_only=True)
counts = [[len(model.tokenizer.encode(t, truncation=False)) for t in v] for v in variants]
vectors = []
for i,v in enumerate(variants):
    print('Encoding', i+1, flush=True)
    vectors.append(np.asarray(model.encode(v, batch_size=32, show_progress_bar=True, normalize_embeddings=True), dtype=np.float32))
np.savez_compressed(ROOT/'embeddings.npz', baseline=vectors[0], stopwords=vectors[1], sha=np.array([x['sha'] for x in items]))

# Common coordinate system makes point positions directly comparable.
pca = PCA(n_components=3, svd_solver='full')
coords = pca.fit_transform(np.vstack(vectors)).reshape(2,len(items),3)
k = 9 # exploratory resolution, not the number of objectively established domains
raw = [KMeans(n_clusters=k, random_state=42, n_init=20).fit_predict(v) for v in vectors]
cont = np.zeros((k,k), dtype=int)
for a,b in zip(*raw): cont[a,b] += 1
rows, cols = linear_sum_assignment(-cont)
mapping = dict(zip(cols,rows))
clusters = [raw[0], np.array([mapping[x] for x in raw[1]])]

# Keywords describe source material, not generated labels; use the same texts for both partitions.
tfidf = TfidfVectorizer(stop_words='english', token_pattern=r'(?u)\b[a-zA-Z][a-zA-Z0-9_+-]{2,}\b', max_df=.85, min_df=2, sublinear_tf=True)
matrix = tfidf.fit_transform(texts)
terms = tfidf.get_feature_names_out()
keywords = []
for c in clusters:
    groups = []
    for j in range(k):
        inside = np.asarray(matrix[c==j].mean(axis=0)).ravel()
        outside = np.asarray(matrix[c!=j].mean(axis=0)).ravel()
        rank = np.argsort(inside-outside)[::-1]
        groups.append([str(terms[q]) for q in rank[:6]])
    keywords.append(groups)

def nearest(v):
    sim = v@v.T
    np.fill_diagonal(sim, -np.inf)
    return np.argsort(-sim, axis=1)[:,:10]
near = [nearest(v) for v in vectors]
overlap = np.mean([len(set(a)&set(b))/10 for a,b in zip(*near)])
data = []
for i,x in enumerate(items):
    data.append({'number':x['number'],'sha':x['sha'],'repository':x['repository'],'path':x['path'],'domain':x['domain'],
        'goal':x.get('goal',x.get('justification','')), 'coords':coords[:,i,:].round(5).tolist(), 'clusters':[int(c[i])+1 for c in clusters],
        'tokens':[int(t[i]) for t in counts], 'neighbors':[[int(items[j]['number']) for j in n[i][:5]] for n in near]})
report = {'model':'sentence-transformers/all-MiniLM-L6-v2', 'n':len(items), 'k':k, 'seed':42,
 'pca_explained_variance_ratio':pca.explained_variance_ratio_.tolist(), 'keywords':keywords,
 'stopwords':sorted(stop), 'max_sequence_length':model.max_seq_length,
 'over_limit':[sum(n>model.max_seq_length for n in c) for c in counts],
 'median_tokens':[float(np.median(c)) for c in counts],
 'neighbor_overlap_at_10':float(overlap), 'cluster_ari':float(adjusted_rand_score(*clusters)),
 'unchanged_cluster_fraction':float(np.mean(clusters[0]==clusters[1])),
 'silhouette_cosine':[float(silhouette_score(v,c,metric='cosine')) for v,c in zip(vectors,clusters)],
 'cluster_sizes':[[int(sum(c==j)) for j in range(k)] for c in clusters]}
(ROOT/'results.json').write_text(json.dumps({'report':report,'skills':data},ensure_ascii=False,indent=2),encoding='utf-8')
with (ROOT/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f); w.writerow(['number','sha','repository','path','previous_domain','cluster_baseline','cluster_stopwords','tokens_baseline','tokens_stopwords'])
    for x in data: w.writerow([x['number'],x['sha'],x['repository'],x['path'],x['domain'],*x['clusters'],*x['tokens']])
template=(ROOT/'template.html').read_text(encoding='utf-8')
payload=json.dumps({'report':report,'skills':data},ensure_ascii=False).replace('</','<\\/')
for mode,name in [('plot','wykres-3d.html'),('table','porownanie.html')]:
    (ROOT/name).write_text(template.replace('/* DATA */', 'const DATA = '+payload+';').replace('/* MODE */', 'const MODE = "'+mode+'";'),encoding='utf-8')
print(json.dumps(report, ensure_ascii=False,indent=2), flush=True)
