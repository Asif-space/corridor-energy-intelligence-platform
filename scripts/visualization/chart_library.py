import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import Config

STYLE = Config.CHART_STYLE
GOLD  = STYLE["gold"]
BLUE  = STYLE["blue"]
RED   = STYLE["red"]
GREEN = STYLE["green"]
BG    = STYLE["background"]
TEXT  = STYLE["text_color"]
GRID  = STYLE["grid_color"]

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor":   BG,
    "axes.edgecolor":   GRID,
    "axes.labelcolor":  TEXT,
    "text.color":       TEXT,
    "xtick.color":      TEXT,
    "ytick.color":      TEXT,
    "grid.color":       GRID,
    "grid.alpha":       0.5,
    "axes.grid":        True,
    "axes.grid.axis":   "y",
    "font.family":      "monospace",
})


class CorridorCharts:

    def __init__(self):
        self.save_dir = Config.EXPORTS_DIR
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def _watermark(self, fig):
        fig.text(0.99, 0.01, "The Corridor Brief",
                 ha="right", va="bottom", fontsize=8,
                 color=GOLD, alpha=0.6, fontstyle="italic")

    def _source(self, ax, source):
        ax.text(0, -0.1, f"Source: {source}",
                transform=ax.transAxes,
                fontsize=8, color=TEXT, alpha=0.5)

    def _save(self, fig, filename):
        ts   = datetime.now().strftime("%Y%m%d")
        path = self.save_dir / f"{ts}_{filename}.png"
        fig.savefig(path, dpi=STYLE["dpi"], bbox_inches="tight",
                    facecolor=BG, edgecolor="none")
        plt.close(fig)
        print(f"  ✓ Chart saved: {path}")
        return path

    def crude_inventory_vs_5yr(self, df):
        """
        Core Wednesday chart.
        Crude oil inventories vs 5-year seasonal average.
        Unit: EIA reports crude stocks in thousand barrels — divide by 1000 for Mb.
        """
        fig, ax = plt.subplots(figsize=(12, 6))

        series = df.iloc[:, 0].dropna() / 1000  # Convert kb to Mb

        cutoff  = pd.Timestamp("2021-01-01")
        hist    = series[series.index < cutoff]
        recent  = series[series.index >= pd.Timestamp("2022-01-01")]

        if hist.empty or recent.empty:
            print("  ⚠ Not enough data for 5yr average calculation")
            return None

        hist_df        = hist.to_frame("val")
        hist_df["week"] = hist_df.index.isocalendar().week.astype(int)
        avg             = hist_df.groupby("week")["val"].mean()
        std             = hist_df.groupby("week")["val"].std()

        rec_df          = recent.to_frame("val")
        rec_df["week"]  = rec_df.index.isocalendar().week.astype(int)
        rec_df["avg"]   = rec_df["week"].map(avg)
        rec_df["upper"] = rec_df["week"].map(
            lambda w: avg.get(w, np.nan) + std.get(w, np.nan))
        rec_df["lower"] = rec_df["week"].map(
            lambda w: avg.get(w, np.nan) - std.get(w, np.nan))

        ax.fill_between(rec_df.index, rec_df["lower"], rec_df["upper"],
                        alpha=0.12, color=BLUE, label="5-Year Range (±1σ)")
        ax.plot(rec_df.index, rec_df["avg"],
                color=BLUE, linewidth=1.5, linestyle="--",
                alpha=0.7, label="5-Year Average")
        ax.plot(rec_df.index, rec_df["val"],
                color=GOLD, linewidth=2.5,
                label="US Crude Stocks (Mb)")

        latest  = rec_df["val"].iloc[-1]
        avg_now = rec_df["avg"].iloc[-1]
        diff    = latest - avg_now
        color   = GREEN if diff > 0 else RED
        label   = f"+{diff:.1f} Mb surplus" if diff > 0 else f"{diff:.1f} Mb deficit"

        ax.annotate(label,
                    xy=(rec_df.index[-1], latest),
                    xytext=(-100, 25), textcoords="offset points",
                    fontsize=10, color=color,
                    arrowprops=dict(arrowstyle="->", color=color))

        ax.set_title("US Crude Oil Inventories vs 5-Year Seasonal Average",
                     fontsize=14, color=TEXT, pad=15, fontweight="bold")
        ax.set_ylabel("Million Barrels (Mb)", fontsize=11)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        plt.xticks(rotation=30, ha="right")
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.legend(fontsize=9, framealpha=0.2, loc="upper left")

        self._watermark(fig)
        self._source(ax, "EIA Weekly Petroleum Status Report")
        return self._save(fig, "crude_inventory_5yr")

    def price_history(self, df, label="Brent Crude", days=365):
        """Price history chart — standard LinkedIn/Twitter format."""
        fig, ax = plt.subplots(figsize=(12, 6))

        data = df.iloc[-days:].dropna()
        ax.plot(data.index, data.iloc[:, 0],
                color=GOLD, linewidth=2, label=label)
        ax.fill_between(data.index, data.iloc[:, 0],
                        alpha=0.08, color=GOLD)

        latest = data.iloc[-1, 0]
        ax.axhline(latest, color=GOLD, linewidth=0.7,
                   linestyle=":", alpha=0.4)
        ax.text(data.index[-1], latest * 1.005,
                f"  ${latest:.2f}",
                va="bottom", ha="right",
                fontsize=11, color=GOLD, fontweight="bold")

        ax.set_title(f"{label} Price",
                     fontsize=14, color=TEXT, pad=15, fontweight="bold")
        ax.set_ylabel("USD / Barrel", fontsize=11)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=30, ha="right")
        ax.legend(fontsize=10, framealpha=0.2)

        self._watermark(fig)
        self._source(ax, "EIA")
        return self._save(fig, "price_history")

    def inventory_draws(self, df, weeks=26):
        """
        Weekly crude inventory change — draws (green) vs builds (red).
        Classic commodity bar chart.
        """
        fig, ax = plt.subplots(figsize=(14, 5))

        series  = df.iloc[:, 0].dropna() / 1000  # Convert to Mb
        changes = series.diff().iloc[-weeks:].dropna()
        colors  = [GREEN if v < 0 else RED for v in changes.values]

        ax.bar(changes.index, changes.values,
               color=colors, alpha=0.85, width=5)
        ax.axhline(0, color=TEXT, linewidth=0.8)
        ax.axhline(changes.mean(), color=GOLD, linewidth=1.2,
                   linestyle="--",
                   label=f"{weeks}wk avg: {changes.mean():.1f} Mb")

        ax.set_title("US Crude Oil Weekly Inventory Change",
                     fontsize=14, color=TEXT, pad=15, fontweight="bold")
        ax.set_ylabel("Change (Million Barrels)", fontsize=11)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.xticks(rotation=30, ha="right")
        ax.legend(fontsize=10, framealpha=0.2)

        self._watermark(fig)
        self._source(ax, "EIA Weekly Petroleum Status Report")
        return self._save(fig, "inventory_draws")