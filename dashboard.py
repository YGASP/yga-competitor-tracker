import streamlit as st
import json
import plotly.graph_objects as go
from pathlib import Path
from datetime import date, timedelta
import random

st.set_page_config(
    page_title="YGA Competitor Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── PREMIUM DARK THEME ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Global ── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #08090d;
    color: #cdd9e5;
    font-family: 'Inter', sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #0e1016;
    border-right: 1px solid #1e2128;
}
[data-testid="stHeader"] { background: transparent; }
section[data-testid="stMain"] > div { padding-top: 1.5rem; }

/* ── Sidebar internals ── */
[data-testid="stSidebar"] .stRadio label {
    color: #768390 !important;
    font-size: 14px;
}
[data-testid="stSidebar"] .stRadio label:hover { color: #cdd9e5 !important; }
[data-testid="stSidebar"] .stSlider label { color: #768390 !important; font-size: 12px; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #768390;
    font-size: 12px;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #111318;
    border: 1px solid #1e2128;
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
}
[data-testid="metric-container"] label {
    color: #768390 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: .07em;
    font-weight: 600 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 34px !important;
    font-weight: 800 !important;
    color: #cdd9e5 !important;
    letter-spacing: -.02em;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 13px !important;
}

/* ── Section divider ── */
.section-divider {
    border: none;
    border-top: 1px solid #1e2128;
    margin: 1.5rem 0 1.2rem 0;
}

/* ── Section title ── */
.section-title {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .1em;
    text-transform: uppercase;
    color: #768390;
    margin: 0 0 14px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1e2128;
}

/* ── Chart legend ── */
.chart-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 10px 20px;
    padding: 10px 4px 4px 4px;
    margin-top: -4px;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 12px;
    color: #768390;
}
.legend-dot-mine {
    width: 18px; height: 3px;
    background: #c9a227;
    border-radius: 2px;
    flex-shrink: 0;
}
.legend-dot {
    width: 14px; height: 2px;
    border-radius: 2px;
    flex-shrink: 0;
    opacity: 0.7;
}

/* ── Standings table ── */
.standings-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.standings-table th {
    text-align: left;
    padding: 7px 12px;
    color: #768390;
    font-weight: 600;
    border-bottom: 1px solid #1e2128;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: .07em;
}
.standings-table td {
    padding: 10px 12px;
    border-bottom: 1px solid #161a21;
    color: #cdd9e5;
}
.standings-table tr:last-child td { border-bottom: none; }
.standings-table tr.mine td {
    background: #141008;
    border-left: 3px solid #c9a227;
}
.standings-table tr.mine td:first-child {
    padding-left: 9px;
}
.standings-table tr:not(.mine):hover td { background: #111318; }

.mine-tag {
    background: #c9a227;
    color: #08090d;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 3px;
    margin-left: 7px;
    vertical-align: middle;
    letter-spacing: .04em;
}
.rank-num { font-weight: 700; color: #cdd9e5; font-size: 15px; }
.rank-1 { color: #c9a227; }
.rank-2 { color: #a8b2be; }
.rank-3 { color: #cd7f32; }

/* ── Alert boxes ── */
.alert-box {
    border-radius: 8px;
    padding: 11px 15px;
    margin: 5px 0;
    font-size: 13px;
    line-height: 1.55;
}
.alert-danger  { background: #1c0a0a; border-left: 3px solid #e05252; color: #f0a8a8; }
.alert-warning { background: #1a1206; border-left: 3px solid #c9a227; color: #e3c97a; }
.alert-ok      { background: #061510; border-left: 3px solid #3fb950; color: #7ee787; }

/* ── Info banner ── */
.stAlert > div {
    background: #111318 !important;
    border: 1px solid #1e2128 !important;
    color: #768390 !important;
    font-size: 13px !important;
}

/* ── Page header ── */
.page-header {
    font-size: 26px;
    font-weight: 800;
    color: #cdd9e5;
    letter-spacing: -.02em;
    margin-bottom: 2px;
}
.page-subheader {
    font-size: 13px;
    color: #768390;
    margin-bottom: 1rem;
}

/* ── Buttons ── */
.stButton > button {
    background: #111318 !important;
    border: 1px solid #1e2128 !important;
    color: #cdd9e5 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border-radius: 7px !important;
    transition: border-color .15s, background .15s;
}
.stButton > button:hover {
    background: #1a1e27 !important;
    border-color: #c9a227 !important;
}
[data-testid="baseButton-primary"] {
    background: #1a1206 !important;
    border-color: #c9a227 !important;
    color: #c9a227 !important;
}
[data-testid="baseButton-primary"]:hover {
    background: #241904 !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #111318 !important;
    border: 1px solid #1e2128 !important;
    border-radius: 8px !important;
    color: #768390 !important;
    font-size: 13px !important;
}
.streamlit-expanderContent {
    background: #0d0e13 !important;
    border: 1px solid #1e2128 !important;
    border-top: none !important;
}

/* ── Slider ── */
[data-testid="stSlider"] > div > div > div { background: #1e2128 !important; }
[data-testid="stSlider"] [data-testid="stThumbValue"] { background: #c9a227 !important; }
</style>
""", unsafe_allow_html=True)

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GROUPS = [
    {
        "id": "basketball",
        "name": "Silent Basketball",
        "icon": "🏀",
        "target_subcategory": "Basketballs",
        "asins": [
            {"asin": "B0GWMKX9YG", "brand": "YGA Sports",    "is_mine": True},
            {"asin": "B0DS25MK1T", "brand": "ALDWDY"},
            {"asin": "B0FBQX1GCR", "brand": "Muted Motion"},
            {"asin": "B0F6L9LJL9", "brand": "LKTNLKT"},
            {"asin": "B0FLJK2HWQ", "brand": "BOUNOVA"},
            {"asin": "B0G2G8NQ3Y", "brand": "BYYNNE"},
        ],
    },
    {
        "id": "puncho",
        "name": "PUNCHO",
        "icon": "🥷",
        "target_subcategory": "Focus Bags",
        "asins": [
            {"asin": "B0F6T2XLZR", "brand": "YGA Sports PUNCHO", "is_mine": True},
            {"asin": "B0BKPM69F8", "brand": "Dino QPAU"},
            {"asin": "B0D6QT1WYS", "brand": "Red QPAU"},
            {"asin": "B0DFMMFMYC", "brand": "360 QPAU"},
            {"asin": "B0FHW391BS", "brand": "HopeRock"},
            {"asin": "B09JVGBFKH", "brand": "MARWAN"},
        ],
    },
    {
        "id": "chompy",
        "name": "CHOMPY",
        "icon": "🦕",
        "target_subcategory": "Pedestal",
        "asins": [
            {"asin": "B0GNTJ9THL", "brand": "YGA Sports CHOMPY", "is_mine": True},
            {"asin": "B0BKPM69F8", "brand": "Dino QPAU"},
            {"asin": "B0D6QT1WYS", "brand": "Red QPAU"},
            {"asin": "B0DFMMFMYC", "brand": "360 QPAU"},
            {"asin": "B0FS1341NF", "brand": "NIBBaNACAL"},
            {"asin": "B09JVGBFKH", "brand": "MARWAN"},
        ],
    },
]

MY_COLOR     = "#c9a227"
COMP_COLORS  = ["#58a6ff", "#ff7b54", "#56d364", "#d2a8ff", "#ffa657"]
BSR_ALERT    = 25
PRICE_ALERT  = 10

# ─── DATA ─────────────────────────────────────────────────────────────────────
DATA_FILE = Path(__file__).parent / "competitor_history.json"

def _placeholder():
    random.seed(42)
    bl = {
        "B0GWMKX9YG": (1800, 27.99), "B0DS25MK1T": (1100, 25.99),
        "B0FBQX1GCR": (3400, 22.99), "B0F6L9LJL9": (2700, 29.99),
        "B0FLJK2HWQ": (4100, 19.99), "B0G2G8NQ3Y": (5200, 24.99),
        "B0F6T2XLZR": (2100, 34.99), "B0BKPM69F8": (750,  32.99),
        "B0D6QT1WYS": (1400, 28.99), "B0DFMMFMYC": (2900, 26.99),
        "B0FHW391BS": (4400, 22.99), "B09JVGBFKH": (2600, 31.99),
        "B0GNTJ9THL": (1900, 36.99), "B0FS1341NF": (3700, 24.99),
    }
    data = {"asins": {}}
    today = date.today()
    for g in GROUPS:
        for item in g["asins"]:
            asin = item["asin"]
            if asin in data["asins"]:
                continue
            bsr0, p0 = bl.get(asin, (2500, 28.99))
            snaps = []
            for i in range(13, -1, -1):
                d = today - timedelta(days=i)
                snaps.append({
                    "date": str(d),
                    "bsr_main":      max(100, int(bsr0 + random.gauss(0, bsr0 * .12))),
                    "buy_box_price": max(9.99, round(p0 + random.gauss(0, 1.2), 2)),
                    "is_oos":        False,
                })
            data["asins"][asin] = {
                "brand": item["brand"],
                "is_mine": item.get("is_mine", False),
                "snapshots": snaps,
            }
    return data

@st.cache_data(ttl=60)
def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f), False
    return _placeholder(), True

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def snaps(data, asin):
    return data["asins"].get(asin, {}).get("snapshots", [])

def last_val(data, asin, field):
    s = snaps(data, asin)
    if not s:
        return None
    return s[-1].get(field)

def alerts(group, data):
    out = []
    mine = next(a for a in group["asins"] if a.get("is_mine"))
    ms = snaps(data, mine["asin"])
    if len(ms) >= 7:
        r, w = ms[-1]["bsr_main"], ms[-7]["bsr_main"]
        if r and w:
            pct = (r - w) / w * 100
            if pct >= BSR_ALERT:
                out.append(("danger", f"Your BSR worsened {pct:.0f}% in 7 days ({w:,} → {r:,})"))
    for item in group["asins"]:
        if item.get("is_mine"):
            continue
        cs = snaps(data, item["asin"])
        if len(cs) >= 8:
            tp  = cs[-1]["buy_box_price"]
            avg = sum(s["buy_box_price"] for s in cs[-8:-1] if s["buy_box_price"]) / max(
                1, sum(1 for s in cs[-8:-1] if s["buy_box_price"])
            )
            if tp and avg and (avg - tp) / avg * 100 >= PRICE_ALERT:
                pct = (avg - tp) / avg * 100
                out.append(("warning", f"{item['brand']} dropped price {pct:.0f}% (avg ${avg:.2f} → ${tp:.2f})"))
    return out

# ─── SUBCATEGORY BSR HELPERS ──────────────────────────────────────────────────
def subcat_bsr_from_snap(snap, target):
    """Return BSR for target subcategory using case-insensitive partial match."""
    subcats = snap.get("bsr_subcats") or {}
    t = target.lower()
    for cat, bsr in subcats.items():
        if t in cat.lower():
            return bsr
    # Fallback: legacy subcategory_name field
    if t in (snap.get("subcategory_name") or "").lower():
        return snap.get("bsr_subcategory")
    return None


def last_subcat_bsr(data, asin, target):
    s = snaps(data, asin)
    return subcat_bsr_from_snap(s[-1], target) if s else None


def matched_subcat_name(data, asin, target):
    """Return the actual Amazon subcategory name that matched target."""
    s = snaps(data, asin)
    if not s:
        return target
    subcats = s[-1].get("bsr_subcats") or {}
    t = target.lower()
    for cat in subcats:
        if t in cat.lower():
            return cat
    return target


# ─── CHART BASE ───────────────────────────────────────────────────────────────
CHART_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#768390", family="Inter, sans-serif", size=11),
    margin=dict(l=8, r=80, t=16, b=36),
    height=380,
    hovermode="x unified",
    showlegend=False,
    hoverlabel=dict(
        bgcolor="#111318",
        bordercolor="#1e2128",
        font=dict(color="#cdd9e5", size=12),
    ),
)

AX = dict(
    gridcolor="#1a1d24",
    linecolor="#1e2128",
    tickcolor="#1e2128",
    zerolinecolor="#1e2128",
    tickfont=dict(color="#768390", size=10),
)


def _moving_avg(ys, window=7):
    result = []
    for j in range(len(ys)):
        chunk = ys[max(0, j - window + 1):j + 1]
        result.append(sum(chunk) / len(chunk))
    return result


def _trend_line(ys):
    """Returns (trend_ys, is_improving) using linear regression."""
    n = len(ys)
    if n < 4:
        return None, None
    idxs = list(range(n))
    sx  = sum(idxs);  sy  = sum(ys)
    sxy = sum(idxs[j] * ys[j] for j in range(n))
    sxx = sum(x * x for x in idxs)
    denom = n * sxx - sx * sx
    if not denom:
        return None, None
    m = (n * sxy - sx * sy) / denom
    b = (sy - m * sx) / n
    return [m * j + b for j in idxs], m < 0   # m<0 means value falling


def trend_chart(group, data, field, ylabel, reverse_y=False, value_fn=None):
    """value_fn(snapshot) -> float|None overrides field when provided."""
    fig = go.Figure()
    has = False
    comp_idx = 0

    for item in group["asins"]:
        s = snaps(data, item["asin"])
        if value_fn:
            pairs = [(x["date"], value_fn(x)) for x in s]
            pairs = [(d, v) for d, v in pairs if v is not None]
        else:
            pairs = [(x["date"], x[field]) for x in s if x.get(field) is not None]
        if not pairs:
            if not item.get("is_mine"):
                comp_idx += 1
            continue
        has = True
        xs, ys = zip(*pairs)
        xs, ys = list(xs), list(ys)
        mine  = item.get("is_mine", False)

        if mine:
            color = MY_COLOR
        else:
            color = COMP_COLORS[comp_idx % len(COMP_COLORS)]
            comp_idx += 1

        # ── Main trace ──────────────────────────────────────────────────────
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            name=item["brand"],
            line=dict(color=color, width=4 if mine else 2),
            mode="lines+markers",
            marker=dict(
                size=8 if mine else 5,
                color=color,
                line=dict(width=2 if mine else 1, color="#08090d"),
            ),
            hovertemplate=f"<b>{item['brand']}</b><br>{ylabel}: %{{y:,.2f}}<extra></extra>",
        ))

        # ── End-of-line label ───────────────────────────────────────────────
        last_x, last_y = xs[-1], ys[-1]
        label_text = f"{last_y:,.0f}" if field == "bsr_main" else f"${last_y:.2f}"
        fig.add_annotation(
            x=last_x, y=last_y,
            text=f"<b>{label_text}</b>" if mine else label_text,
            xanchor="left", xshift=8, yshift=0,
            showarrow=False,
            font=dict(color=color, size=11 if mine else 10),
        )

        # ── 7-day moving average (mine only) ────────────────────────────────
        if mine and len(ys) >= 3:
            ma = _moving_avg(ys, window=7)
            fig.add_trace(go.Scatter(
                x=xs, y=ma,
                name="7-day avg",
                line=dict(color=MY_COLOR, width=1.5, dash="dot"),
                mode="lines",
                opacity=0.55,
                showlegend=False,
                hovertemplate="<b>7d avg</b>: %{y:,.0f}<extra></extra>",
            ))

        # ── Linear trend line (mine only) ───────────────────────────────────
        if mine and len(ys) >= 4:
            trend_ys, falling = _trend_line(ys)
            if trend_ys:
                # For BSR (reverse_y): falling = improving. For price: falling = bad.
                improving = falling if reverse_y else not falling
                trend_color = "#3fb950" if improving else "#e05252"
                fig.add_trace(go.Scatter(
                    x=xs, y=trend_ys,
                    name="Trend",
                    line=dict(color=trend_color, width=2, dash="longdash"),
                    mode="lines",
                    opacity=0.55,
                    showlegend=False,
                    hoverinfo="skip",
                ))

    if not has:
        fig.add_annotation(
            text="No data yet — run the collection script",
            xref="paper", yref="paper", x=.5, y=.5,
            showarrow=False,
            font=dict(color="#768390", size=13),
        )

    yaxis_cfg = dict(**AX, title=dict(text=ylabel, font=dict(color="#768390", size=11)))
    if reverse_y:
        yaxis_cfg["autorange"] = "reversed"

    fig.update_layout(
        **CHART_BASE,
        xaxis=dict(**AX),
        yaxis=yaxis_cfg,
    )
    return fig


def _legend_html(group):
    items = []
    comp_idx = 0
    for item in group["asins"]:
        mine  = item.get("is_mine", False)
        if mine:
            color = MY_COLOR
            dot   = '<span class="legend-dot-mine"></span>'
            label = f'<b style="color:#cdd9e5">{item["brand"]}</b>'
        else:
            color = COMP_COLORS[comp_idx % len(COMP_COLORS)]
            comp_idx += 1
            dot   = f'<span class="legend-dot" style="background:{color};"></span>'
            label = f'<span style="color:{color}">{item["brand"]}</span>'
        items.append(f'<span class="legend-item">{dot}{label}</span>')
    return f'<div class="chart-legend">{"".join(items)}</div>'

# ─── STANDINGS TABLE ──────────────────────────────────────────────────────────
def standings_html(group, data):
    rows = []
    for item in group["asins"]:
        bsr = last_val(data, item["asin"], "bsr_main")
        prc = last_val(data, item["asin"], "buy_box_price")
        rows.append({"item": item, "bsr": bsr, "prc": prc})

    rows_with_bsr = [r for r in rows if r["bsr"]]
    rows_no_bsr   = [r for r in rows if not r["bsr"]]
    rows_with_bsr.sort(key=lambda r: r["bsr"])
    rows_sorted = rows_with_bsr + rows_no_bsr

    html = '<table class="standings-table"><thead><tr>'
    html += "<th>#</th><th>Brand</th><th>BSR</th><th>Price</th></tr></thead><tbody>"

    rank_colors = {1: "rank-1", 2: "rank-2", 3: "rank-3"}
    for rank, r in enumerate(rows_sorted, 1):
        mine_class = " mine" if r["item"].get("is_mine") else ""
        rc         = rank_colors.get(rank, "")
        bsr_str    = f"{r['bsr']:,}" if r["bsr"] else "—"
        prc_str    = f"${r['prc']:.2f}" if r["prc"] else "—"
        mine_tag   = '<span class="mine-tag">YOU</span>' if r["item"].get("is_mine") else ""
        html += (
            f'<tr class="{mine_class}">'
            f'<td><span class="rank-num {rc}">#{rank}</span></td>'
            f'<td>{r["item"]["brand"]}{mine_tag}</td>'
            f'<td>{bsr_str}</td>'
            f'<td>{prc_str}</td>'
            f"</tr>"
        )
    html += "</tbody></table>"
    return html

# ─── RENDER ───────────────────────────────────────────────────────────────────
def render(group, data):
    mine_item   = next(a for a in group["asins"] if a.get("is_mine"))
    ms          = snaps(data, mine_item["asin"])
    target_sub  = group.get("target_subcategory", "")

    # ── Hero metrics ─────────────────────────────────────────────────────
    bsr_now    = last_val(data, mine_item["asin"], "bsr_main")
    price_now  = last_val(data, mine_item["asin"], "buy_box_price")
    bsr_prev   = ms[-2]["bsr_main"]       if len(ms) >= 2 else None
    price_prev = ms[-2]["buy_box_price"]  if len(ms) >= 2 else None
    sub_bsr_now  = last_subcat_bsr(data, mine_item["asin"], target_sub) if target_sub else None
    sub_bsr_prev = subcat_bsr_from_snap(ms[-2], target_sub) if (len(ms) >= 2 and target_sub) else None
    sub_label    = matched_subcat_name(data, mine_item["asin"], target_sub) if target_sub else ""

    comp_bsrs = [
        last_val(data, a["asin"], "bsr_main")
        for a in group["asins"] if not a.get("is_mine")
    ]
    comp_bsrs = [b for b in comp_bsrs if b]

    if bsr_now and comp_bsrs:
        rank = sorted([bsr_now] + comp_bsrs).index(bsr_now) + 1
    else:
        rank = None

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(
        "Your BSR (Overall)",
        f"{bsr_now:,}" if bsr_now else "N/A",
        delta=f"{bsr_now - bsr_prev:+,}" if (bsr_now and bsr_prev) else None,
        delta_color="inverse",
        help="Overall Amazon BSR — lower is better",
    )
    c2.metric(
        f"Your BSR — {sub_label or target_sub}",
        f"{sub_bsr_now:,}" if sub_bsr_now else "N/A",
        delta=f"{sub_bsr_now - sub_bsr_prev:+,}" if (sub_bsr_now and sub_bsr_prev) else None,
        delta_color="inverse",
        help=f"Rank within the '{sub_label or target_sub}' subcategory",
    )
    c3.metric(
        "Your Price",
        f"${price_now:.2f}" if price_now else "N/A",
        delta=f"${price_now - price_prev:+.2f}" if (price_now and price_prev) else None,
    )
    c4.metric("Best Competitor BSR", f"{min(comp_bsrs):,}" if comp_bsrs else "N/A")
    c5.metric(
        "Your Rank in Group",
        f"#{rank} of 6" if rank else "N/A",
        help="Ranked by BSR — lower BSR = better rank",
    )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Standings + Alerts ───────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<p class="section-title">Today\'s Standings</p>', unsafe_allow_html=True)
        st.markdown(standings_html(group, data), unsafe_allow_html=True)

    with col_right:
        st.markdown('<p class="section-title">Alerts</p>', unsafe_allow_html=True)
        al = alerts(group, data)
        if not al:
            st.markdown(
                '<div class="alert-box alert-ok">&#10003;&nbsp; All clear — no alerts today</div>',
                unsafe_allow_html=True,
            )
        else:
            for level, msg in al:
                icon = "&#9888;&nbsp;" if level == "warning" else "&#9888;&nbsp;"
                st.markdown(
                    f'<div class="alert-box alert-{level}">{icon}{msg}</div>',
                    unsafe_allow_html=True,
                )

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── BSR Chart ────────────────────────────────────────────────────────
    st.markdown(
        '<p class="section-title">'
        'BSR Trend'
        '&nbsp;<span style="color:#768390;font-weight:400;text-transform:none;'
        'letter-spacing:0;font-size:10px">— Lower is Better &nbsp;|&nbsp; '
        '<span style="color:#c9a227">&#9472;&#9472;</span> You &nbsp; '
        '<span style="color:#c9a227;opacity:.6">&#183;&#183;&#183;</span> 7-day avg &nbsp; '
        '<span style="color:#3fb950">&#9135;&#9135;</span>/<span style="color:#e05252">&#9135;&#9135;</span> Trend</span>'
        '</p>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        trend_chart(group, data, "bsr_main", "BSR", reverse_y=True),
        use_container_width=True,
        key=f"{group['id']}_bsr",
    )
    st.markdown(_legend_html(group), unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Subcategory BSR Chart ────────────────────────────────────────────
    if target_sub:
        sub_display = matched_subcat_name(data, mine_item["asin"], target_sub)
        st.markdown(
            f'<p class="section-title">'
            f'Subcategory BSR — {sub_display}'
            f'&nbsp;<span style="color:#768390;font-weight:400;text-transform:none;'
            f'letter-spacing:0;font-size:10px">— Lower is Better</span>'
            f'</p>',
            unsafe_allow_html=True,
        )
        fn = lambda snap, t=target_sub: subcat_bsr_from_snap(snap, t)
        st.plotly_chart(
            trend_chart(group, data, "bsr_subcategory", f"BSR in {sub_display}",
                        reverse_y=True, value_fn=fn),
            use_container_width=True,
            key=f"{group['id']}_subcat_bsr",
        )
        st.markdown(_legend_html(group), unsafe_allow_html=True)
        st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Price Chart ──────────────────────────────────────────────────────
    st.markdown('<p class="section-title">Price Trend ($)</p>', unsafe_allow_html=True)
    st.plotly_chart(
        trend_chart(group, data, "buy_box_price", "Price ($)"),
        use_container_width=True,
        key=f"{group['id']}_price",
    )
    st.markdown(_legend_html(group), unsafe_allow_html=True)

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Correlation expander ─────────────────────────────────────────────
    with st.expander("Price vs BSR Correlation (your ASIN)"):
        pairs = [
            (s["buy_box_price"], s["bsr_main"], s["date"][5:])
            for s in ms
            if s.get("buy_box_price") and s.get("bsr_main")
        ]
        if pairs:
            xs, ys, labels = zip(*pairs)
            fig = go.Figure(go.Scatter(
                x=list(xs),
                y=list(ys),
                mode="markers+text",
                text=list(labels),
                textposition="top center",
                textfont=dict(size=9, color="#768390"),
                marker=dict(color=MY_COLOR, size=10, opacity=.9,
                            line=dict(width=1.5, color="#08090d")),
                hovertemplate="Price: $%{x:.2f}<br>BSR: %{y:,}<extra></extra>",
            ))
            corr_base = dict(CHART_BASE)
            corr_base["height"] = 260
            fig.update_layout(
                **corr_base,
                xaxis=dict(**AX, title=dict(text="Your Price ($)", font=dict(color="#768390", size=11))),
                yaxis=dict(**AX, title=dict(text="Your BSR", font=dict(color="#768390", size=11)),
                           autorange="reversed"),
            )
            st.plotly_chart(fig, use_container_width=True, key=f"{group['id']}_corr")
        else:
            st.caption("Not enough data yet.")

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
data, is_placeholder = load_data()

with st.sidebar:
    st.markdown(
        '<div style="font-size:18px;font-weight:800;color:#cdd9e5;'
        'letter-spacing:-.01em;padding:4px 0 2px 0;">YGA Tracker</div>'
        '<div style="font-size:11px;color:#768390;margin-bottom:16px;">'
        'Amazon Competitor Intelligence</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    group_names  = [f"{g['icon']}  {g['name']}" for g in GROUPS]
    selected_idx = st.radio(
        "Product",
        range(len(GROUPS)),
        format_func=lambda i: group_names[i],
        label_visibility="collapsed",
    )
    group = GROUPS[selected_idx]

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    if is_placeholder:
        st.warning("Showing placeholder data")
    else:
        last = max(
            s["date"]
            for d in data["asins"].values()
            for s in d.get("snapshots", [{"date": ""}])
            if s["date"]
        )
        st.markdown(
            f'<div style="font-size:11px;color:#768390;margin-bottom:8px;">'
            f'Last updated: <b style="color:#cdd9e5">{last}</b></div>',
            unsafe_allow_html=True,
        )

    if st.button("Refresh Data", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown('<p class="section-title">Alert Thresholds</p>', unsafe_allow_html=True)
    BSR_ALERT   = st.slider("BSR worsening (%)",        10, 50, 25, 5)
    PRICE_ALERT = st.slider("Competitor price drop (%)", 5, 30, 10, 5)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="page-header">{group["icon"]} {group["name"]}</div>'
    f'<div class="page-subheader">BSR & price tracking vs. top competitors</div>',
    unsafe_allow_html=True,
)
if is_placeholder:
    st.info("Showing placeholder data — run **run_collect.bat** to populate real numbers.")

st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

render(group, data)
