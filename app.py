import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
import os

st.set_page_config(page_title="Smart Cooling Solar", page_icon="☀️", layout="wide")

FIREBASE_URL  = "https://solar-monitor-641e3-default-rtdb.asia-southeast1.firebasedatabase.app"
ESP32_INTERVAL = 5  # must match INTERVAL in ESP32 firmware (seconds)

def get_auth():
    try:
        return st.secrets["FIREBASE_AUTH"]
    except:
        return os.environ.get("FIREBASE_AUTH", "")

def get_latest():
    try:
        r = requests.get(f"{FIREBASE_URL}/solar/latest.json?auth={get_auth()}", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_history():
    try:
        r = requests.get(f"{FIREBASE_URL}/solar/history.json?auth={get_auth()}", timeout=5)
        if r.status_code == 200 and r.json():
            rows = list(r.json().values())
            df = pd.DataFrame(rows)
            df["voltage"] = pd.to_numeric(df["voltage"], errors="coerce")
            df["current"] = pd.to_numeric(df["current"], errors="coerce")
            df["power"]   = pd.to_numeric(df["power"],   errors="coerce")
            df["uptime"]  = pd.to_numeric(df["uptime"],  errors="coerce")
            df = df.reset_index(drop=True)
            return df.tail(200)
    except:
        pass
    return pd.DataFrame()

def uptime_str(seconds):
    if pd.isna(seconds): return "—"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"

def device_status(latest):
    """Returns online/offline based on last uptime change."""
    if not latest:
        return "offline", "🔴"
    return "online", "🟢"

# ── Sidebar ────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    st.info(f"ESP32 sends every **{ESP32_INTERVAL}s**\nDashboard syncs at same rate.")
    st.divider()
    st.markdown("**Device:** ESP32 + INA219")
    st.markdown("**Repo:** maxxsuiii/SmartCoolingSolar")
    st.divider()
    device_ph  = st.empty()   # online/offline badge
    uptime_ph  = st.empty()   # ESP32 uptime
    updated_ph = st.empty()   # last fetch time

st.title("Smart Cooling Solar Monitor")
st.caption("ESP32 + INA219 · synchronized real-time monitoring")

# ── Placeholders ───────────────────────────────────────
alert_ph   = st.empty()
metrics_ph = st.empty()
div_ph     = st.empty()
power_ph   = st.empty()
cols_ph    = st.empty()
table_ph   = st.empty()

# ── Real-time loop — synced to ESP32 interval ──────────
iteration  = 0
prev_uptime = None

while True:
    latest = get_latest()
    df     = get_history()

    # ── Device status ──────────────────────────────────
    status_text, status_icon = device_status(latest)
    device_ph.markdown(
        f"**Status:** {status_icon} {status_text.upper()}"
    )

    if latest:
        current_uptime = latest.get("uptime")

        # Warn if ESP32 stopped sending (uptime unchanged)
        if prev_uptime is not None and current_uptime == prev_uptime:
            alert_ph.warning("ESP32 may have stopped sending data.")
        else:
            alert_ph.empty()

        prev_uptime = current_uptime
        uptime_ph.markdown(f"**ESP32 uptime:** `{uptime_str(current_uptime)}`")

    updated_ph.markdown(
        f"<div style='font-size:12px;color:gray'>Dashboard synced:<br>"
        f"{pd.Timestamp.now().strftime('%H:%M:%S')}</div>",
        unsafe_allow_html=True
    )

    # ── Metrics ────────────────────────────────────────
    with metrics_ph.container():
        if not latest:
            st.warning("No data yet — waiting for ESP32 to connect.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Voltage",  f"{float(latest['voltage']):.2f} V")
            col2.metric("Current",  f"{float(latest['current']):.0f} mA")
            col3.metric("Power",    f"{float(latest['power']):.2f} W")
            col4.metric("Readings", len(df))

    # ── Charts ─────────────────────────────────────────
    if latest and not df.empty:
        div_ph.divider()

        with power_ph.container():
            st.subheader("Power output history")
            fig = px.area(df, y="power",
                          labels={"power": "Power (W)", "index": "Reading"},
                          color_discrete_sequence=["#1D9E75"])
            fig.update_layout(height=280, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, width="stretch", key=f"power_{iteration}")

        with cols_ph.container():
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Voltage")
                fig2 = px.line(df, y="voltage",
                               color_discrete_sequence=["#BA7517"])
                fig2.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig2, width="stretch", key=f"voltage_{iteration}")
            with c2:
                st.subheader("Current")
                fig3 = px.line(df, y="current",
                               color_discrete_sequence=["#534AB7"])
                fig3.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig3, width="stretch", key=f"current_{iteration}")

        with table_ph.container():
            with st.expander("Raw data table"):
                display_df = df[["uptime","voltage","current","power"]].copy()
                display_df["uptime"] = display_df["uptime"].apply(uptime_str)
                display_df.columns = ["Uptime","Voltage (V)","Current (mA)","Power (W)"]
                st.dataframe(display_df[::-1], width="stretch")

    iteration += 1
    time.sleep(ESP32_INTERVAL)  # sleep exactly as long as ESP32 interval