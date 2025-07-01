# src/portfolio_mapper/dashboard.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

# NOTE: this is a todo area for the future...

import streamlit as st
import pandas as pd
import json

st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="📊",
    layout="wide"
)

def check_password():
    """Returns `True` if the user has entered the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    # Show password input.
    password = st.text_input("Enter password to view dashboard", type="password")
    if not password:
        st.stop()

    if password == st.secrets.app.admin_password:
        st.session_state.password_correct = True
        st.rerun()
    else:
        st.error("Incorrect password.")
        st.stop()

@st.cache_data(ttl=600) # Cache data for 10 minutes
def load_analytics_data():
    """Connects to Supabase and fetches all event data."""
    try:
        conn = st.connection("db", type="sql")
        df = conn.query("SELECT * FROM events ORDER BY created_at DESC;", ttl=600)

        # --- Process the DataFrame ---
        # 1. Parse the JSON 'properties' column
        def safe_json_loads(s):
            try:
                return json.loads(s) if isinstance(s, str) else s
            except (json.JSONDecodeError, TypeError):
                return {}

        df['properties'] = df['properties'].apply(safe_json_loads)
        
        # 2. Expand the JSON properties into their own columns
        properties_df = pd.json_normalize(df['properties'])
        
        # 3. Combine the original DataFrame with the new properties columns
        df = pd.concat([df.drop(columns=['properties']), properties_df], axis=1)

        # 4. Convert timestamp to a more readable timezone
        df['created_at'] = pd.to_datetime(df['created_at']).dt.tz_convert('Europe/London')

        return df
    except Exception as e:
        st.error(f"Failed to load analytics data: {e}")
        return pd.DataFrame()

def display_dashboard(df):
    """Renders the dashboard using the provided DataFrame."""
    st.title("📊 Admin Dashboard")
    st.markdown("Live analytics and usage metrics for the Portfolio Mapper.")

    if df.empty:
        st.warning("No analytics data found.")
        return

    # --- Key Metrics ---
    st.header("Key Metrics")
    analyses_started = df[df['event_name'] == 'analysis_started'].shape[0]
    analyses_completed = df[df['event_name'] == 'analysis_completed'].shape[0]
    reports_downloaded = df[df['event_name'] == 'report_downloaded'].shape[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Analyses Started", f"{analyses_started:,}")
    col2.metric("Analyses Completed", f"{analyses_completed:,}")
    col3.metric("Reports Downloaded", f"{reports_downloaded:,}")

    # --- Usage Over Time ---
    st.header("Usage Over Time")
    usage_df = df[df['event_name'] == 'analysis_started'].copy()
    usage_df.set_index('created_at', inplace=True)
    daily_usage = usage_df.resample('D').size().rename("Analyses per Day")
    st.line_chart(daily_usage)

    # --- Popularity Metrics ---
    st.header("Most Popular Selections")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Roles")
        role_counts = df[df['event_name'] == 'analysis_started']['role'].value_counts()
        st.bar_chart(role_counts)

    with col2:
        st.subheader("Top Frameworks")
        framework_df = df[df['event_name'] == 'analysis_started'][['frameworks']].copy()
        framework_df = framework_df.dropna().explode('frameworks')
        framework_counts = framework_df['frameworks'].value_counts()
        st.bar_chart(framework_counts)

    # --- Safety Metrics ---
    st.header("Safety & PII Flags")
    distress_detected = df[df['event_name'] == 'safety_check_distress_detected'].shape[0]
    pii_detected = df[df['event_name'] == 'safety_check_pii_detected'].shape[0]
    pii_acknowledged = df[df['event_name'] == 'pii_warning_acknowledged'].shape[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("User Distress Flags", f"{distress_detected:,}")
    col2.metric("PII Warnings Shown", f"{pii_detected:,}")
    col3.metric("PII Warnings Acknowledged", f"{pii_acknowledged:,}")

    # --- Raw Data View ---
    with st.expander("View Raw Event Data"):
        st.dataframe(df)


if __name__ == "__main__":
    if check_password():
        analytics_df = load_analytics_data()
        display_dashboard(analytics_df)

