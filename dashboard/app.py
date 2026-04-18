import sys
import os
import json
import time
import requests
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load secrets from Streamlit Cloud if available
if hasattr(st, "secrets"):
    for key in ["EIA_API_KEY", "FRED_API_KEY",
                "ALPHA_VANTAGE_API_KEY", "RESEARCHER_NAME"]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]

from config.settings import Config

st.set_page_config(
    page_title="GEIP — Gulf Energy Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0a0a0a; }
[data-testid="stSidebar"]          { background-color: #111111; }
h1, h2, h3                         { color: #c8a96e; }
[data-testid="stMetric"] {
    background-color: #111111;
    border-radius: 8px;
    padding: 10px;
    border-left: 3px solid #c8a96e;
}
</style>
""", unsafe_allow_html=True)

GOLD  = "#c8a96e"
BLUE  = "#4a90d9"
RED   = "#e05c5c"
GREEN = "#5cb85c"
BG    = "#0a0a0a"
TEXT  = "#e8e8e8"

LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor=BG,
    font=dict(color=TEXT, family="monospace"),
    margin=dict(l=50, r=20, t=30, b=50),
    hovermode="x unified",
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ GEIP")
    st.markdown("*Gulf Energy Intelligence Platform*")
    st.divider()
    st.markdown("**Corridor:** South Asia · Gulf · Africa")
    st.markdown(f"**Updated:** {datetime.now().strftime('%Y-%m-%d')}")
    st.divider()
    st.markdown("**Newsletter**")
    st.markdown("[The Corridor Brief](https://thecorridorbrief.substack.com)")
    st.markdown("**Twitter**")
    st.markdown("[@quantbyasif](https://twitter.com/quantbyasif)")
    st.markdown("**GitHub**")
    st.markdown("[Asif-space](https://github.com/Asif-space)")


# ── Header ────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#0a0a0a,#1a1200);
padding:20px;border-left:4px solid #c8a96e;margin-bottom:20px;
border-radius:4px;'>
<h1 style='margin:0;color:#c8a96e;'>
⚡ Gulf Energy Intelligence Platform</h1>
<p style='color:#888;margin:6px 0 0 0;'>
Physical commodity market analytics · South Asia · Gulf · Africa
</p>
</div>
""", unsafe_allow_html=True)


# ── Data Loading ──────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_eia():
    api_key = os.environ.get("EIA_API_KEY") or Config.EIA_API_KEY
    if not api_key or api_key == "paste_your_key_here":
        return {}, None

    series_map = {
        "crude_stocks_total":    "PET.WCRSTUS1.W",
        "crude_production_us":   "PET.WCRFPUS2.W",
        "crude_imports":         "PET.WCRIMUS2.W",
        "crude_exports":         "PET.WCREXUS2.W",
        "refinery_utilisation":  "PET.WPULEUS3.W",
        "gasoline_stocks_total": "PET.WGTSTUS1.W",
        "distillate_stocks":     "PET.WDISTUS1.W",
        "jet_fuel_stocks":       "PET.WKJSTUS1.W",
        "wti_spot":              "PET.RWTC.D",
        "brent_spot":            "PET.RBRTE.D",
    }

    data = {}
    for name, series_id in series_map.items():
        try:
            url = f"https://api.eia.gov/v2/seriesid/{series_id}"
            params = {
                "api_key": api_key,
                "start":   "2019-01-01",
                "length":  5000
            }
            r       = requests.get(url, params=params, timeout=30)
            records = r.json().get("response", {}).get("data", [])
            if records:
                df          = pd.DataFrame(records)
                df["period"] = pd.to_datetime(df["period"], errors="coerce")
                df          = df.dropna(subset=["period"])
                df          = df.set_index("period").sort_index()
                val_col     = [c for c in df.columns if "value" in c.lower()]
                if not val_col:
                    val_col = [df.columns[0]]
                df          = df[[val_col[0]]].copy()
                df.columns  = [name]
                df[name]    = pd.to_numeric(df[name], errors="coerce")
                data[name]  = df
            time.sleep(0.2)
        except Exception:
            pass

    # Build summary
    summary = {
        "date":    datetime.now().strftime("%Y-%m-%d"),
        "metrics": {}
    }
    for key in ["crude_stocks_total", "refinery_utilisation",
                "crude_production_us", "gasoline_stocks_total"]:
        if key in data and not data[key].empty:
            latest = float(data[key].iloc[-1, 0])
            prev   = float(data[key].iloc[-2, 0]) if len(data[key]) > 1 else latest
            summary["metrics"][key] = {
                "label":  key,
                "latest": latest,
                "change": latest - prev
            }

    return data, summary


@st.cache_data(ttl=3600)
def load_scenarios():
    path = Config.DATA_DIR / "scenario_journal.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


# ── Load ──────────────────────────────────────────────────────────
with st.spinner("Fetching live EIA data..."):
    data, summary = load_eia()

scenarios = load_scenarios()

# ── Tabs ──────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Weekly Petroleum",
    "📈 Price Analysis",
    "🎯 Scenarios",
    "🌍 Corridor Thesis"
])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 1 — WEEKLY PETROLEUM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    st.subheader("EIA Weekly Petroleum Status Report")

    if not data:
        st.error("Could not fetch EIA data. Check API key in secrets.")
        st.stop()

    # KPI row
    if summary and summary.get("metrics"):
        c1, c2, c3, c4 = st.columns(4)
        kpis = [
            ("crude_stocks_total",    "Crude Stocks",    "Mb",  c1),
            ("refinery_utilisation",  "Refinery Util",   "%",   c2),
            ("crude_production_us",   "US Production",   "Mbd", c3),
            ("gasoline_stocks_total", "Gasoline Stocks", "Mb",  c4),
        ]
        for key, label, unit, col in kpis:
            m = summary["metrics"].get(key)
            if m:
                val    = m["latest"]
                change = m.get("change", 0)
                if unit == "Mb":
                    val    = val / 1000
                    change = change / 1000
                col.metric(
                    label=label,
                    value=f"{val:.1f} {unit}",
                    delta=f"{change:+.1f} {unit}"
                )

    st.divider()

    # Crude inventory vs 5yr chart
    if "crude_stocks_total" in data:
        st.markdown("**US Crude Oil Inventories vs 5-Year Seasonal Average**")

        series  = data["crude_stocks_total"].iloc[:, 0].dropna() / 1000
        cutoff  = pd.Timestamp("2021-01-01")
        hist    = series[series.index < cutoff]
        recent  = series[series.index >= pd.Timestamp("2022-01-01")]

        hist_df         = hist.to_frame("val")
        hist_df["week"] = hist_df.index.isocalendar().week.astype(int)
        avg             = hist_df.groupby("week")["val"].mean()
        std             = hist_df.groupby("week")["val"].std()

        rec             = recent.to_frame("val")
        rec["week"]     = rec.index.isocalendar().week.astype(int)
        rec["avg"]      = rec["week"].map(avg)
        rec["upper"]    = rec["week"].map(
            lambda w: avg.get(w, np.nan) + std.get(w, np.nan))
        rec["lower"]    = rec["week"].map(
            lambda w: avg.get(w, np.nan) - std.get(w, np.nan))

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=rec.index, y=rec["upper"],
            fill=None, mode="lines",
            line=dict(color="rgba(74,144,217,0)"),
            showlegend=False
        ))
        fig.add_trace(go.Scatter(
            x=rec.index, y=rec["lower"],
            fill="tonexty", mode="lines",
            fillcolor="rgba(74,144,217,0.10)",
            line=dict(color="rgba(74,144,217,0)"),
            name="5-Year Range"
        ))
        fig.add_trace(go.Scatter(
            x=rec.index, y=rec["avg"],
            name="5-Year Average",
            line=dict(color=BLUE, width=1.5, dash="dash"),
            opacity=0.7
        ))
        fig.add_trace(go.Scatter(
            x=rec.index, y=rec["val"],
            name="Crude Stocks (Mb)",
            line=dict(color=GOLD, width=2.5)
        ))

        latest  = rec["val"].iloc[-1]
        avg_now = rec["avg"].iloc[-1]
        diff    = latest - avg_now
        fig.add_annotation(
            x=rec.index[-1], y=latest,
            text=f"{'+'if diff>0 else''}{diff:.1f} Mb vs 5yr avg",
            showarrow=True, arrowhead=2,
            arrowcolor=GREEN if diff > 0 else RED,
            font=dict(color=GREEN if diff > 0 else RED, size=11),
            ax=-100, ay=-40
        )
        fig.update_layout(**LAYOUT, height=420,
                          yaxis_title="Million Barrels (Mb)")
        st.plotly_chart(fig, use_container_width=True)

    # Two column charts
    col_a, col_b = st.columns(2)
    with col_a:
        if "gasoline_stocks_total" in data:
            st.markdown("**Gasoline Stocks**")
            d   = data["gasoline_stocks_total"].iloc[:, 0].dropna() / 1000
            d   = d.iloc[-104:]
            fig = go.Figure(go.Scatter(
                x=d.index, y=d.values,
                line=dict(color=GREEN, width=1.8),
                fill="tozeroy",
                fillcolor="rgba(92,184,92,0.05)"
            ))
            fig.update_layout(**LAYOUT, height=280,
                              yaxis_title="Mb", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        if "distillate_stocks" in data:
            st.markdown("**Distillate Stocks**")
            d   = data["distillate_stocks"].iloc[:, 0].dropna() / 1000
            d   = d.iloc[-104:]
            fig = go.Figure(go.Scatter(
                x=d.index, y=d.values,
                line=dict(color=RED, width=1.8),
                fill="tozeroy",
                fillcolor="rgba(224,92,92,0.05)"
            ))
            fig.update_layout(**LAYOUT, height=280,
                              yaxis_title="Mb", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 2 — PRICE ANALYSIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.subheader("Crude Oil Price Analysis")

    days = st.select_slider(
        "Time period",
        options=[90, 180, 365, 730],
        value=365,
        format_func=lambda x: f"{x} days"
    )

    if "brent_spot" in data and "wti_spot" in data:
        brent = data["brent_spot"].iloc[:, 0].dropna().iloc[-days:]
        wti   = data["wti_spot"].iloc[:, 0].dropna().iloc[-days:]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=brent.index, y=brent.values,
            name="Brent", line=dict(color=GOLD, width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=wti.index, y=wti.values,
            name="WTI", line=dict(color=BLUE, width=1.8, dash="dot")
        ))
        fig.update_layout(**LAYOUT, height=380, yaxis_title="USD/barrel")
        st.plotly_chart(fig, use_container_width=True)

        m1, m2, m3 = st.columns(3)
        b_latest = float(brent.iloc[-1])
        b_prev   = float(brent.iloc[-2])
        w_latest = float(wti.iloc[-1])
        spread   = b_latest - w_latest
        m1.metric("Brent", f"${b_latest:.2f}", f"{b_latest-b_prev:+.2f}")
        m2.metric("WTI",   f"${w_latest:.2f}")
        m3.metric("Brent–WTI Spread", f"${spread:.2f}")

        st.divider()
        st.markdown("**Brent–WTI Spread (USD/bbl)**")

        combined = brent.to_frame("brent").join(
            wti.to_frame("wti"), how="inner")
        spread_s = combined["brent"] - combined["wti"]
        colors   = [GREEN if v >= 0 else RED for v in spread_s.values]

        fig2 = go.Figure(go.Bar(
            x=spread_s.index, y=spread_s.values,
            marker_color=colors
        ))
        fig2.add_hline(
            y=float(spread_s.mean()),
            line_color=GOLD, line_dash="dash",
            annotation_text=f"Mean: ${spread_s.mean():.2f}"
        )
        fig2.update_layout(**LAYOUT, height=280,
                           yaxis_title="USD/bbl", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.info("Price data not available. Check API key.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 3 — SCENARIOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab3:
    st.subheader("Commodity Scenario Framework")
    st.caption("Updated every Sunday via: python scripts/scenario_journal.py")

    if not scenarios:
        st.info("No scenarios found locally. Run the scenario journal.")
    else:
        ICONS = {"Bull": "🟢", "Base": "🟡", "Bear": "🔴", "Tail": "🟣"}
        for key, commodity in scenarios.items():
            st.markdown(f"#### {commodity['commodity']}")
            st.caption(
                f"*{commodity['current_view']}*  |  "
                f"Last updated: {commodity.get('last_updated') or 'Never'}"
            )
            scens = commodity.get("scenarios", {})
            cols  = st.columns(len(scens))
            for col, (name, s) in zip(cols, scens.items()):
                lo, hi = s["range"]
                prob   = s["prob"] * 100
                icon   = ICONS.get(name, "⚪")
                col.metric(
                    label=f"{icon} {name}",
                    value=f"{prob:.0f}%",
                    delta=f"${lo}–${hi}"
                )
                col.caption(s["label"])
            st.divider()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TAB 4 — CORRIDOR THESIS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab4:
    st.subheader("The Corridor Thesis")

    st.markdown("""
<div style='background:#111;border-left:4px solid #c8a96e;
padding:16px;border-radius:4px;margin-bottom:20px;'>
<p style='color:#e8e8e8;margin:0;line-height:1.7;'>
The South Asia · Gulf · Africa corridor is the most important and most
underanalysed energy trade route in the world. It is being reshaped by
four simultaneous structural forces that almost no analyst covers in
integrated form.
</p>
</div>
""", unsafe_allow_html=True)

    f1, f2 = st.columns(2)
    with f1:
        st.markdown("#### 🛢 India's Russian Pivot")
        st.markdown("""
India has shifted **~35–40% of crude imports** to Russian supply,
permanently displacing Gulf barrels from their most important Asian
market. Saudi, Iraqi, and UAE producers now compete aggressively
for African, European, and remaining Asian offtake.
        """)
        st.markdown("#### 💱 South Asian LNG Dependency")
        st.markdown("""
Bangladesh and Pakistan face structural LNG import vulnerability.
Foreign exchange shortages constrain their ability to clear
international spot cargos — creating demand that Gulf and East
African LNG suppliers must finance creatively to capture.
        """)
    with f2:
        st.markdown("#### 🌍 East Africa's LNG Moment")
        st.markdown("""
Mozambique (Coral South FLNG operational; TotalEnergies under force
majeure) and Tanzania LNG represent significant emerging export
capacity targeting the same Asian buyers Gulf producers serve.
        """)
        st.markdown("#### 🏦 Gulf-Africa Sovereign Pivot")
        st.markdown("""
Gulf sovereign wealth funds — ADIA, Mubadala, PIF — are deploying
capital into African energy infrastructure at accelerating pace,
replacing lost Asian market relationships with new African
commercial ties.
        """)

    st.divider()
    st.markdown("""
<p style='color:#555;font-size:12px;text-align:center;'>
GEIP v1.0 · The Corridor Brief ·
<a href='https://thecorridorbrief.substack.com'
style='color:#c8a96e;'>thecorridorbrief.substack.com</a>
</p>
""", unsafe_allow_html=True)