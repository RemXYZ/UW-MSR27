#!/usr/bin/env python3
"""Reproducible near-clone pilot using NumPy for MinHash signatures."""
import argparse
import csv
import functools
import hashlib
import json
import re
import sqlite3
import struct
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
WORD = re.compile(r"\w+", re.UNICODE)
N = 5
MIN_SHINGLES = 20
BANDS = 32
ROWS = 4

def mix64(x):
    """SplitMix64, using unsigned arithmetic modulo 2**64 as in the first pilot."""
    with np.errstate(over='ignore'):
        x = x + np.uint64(0x9e3779b97f4a7c15)
        x = (x ^ (x >> np.uint64(30))) * np.uint64(0xbf58476d1ce4e5b9)
        x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94d049bb133111eb)
        return x ^ (x >> np.uint64(31))

SEEDS = mix64(np.arange(BANDS * ROWS, dtype=np.uint64))

def minhash_signature(shingle_set):
    """Return the same 128 minima as the original C# implementation."""
    if not shingle_set:
        raise ValueError('MinHash wymaga co najmniej jednego shingla')
    values = np.fromiter(shingle_set, dtype=np.uint64, count=len(shingle_set))
    minima = np.full(BANDS * ROWS, np.iinfo(np.uint64).max, dtype=np.uint64)
    for start in range(0, len(values), 1024):
        hashes = mix64(values[start:start+1024, None] ^ SEEDS)
        minima = np.minimum(minima, hashes.min(axis=0))
    return tuple(int(x) for x in minima)

def body(text):
    # Recognise front matter only when the closing delimiter exists.
    match = re.match(r"\A\ufeff?---[ \t]*\r?\n.*?\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|$)", text, re.S)
    return text[match.end():] if match else text

def shingles(text):
    words = WORD.findall(text.casefold())
    # Stable 64-bit hashes make sets much smaller; hash collisions are possible.
    return {int.from_bytes(hashlib.blake2b(' '.join(words[i:i+N]).encode('utf-8'), digest_size=8).digest(), 'little')
            for i in range(len(words)-N+1)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', type=Path, default=ROOT.parent / 'gitskills-sample-main/agent_skills_sample/agent_skills_sample.db')
    ap.add_argument('--output', type=Path, default=ROOT / 'lsh_results')
    ap.add_argument('--min-jaccard', type=float, default=.5)
    ap.add_argument('--min-containment', type=float, default=.8)
    args = ap.parse_args()
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(args.db.resolve().as_uri() + '?mode=ro', uri=True)
    cache = sqlite3.connect(out / 'robocze.sqlite')
    cache.executescript('DROP TABLE IF EXISTS sets; CREATE TABLE sets (id INTEGER PRIMARY KEY, sha TEXT, view TEXT, n INTEGER, data BLOB);')
    rows = source.execute('''SELECT a.file_sha, a.repo_full_name, a.path, a.name, a.content,
       (SELECT COUNT(*) FROM artifacts b WHERE b.file_sha=a.file_sha),
       (SELECT COUNT(DISTINCT repo_full_name) FROM artifacts b WHERE b.file_sha=a.file_sha)
       FROM artifacts a WHERE a.dedup_primary=1 AND a.content IS NOT NULL ORDER BY a.file_sha''').fetchall()
    metadata = {}; counts = Counter(); sig = out / 'signatures.tmp'
    print('Przygotowanie dokumentów:', len(rows), flush=True)
    with sig.open('w', encoding='ascii') as f:
        idx = 0
        for sha, repo, path, name, text, copies, repos in rows:
            metadata[sha] = dict(repo=repo, path=path, name=name or '', copies=copies, repos=repos)
            for view, value in [('full', text), ('body', body(text))]:
                s = shingles(value); counts[view + '_total'] += 1
                if len(s) < MIN_SHINGLES:
                    counts[view + '_short'] += 1; continue
                idx += 1
                cache.execute('INSERT INTO sets VALUES (?,?,?,?,?)', (idx, sha, view, len(s), struct.pack('<%dQ' % len(s), *s)))
                signature = minhash_signature(s)
                f.write(str(idx) + ' ' + ' '.join(format(x, '016x') for x in signature) + '\n')
        cache.commit()
    print('Obliczone sygnatury:', idx, flush=True)
    buckets = defaultdict(list)
    idinfo = {i:(sha,v,n) for i,sha,v,n in cache.execute('SELECT id,sha,view,n FROM sets')}
    pairs = set()
    with sig.open(encoding='ascii') as f:
        for line in f:
            parts = line.split(); i = int(parts[0]); view = idinfo[i][1]
            for band in range(BANDS):
                key = (view, band, *parts[1+band*ROWS:1+(band+1)*ROWS])
                for j in buckets[key]:
                    pairs.add((j, i))
                buckets[key].append(i)
    print('Pary kandydatów:', len(pairs), flush=True)
    @functools.lru_cache(maxsize=256)
    def get_set(i):
        n, blob = cache.execute('SELECT n,data FROM sets WHERE id=?', (i,)).fetchone()
        return set(struct.unpack('<%dQ' % n, blob))
    # One row per pair of hashes, reporting scores separately for each view.
    results = {}
    for i,j in sorted(pairs):
        sha1, view, n1 = idinfo[i]; sha2, _, n2 = idinfo[j]
        if sha1 == sha2: continue
        intersection = len(get_set(i) & get_set(j))
        jac = intersection / (n1+n2-intersection)
        contain = intersection / min(n1,n2)
        if jac < args.min_jaccard and contain < args.min_containment: continue
        key = tuple(sorted((sha1,sha2)))
        result = results.setdefault(key, {'sha_a':key[0], 'sha_b':key[1]})
        result.update({view+'_jaccard': round(jac,4), view+'_containment': round(contain,4),
                       view+'_shared': intersection, view+'_size_a': n1 if sha1 == key[0] else n2,
                       view+'_size_b': n2 if sha1 == key[0] else n1})
    # Evaluate both views for every retained pair, even if LSH found only one view.
    ids = {(sha, view):i for i,(sha,view,n) in idinfo.items()}
    for key, result in results.items():
        for view in ('full','body'):
            a, b = ids.get((key[0],view)), ids.get((key[1],view))
            if a is None or b is None: continue
            sa,sb = get_set(a),get_set(b); common=len(sa & sb)
            result.update({view+'_jaccard':round(common/len(sa|sb),4), view+'_containment':round(common/min(len(sa),len(sb)),4), view+'_shared':common, view+'_size_a':len(sa), view+'_size_b':len(sb)})
        for suffix,sha in zip(('a','b'),key):
            for field,value in metadata[sha].items(): result[field+'_'+suffix] = value
    fields = ['sha_a','sha_b','name_a','name_b','repo_a','path_a','repo_b','path_b','copies_a','repos_a','copies_b','repos_b'] + [v+'_'+x for v in ('full','body') for x in ('jaccard','containment','shared','size_a','size_b')]
    ranked = sorted(results.values(),key=lambda r:max(r.get('full_jaccard',0),r.get('body_jaccard',0)),reverse=True)
    with (out/'lsh_pairs.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(ranked)
    stats = dict(documents=len(rows), views=dict(counts), candidate_view_pairs=len(pairs), retained_content_pairs=len(results), parameters={'shingle_words':N,'min_shingles':MIN_SHINGLES,'hash_bits':64,'permutations':128,'bands':BANDS,'rows_per_band':ROWS,'min_jaccard':args.min_jaccard,'min_containment':args.min_containment})
    (out/'lsh_statistics.json').write_text(json.dumps(stats,indent=2,ensure_ascii=False),encoding='utf-8')
    cache.close(); source.close(); sig.unlink(); (out / 'robocze.sqlite').unlink()
    print(json.dumps(stats,ensure_ascii=False,indent=2),flush=True)

if __name__ == '__main__': main()
