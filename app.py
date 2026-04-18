import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(
    page_title="S&P 500 Correction & Recovery Tracker",
    page_icon="📉",
    layout="wide"
)

PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"]
}

st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"] {
        background: #05070b;
        color: #f8fafc;
    }
    [data-testid="stHeader"] {
        background: rgba(0, 0, 0, 0);
    }
    .hero-wrap {
        background: linear-gradient(135deg, #0b1220 0%, #111827 100%);
        border: 1px solid #1f2937;
        border-radius: 24px;
        padding: 1.35rem 1.5rem 1.45rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.35);
    }
    .hero-badge {
        display: inline-block;
        padding: 0.36rem 0.7rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #dbeafe;
        background: #0f172a;
        border: 1px solid #334155;
        margin-bottom: 0.75rem;
    }
    .main-header {
        font-size: 2.7rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.03;
        letter-spacing: -0.03em;
        margin-bottom: 0.28rem;
    }
    .sub-header {
        font-size: 1.02rem;
        color: #cbd5e1;
        line-height: 1.55;
        max-width: 860px;
    }
    .metric-card {
        background: #0b1220;
        border-radius: 18px;
        padding: 1.1rem 1.1rem 1rem 1.1rem;
        border: 1px solid #1f2937;
        box-shadow: 0 10px 26px rgba(0, 0, 0, 0.28);
        min-height: 120px;
    }
    .metric-label {
        font-size: 0.76rem;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        color: #94a3b8;
        font-weight: 800;
        margin-bottom: 0.55rem;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 800;
        line-height: 1.02;
        color: #f8fafc;
    }
    .metric-sub {
        font-size: 0.94rem;
        color: #cbd5e1;
        margin-top: 0.42rem;
        line-height: 1.45;
    }
    .green { color: #34d399; }
    .red { color: #f87171; }
    .blue { color: #60a5fa; }
    .section-label {
        display: inline-block;
        font-size: 0.74rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #cbd5e1;
        font-weight: 800;
        margin-top: 1.8rem;
        margin-bottom: 0.8rem;
        padding: 0.32rem 0.62rem;
        border-radius: 999px;
        background: #111827;
        border: 1px solid #334155;
    }
    .insight-box {
        background: linear-gradient(135deg, #0b1220, #0f172a);
        border: 1px solid #1d4ed8;
        border-left: 6px solid #60a5fa;
        border-radius: 18px;
        padding: 1.05rem 1.15rem;
        margin-top: 0.9rem;
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.28);
    }
    .insight-title {
        font-size: 0.76rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #93c5fd;
        font-weight: 800;
        margin-bottom: 0.42rem;
    }
    .insight-copy {
        color: #f8fafc;
        font-size: 1rem;
        line-height: 1.65;
    }
    .footer-text {
        text-align: center;
        font-size: 0.88rem;
        color: #cbd5e1;
    }
    .footer-text a {
        color: #93c5fd;
        text-decoration: none;
        font-weight: 700;
    }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_sp500_data():
    sp500 = yf.download(
        "^GSPC",
        start="2007-01-01",
        end=datetime.today().strftime("%Y-%m-%d"),
        progress=False,
        auto_adjust=True,
    )
    if isinstance(sp500.columns, pd.MultiIndex):
        sp500.columns = sp500.columns.get_level_values(0)
    sp500 = sp500[["Close"]].dropna()
    sp500.columns = ["Close"]
    return sp500


def find_corrections(df, threshold=-0.10):
    df = df.copy()
    df["Peak"] = df["Close"].cummax()
    df["Drawdown"] = (df["Close"] - df["Peak"]) / df["Peak"]

    corrections = []
    in_correction = False
    correction_start = None
    peak_value = None
    trough_value = None
    trough_date = None
    max_drawdown = 0

    for date, row in df.iterrows():
        if not in_correction:
            if row["Drawdown"] <= threshold:
                in_correction = True
                peak_idx = df.loc[:date, "Close"].idxmax()
                correction_start = peak_idx
                peak_value = df.loc[peak_idx, "Close"]
                trough_value = row["Close"]
                trough_date = date
                max_drawdown = row["Drawdown"]
        else:
            if row["Drawdown"] < max_drawdown:
                max_drawdown = row["Drawdown"]
                trough_value = row["Close"]
                trough_date = date

            if row["Close"] >= peak_value:
                recovery_date = date
                correction_days = (trough_date - correction_start).days
                recovery_days = (recovery_date - trough_date).days
                total_days = (recovery_date - correction_start).days

                corrections.append({
                    "Peak Date": correction_start.strftime("%Y-%m-%d"),
                    "Trough Date": trough_date.strftime("%Y-%m-%d"),
                    "Recovery Date": recovery_date.strftime("%Y-%m-%d"),
                    "Peak Value": round(peak_value, 2),
                    "Trough Value": round(trough_value, 2),
                    "Max Drawdown": round(max_drawdown * 100, 1),
                    "Days to Bottom": correction_days,
                    "Days to Recover": recovery_days,
                    "Total Cycle (Days)": total_days,
                })

                in_correction = False
                max_drawdown = 0

    if in_correction:
        correction_days = (trough_date - correction_start).days
        latest_date = df.index[-1]
        latest_close = df.iloc[-1]["Close"]

        corrections.append({
            "Peak Date": correction_start.strftime("%Y-%m-%d"),
            "Trough Date": trough_date.strftime("%Y-%m-%d"),
            "Recovery Date": "Ongoing" if latest_close < peak_value else latest_date.strftime("%Y-%m-%d"),
            "Peak Value": round(peak_value, 2),
            "Trough Value": round(trough_value, 2),
            "Max Drawdown": round(max_drawdown * 100, 1),
            "Days to Bottom": correction_days,
            "Days to Recover": (latest_date - trough_date).days,
            "Total Cycle (Days)": (latest_date - correction_start).days,
        })

    return corrections


def label_correction(row):
    peak_year = int(row["Peak Date"][:4])
    peak_month = int(row["Peak Date"][5:7])
    drawdown = abs(row["Max Drawdown"])

    if peak_year == 2007 or (peak_year == 2008 and peak_month <= 3):
        return "2008 Financial Crisis"
    elif peak_year == 2010 and peak_month in [4, 5]:
        return "2010 Flash Crash"
    elif peak_year == 2011:
        return "2011 EU Debt Crisis"
    elif peak_year == 2015 or (peak_year == 2016 and peak_month <= 2):
        return "2015-16 China Slowdown"
    elif peak_year == 2018 and peak_month >= 9:
        return "2018 Rate Hike Selloff"
    elif peak_year == 2020 and peak_month <= 3:
        return "2020 COVID Crash"
    elif peak_year == 2022:
        return "2022 Rate Hike Bear Market"
    elif peak_year == 2025 and peak_month >= 10:
        return "2025-26 Iran War Correction"
    elif peak_year == 2026:
        return "2026 Iran War Correction"
    else:
        return f"{peak_year} Correction ({drawdown:.0f}%)"


def style_axes(fig, x_title=None, y_title=None, row=None, col=None):
    common_x = dict(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.06)",
        zeroline=False,
        showline=True,
        linecolor="#475569",
        tickfont=dict(color="#e5e7eb", size=12),
        title_font=dict(color="#e5e7eb", size=13),
    )
    common_y = dict(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False,
        showline=True,
        linecolor="#475569",
        tickfont=dict(color="#e5e7eb", size=12),
        title_font=dict(color="#e5e7eb", size=13),
    )
    if row is None:
        fig.update_xaxes(title_text=x_title, **common_x)
        fig.update_yaxes(title_text=y_title, **common_y)
    else:
        fig.update_xaxes(title_text=x_title, row=row, col=col, **common_x)
        fig.update_yaxes(title_text=y_title, row=row, col=col, **common_y)


def create_price_chart(df):
    fig = go.Figure()
    latest_date = df.index[-1]
    latest_close = df.iloc[-1]["Close"]

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Close"],
        line=dict(color="#60a5fa", width=2.8),
        fill="tozeroy",
        fillcolor="rgba(96,165,250,0.08)",
        name="S&P 500",
        hovertemplate="Date: %{x}<br>Close: %{y:,.0f}<extra></extra>",
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=[latest_date],
        y=[latest_close],
        mode="markers",
        marker=dict(size=10, color="#38bdf8", line=dict(color="#ffffff", width=1.8)),
        hovertemplate="Latest close: %{y:,.0f}<extra></extra>",
        showlegend=False,
    ))

    fig.add_hline(
        y=7000,
        line_dash="dash",
        line_color="#34d399",
        annotation_text="7,000 milestone",
        annotation_position="top left",
        annotation_font_color="#34d399"
    )

    fig.add_annotation(
        x=latest_date,
        y=latest_close,
        text=f"Latest: {latest_close:,.0f}",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#38bdf8",
        font=dict(color="#f8fafc", size=12),
        bgcolor="#0f172a",
        bordercolor="#38bdf8",
        borderwidth=1,
        ax=-55,
        ay=-35,
    )

    fig.update_layout(
        title="",
        template="plotly_white",
        height=430,
        margin=dict(l=70, r=30, t=20, b=40),
        font=dict(family="Inter, sans-serif", size=12, color="#e5e7eb"),
        hovermode="x unified",
        showlegend=False,
        paper_bgcolor="#0b1117",
        plot_bgcolor="#0b1117",
    )
    style_axes(fig, y_title="S&P 500 Close")
    return fig


def create_drawdown_chart(df):
    df = df.copy()
    df["Peak"] = df["Close"].cummax()
    df["Drawdown"] = (df["Close"] - df["Peak"]) / df["Peak"] * 100

    latest_date = df.index[-1]
    latest_drawdown = df.iloc[-1]["Drawdown"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Drawdown"],
        fill="tozeroy",
        fillcolor="rgba(248,113,113,0.12)",
        line=dict(color="#f87171", width=2.2),
        hovertemplate="Date: %{x}<br>Drawdown: %{y:.1f}%<extra></extra>",
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=[latest_date],
        y=[latest_drawdown],
        mode="markers",
        marker=dict(size=9, color="#f87171", line=dict(color="#ffffff", width=1.8)),
        hovertemplate="Latest: %{y:.1f}%<extra></extra>",
        showlegend=False,
    ))

    fig.add_hline(
        y=-10,
        line_dash="dot",
        line_color="#94a3b8",
        annotation_text="Correction (-10%)",
        annotation_position="bottom left",
        annotation_font_color="#cbd5e1"
    )
    fig.add_hline(
        y=-20,
        line_dash="dot",
        line_color="#94a3b8",
        annotation_text="Bear Market (-20%)",
        annotation_position="bottom left",
        annotation_font_color="#cbd5e1"
    )

    latest_text = "Recovered / near peak" if latest_drawdown > -0.5 else f"Latest: {latest_drawdown:.1f}%"
    fig.add_annotation(
        x=latest_date,
        y=latest_drawdown,
        text=latest_text,
        showarrow=True,
        arrowhead=2,
        arrowcolor="#f87171",
        font=dict(color="#f8fafc", size=12),
        bgcolor="#0f172a",
        bordercolor="#f87171",
        borderwidth=1,
        ax=-55,
        ay=-35,
    )

    fig.update_layout(
        title="",
        template="plotly_white",
        height=430,
        margin=dict(l=70, r=30, t=20, b=40),
        font=dict(family="Inter, sans-serif", size=12, color="#e5e7eb"),
        hovermode="x unified",
        showlegend=False,
        paper_bgcolor="#0b1117",
        plot_bgcolor="#0b1117",
    )
    style_axes(fig, y_title="Drawdown from Peak (%)")
    fig.update_yaxes(ticksuffix="%")
    return fig


def create_recovery_comparison(corrections_df):
    df = corrections_df.copy()
    df = df[df["Recovery Date"] != "Ongoing"]

    max_bottom = df["Days to Bottom"].max() if not df.empty else 1
    max_recovery = df["Days to Recover"].max() if not df.empty else 1

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Days to Bottom", "Days to Recover"),
        horizontal_spacing=0.22,
        shared_yaxes=True,
    )

    colors_down = ["#fca5a5"] * len(df)
    colors_up = ["#6ee7b7"] * len(df)
    if len(df) > 0:
        colors_down[-1] = "#f87171"
        colors_up[-1] = "#34d399"

    fig.add_trace(go.Bar(
        y=df["Label"],
        x=df["Days to Bottom"],
        orientation="h",
        marker=dict(color=colors_down),
        text=df["Days to Bottom"].astype(str) + "d",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}<br>Days to bottom: %{x}<extra></extra>",
        showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        y=df["Label"],
        x=df["Days to Recover"],
        orientation="h",
        marker=dict(color=colors_up),
        text=df["Days to Recover"].astype(str) + "d",
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}<br>Days to recover: %{x}<extra></extra>",
        showlegend=False,
    ), row=1, col=2)

    fig.update_layout(
        title="",
        height=max(360, len(df) * 62 + 90),
        template="plotly_white",
        margin=dict(l=230, r=110, t=50, b=20),
        font=dict(family="Inter, sans-serif", size=12, color="#e5e7eb"),
        showlegend=False,
        paper_bgcolor="#0b1117",
        plot_bgcolor="#0b1117",
    )

    style_axes(fig, x_title="Days", y_title=None, row=1, col=1)
    style_axes(fig, x_title="Days", y_title=None, row=1, col=2)
    fig.update_yaxes(showgrid=False, tickfont=dict(color="#e5e7eb", size=12), row=1, col=1)
    fig.update_yaxes(showgrid=False, showticklabels=False, row=1, col=2)
    fig.update_xaxes(range=[0, max_bottom * 1.18], row=1, col=1)
    fig.update_xaxes(range=[0, max_recovery * 1.18], row=1, col=2)

    return fig


# MAIN APP
with st.spinner("Loading S&P 500 data..."):
    sp500 = load_sp500_data()

if sp500.empty:
    st.error("Could not load S&P 500 data. Please try again.")
    st.stop()

corrections = find_corrections(sp500, threshold=-0.10)
corrections_df = pd.DataFrame(corrections)

if not corrections_df.empty:
    corrections_df["Label"] = corrections_df.apply(label_correction, axis=1)
    corrections_df = (
        corrections_df.sort_values("Max Drawdown")
        .drop_duplicates(subset="Label", keep="first")
        .sort_values("Peak Date")
        .reset_index(drop=True)
    )

latest_close = sp500.iloc[-1]["Close"]
latest_date = sp500.index[-1].strftime("%B %d, %Y")
ytd_return = ((sp500.iloc[-1]["Close"] / sp500.loc[sp500.index >= "2026-01-01"].iloc[0]["Close"]) - 1) * 100
all_time_high = sp500["Close"].max()
ath_date = sp500["Close"].idxmax().strftime("%B %d, %Y")

st.markdown(
    '''
    <div class="hero-wrap">
        <div class="main-header">S&amp;P 500 Correction &amp; Recovery Tracker</div>
        <div class="sub-header">Track every 10%+ S&amp;P 500 drawdown since 2008, compare how long each selloff took to bottom, and see how quickly markets recovered back to prior highs.</div>
    </div>
    ''',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Latest Close</div>
        <div class="metric-value blue">{latest_close:,.0f}</div>
        <div class="metric-sub">As of {latest_date}</div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    color_class = "green" if ytd_return >= 0 else "red"
    sign = "+" if ytd_return >= 0 else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">YTD Return (2026)</div>
        <div class="metric-value {color_class}">{sign}{ytd_return:.1f}%</div>
        <div class="metric-sub">Performance from the first trading day of the year</div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">All-Time High</div>
        <div class="metric-value green">{all_time_high:,.0f}</div>
        <div class="metric-sub">Recorded on {ath_date}</div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    from_ath = ((latest_close - all_time_high) / all_time_high) * 100
    ath_text = "At Record" if abs(from_ath) < 0.5 else f"{from_ath:.1f}%"
    ath_color = "green" if abs(from_ath) < 0.5 or from_ath > 0 else "red"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">From All-Time High</div>
        <div class="metric-value {ath_color}">{ath_text}</div>
        <div class="metric-sub">Distance from the market peak</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="section-label">S&amp;P 500 Price History</div>', unsafe_allow_html=True)
st.plotly_chart(create_price_chart(sp500), use_container_width=True, config=PLOTLY_CONFIG)

st.markdown('<div class="section-label">Drawdown from Peak</div>', unsafe_allow_html=True)
st.plotly_chart(create_drawdown_chart(sp500), use_container_width=True, config=PLOTLY_CONFIG)

if not corrections_df.empty:
    st.markdown('<div class="section-label">Correction &amp; Recovery Comparison</div>', unsafe_allow_html=True)
    st.plotly_chart(create_recovery_comparison(corrections_df), use_container_width=True, config=PLOTLY_CONFIG)

    st.markdown('<div class="section-label">All Corrections Since 2008</div>', unsafe_allow_html=True)
    display_df = corrections_df[["Label", "Peak Date", "Trough Date", "Recovery Date", "Max Drawdown", "Days to Bottom", "Days to Recover", "Total Cycle (Days)"]].copy()
    display_df.columns = ["Event", "Peak", "Trough", "Recovered", "Max Drawdown (%)", "Days Down", "Days Up", "Total Days"]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Event": st.column_config.TextColumn("Event", width="medium"),
            "Peak": st.column_config.TextColumn("Peak", width="small"),
            "Trough": st.column_config.TextColumn("Trough", width="small"),
            "Recovered": st.column_config.TextColumn("Recovered", width="small"),
            "Max Drawdown (%)": st.column_config.NumberColumn("Max Drawdown (%)", format="%.1f"),
            "Days Down": st.column_config.NumberColumn("Days Down", format="%d"),
            "Days Up": st.column_config.NumberColumn("Days Up", format="%d"),
            "Total Days": st.column_config.NumberColumn("Total Days", format="%d"),
        },
    )

    st.markdown('<div class="section-label">Summary Statistics</div>', unsafe_allow_html=True)
    recovered = corrections_df[corrections_df["Recovery Date"] != "Ongoing"]
    if not recovered.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_drawdown = recovered["Max Drawdown"].mean()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg. Max Drawdown</div>
                <div class="metric-value red">{avg_drawdown:.1f}%</div>
                <div class="metric-sub">Average peak-to-trough decline across recovered events</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            avg_bottom = recovered["Days to Bottom"].mean()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg. Days to Bottom</div>
                <div class="metric-value blue">{avg_bottom:.0f}</div>
                <div class="metric-sub">Average time markets took to reach the trough</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            avg_recovery = recovered["Days to Recover"].mean()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg. Days to Recover</div>
                <div class="metric-value green">{avg_recovery:.0f}</div>
                <div class="metric-sub">Average time needed to get back to the prior peak</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="insight-box">
        <div class="insight-title">Key insight</div>
        <div class="insight-copy">Markets have recovered from every single correction since 2008. The average recovery takes longer than the selloff, but it always comes. The 2026 Iran War correction followed this pattern exactly.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown(
    '<div class="footer-text">'
    'Built by <a href="https://www.linkedin.com/in/shivangi-gaur" target="_blank">Shivangi Gaur</a> · '
    'MS Quantitative Finance (STEM), University at Buffalo "26 · '
    'Data: Yahoo Finance (yfinance) · '
    '<a href="https://github.com/Shiv290296" target="_blank">GitHub</a>'
    '</div>',
    unsafe_allow_html=True,
)
