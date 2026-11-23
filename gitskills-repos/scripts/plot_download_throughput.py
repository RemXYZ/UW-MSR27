"""Render the throughput log for display in chat, independently of the notebook."""

from pathlib import Path
from zoneinfo import ZoneInfo
import os

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".jupyter" / "matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

data = pd.read_csv(ROOT / "results" / "download_throughput.csv")
data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True)
data = data.set_index("timestamp_utc")
rate = data["throughput_MB_s"]
smooth = rate.rolling("60s", min_periods=1).mean()

fig, ax = plt.subplots(figsize=(11, 4.5))
ax.plot(rate.index, rate, color="#93c5fd", linewidth=1, label="Pomiary co 10 s")
ax.plot(smooth.index, smooth, color="#1d4ed8", linewidth=2, label="Średnia z 1 minuty")
ax.set(title="GitSkills — przepustowość pobierania", xlabel="Czas lokalny (Europe/Warsaw)",
       ylabel="MB/s (1 MB = 1 000 000 bajtów)", ylim=(0, None))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=ZoneInfo("Europe/Warsaw")))
ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=10))
ax.grid(alpha=0.2)
ax.legend(frameon=False, loc="upper right")
fig.text(0.08, 0.01, "Tempo przyrostu lokalnych plików datasetu; pomiar rozpoczęto podczas pobierania.",
         fontsize=9, color="#475569")
fig.tight_layout(rect=(0, 0.05, 1, 1))
output = ROOT / "results" / "download_throughput.png"
fig.savefig(output, dpi=160)
plt.close(fig)
print(output)
