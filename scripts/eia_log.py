import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config

LOG_FILE = Config.DATA_DIR / "eia_interpretation_log.json"


def load_log():
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return []


def save_log(entries):
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2, default=str)


def new_entry():
    week = datetime.now().isocalendar()[1]
    date = datetime.now().strftime("%Y-%m-%d")

    print(f"\n{'='*55}")
    print(f"  EIA Interpretation Log — Week {week}")
    print(f"  {date}")
    print(f"{'='*55}\n")

    data = {}
    data["crude_change"]      = input("  Crude inventory change this week (Mb): ")
    data["refinery_util"]     = input("  Refinery utilisation (%): ")
    data["production"]        = input("  US crude production (Mbd): ")
    data["gasoline_change"]   = input("  Gasoline inventory change (Mb): ")
    data["distillate_change"] = input("  Distillate inventory change (Mb): ")
    data["analyst_expect"]    = input("  Analyst consensus expectation (Mb): ")
    data["surprise"]          = input("  Surprise [bullish / bearish / neutral]: ")
    data["brent"]             = input("  Brent spot price (USD/bbl): ")
    data["wti"]               = input("  WTI spot price (USD/bbl): ")

    print("\n  Write your market interpretation.")
    print("  What does this data mean for oil prices?")
    print("  150-250 words. Press Enter twice when done.\n")

    lines = []
    while True:
        line = input("  ")
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    interpretation = "\n".join(lines).strip()

    corridor = input("\n  Corridor angle (South Asia / Gulf / Africa implication): ")
    twitter  = input("  X/Twitter draft (2 sentences max): ")

    return {
        "week":           week,
        "date":           date,
        "data":           data,
        "interpretation": interpretation,
        "corridor_note":  corridor,
        "twitter_draft":  twitter,
    }


def review(entries, n=5):
    if not entries:
        print("\n  No entries yet. Run your first log this Wednesday.")
        return

    print(f"\n{'='*55}")
    print(f"  EIA Log — Last {min(n, len(entries))} Entries")
    print(f"{'='*55}")

    for e in entries[-n:]:
        print(f"\n  Week {e['week']} | {e['date']}")
        print(f"  Crude Δ: {e['data'].get('crude_change','?')} Mb  |  "
              f"Brent: ${e['data'].get('brent','?')}  |  "
              f"{e['data'].get('surprise','?').upper()}")
        preview = e.get("interpretation", "")[:120]
        print(f"  → {preview}...")

    print(f"\n  Total entries: {len(entries)}")


def export_markdown(entries):
    if not entries:
        print("\n  No entries to export yet.")
        return

    out = Config.REPORTS_DIR / f"eia_log_{datetime.now().strftime('%Y%m%d')}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# The Corridor Brief — EIA Interpretation Log\n",
        f"*{len(entries)} entries | Exported {datetime.now().strftime('%Y-%m-%d')}*\n\n---\n"
    ]

    for e in entries:
        lines += [
            f"## Week {e['week']} — {e['date']}\n\n",
            f"**Crude Δ:** {e['data'].get('crude_change','?')} Mb | "
            f"**Brent:** ${e['data'].get('brent','?')} | "
            f"**Surprise:** {e['data'].get('surprise','?').upper()}\n\n",
            f"{e.get('interpretation','')}\n\n",
            f"**Corridor:** {e.get('corridor_note','')}\n\n",
            f"> **Twitter:** {e.get('twitter_draft','')}\n\n---\n\n"
        ]

    with open(out, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"\n  ✓ Log exported to: {out}")


def main():
    entries = load_log()
    print(f"\n  EIA Interpretation Log | {len(entries)} entries recorded")
    print(f"  {'First entry: ' + entries[0]['date'] if entries else 'No entries yet'}")

    print("\n  Actions:")
    print("    new    — record this week's EIA interpretation")
    print("    review — see recent entries")
    print("    export — export full log to markdown")

    action = input("\n  Choose action: ").strip().lower()

    if action == "new":
        entry = new_entry()
        entries.append(entry)
        save_log(entries)
        print(f"\n  ✓ Week {entry['week']} saved. Total entries: {len(entries)}")

    elif action == "review":
        review(entries)

    elif action == "export":
        export_markdown(entries)

    else:
        print("  Invalid action. Choose: new, review, or export")


if __name__ == "__main__":
    main()