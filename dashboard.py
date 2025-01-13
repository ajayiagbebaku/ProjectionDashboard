import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime
from pytz import timezone

# Global variable to store the last data hash and timestamp
LAST_UPDATED = {"hash": None, "timestamp": None}

# Central Time Zone
CENTRAL_TZ = timezone("US/Central")

# Page configuration (Set title and icon)
st.set_page_config(
    page_title="NBA EV Projections App",
    page_icon="🏀",  # Emoji or custom icon file path
    layout="wide"
)

# Calculate the hash of the CSV data
def calculate_data_hash(data: pd.DataFrame) -> str:
    data_string = data.to_csv(index=False)
    return hashlib.md5(data_string.encode()).hexdigest()

# Load the CSV file and manage "Last Updated" timestamp
@st.cache_data(ttl=60)
def load_data():
    global LAST_UPDATED

    try:
        data = pd.read_csv("nba_player_best_ev_projections.csv")
        
        # Ensure Confidence is numeric
        if 'Confidence' in data.columns:
            data['Confidence'] = (
                data['Confidence']
                .str.rstrip('%')  # Remove %
                .astype(float)    # Convert to float
            )

        current_hash = calculate_data_hash(data)

        # Update "Last Updated" if the data hash has changed
        if LAST_UPDATED["hash"] != current_hash:
            LAST_UPDATED["hash"] = current_hash
            now_central = datetime.now(CENTRAL_TZ).strftime("%Y-%m-%d %I:%M:%S %p")
            LAST_UPDATED["timestamp"] = now_central

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
        st.sidebar.info(f"Last Updated: {last_updated} (Central Time)")

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
        (data['Confidence'].between(*confidence_filter))
    ]

    # Sort data by Confidence in descending order
    sorted_data = filtered_data.sort_values(by="Confidence", ascending=False)

    # Display filtered and sortable data
    st.subheader("Filtered Results")
    st.dataframe(sorted_data, use_container_width=True)

    # Option to download filtered data
    st.download_button(
        label="Download Filtered Data as CSV",
        data=sorted_data.to_csv(index=False),
        file_name="filtered_nba_projections.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    run_streamlit_app()
