import os

import plotly.express as px
import streamlit as st

from analytics import load_dashboard_data, refresh_metrics

st.set_page_config(page_title="FinAnalytics Operations", page_icon="📈", layout="wide")
st.title("FinAnalytics Operations")
st.caption("Live payment reliability and revenue monitoring")

refresh_metrics()
metrics, alerts = load_dashboard_data(int(os.getenv("DASHBOARD_LOOKBACK_HOURS", "24")))

if metrics.empty:
    st.warning("No metrics available yet. Start the simulator and pipeline workers.")
else:
    latest = metrics.sort_values("bucket_start").iloc[-1]
    total = int(metrics["total_transactions"].sum())
    failures = int(metrics["failed_transactions"].sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Transactions", f"{total:,}")
    c2.metric("Failure rate", f"{failures / total:.2%}" if total else "0.00%")
    c3.metric("Revenue", f"₹{metrics['total_revenue'].sum():,.0f}")
    c4.metric("Latest provider", str(latest["provider"]))

    chart = metrics.copy()
    chart["failure_rate"] = chart["failure_rate"] * 100
    st.plotly_chart(px.line(chart, x="bucket_start", y="failure_rate", color="provider",
                            labels={"failure_rate": "Failure rate (%)"}), use_container_width=True)
    st.subheader("Recent alerts")
    st.dataframe(alerts, use_container_width=True, hide_index=True)

