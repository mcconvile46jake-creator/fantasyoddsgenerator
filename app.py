import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Fantasy Start/Sit Player Analyzer", layout="wide")

st.title("🏈 Fantasy Football Start/Sit Analyzer")
st.write("Upload the **NFL Stats 1999–2022** Kaggle dataset to begin.")

# ---------------------------
# DATA UPLOAD
# ---------------------------
uploaded = st.sidebar.file_uploader("Upload nfl_stats_1999_2022.csv", type=["csv"])

if uploaded is None:
    st.stop()

@st.cache_data
def load_data(f):
    df = pd.read_csv(f, low_memory=False)
    df.columns = [c.strip() for c in df.columns]   # clean column names
    return df

df = load_data(uploaded)

# ---------------------------
# COLUMN DETECTION
# ---------------------------

# Player column
player_col = next((c for c in df.columns if c.lower() == "player"), None)
season_col = next((c for c in df.columns if c.lower() in ("season","year")), None)

if player_col is None:
    st.error("❌ Could not find a 'Player' column — please confirm dataset format.")
    st.stop()

# ---------------------------
# PLAYER SEARCH
# ---------------------------

st.header("🔍 Search Player Statistics")

player_name = st.text_input("Enter player name (e.g., **Tom Brady**, **Adrian Peterson**, etc.)")

if player_name == "":
    st.stop()

matches = df[df[player_col].str.contains(player_name, case=False, na=False)]

if matches.empty:
    st.warning("No players found with that name. Try a different spelling.")
    st.stop()

# List possible matches
match_names = sorted(matches[player_col].unique())
selected_player = st.selectbox("Select a player", match_names)

player_df = df[df[player_col] == selected_player]

# ---------------------------
# BASIC STATS SUMMARY
# ---------------------------

st.subheader(f"📊 Career Summary: {selected_player}")

numeric_cols = player_df.select_dtypes(include=[np.number]).columns
career_totals = player_df[numeric_cols].sum().sort_index()

st.write("### Career Totals")
st.dataframe(career_totals.to_frame("Total"))

if season_col:
    st.write("### Per-Season Stats")
    season_stats = player_df.groupby(season_col)[numeric_cols].sum()
    st.dataframe(season_stats)

    # Trend plot
    stat_to_plot = st.selectbox("Plot stat over time", numeric_cols)
    fig = px.line(
        season_stats.reset_index(),
        x=season_col,
        y=stat_to_plot,
        markers=True,
        title=f"{selected_player} — {stat_to_plot} by Season"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------
# FANTASY-RELEVANT METRICS
# ---------------------------

# Auto-detect relevant fantasy stats
def get_col(possible):
    return next((c for c in df.columns if c.lower() in possible), None)

yards = get_col(["yards","yds"])
td = get_col(["td","touchdowns","rush_td","rec_td","pass_td"])
receptions = get_col(["rec","receptions"])
rush_attempts = get_col(["att","rush_att"])
targets = get_col(["tgt","targets"])
comp = get_col(["cmp","completions"])
ints = get_col(["int","interceptions"])

st.subheader("⭐ Fantasy-Relevant Stats")

if yards or td:
    fantasy_cols = [c for c in [yards, td, receptions, rush_attempts, targets, comp, ints] if c]
    st.write(player_df[fantasy_cols].describe())

# ---------------------------
# PLAYER COMPARISON
# ---------------------------

st.header("🆚 Compare Two Players for Fantasy Start/Sit")

compare_name = st.text_input("Enter another player name to compare:")

if compare_name:
    matches2 = df[df[player_col].str.contains(compare_name, case=False, na=False)]

    if not matches2.empty:
        match2_names = sorted(matches2[player_col].unique())
        selected_player2 = st.selectbox("Select comparison player", match2_names)

        player2_df = df[df[player_col] == selected_player2]

        st.subheader(f"📈 Comparison: {selected_player} vs {selected_player2}")

        comp_df = pd.DataFrame({
            selected_player: player_df[numeric_cols].mean(),
            selected_player2: player2_df[numeric_cols].mean()
        })

        st.write("### Avg Per-Game / Per-Row Stats (fantasy-useful averages)")
        st.dataframe(comp_df)

        # Plot comparison
        stat_choice = st.selectbox("Choose a stat to compare", numeric_cols)
        fig2 = px.bar(
            x=[selected_player, selected_player2],
            y=[player_df[stat_choice].mean(), player2_df[stat_choice].mean()],
            labels={"x": "Player", "y": stat_choice},
            title=f"{stat_choice}: Per-Game/Row Comparison",
        )
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
st.caption("Upload the official Kaggle dataset: *NFL Stats (1999–2022)*. This tool is designed for quick fantasy football comparisons based on historical stats.")
