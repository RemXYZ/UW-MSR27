# PCA and embeddings for the combined 1,000-skill sample

Open `wykres-3d.html` for two 3D plots or `porownanie.html` for the searchable comparison. The unified review with source text and earlier domain assessments is `../gitskills-semantic-board/review-1000.html`. Both plots run locally without internet.

Both variants use the same local `sentence-transformers/all-MiniLM-L6-v2` model, preprocessing and stopword list as the previous 500-skill experiment. They are recomputed for all 1,000 skills. Source text is front matter plus at most 4,000 body characters with fenced code removed; the model truncates the prepared input to 256 tokens including special tokens. The second variant removes selected stopwords before token truncation. See `results.json` for token counts and the exact stopword list.

PCA is fitted jointly to both sets of embeddings; k-means uses the full vectors and is fitted separately for each variant, with nine groups chosen for exploration. Group numbers are aligned to maximize overlap; equal numbers do not guarantee identical topics. Keywords are selected by the difference in mean TF-IDF inside versus outside each group, using the original prepared texts, and are descriptive rather than domain predictions. Domain labels are prior preliminary AI analyses; they are not independent human ground truth. The new joint PCA and clusters have been refitted, so coordinates, colors and group numbers are not directly comparable to the previous 500-skill plot. The combined sample is not a random sample of the full database.

`embeddings.npz` contains both vector matrices and their SHAs. `results.json` includes points, token counts, nearest-neighbor IDs and evaluation summaries; `comparison.csv` is a flat table. Neighbor overlap is computed in the original vector space, not 3D. Its interpretation includes both removal of words and changes to which text fits within the token limit.

Rebuild the combined board first using `../gitskills-semantic-board/build-1000.py`, then run from the workspace root:

```powershell
python -m pip install numpy scipy scikit-learn sentence-transformers
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
python .\gitskills-pca-1000\run.py
```

The script requires the GitSkills sample database at `gitskills-sample-main/agent_skills_sample/agent_skills_sample.db` in the repository root. The database is not included in this repository. Download the model once before running; the analysis itself loads it from the local cache. The script overwrites outputs in this folder. The 1,000-skill embedding files contain the original 500 vectors as well.
