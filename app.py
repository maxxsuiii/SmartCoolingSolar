import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import datetime
import os

st.set_page_config(
    page_title="Smart Cooling Solar",
    page_icon="☀️",
    layout="wide"
)

st.title("Smart Cooling Solar Monitor")
st.caption("ESP32 + INA219 · real-time solar monitoring")

# ── Sidebar ──────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    refresh = st.slider("Auto-refresh (seconds)", 2, 30, 5)
    max_rows = st.slider("History points", 50, 500, 100)
    st.divider()
    st.markdown("**Device:** ESP32 + INA219")
    st.markdown("**Repo:** maxxsuiii/SmartCoolingSolar")

# ── Auto-refresh ──────────────────────────────────────
st.markdown(
    f"<script>setTimeout(()=>location.reload(),{refresh*1000});</script>",
    unsafe_allow_html=True
)

# ── Load data ─────────────────────────────────────────
CSV_FILE = "data.csv"

if not os.path.exists(CSV_FILE):
    # Create a demo file so the dashboard isn't blank
    demo = pd.DataFrame([
        {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
         "voltage": 0.0, "current": 0.0, "power": 0.0}
    ])
    demo.to_csv(CSV_FILE, index=False)
    st.warning("No data yet — waiting for ESP32. Showing placeholder.")

df = pd.read_csv(CSV_FILE, parse_dates=["time"])
df = df.tail(max_rows)

# ── Latest reading ─────────────────────────────────────
latest = df.iloc[-1]
prev   = df.iloc[-2] if len(df) > 1 else latest

col1, col2, col3, col4 = st.columns(4)
col1.metric("Voltage",  f"{latest['voltage']:.2f} V",
            f"{latest['voltage']-prev['voltage']:+.2f}")
col2.metric("Current",  f"{latest['current']:.0f} mA",
            f"{latest['current']-prev['current']:+.0f}")
col3.metric("Power",    f"{latest['power']:.2f} W",
            f"{latest['power']-prev['power']:+.2f}")
col4.metric("Total readings", len(df))

st.divider()

# ── Charts ─────────────────────────────────────────────
st.subheader("Power output history")
fig = px.area(df, x="time", y="power",
              labels={"power": "Power (W)", "time": ""},
              color_discrete_sequence=["#1D9E75"])
fig.update_layout(height=280, margin=dict(l=0,r=0,t=0,b=0))
st.plotly_chart(fig, use_container_width=True)

c1, c2 = st.columns(2)
with c1:
    st.subheader("Voltage")
    fig2 = px.line(df, x="time", y="voltage",
                   color_discrete_sequence=["#BA7517"])
    fig2.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig2, use_container_width=True)

with c2:
    st.subheader("Current")
    fig3 = px.line(df, x="time", y="current",
                   color_discrete_sequence=["#534AB7"])
    fig3.update_layout(height=200, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── Raw data table ──────────────────────────────────────
with st.expander("Raw data table"):
    st.dataframe(df[::-1], use_container_width=True)