import re
from collections import Counter
from datetime import datetime, timedelta
from patient.db import get_db_connection, init_db

FLARE_THRESHOLD = 7   # skin_score >= this is a flare
LOOKBACK_DAYS   = 3   # days before a flare to examine for triggers

def get_logs():
    init_db()
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT date, foods, skin_score FROM daily_logs ORDER BY date ASC"
        ).fetchall()
    return [dict(r) for r in rows]

def scores_over_time(logs):
    """Returns (dates_list, scores_list) for plotting."""
    pairs = [(r["date"], r["skin_score"]) for r in logs
             if r["skin_score"] is not None]
    if not pairs:
        return [], []
    dates, scores = zip(*pairs)
    return list(dates), [int(s) for s in scores]

def pre_flare_foods(logs):
    """
    For each flare day (score >= FLARE_THRESHOLD), collect all foods
    eaten in the LOOKBACK_DAYS before it. Returns a Counter.
    """
    by_date = {r["date"]: r for r in logs}
    counter = Counter()
    for row in logs:
        if not row["skin_score"] or int(row["skin_score"]) < FLARE_THRESHOLD:
            continue
        dt = datetime.strptime(row["date"], "%Y-%m-%d")
        for delta in range(1, LOOKBACK_DAYS + 1):
            prev = (dt - timedelta(days=delta)).strftime("%Y-%m-%d")
            if prev in by_date and by_date[prev]["foods"]:
                for item in re.split(r"[,\n;]+", by_date[prev]["foods"]):
                    item = item.strip().lower()
                    if item:
                        counter[item] += 1
    return counter

def build_plot():
    """Returns a matplotlib Figure for gr.Plot."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    logs  = get_logs()
    dates, scores = scores_over_time(logs)
    counter = pre_flare_foods(logs)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7),
                                   gridspec_kw={"height_ratios": [2, 1]})

    # Top: skin score timeline
    if dates:
        ax1.plot(dates, scores, marker="o", color="#e05c5c", linewidth=2)
        ax1.axhline(FLARE_THRESHOLD, color="#aaa", linestyle="--",
                    label=f"Flare threshold ({FLARE_THRESHOLD})")
        ax1.set_ylabel("Skin Score (1–10)")
        ax1.set_title("Skin Response Over Time")
        ax1.set_ylim(0, 11)
        ax1.legend()
        step = max(1, len(dates) // 10)
        ax1.set_xticks(dates[::step])
        ax1.tick_params(axis="x", rotation=45)
    else:
        ax1.text(0.5, 0.5, "No data yet", ha="center", va="center",
                 transform=ax1.transAxes)

    # Bottom: pre-flare ingredient frequency
    if counter:
        top = counter.most_common(10)
        items, counts = zip(*top)
        bars = ax2.barh(list(items), list(counts), color="#5c8de0")
        ax2.set_xlabel("Frequency before flares")
        ax2.set_title(f"Most Common Foods in {LOOKBACK_DAYS} Days Before Flare-Ups")
    else:
        ax2.text(0.5, 0.5, "No flare data yet", ha="center", va="center",
                 transform=ax2.transAxes)

    fig.tight_layout()
    return fig