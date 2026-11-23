"""Check the complete dataset and exported aggregation outside the simple notebook."""

from datetime import datetime, timezone
import json
from pathlib import Path

import duckdb
import nbformat
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "gitskills"
OUT = ROOT / "results"
manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
assert manifest.get("verified_files") == len(manifest["files"])
for entry in manifest["files"]:
    assert (DATA / entry["path"]).stat().st_size == entry["size"], entry["path"]

con = duckdb.connect()
expected = {"artifacts": 3_797_117, "repos": 282_200, "artifact_siblings": 7_264_865, "mining_runs": 7}
actual = {}
for table in expected:
    con.read_parquet(str(DATA / f"data/{table}/*.parquet")).create_view(table)
    actual[table] = con.sql(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
assert actual == expected, actual

checks = {
    "invalid_artifact_keys": "SELECT COUNT(*) FROM artifacts WHERE repo_full_name IS NULL OR trim(repo_full_name) = '' OR path IS NULL OR trim(path) = ''",
    "duplicate_repo_path_pairs": "SELECT COUNT(*) FROM (SELECT repo_full_name, path FROM artifacts GROUP BY repo_full_name, path HAVING COUNT(*) > 1)",
    "invalid_repo_names": "SELECT COUNT(*) FROM repos WHERE full_name IS NULL OR trim(full_name) = ''",
    "duplicate_repositories": "SELECT COUNT(*) - COUNT(DISTINCT full_name) FROM repos",
    "artifact_repos_missing_from_repos": "SELECT COUNT(*) FROM artifacts a LEFT JOIN repos r ON a.repo_full_name = r.full_name WHERE r.full_name IS NULL",
}
validation = {name: con.sql(sql).fetchone()[0] for name, sql in checks.items()}
assert all(value == 0 for value in validation.values()), validation

result = pd.read_csv(OUT / "skills_per_repository.csv", dtype={"repo_full_name": "str", "n_skills": "int64"})
pd.testing.assert_frame_equal(result, con.read_parquet(str(OUT / "skills_per_repository.parquet")).df())
assert len(result) == expected["repos"]
assert result["repo_full_name"].is_unique
assert result["n_skills"].ge(0).all()
assert int(result["n_skills"].sum()) == expected["artifacts"]

notebook = nbformat.read(ROOT / "notebooks" / "skills_per_repository.ipynb", as_version=4)
nbformat.validate(notebook)
code_cells = [cell for cell in notebook.cells if cell.cell_type == "code"]
assert all(cell.execution_count is not None for cell in code_cells)
assert not any(output.output_type == "error" for cell in code_cells for output in cell.outputs)
assert sum("image/png" in output.get("data", {}) for cell in code_cells for output in cell.outputs) == 3

summary = {
    "repositories": len(result),
    "skill_occurrences": int(result["n_skills"].sum()),
    "repositories_with_zero_skills": int(result["n_skills"].eq(0).sum()),
    "min_skills": int(result["n_skills"].min()),
    "median_skills": float(result["n_skills"].median()),
    "mean_skills": float(result["n_skills"].mean()),
    "max_skills": int(result["n_skills"].max()),
    "dataset": manifest["dataset"],
    "dataset_revision": manifest["revision"],
    "source_url": manifest["source_url"],
    "download_completed_at_utc": manifest["download_completed_at_utc"],
    "validated_at_utc": datetime.now(timezone.utc).isoformat(),
    "table_rows": actual,
    "validation": validation,
    "csv_parquet_match": True,
    "notebook_code_cells_executed": len(code_cells),
    "notebook_charts": 3,
}
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
con.close()
