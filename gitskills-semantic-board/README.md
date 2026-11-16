# Review of 500 skills

Open `review-500-english.html` to review the cards and expand their source texts. `domain-statistics.md` counts the preliminary domain assignments in those cards. The counts do not reflect corrections saved in the browser.

The analyses are preliminary and were prepared mainly from opening excerpts of the source files; they have not been independently validated. Each card has one primary domain. `Insufficient Information` denotes cases where the sampled file does not describe a substantive skill clearly enough. The findings describe this sample and do not establish the distribution of the entire dataset.

**10 of the 500 skills (2.0%)** are classified as `Insufficient Information`.

Generating cards for 100 skills took approximately 2 minutes.

The selected 500 unique file identities are recorded in `sample-500-identities.json`. The sample was assembled in stages from unique nonempty contents in the local GitSkills database; it is not a simple random sample of 500 from the whole dataset.

`analyses-500.json` contains the analyses in sample order. `english-template.html` and `build-500.py` regenerate the review and statistics. The review HTML is self-contained; opening it does not require the database. Rebuilding requires the separate GitSkills sample SQLite database, which is not included here. The builder reads it without modification and verifies the selected identities. Run `python build-500.py --db PATH_TO_DATABASE` to rebuild; the `--db` argument can be omitted if the sample is in the adjacent `gitskills-sample-main/agent_skills_sample/agent_skills_sample.db` directory.

Reviews are stored locally in the browser. Export a JSON copy to keep them. Previously exported reviews for the 1,000-card version can be imported; only entries for the current 500 are retained.
