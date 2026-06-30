import os
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="RetailPulse",
    page_icon="📊",
    layout="wide"
)

LIVE_FILE = Path("output/kpis_by_country/latest_kpis.csv")
DEMO_FILE = Path("sample_data/latest_kpis.csv")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #111827 45%, #1e293b 100%);
    color: white;
}
.block-container {
    padding-top: 1.5rem;
}
.hero {
    padding: 30px;
    border-radius: 26px;
    background: linear-gradient(120deg, rgba(37,99,235,.34), rgba(124,58,237,.30));
    border: 1px solid rgba(255,255,255,.12);
    box-shadow: 0 22px 65px rgba(0,0,0,.38);
}
.hero h1 {
    font-size: 52px;
    margin-bottom: 0px;
}
.hero p {
    font-size: 18px;
    color: #cbd5e1;
}
.live-badge {
    display: inline-block;
    padding: 8px 14px;
    border-radius: 999px;
    background: rgba(34,197,94,.14);
    color: #86efac;
    border: 1px solid rgba(34,197,94,.35);
    font-weight: 800;
    margin-bottom: 12px;
}
.metric-card {
    padding: 23px;
    border-radius: 22px;
    background: linear-gradient(135deg, rgba(255,255,255,.09), rgba(255,255,255,.045));
    border: 1px solid rgba(255,255,255,.12);
    box-shadow: 0 12px 35px rgba(0,0,0,.28);
}
.metric-card.revenue { border-left: 5px solid #22c55e; }
.metric-card.orders { border-left: 5px solid #38bdf8; }
.metric-card.avg { border-left: 5px solid #a78bfa; }
.metric-card.market { border-left: 5px solid #f59e0b; }

.metric-label {
    font-size: 15px;
    color: #cbd5e1;
    font-weight: 700;
}
.metric-value {
    font-size: 36px;
    font-weight: 900;
    color: white;
}
.small-note {
    color: #94a3b8;
    font-size: 13px;
}
.footer {
    padding: 22px;
    border-radius: 18px;
    background: rgba(255,255,255,.055);
    border: 1px solid rgba(255,255,255,.10);
    color: #cbd5e1;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)


def load_latest_csv():
    required_columns = ["country", "total_revenue", "total_orders", "avg_order_value"]

    for file_path, mode in [
        (LIVE_FILE, "🟢 Live Mode"),
        (DEMO_FILE, "🟣 Demo Snapshot")
    ]:
        if file_path.exists() and file_path.stat().st_size > 0:
            try:
                df = pd.read_csv(file_path)
                if not df.empty and all(col in df.columns for col in required_columns):
                    st.session_state["data_mode"] = mode
                    st.session_state["last_good_df"] = df
                    return df, str(file_path)
            except pd.errors.EmptyDataError:
                pass

    if "last_good_df" in st.session_state:
        st.session_state["data_mode"] = "🟡 Cached Data"
        return st.session_state["last_good_df"], "cached"

    return pd.DataFrame(), None


df, latest_file = load_latest_csv()

data_mode = st.session_state.get("data_mode", "Unknown")
now_time = datetime.now().strftime("%H:%M:%S")

st.markdown(f"""
<div class="hero">
    <div class="live-badge">● {data_mode} | Last refresh {now_time}</div>
    <h1>📊 RetailPulse</h1>
    <p>Real-Time Retail Analytics Platform using Kafka, Apache Spark Streaming, CSV, Plotly, and Streamlit.</p>
</div>
""", unsafe_allow_html=True)

st.write("")

if df.empty:
    st.warning("No KPI data found. Run the real-time pipeline or add sample_data/latest_kpis.csv.")
    st.stop()

df = df.sort_values("total_revenue", ascending=False).reset_index(drop=True)

total_revenue = df["total_revenue"].sum()
total_orders = df["total_orders"].sum()
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
top_country = df.iloc[0]["country"]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card revenue">
        <div class="metric-label">💰 Total Revenue</div>
        <div class="metric-value">${total_revenue:,.2f}</div>
        <div class="small-note">Across all countries</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card orders">
        <div class="metric-label">🛒 Total Orders</div>
        <div class="metric-value">{int(total_orders):,}</div>
        <div class="small-note">Streaming orders processed</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card avg">
        <div class="metric-label">📦 Avg Order Value</div>
        <div class="metric-value">${avg_order_value:,.2f}</div>
        <div class="small-note">Revenue per order</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card market">
        <div class="metric-label">🌍 Top Market</div>
        <div class="metric-value">{top_country}</div>
        <div class="small-note">Highest revenue country</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")
st.write("")

left, right = st.columns([1.35, 1])

bar_colors = ["#fbbf24" if i == 0 else "#60a5fa" for i in range(len(df))]

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(
    x=df["country"],
    y=df["total_revenue"],
    text=[f"${v:,.0f}" for v in df["total_revenue"]],
    textposition="outside",
    marker=dict(color=bar_colors),
    customdata=df[["total_orders", "avg_order_value"]],
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Revenue: $%{y:,.2f}<br>"
        "Orders: %{customdata[0]:,.0f}<br>"
        "Avg Order: $%{customdata[1]:,.2f}<extra></extra>"
    )
))
fig_bar.update_layout(
    title="💰 Top Revenue Markets",
    template="plotly_dark",
    height=430,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis_title="Total Revenue ($)",
    xaxis_title="Country",
    margin=dict(t=70, l=20, r=20, b=20)
)

fig_pie = px.pie(
    df,
    names="country",
    values="total_orders",
    title="🛒 Market Share",
    hole=0.58
)
fig_pie.update_traces(
    textinfo="percent+label",
    pull=[0.05 if i == 0 else 0 for i in range(len(df))]
)
fig_pie.update_layout(
    template="plotly_dark",
    height=430,
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=70, l=20, r=20, b=20),
    legend_title_text="Country"
)

with left:
    st.plotly_chart(fig_bar, use_container_width=True)

with right:
    st.plotly_chart(fig_pie, use_container_width=True)

st.write("")

avg_df = df.sort_values("avg_order_value", ascending=True)

fig_avg = go.Figure()
fig_avg.add_trace(go.Bar(
    x=avg_df["avg_order_value"],
    y=avg_df["country"],
    orientation="h",
    text=[f"${v:,.2f}" for v in avg_df["avg_order_value"]],
    textposition="outside",
    marker=dict(
        color=avg_df["avg_order_value"],
        colorscale="Purples"
    ),
    hovertemplate="<b>%{y}</b><br>Average Order Value: $%{x:,.2f}<extra></extra>"
))
fig_avg.update_layout(
    title="📈 Average Order Value by Country",
    template="plotly_dark",
    height=390,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Average Order Value ($)",
    yaxis_title="Country",
    margin=dict(t=70, l=20, r=60, b=20)
)
st.plotly_chart(fig_avg, use_container_width=True)

st.write("")

st.subheader("📋 Live KPI Table")

display_df = df.copy()
display_df["total_revenue"] = display_df["total_revenue"].map(lambda x: f"${x:,.2f}")
display_df["avg_order_value"] = display_df["avg_order_value"].map(lambda x: f"${x:,.2f}")
display_df["total_orders"] = display_df["total_orders"].map(lambda x: f"{x:,.0f}")

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

if latest_file and latest_file != "cached":
    last_updated = datetime.fromtimestamp(os.path.getmtime(latest_file)).strftime("%Y-%m-%d %H:%M:%S")
else:
    last_updated = "Cached session data"

st.caption(f"Last updated: {last_updated} | Mode: {data_mode}")
st.caption("Data pipeline: Kafka → Spark Structured Streaming → CSV → Streamlit Dashboard")

st.write("")

st.markdown("""
<div class="footer">
    <b>Built with</b> &nbsp; Python · Apache Kafka · Apache Spark · Streamlit · Plotly
</div>
""", unsafe_allow_html=True)

time.sleep(2)
st.rerun()
