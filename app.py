import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os

st.set_page_config(page_title="Smart Cooling Solar", page_icon="☀️", layout="wide")

FIREBASE_URL = "https://solar-monitor-641e3-default-rtdb.asia-southeast1.firebasedatabase.app"

def get_auth():
    try:
        return st.secrets["FIREBASE_AUTH"]
    except:
        return os.environ.get("FIREBASE_AUTH", "")

def get_latest():
    try:
        auth = get_auth()
        r = requests.get(f"{FIREBASE_URL}/solar/latest.json?auth={auth}", timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_history():
    try:
        auth = get_auth()
        r = requests.get(f"{FIREBASE_URL}/solar/history.json?auth={auth}", timeout=5)
        if r.status_code == 200 and r.json():
            rows = list(r.json().values())
            df = pd.DataFrame(rows)
            df["voltage"] = pd.to_numeric(df["voltage"], errors="coerce")
            df["current"] = pd.to_numeric(df["current"], errors="coerce")
            df["power"]   = pd.to_numeric(df["power"],   errors="coerce")
            return df.tail(200)
    except:
        pass
    return pd.DataFrame()

with st.sidebar:
    st.header("Settings")
    refresh = st.slider("Auto-refresh (seconds)", 2, 30, 5)
    st.divider()
    st.markdown("**Device:** ESP32 + INA219")
    st.markdown("**Repo:** maxxsuiii/SmartCoolingSolar")

st.markdown(
    f"<script>setTimeout(()=>location.reload(),{refresh*1000});</script>",
    unsafe_allow_html=True
)

st.title("Smart Cooling Solar Monitor")
st.caption("ESP32 + INA219 · real-time solar monitoring")

latest = get_latest()
df     = get_history()

if not latest:
    st.warning("No data yet — waiting for ESP32 to connect.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Voltage", f"{float(latest['voltage']):.2f} V")
col2.metric("Current", f"{float(latest['current']):.0f} mA")
col3.metric("Power",   f"{float(latest['power']):.2f} W")
col4.metric("Readings", len(df))

st.divider()

if not df.empty:
    st.subheader("Power output history")
    fig = px.area(df, y="power",
                  labels={"power": "Power (W)", "index": ""},
                  color_discrete_sequence=["#1D9E75"])
    fig.update_layout(height=280, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Voltage")
        fig2 = px.line(df, y="voltage",
                       color_discrete_sequence=["#BA7517"])
        fig2.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig2, use_container_width=True)
    with c2:
        st.subheader("Current")
        fig3 = px.line(df, y="current",
                       color_discrete_sequence=["#534AB7"])
        fig3.update_layout(height=200, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig3, use_container_width=True)

    with st.expander("Raw data table"):
        st.dataframe(df[::-1], use_container_width=True)