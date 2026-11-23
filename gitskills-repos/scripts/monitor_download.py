"""Record useful download throughput every 10 seconds (outside the notebook)."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "gitskills"
MANIFEST = DATA_DIR / "manifest.json"
OUTPUT = ROOT / "results" / "download_throughput.csv"
INTERVAL = 10


def downloaded_bytes(manifest):
    total = 0
    for entry in manifest["files"]:
        if not entry["path"].endswith(".parquet"):
            continue
        target = DATA_DIR / entry["path"]
        partial = target.with_suffix(target.suffix + ".partial")
        # The downloader atomically renames .partial to the final filename.
        for candidate in (target, partial, target):
            try:
                total += candidate.stat().st_size
                break
            except FileNotFoundError:
                pass
    return total


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    fields = ["timestamp_utc", "interval_seconds", "downloaded_bytes", "delta_bytes", "throughput_MB_s"]
    first = not OUTPUT.exists() or OUTPUT.stat().st_size == 0
    previous_bytes = None
    previous_time = None
    samples = 0
    with OUTPUT.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        if first:
            writer.writeheader()
        while True:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
            current_bytes = downloaded_bytes(manifest)
            now = time.monotonic()
            interval = now - previous_time if previous_time is not None else None
            delta = current_bytes - previous_bytes if previous_bytes is not None else None
            # A negative change can mean a corrupt partial file was discarded;
            # leave that interval unestimated instead of inventing a speed.
            speed = delta / interval / 1e6 if delta is not None and delta >= 0 else None
            writer.writerow({
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "interval_seconds": round(interval, 3) if interval is not None else "",
                "downloaded_bytes": current_bytes,
                "delta_bytes": delta if delta is not None else "",
                "throughput_MB_s": round(speed, 6) if speed is not None else "",
            })
            stream.flush()
            samples += 1
            if samples == 1 or samples % 6 == 0:
                rate = f"{speed:.2f} MB/s" if speed is not None else "baseline"
                print(f"{current_bytes / 1e9:.2f} GB downloaded; {rate}", flush=True)
            if manifest.get("download_completed_at_utc"):
                print(f"Monitoring complete: {OUTPUT}", flush=True)
                break
            previous_bytes, previous_time = current_bytes, now
            time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
