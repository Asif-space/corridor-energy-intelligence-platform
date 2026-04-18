import sys
import json
import time
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import Config


class EIAPipeline:

    def __init__(self):
        if not Config.EIA_API_KEY or Config.EIA_API_KEY == "paste_your_key_here":
            print("ERROR: EIA API key not set.")
            sys.exit(1)
        self.api_key = Config.EIA_API_KEY

    def fetch_series(self, name, series_id, start="2019-01-01"):
        url = f"https://api.eia.gov/v2/seriesid/{series_id}"
        params = {
            "api_key": self.api_key,
            "start":   start,
            "length":  5000,
        }

        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()

            records = data.get("response", {}).get("data", [])
            if not records:
                print(f"  ⚠ No data for: {name}")
                return pd.DataFrame()

            df = pd.DataFrame(records)

            # Handle both weekly (YYYYMMDD) and daily period formats
            df["period"] = pd.to_datetime(df["period"], errors="coerce")
            df = df.dropna(subset=["period"])
            df = df.set_index("period").sort_index()

            # EIA v2 returns value in a column — find it
            val_col = [c for c in df.columns if "value" in c.lower()]
            if not val_col:
                val_col = [df.columns[0]]
            df = df[[val_col[0]]].copy()
            df.columns = [name]
            df[name] = pd.to_numeric(df[name], errors="coerce")
            return df

        except Exception as e:
            print(f"  ✗ Failed {name}: {e}")
            return pd.DataFrame()

    def run(self):
        print(f"\n{'='*55}")
        print(f"  EIA Weekly Petroleum Status Report")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*55}")

        results = {}
        for name, series_id in Config.EIA_SERIES.items():
            print(f"  Pulling: {name}...")
            df = self.fetch_series(name, series_id)
            if not df.empty:
                results[name] = df
                print(f"  ✓ {len(df)} observations")
            else:
                print(f"  ✗ No data returned")
            time.sleep(0.3)

        return results

    def save(self, data):
        timestamp = datetime.now().strftime("%Y%m%d")
        save_dir = Config.EIA_RAW / timestamp
        save_dir.mkdir(parents=True, exist_ok=True)

        for name, df in data.items():
            if not df.empty:
                df.to_csv(save_dir / f"{name}.csv")

        dfs = [df for df in data.values() if not df.empty]
        if dfs:
            combined = pd.concat(dfs, axis=1)
            combined.to_parquet(save_dir / f"eia_weekly_{timestamp}.parquet")

        print(f"\n  ✓ Data saved to: data/raw/eia/{timestamp}/")
        return save_dir

    def summary(self, data):
        print(f"\n{'='*55}")
        print(f"  WEEKLY SUMMARY")
        print(f"{'='*55}")

        metrics = [
            ("crude_stocks_total",    "Crude Stocks (Mb)"),
            ("crude_stocks_cushing",  "Cushing Stocks (Mb)"),
            ("crude_production_us",   "US Production (Mbd)"),
            ("refinery_utilisation",  "Refinery Util (%)"),
            ("gasoline_stocks_total", "Gasoline Stocks (Mb)"),
            ("distillate_stocks",     "Distillate Stocks (Mb)"),
            ("crude_imports",         "Crude Imports (Mbd)"),
        ]

        summary_dict = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "metrics": {}
        }

        for key, label in metrics:
            if key in data and not data[key].empty:
                latest = data[key].iloc[-1, 0]
                prev   = data[key].iloc[-2, 0] if len(data[key]) > 1 else None
                change = latest - prev if prev is not None else 0
                arrow  = "▲" if change > 0 else "▼" if change < 0 else "—"
                print(f"  {label:<30} {latest:>8.1f}  {arrow} {abs(change):.1f}")
                summary_dict["metrics"][key] = {
                    "label":  label,
                    "latest": round(float(latest), 2),
                    "change": round(float(change), 2)
                }
            else:
                print(f"  {label:<30} {'N/A':>8}")

        for price_key, label in [("wti_spot", "WTI Spot"), ("brent_spot", "Brent Spot")]:
            if price_key in data and not data[price_key].empty:
                price = data[price_key].iloc[-1, 0]
                print(f"  {label:<30} ${price:>7.2f}")

        print(f"{'='*55}\n")

        summary_path = Config.EIA_RAW / "latest_summary.json"
        with open(summary_path, "w") as f:
            json.dump(summary_dict, f, indent=2)
        print(f"  Summary saved to: data/raw/eia/latest_summary.json")


def main():
    pipeline = EIAPipeline()
    data = pipeline.run()
    pipeline.save(data)
    pipeline.summary(data)
    print("  Pipeline complete.\n")


if __name__ == "__main__":
    main()