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

# Load the projections CSV file and manage "Last Updated" timestamp
@st.cache_data(ttl=60)
def load_projections_data():
    global LAST_UPDATED

    try:
        data = pd.read_csv("nba_player_best_ev_projections.csv")
        
        # Ensure Confidence is numeric
        if 'Confidence' in data.columns:
            data['Confidence'] = (
                data['Confidence']
                .str.rstrip('%')  # Remove % if present
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
        st.error("Projections CSV file not found. Please run the data generation script first.")
        return pd.DataFrame(), None

# Load the results CSV file
def load_results_data():
    try:
        results_data = pd.read_csv("nba_projection_results.csv")
        return results_data
    except FileNotFoundError:
        st.error("Results CSV file not found. Please ensure it has been generated.")
        return pd.DataFrame()

# Calculate Win/Loss Summary
def calculate_win_loss_summary(results_data):
    if results_data.empty:
        return None

    win_count = (results_data['Result'] == 'Win').sum()
    loss_count = (results_data['Result'] == 'Loss').sum()
    push_count = (results_data['Result'] == 'Push').sum()
    total = win_count + loss_count + push_count

    win_percentage = (win_count / total) * 100 if total > 0 else 0

    return {
        "Wins": win_count,
        "Losses": loss_count,
        "Pushes": push_count,
        "Win Percentage": win_percentage
    }

# Streamlit UI
def run_streamlit_app():
    st.title("NBA Player Best EV Projections")

    # Load data
    projections_data, last_updated = load_projections_data()
    results_data = load_results_data()

    if projections_data.empty and results_data.empty:
        st.warning("No data to display. Ensure the necessary CSV files are generated.")
        return

    # Display last updated time
    if last_updated:
        st.sidebar.info(f"Last Updated: {last_updated} (Central Time)")

    # Sidebar for filters
    st.sidebar.header("Filters")
    player_filter = st.sidebar.text_input("Search by Player Name:", placeholder="Type player name...")
    metric_filter = st.sidebar.multiselect(
        "Filter by Metric:",
        options=projections_data['Metric'].unique() if not projections_data.empty else [],
        default=projections_data['Metric'].unique() if not projections_data.empty else []
    )
    sportsbook_filter = st.sidebar.multiselect(
        "Filter by Sportsbook:",
        options=projections_data['Bookmaker'].unique() if not projections_data.empty else [],
        default=projections_data['Bookmaker'].unique() if not projections_data.empty else []
    )
    confidence_filter = st.sidebar.slider(
        "Filter by Confidence (%)",
        min_value=0,
        max_value=100,
        value=(0, 100)
    )

    # Apply filters
    filtered_projections = projections_data[
        (projections_data['Player Name'].str.contains(player_filter, case=False, na=False)) &
        (projections_data['Metric'].isin(metric_filter)) &
        (projections_data['Bookmaker'].isin(sportsbook_filter)) &
        (projections_data['Confidence'].between(*confidence_filter))
    ]

    # Sort data by Confidence in descending order
    sorted_projections = filtered_projections.sort_values(by="Confidence", ascending=False)

    # Display filtered and sortable data
    st.subheader("Filtered Results")
    st.dataframe(sorted_projections, use_container_width=True)

    # Option to download filtered data
    st.download_button(
        label="Download Filtered Data as CSV",
        data=sorted_projections.to_csv(index=False),
        file_name="filtered_nba_projections.csv",
        mime="text/csv"
    )

    # Highlight Top Prop Bets for Today
    st.subheader("Top Prop Bets for Today")
    top_bets = sorted_projections.head(10)  # Get top 10 rows from sorted data
    st.dataframe(top_bets, use_container_width=True)  # Display all columns in a table

    # Display Win/Loss Summary
    if not results_data.empty:
        st.subheader("Win/Loss Record")
        summary = calculate_win_loss_summary(results_data)
        if summary:
            st.write(f"**Wins:** {summary['Wins']} | **Losses:** {summary['Losses']} | **Pushes:** {summary['Pushes']}")
            st.write(f"**Overall Win Percentage:** {summary['Win Percentage']:.2f}%")

        # Display results data
        st.subheader("Results Data")
        st.dataframe(results_data, use_container_width=True)

if __name__ == "__main__":
    run_streamlit_app()
