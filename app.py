import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import time
import os

st.set_page_config(page_title="Smart Cooling Solar", page_icon="☀️", layout="wide")

FIREBASE_URL   = "https://solar-monitor-641e3-default-rtdb.asia-southeast1.firebasedatabase.app"
ESP32_INTERVAL = 5

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
            for col in ["voltage", "current", "power", "energy", "uptime"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                else:
                    df[col] = 0.0
            if "time" not in df.columns:
                df["time"] = "—"
            return df.tail(200).reset_index(drop=True)
    except:
        pass
    return pd.DataFrame()

def uptime_str(seconds):
    if pd.isna(seconds): return "—"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"

# ── Sidebar ────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    st.info(f"ESP32 sends every **{ESP32_INTERVAL}s**")
    st.divider()
    st.markdown("**Device:** ESP32 + INA219")
    st.markdown("**Location:** Malaysia (UTC+8)")
    st.markdown("**Repo:** maxxsuiii/SmartCoolingSolar")
    st.divider()
    device_ph  = st.empty()
    uptime_ph  = st.empty()
    updated_ph = st.empty()

st.title("Smart Cooling Solar Monitor")
st.caption("ESP32 + INA219 · Malaysia time (UTC+8)")

alert_ph   = st.empty()
metrics_ph = st.empty()
energy_ph  = st.empty()
div_ph     = st.empty()
power_ph   = st.empty()
cols_ph    = st.empty()
energy_chart_ph = st.empty()
table_ph   = st.empty()

iteration   = 0
prev_uptime = None

while True:
    latest = get_latest()
    df     = get_history()

    # ── Sidebar ────────────────────────────────────────
    if latest:
        current_uptime = latest.get("uptime")
        last_time      = latest.get("time", "—")

        if prev_uptime is not None and current_uptime == prev_uptime:
            device_ph.markdown("**Status:** 🔴 OFFLINE")
            alert_ph.warning("ESP32 stopped sending. Check your device.")
        else:
            device_ph.markdown("**Status:** 🟢 ONLINE")
            alert_ph.empty()

        prev_uptime = current_uptime
        uptime_ph.markdown(f"**Uptime:** `{uptime_str(current_uptime)}`")
        updated_ph.markdown(f"**Last reading:**\n\n`{last_time}`")
    else:
        device_ph.markdown("**Status:** 🔴 OFFLINE")
        updated_ph.markdown("**Last reading:** —")

    # ── Metric cards (row 1) ───────────────────────────
    with metrics_ph.container():
        if not latest:
            st.warning("No data yet — waiting for ESP32 to connect.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Voltage",  f"{float(latest['voltage']):.2f} V")
            col2.metric("Current",  f"{float(latest['current']):.0f} mA")
            col3.metric("Power",    f"{float(latest['power']):.2f} W")
            col4.metric("Readings", len(df))

    # ── Energy summary (row 2) ─────────────────────────
    if latest and not df.empty:
        total_energy = float(latest.get("energy", 0))
        session_peak = float(df["power"].max())
        avg_power    = float(df["power"].mean())

        with energy_ph.container():
            st.subheader("Energy summary")
            e1, e2, e3 = st.columns(3)
            e1.metric(
                "Total energy",
                f"{total_energy:.2f} Wh" if total_energy < 1000
                else f"{total_energy/1000:.3f} kWh"
            )
            e2.metric("Peak power",   f"{session_peak:.2f} W")
            e3.metric("Average power", f"{avg_power:.2f} W")

    # ── Charts ─────────────────────────────────────────
    if latest and not df.empty:
        div_ph.divider()

        with power_ph.container():
            st.subheader("Power output history")
            fig = px.area(df, x="time", y="power",
                          labels={"power": "Power (W)", "time": "Malaysia Time"},
                          color_discrete_sequence=["#1D9E75"])
            fig.update_layout(height=260, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, width="stretch", key=f"power_{iteration}")

        with cols_ph.container():
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Voltage")
                fig2 = px.line(df, x="time", y="voltage",
                               labels={"voltage": "V", "time": ""},
                               color_discrete_sequence=["#BA7517"])
                fig2.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig2, width="stretch", key=f"voltage_{iteration}")
            with c2:
                st.subheader("Current")
                fig3 = px.line(df, x="time", y="current",
                               labels={"current": "mA", "time": ""},
                               color_discrete_sequence=["#534AB7"])
                fig3.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig3, width="stretch", key=f"current_{iteration}")

        with energy_chart_ph.container():
            st.subheader("Cumulative energy (Wh)")
            fig4 = px.area(df, x="time", y="energy",
                           labels={"energy": "Energy (Wh)", "time": "Malaysia Time"},
                           color_discrete_sequence=["#534AB7"])
            fig4.update_layout(height=220, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig4, width="stretch", key=f"energy_{iteration}")

        with table_ph.container():
            with st.expander("Raw data table"):
                display_df = df[["time", "uptime", "voltage",
                                 "current", "power", "energy"]].copy()
                display_df["uptime"] = display_df["uptime"].apply(uptime_str)
                display_df["energy"] = display_df["energy"].apply(
                    lambda x: f"{x:.4f}" if not pd.isna(x) else "—"
                )
                display_df.columns = [
                    "Malaysia Time", "Uptime",
                    "Voltage (V)", "Current (mA)",
                    "Power (W)", "Energy (Wh)"
                ]
                st.dataframe(display_df[::-1], width="stretch")

    iteration += 1
    time.sleep(ESP32_INTERVAL)