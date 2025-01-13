# nba_streamlit_app.py

import streamlit as st
import pandas as pd

# Load the CSV file
@st.cache_data(ttl=60)
def load_data():
    try:
        return pd.read_csv("nba_player_best_ev_projections.csv")
    except FileNotFoundError:
        st.error("CSV file not found. Please run the data generation script first.")
        return pd.DataFrame()

# Streamlit UI
def run_streamlit_app():
    st.title("NBA Player Best EV Projections")
    data = load_data()

    if data.empty:
        st.warning("No data to display. Ensure the CSV file is generated.")
        return

    # Search and filter functionality
    player_filter = st.text_input("Search by Player Name:", placeholder="Type player name...")
    metric_filter = st.multiselect(
        "Filter by Metric:",
        options=data['Metric'].unique(),
        default=data['Metric'].unique()
    )

    filtered_data = data[
        (data['Player Name'].str.contains(player_filter, case=False, na=False)) &
        (data['Metric'].isin(metric_filter))
    ]

    # Display filtered and sortable data
    st.dataframe(filtered_data, use_container_width=True)

    # Option to download filtered data
    st.download_button(
        label="Download Filtered Data as CSV",
        data=filtered_data.to_csv(index=False),
        file_name="nba_player_best_ev_projections.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    run_streamlit_app()
