import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:

    PROJECT_NAME = "The Corridor Brief"
    RESEARCHER = os.getenv("RESEARCHER_NAME", "Corridor Researcher")
    CORRIDOR = "South Asia · Gulf · Africa"

    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "data"
    RAW_DIR = DATA_DIR / "raw"
    PROCESSED_DIR = DATA_DIR / "processed"
    EXPORTS_DIR = DATA_DIR / "exports"
    REPORTS_DIR = BASE_DIR / "reports"
    LOGS_DIR = BASE_DIR / "logs"
    PUBLISHING_DIR = BASE_DIR / "publishing"

    EIA_RAW = RAW_DIR / "eia"
    OPEC_RAW = RAW_DIR / "opec"
    IEA_RAW = RAW_DIR / "iea"
    PPAC_RAW = RAW_DIR / "ppac"
    JODI_RAW = RAW_DIR / "jodi"

    EIA_API_KEY = os.getenv("EIA_API_KEY")
    FRED_API_KEY = os.getenv("FRED_API_KEY")
    ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

    EIA_BASE_URL = "https://api.eia.gov/v2"

    EIA_SERIES = {
        "crude_stocks_total":     "PET.WCRSTUS1.W",
        "crude_production_us":    "PET.WCRFPUS2.W",
        "crude_imports":          "PET.WCRIMUS2.W",
        "crude_exports":          "PET.WCREXUS2.W",
        "refinery_utilisation":   "PET.WPULEUS3.W",
        "refinery_crude_inputs":  "PET.WCRRIUS2.W",
        "gasoline_stocks_total":  "PET.WGTSTUS1.W",
        "gasoline_production":    "PET.WGFRPUS2.W",
        "distillate_stocks":      "PET.WDISTUS1.W",
        "jet_fuel_stocks":        "PET.WKJSTUS1.W",
        "wti_spot":               "PET.RWTC.D",
        "brent_spot":             "PET.RBRTE.D",
    }

    FRED_SERIES = {
        "dxy":       "DTWEXBGS",
        "usd_bdt":   "DEXBNUS",
        "usd_inr":   "DEXINUS",
        "fed_funds": "FEDFUNDS",
        "us_10yr":   "DGS10",
    }

    CHART_STYLE = {
        "background": "#0a0a0a",
        "text_color": "#e8e8e8",
        "gold":       "#c8a96e",
        "blue":       "#4a90d9",
        "red":        "#e05c5c",
        "green":      "#5cb85c",
        "grid_color": "#1e1e1e",
        "dpi":        300,
    }

    SOUTH_ASIA     = ["Bangladesh", "India", "Pakistan", "Sri Lanka"]
    GULF_STATES    = ["Saudi Arabia", "UAE", "Qatar", "Kuwait", "Iraq", "Oman"]
    AFRICA_CORRIDOR = ["Egypt", "Mozambique", "Tanzania", "Kenya",
                       "South Africa", "Morocco", "Nigeria"]

    @classmethod
    def verify(cls):
        print(f"\n{'='*50}")
        print(f"  {cls.PROJECT_NAME} — Config Check")
        print(f"  Researcher: {cls.RESEARCHER}")
        print(f"{'='*50}")
        items = {
            "EIA API Key":  bool(cls.EIA_API_KEY and cls.EIA_API_KEY != "paste_your_key_here"),
            "FRED API Key": bool(cls.FRED_API_KEY and cls.FRED_API_KEY != "paste_your_key_here"),
            "Data dir":     cls.DATA_DIR.exists(),
            "EIA raw dir":  cls.EIA_RAW.exists(),
            "Logs dir":     cls.LOGS_DIR.exists(),
        }
        for label, ok in items.items():
            print(f"  {'✓' if ok else '✗'} {label}")
        print(f"{'='*50}\n")