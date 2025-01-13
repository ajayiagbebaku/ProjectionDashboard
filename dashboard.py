# nba_streamlit_app.py

import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime

# Global variable to store the last data hash and timestamp
LAST_UPDATED = {"hash": None, "timestamp": None}

# Calculate the hash of the CSV data
def calculate_data_hash(data: pd.DataFrame) -> str:
    # Convert data to a string and calculate its hash
    data_string = data.to_csv(index=False)
    return hashlib.md5(data_string.encode()).hexdigest()

# Load the CSV file and manage "Last Updated" timestamp
@st.cache_data(ttl=60)
def load_data():
    global LAST_UPDATED

    try:
        data = pd.read_csv("nba_player_best_ev_projections.csv")
        current_hash = calculate_data_hash(data)

        # Check if the hash has changed
        if LAST_UPDATED["hash"] != current_hash:
            LAST_UPDATED["hash"] = current_hash
            # Format the time in 12-hour format with AM/PM
            LAST_UPDATED["timestamp"] = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

        return data, LAST_UPDATED["timestamp"]
    except FileNotFoundError:
        st.error("CSV file not found. Please run the data generation script first.")
        return pd.DataFrame(), None

# Streamlit UI
def run_streamlit_app():
    st.title("NBA Player Best EV Projections")
    data, last_updated = load_data()

    if data.empty:
        st.warning("No data to display. Ensure the CSV file is generated.")
        return

    # Display last updated time
    if last_updated:
        st.sidebar.info(f"Last Updated: {last_updated}")

    # Sidebar for filters
    st.sidebar.header("Filters")
    player_filter = st.sidebar.text_input("Search by Player Name:", placeholder="Type player name...")
    metric_filter = st.sidebar.multiselect(
        "Filter by Metric:",
        options=data['Metric'].unique(),
        default=data['Metric'].unique()
    )
    sportsbook_filter = st.sidebar.multiselect(
        "Filter by Sportsbook:",
        options=data['Bookmaker'].unique(),
        default=data['Bookmaker'].unique()
    )
    confidence_filter = st.sidebar.slider(
        "Filter by Confidence (%)",
        min_value=0,
        max_value=100,
        value=(0, 100)
    )

    # Apply filters
    filtered_data = data[
        (data['Player Name'].str.contains(player_filter, case=False, na=False)) &
        (data['Metric'].isin(metric_filter)) &
        (data['Bookmaker'].isin(sportsbook_filter)) &
        (data['Confidence'].str.rstrip('%').astype(float).between(*confidence_filter))
    ]

    # Display filtered and sortable data
    st.subheader("Filtered Results")
    st.dataframe(filtered_data, use_container_width=True)

    # Option to download filtered data
    st.download_button(
        label="Download Filtered Data as CSV",
        data=filtered_data.to_csv(index=False),
        file_name="filtered_nba_projections.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    run_streamlit_app()
