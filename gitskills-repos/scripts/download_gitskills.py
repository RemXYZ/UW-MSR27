"""Download all four GitSkills tables at a pinned Hugging Face revision.

Uses only the Python standard library. Files are streamed to disk, resumable,
and checked against the SHA-256 hashes published by Hugging Face.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError


ROOT = Path(__file__).resolve().parents[1]
DATASET = "mvaccargiu/gitskills"
API = f"https://huggingface.co/api/datasets/{DATASET}"
TABLES = {"artifacts", "repos", "artifact_siblings", "mining_runs"}
REQUEST_TIMEOUT = 120


def request(url, headers=None):
    return urlopen(Request(url, headers={"User-Agent": "GitSkills-analysis/1.0", **(headers or {})}), timeout=REQUEST_TIMEOUT)


def get_json(url):
    with request(url) as response:
        return json.load(response)


def save_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def file_hash(path, entry):
    algorithm = "sha256" if entry.get("sha256") else "sha1"
    digest = hashlib.new(algorithm)
    if algorithm == "sha1":
        digest.update(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid_file(path, entry):
    return (
        path.is_file()
        and path.stat().st_size == entry["size"]
        and file_hash(path, entry) == (entry.get("sha256") or entry["git_blob_sha1"])
    )


def load_manifest(destination, revision):
    manifest_path = destination / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if revision and revision != manifest["revision"]:
            raise ValueError("Use a different destination for another dataset revision.")
        return manifest
    revision = get_json(API + "/revision/" + (revision or "main"))["sha"]
    entries = []
    url = f"{API}/tree/{revision}?recursive=true&expand=false&limit=1000"
    while url:
        with request(url) as response:
            entries.extend(json.load(response))
            link = response.headers.get("Link", "")
        url = next((part.split("<", 1)[1].split(">", 1)[0] for part in link.split(",") if 'rel="next"' in part), None)
    files = []
    for entry in entries:
        name = entry["path"]
        if entry["type"] != "file" or not (name.endswith(".parquet") or name == "README.md"):
            continue
        parts = PurePosixPath(name)
        if parts.is_absolute() or ".." in parts.parts:
            raise ValueError(f"Unexpected remote path: {name}")
        lfs = entry.get("lfs") or {}
        files.append({"path": name, "size": entry["size"], "sha256": lfs.get("oid"), "git_blob_sha1": entry["oid"]})
    tables = {PurePosixPath(item["path"]).parts[1] for item in files if item["path"].endswith(".parquet")}
    if tables != TABLES:
        raise ValueError(f"Unexpected tables: {tables}")
    manifest = {
        "dataset": DATASET,
        "source_url": f"https://huggingface.co/datasets/{DATASET}",
        "zenodo_doi": "10.5281/zenodo.21875637",
        "revision": revision,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": sorted(files, key=lambda item: item["path"]),
    }
    save_json(manifest_path, manifest)
    return manifest


def download(entry, destination, revision):
    target = destination / entry["path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if valid_file(target, entry):
        return f"Verified existing: {entry['path']}"
    partial = target.with_suffix(target.suffix + ".partial")
    source_url = f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{entry['path']}?download=true"
    url = source_url
    consecutive_failures = 0
    for attempt in range(1, 10001):
        start_size = partial.stat().st_size if partial.exists() else 0
        try:
            offset = partial.stat().st_size if partial.exists() else 0
            if offset >= entry["size"]:
                if valid_file(partial, entry):
                    partial.replace(target)
                    return f"Verified: {entry['path']}"
                partial.unlink()
                offset = 0
            headers = {"Range": f"bytes={offset}-"} if offset else {}
            with request(url, headers) as response:
                # Reuse the CDN redirect while its signed URL is valid.
                # This avoids repeating all redirects for each resumed request.
                url = response.url
                append = offset > 0 and response.status == 206
                if append and not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
                    raise ValueError("Unexpected range response")
                with partial.open("ab" if append else "wb") as output:
                    # Persist short reads, so a broken TLS connection does not
                    # discard megabytes already received before the failure.
                    for chunk in iter(lambda: response.read1(64 * 1024), b""):
                        output.write(chunk)
            if not valid_file(partial, entry):
                raise ValueError(f"Size or checksum mismatch: {entry['path']}")
            partial.replace(target)
            return f"Downloaded and verified: {entry['path']}"
        except Exception as error:
            if isinstance(error, HTTPError) and error.code in (401, 403):
                url = source_url
            end_size = partial.stat().st_size if partial.exists() else 0
            consecutive_failures = 0 if end_size > start_size else consecutive_failures + 1
            if consecutive_failures >= 12 or attempt == 10000:
                raise
            if attempt <= 3 or attempt % 25 == 0 or consecutive_failures:
                print(f"Resuming {entry['path']} at {end_size:,} bytes: {error}", flush=True)
            time.sleep(min(2 ** consecutive_failures, 10) if consecutive_failures else 0.05)
    raise RuntimeError("Unreachable")


def main():
    global REQUEST_TIMEOUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=ROOT / "data" / "gitskills")
    parser.add_argument("--revision", help="Exact Hugging Face commit; resolved from main on the first run.")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=120, help="Per-connection socket timeout in seconds.")
    args = parser.parse_args()
    if not 1 <= args.workers <= 64 or args.timeout <= 0:
        parser.error("Use 1–64 workers and a positive timeout.")
    REQUEST_TIMEOUT = args.timeout
    args.destination.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(args.destination, args.revision)
    files = manifest["files"]
    total_bytes = sum(item["size"] for item in files)
    print(f"Revision: {manifest['revision']}", flush=True)
    print(f"Downloading {len(files)} files ({total_bytes / 1e9:.2f} GB) to {args.destination}", flush=True)
    priority = {"repos": 0, "artifacts": 1, "mining_runs": 2, "artifact_siblings": 3}
    ordered = sorted(files, key=lambda item: (priority.get(PurePosixPath(item["path"]).parent.name, -1), item["path"]))
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {pool.submit(download, item, args.destination, manifest["revision"]): item for item in ordered}
        for number, future in enumerate(as_completed(pending), 1):
            try:
                print(f"[{number}/{len(files)}] {future.result()}", flush=True)
            except Exception as error:
                failures.append(pending[future]["path"])
                print(f"FAILED {pending[future]['path']}: {error}", flush=True)
    if failures:
        raise RuntimeError(f"Rerun to resume {len(failures)} incomplete files: {failures}")
    manifest["download_completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["verified_files"] = len(files)
    manifest["total_bytes"] = total_bytes
    save_json(args.destination / "manifest.json", manifest)
    print("All dataset files downloaded and checksums verified.", flush=True)


if __name__ == "__main__":
    main()
