## Dataset sample

The GitSkills sample contains **29,786 files** representing **13,000 distinct `SKILL.md` files**.

## Method 1: MinHash and LSH

The main script, `gitskills-lsh/scripts/lsh_analysis.py`, detects pairs
of potentially similar skills. It:

1. Reads the sample database and selects one representative per distinct content.
2. Divides each skill into five words shingles.
3. Uses MinHash and Locality-Sensitive Hashing (LSH) to identify candidate pairs.
4. Calculates two similarity measures for each candidate pair:
   - **Jaccard similarity** between the sets of shingles.
   - **Coverage of the shorter skill**: the proportion of its shingles that
     also appear in the longer skill. This helps identify cases where one
     version contains additional instructions.
5. Keeps pairs with a Jaccard similarity of at least 0.50 or a shorter-text
   coverage of at least 0.80.

The analysis is performed twice: on the full file and on the body without
front matter. A pair is kept if it meets either threshold in at least one
of these views.

The script produces two files in `gitskills-lsh/lsh_results/`:

- `lsh_pairs.csv` — the selected pairs and their similarity measures.
- `lsh_statistics.json` — summary counts and analysis parameters.

## Statistics

The analysis processed all **13,000 distinct contents** in the sample.
LSH identified **109,926 candidate pairs across the two views**; the same
pair could be counted once in each view. After calculating similarity
measures and combining the views, **11,249 pairs of distinct contents**
met the selected thresholds.

A view was excluded when it contained fewer than 20 distinct shingles.
This affected 104 full-file views and 228 body views.

## Manual review

A sample of 40 detected pairs was selected for an initial manual review.
Of these, 14 were labelled as probable modified copies and 26 as sharing
a template or fragment while serving different tasks.

The review files are:

- `lsh_review.html` — the selected pairs and their text differences.
- `lsh_labels.csv` — the labels and short explanations for the 40 pairs.

## Repository analysis

The script `gitskills-lsh/scripts/lsh_repository_stats.py` reads
`lsh_pairs.csv` and reports how many pairs have representatives
in the same repository or in repositories owned by the same account.
It also reports counts for the NeuralBlitz account.

Of the 11,249 detected pairs:

- 4,845 (43.1%) have both representatives in the same repository.
- 10,376 (92.2%) have both representatives under the same owner.
- 8,976 (79.8%) have both representatives in repositories owned
  by NeuralBlitz.
- 3,452 (30.7%) have both representatives in the same repository
  owned by NeuralBlitz.
