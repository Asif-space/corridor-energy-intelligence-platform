import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.settings import Config

JOURNAL_FILE = Config.DATA_DIR / "scenario_journal.json"

DEFAULT = {
    "Brent_Crude": {
        "commodity": "Brent Crude Oil",
        "unit": "USD/bbl",
        "last_updated": None,
        "current_view": "Base case holds. OPEC+ compliance and Fed path are the swing factors.",
        "scenarios": {
            "Bull": {
                "range": [90, 110],
                "prob": 0.20,
                "label": "Supply disruption / OPEC+ surprise cut",
                "trigger": "Hormuz escalation or deeper-than-expected OPEC+ cut"
            },
            "Base": {
                "range": [70, 88],
                "prob": 0.50,
                "label": "Managed balance — OPEC+ extensions hold",
                "trigger": "OPEC+ maintains cuts, demand grows at IEA baseline"
            },
            "Bear": {
                "range": [55, 70],
                "prob": 0.25,
                "label": "Demand miss + OPEC fracture",
                "trigger": "Global slowdown or Saudi market share defence"
            },
            "Tail": {
                "range": [35, 55],
                "prob": 0.05,
                "label": "Full OPEC collapse / global recession",
                "trigger": "Simultaneous quota abandonment and financial crisis"
            }
        },
        "history": []
    },
    "JKM_LNG": {
        "commodity": "JKM LNG — Asia Benchmark",
        "unit": "USD/MMBtu",
        "last_updated": None,
        "current_view": "South Asian demand constrained by FX. Corridor freight economics are the key variable.",
        "scenarios": {
            "Bull": {
                "range": [15, 22],
                "prob": 0.25,
                "label": "Cold snap + East African supply delay",
                "trigger": "Weather event + Mozambique LNG restart delayed further"
            },
            "Base": {
                "range": [10, 15],
                "prob": 0.55,
                "label": "Moderate demand, adequate supply",
                "trigger": "Qatar contracts hold, Australian LNG stable"
            },
            "Bear": {
                "range": [6, 10],
                "prob": 0.20,
                "label": "Mild weather + oversupply",
                "trigger": "Warm Asian winter, US LNG export surge"
            }
        },
        "history": []
    }
}


def load():
    if JOURNAL_FILE.exists():
        with open(JOURNAL_FILE) as f:
            return json.load(f)
    return DEFAULT


def save(data):
    JOURNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def display(journal):
    for key, data in journal.items():
        print(f"\n{'='*55}")
        print(f"  {data['commodity']}")
        print(f"  Last updated: {data.get('last_updated') or 'Never'}")
        print(f"{'='*55}")
        print(f"  {'Scenario':<12} {'Range':<14} {'Prob':>6}  Label")
        print(f"  {'-'*50}")
        for name, s in data["scenarios"].items():
            lo, hi = s["range"]
            prob   = s["prob"] * 100
            print(f"  {name:<12} ${lo}–{hi:<11} {prob:>5.0f}%  {s['label']}")
        print(f"\n  View: {data['current_view']}")


def update(journal):
    today = datetime.now().strftime("%Y-%m-%d")

    for key, data in journal.items():
        print(f"\n  Updating: {data['commodity']}")
        print(f"  Current probabilities shown.")
        print(f"  Enter new % or press Enter to keep.\n")

        snapshot = {
            "date":   today,
            "probs":  {n: s["prob"] for n, s in data["scenarios"].items()},
            "view":   data["current_view"]
        }

        total = 0
        for name, s in data["scenarios"].items():
            current = s["prob"] * 100
            val = input(f"    {name:<12} (current {current:.0f}%): ").strip()
            if val:
                try:
                    s["prob"] = float(val) / 100
                except ValueError:
                    pass
            total += s["prob"]

        if abs(total - 1.0) > 0.02:
            print(f"\n  ⚠ Probabilities sum to {total*100:.1f}% — should be 100%")

        reason = input("\n  Why did you change these? ").strip()
        snapshot["reason"] = reason
        data["history"].append(snapshot)

        new_view = input(f"  Updated one-line view: ").strip()
        if new_view:
            data["current_view"] = new_view

        data["last_updated"] = today

    return journal


def export_substack(journal):
    today = datetime.now().strftime("%B %d, %Y")
    lines = [f"## Scenario Framework — {today}\n\n"]

    for key, data in journal.items():
        lines.append(f"### {data['commodity']}\n\n")
        for name, s in data["scenarios"].items():
            lo, hi = s["range"]
            prob   = s["prob"] * 100
            lines.append(
                f"**{name} ({prob:.0f}%)** | "
                f"${lo}–{hi} | "
                f"*{s['label']}*  \n"
            )
            lines.append(f"Key trigger: {s['trigger']}\n\n")
        lines.append(f"*View: {data['current_view']}*\n\n---\n\n")

    out = (Config.PUBLISHING_DIR / "substack_drafts" /
           f"scenarios_{datetime.now().strftime('%Y%m%d')}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"\n  ✓ Substack section saved: {out}")


def main():
    journal = load()

    print(f"\n  Scenario Journal — The Corridor Brief")
    print(f"\n  Actions:")
    print(f"    view   — display current scenarios")
    print(f"    update — update probability weights")
    print(f"    export — export Substack section")

    action = input("\n  Choose action: ").strip().lower()

    if action == "view":
        display(journal)

    elif action == "update":
        journal = update(journal)
        save(journal)
        display(journal)
        print("\n  ✓ Scenarios saved.")

    elif action == "export":
        display(journal)
        export_substack(journal)

    else:
        print("  Invalid action. Choose: view, update, or export")


if __name__ == "__main__":
    main()