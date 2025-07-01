# src/portfolio_mapper/analytics.py

# Copyright (c) Adrian Robinson 2025
# This software is dual-licensed under the MIT License (for NHS use only)
# and a Commercial License (for other use).
# For commercial licensing inquiries, please contact adrian.j.robinson@gmail.com

import streamlit as st
from typing import Dict, Any
import json
from sqlalchemy import text

def track_event(event_name: str, properties: Dict[str, Any] = None):
    """
    Tracks an event by inserting it into a Supabase database.
    This is privacy-preserving and does not log user reflection text.
    """
    try:
        # Initialize connection to Supabase.
        conn = st.connection("db", type="sql")

        # Create a copy to avoid modifying the original dict passed to the function
        event_properties = properties.copy() if properties else {}
        
        # Automatically add session_id if it exists in the state
        if "session_id" in st.session_state:
            event_properties["session_id"] = st.session_state.session_id
        
        # Use a session to execute the query
        with conn.session as s:
            s.execute(
                text('INSERT INTO events (event_name, properties) VALUES (:event_name, :properties);'),
                params=dict(event_name=event_name, properties=json.dumps(event_properties))
            )
            s.commit()
    except Exception as e:
        # Fail silently to not disrupt the user experience.
        # In a production environment, you might log this error elsewhere.
        print(f"Analytics Error: Failed to track event '{event_name}'. Reason: {e}")