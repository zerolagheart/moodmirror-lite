import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="MoodMirror Lite",
    page_icon="🪞",
    layout="wide"
)

# ==========================================
# FILE PATHS
# ==========================================
DATA_FILE = "data/mood_data.csv"
CSS_FILE = "styles.css"

# ==========================================
# APP CONSTANTS
# ==========================================
MOOD_OPTIONS = {
    "Happy": "😊",
    "Calm": "😌",
    "Excited": "🤩",
    "Neutral": "😐",
    "Tired": "😴",
    "Stressed": "😵‍💫",
    "Anxious": "😟",
    "Sad": "🥺"
}

MOOD_SCORE_MAP = {
    "Sad": 1,
    "Anxious": 2,
    "Stressed": 3,
    "Tired": 4,
    "Neutral": 5,
    "Calm": 6,
    "Happy": 8,
    "Excited": 9
}

CHART_COLORS = [
    "#FF4D9D", "#52E5FF", "#A970FF", "#7CFC00",
    "#F6C945", "#FF8C42", "#6C63FF", "#FF6B81"
]

# ==========================================
# SETUP FUNCTIONS
# ==========================================
def ensure_data_file():
    if not os.path.exists("data"):
        os.makedirs("data")

    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["date", "mood", "energy", "note"])
        df.to_csv(DATA_FILE, index=False)


def load_css():
    if os.path.exists(CSS_FILE):
        with open(CSS_FILE, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        if df.empty:
            return pd.DataFrame(columns=["date", "mood", "energy", "note"])
        return df
    except Exception:
        return pd.DataFrame(columns=["date", "mood", "energy", "note"])


def save_entry(entry_date, mood, energy, note):
    df = load_data()
    new_row = pd.DataFrame([{
        "date": str(entry_date),
        "mood": mood,
        "energy": energy,
        "note": note.strip() if note.strip() else "No note added."
    }])

    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)


def delete_entry_by_position(position_to_delete):
    df = load_data()
    if df.empty:
        return False

    if 0 <= position_to_delete < len(df):
        df = df.drop(index=position_to_delete).reset_index(drop=True)
        df.to_csv(DATA_FILE, index=False)
        return True
    return False


# ==========================================
# DATA / ANALYTICS HELPERS
# ==========================================
def get_latest_entry(df):
    if df.empty:
        return None
    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["date"])
    temp = temp.sort_values("date", ascending=False)
    return temp.iloc[0]


def get_total_entries(df):
    return len(df)


def get_average_energy(df):
    if df.empty:
        return 0
    return round(pd.to_numeric(df["energy"], errors="coerce").mean(), 1)


def get_most_common_mood(df):
    if df.empty:
        return "No data"
    return df["mood"].mode()[0]


def get_mood_counts(df):
    if df.empty:
        return pd.DataFrame(columns=["Mood", "Count"])
    mood_counts = df["mood"].value_counts().reset_index()
    mood_counts.columns = ["Mood", "Count"]
    return mood_counts


def get_mood_score(mood):
    return MOOD_SCORE_MAP.get(mood, 5)


def add_mood_score_column(df):
    if df.empty:
        return df
    temp = df.copy()
    temp["mood_score"] = temp["mood"].apply(get_mood_score)
    return temp


def get_longest_logging_streak(df):
    if df.empty:
        return 0

    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["date"]).dt.date
    unique_dates = sorted(temp["date"].unique(), reverse=True)

    if not unique_dates:
        return 0

    streak = 1
    for i in range(len(unique_dates) - 1):
        if unique_dates[i] - unique_dates[i + 1] == timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def get_best_energy_day(df):
    if df.empty:
        return None

    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["date"])
    temp["energy"] = pd.to_numeric(temp["energy"], errors="coerce")

    grouped = temp.groupby(temp["date"].dt.date)["energy"].mean().reset_index()
    grouped = grouped.sort_values("energy", ascending=False)

    if grouped.empty:
        return None

    return grouped.iloc[0]


def get_weekly_summary(df):
    if df.empty:
        return None

    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["date"])

    latest_date = temp["date"].max()
    week_start = latest_date - timedelta(days=6)

    weekly_df = temp[temp["date"] >= week_start]

    if weekly_df.empty:
        return None

    summary = {
        "entries": len(weekly_df),
        "avg_energy": round(pd.to_numeric(weekly_df["energy"], errors="coerce").mean(), 1),
        "top_mood": weekly_df["mood"].mode()[0] if not weekly_df["mood"].mode().empty else "No data",
        "start_date": week_start.date(),
        "end_date": latest_date.date()
    }
    return summary


# ==========================================
# CHARTS
# ==========================================
def create_mood_frequency_chart(df):
    mood_counts = get_mood_counts(df)

    fig = px.bar(
        mood_counts,
        x="Mood",
        y="Count",
        text="Count",
        color="Mood",
        color_discrete_sequence=CHART_COLORS
    )

    fig.update_traces(
        textposition="outside",
        marker_line_color="rgba(255,255,255,0.15)",
        marker_line_width=1.2
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        font=dict(color="#F5F7FB"),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(title="Mood", showgrid=False),
        yaxis=dict(title="Count", gridcolor="rgba(255,255,255,0.08)", zeroline=False),
        showlegend=False
    )
    return fig


def create_mood_donut_chart(df):
    mood_counts = get_mood_counts(df)
    if mood_counts.empty:
        return None

    fig = px.pie(
        mood_counts,
        names="Mood",
        values="Count",
        hole=0.6,
        color="Mood",
        color_discrete_sequence=CHART_COLORS
    )

    fig.update_traces(
        textinfo="percent+label",
        marker=dict(line=dict(color="rgba(255,255,255,0.12)", width=1))
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F5F7FB"),
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False
    )
    return fig


def create_energy_trend_chart(df):
    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["date"])
    temp = temp.sort_values("date")

    fig = px.line(
        temp,
        x="date",
        y="energy",
        markers=True
    )

    fig.update_traces(
        line=dict(color="#52E5FF", width=4),
        marker=dict(size=9, color="#FF4D9D", line=dict(color="white", width=1))
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        font=dict(color="#F5F7FB"),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(title="Date", gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(title="Energy", range=[0, 10], gridcolor="rgba(255,255,255,0.08)", zeroline=False)
    )
    return fig


def create_mood_score_trend_chart(df):
    temp = add_mood_score_column(df)
    temp["date"] = pd.to_datetime(temp["date"])
    temp = temp.sort_values("date")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=temp["date"],
        y=temp["mood_score"],
        mode="lines+markers",
        line=dict(color="#7CFC00", width=4),
        marker=dict(size=9, color="#A970FF", line=dict(color="white", width=1)),
        name="Mood Score"
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.02)",
        font=dict(color="#F5F7FB"),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(title="Date", gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(title="Mood Score", range=[0, 10], gridcolor="rgba(255,255,255,0.08)", zeroline=False)
    )
    return fig


# ==========================================
# UI HELPERS
# ==========================================
def render_sidebar():
    st.sidebar.markdown('<div class="sidebar-brand">🪞 MoodMirror Lite</div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="sidebar-sub">Neon Glass Edition — track your mood, energy and reflections.</div>',
        unsafe_allow_html=True
    )

    page = st.sidebar.radio(
        "Navigate",
        ["Dashboard", "Log Mood", "Mood Journal", "Insights"]
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("Built with Streamlit, Plotly and custom CSS.")
    st.sidebar.markdown(
        "<p style='color:#AAB3C5; font-size:0.9rem; margin-top:0.2rem;'>Built by <strong style='color:#F5F7FB;'>Titiksha</strong> ✨</p>",
        unsafe_allow_html=True
    )
    return page


def render_dashboard(df):
    st.markdown("""
        <div class="glass-card-hero">
            <div class="hero-title">MoodMirror Lite</div>
            <div class="hero-sub">
                A dark, dreamy mood journaling dashboard for tracking how you feel, how much energy you have,
                and what your emotional patterns look like over time.
            </div>
        </div>
    """, unsafe_allow_html=True)

    total_entries = get_total_entries(df)
    avg_energy = get_average_energy(df)
    common_mood = get_most_common_mood(df)
    streak = get_longest_logging_streak(df)

    latest_entry = get_latest_entry(df)
    latest_mood = "No data yet"
    latest_note = "Start by logging your first mood reflection."
    latest_date = "—"

    if latest_entry is not None:
        latest_mood = f"{MOOD_OPTIONS.get(latest_entry['mood'], '✨')} {latest_entry['mood']}"
        latest_note = latest_entry["note"]
        latest_date = latest_entry["date"].strftime("%d %b %Y")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Total reflections</div>
                <div class="stat-value">{total_entries}</div>
                <div class="stat-caption">Every saved mood entry lives here.</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Average energy</div>
                <div class="stat-value">{avg_energy}/10</div>
                <div class="stat-caption">Your average energy level across all entries.</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Most common mood</div>
                <div class="stat-value">{common_mood}</div>
                <div class="stat-caption">The mood showing up most often lately.</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">Current streak</div>
                <div class="stat-value">{streak} day(s)</div>
                <div class="stat-caption">Consecutive days with at least one check-in.</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="spacer-24"></div>', unsafe_allow_html=True)

    left, right = st.columns([1.15, 0.85])

    with left:
        st.markdown('<div class="section-title">Your latest reflection</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="glass-card">
                <p class="muted" style="margin-top:0;">Latest note</p>
                <p style="font-size:1.05rem; line-height:1.8; margin-bottom:0.6rem;">{latest_note}</p>
                <p class="muted" style="margin-bottom:0;">Mood: {latest_mood} • {latest_date}</p>
            </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-title">Weekly summary</div>', unsafe_allow_html=True)
        weekly = get_weekly_summary(df)

        if weekly is None:
            st.markdown("""
                <div class="glass-card">
                    <p class="muted" style="margin-top:0;">No weekly summary yet.</p>
                    <p>Add a few entries to unlock your weekly snapshot.</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            top_mood_emoji = MOOD_OPTIONS.get(weekly["top_mood"], "✨")
            st.markdown(f"""
                <div class="glass-card">
                    <p class="muted" style="margin-top:0;">Last 7-day snapshot</p>
                    <p style="font-size:1rem; margin-bottom:0.5rem;"><strong>Total entries:</strong> {weekly["entries"]}</p>
                    <p style="font-size:1rem; margin-bottom:0.5rem;"><strong>Average energy:</strong> {weekly["avg_energy"]}/10</p>
                    <p style="font-size:1rem; margin-bottom:0.5rem;"><strong>Most frequent mood:</strong> {top_mood_emoji} {weekly["top_mood"]}</p>
                    <p class="muted" style="margin-bottom:0;">{weekly["start_date"]} → {weekly["end_date"]}</p>
                </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="spacer-24"></div>', unsafe_allow_html=True)

    bottom_left, bottom_right = st.columns(2)

    with bottom_left:
        st.markdown('<div class="section-title">Mood frequency snapshot</div>', unsafe_allow_html=True)
        if df.empty:
            st.info("No entries yet.")
        else:
            st.plotly_chart(create_mood_frequency_chart(df), use_container_width=True)

    with bottom_right:
        st.markdown('<div class="section-title">Best energy day</div>', unsafe_allow_html=True)
        best_day = get_best_energy_day(df)
        if best_day is None:
            st.info("No entries yet.")
        else:
            st.markdown(f"""
                <div class="glass-card">
                    <p class="muted" style="margin-top:0;">Your highest average-energy day</p>
                    <p style="font-size:1.3rem; font-weight:700; margin-bottom:0.5rem;">{pd.to_datetime(best_day['date']).strftime('%d %b %Y')}</p>
                    <p style="font-size:1rem; margin-bottom:0;">Average energy: <strong>{round(best_day['energy'], 1)}/10</strong></p>
                </div>
            """, unsafe_allow_html=True)


def render_log_mood():
    st.markdown('<div class="hero-title" style="font-size:2.2rem;">Log your mood</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Capture how you feel today, how much energy you have, and a quick reflection about your day.</div>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    with st.form("mood_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            selected_date = st.date_input("Date", datetime.today())
            mood = st.selectbox(
                "How are you feeling today?",
                list(MOOD_OPTIONS.keys()),
                format_func=lambda x: f"{MOOD_OPTIONS[x]} {x}"
            )

        with col2:
            energy = st.slider(
                "Energy level",
                min_value=1,
                max_value=10,
                value=5,
                help="1 = drained, 10 = unstoppable"
            )

        note = st.text_area(
            "Write a short reflection",
            placeholder="What happened today? What affected your mood? What are you feeling right now?"
        )

        submit = st.form_submit_button("Save reflection")

        if submit:
            save_entry(selected_date, mood, energy, note)
            st.success("Reflection saved. Your mood has been added to MoodMirror ✨")

    st.markdown('</div>', unsafe_allow_html=True)


def render_journal(df):
    st.markdown('<div class="hero-title" style="font-size:2.2rem;">Mood journal</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Filter, browse and clean up your past reflections.</div>',
        unsafe_allow_html=True
    )

    if df.empty:
        st.warning("No entries yet. Add your first mood reflection from the **Log Mood** page.")
        return

    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["date"])
    temp["energy"] = pd.to_numeric(temp["energy"], errors="coerce")
    temp["original_index"] = temp.index

    st.markdown('<div class="section-title">Filter entries</div>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        selected_mood = st.selectbox("Mood filter", ["All"] + list(MOOD_OPTIONS.keys()), index=0)

    with f2:
        min_energy = st.slider("Minimum energy", 1, 10, 1)

    with f3:
        min_date = temp["date"].min().date()
        selected_start = st.date_input("Start date", value=min_date)

    with f4:
        max_date = temp["date"].max().date()
        selected_end = st.date_input("End date", value=max_date)

    filtered = temp.copy()

    if selected_mood != "All":
        filtered = filtered[filtered["mood"] == selected_mood]

    filtered = filtered[filtered["energy"] >= min_energy]
    filtered = filtered[
        (filtered["date"].dt.date >= selected_start) &
        (filtered["date"].dt.date <= selected_end)
    ]

    filtered = filtered.sort_values("date", ascending=False)

    st.markdown('<div class="spacer-16"></div>', unsafe_allow_html=True)

    if filtered.empty:
        st.info("No entries match the selected filters.")
        return

    st.markdown('<div class="section-title">Journal entries</div>', unsafe_allow_html=True)

    for _, row in filtered.iterrows():
        mood_label = row["mood"]
        mood_emoji = MOOD_OPTIONS.get(mood_label, "✨")
        entry_date = row["date"].strftime("%d %b %Y")
        energy = row["energy"]
        note = row["note"]
        original_index = int(row["original_index"])

        with st.container():
            c1, c2 = st.columns([6, 1])

            with c1:
                st.markdown(f"""
                    <div class="glass-card" style="margin-bottom: 1rem;">
                        <p style="margin:0 0 0.4rem 0; font-size:1.05rem;">
                            <strong>{mood_emoji} {mood_label}</strong> • {entry_date} • Energy {energy}/10
                        </p>
                        <p style="margin:0; line-height:1.8;">{note}</p>
                    </div>
                """, unsafe_allow_html=True)

            with c2:
                if st.button("🗑 Delete", key=f"delete_{original_index}"):
                    success = delete_entry_by_position(original_index)
                    if success:
                        st.success("Entry deleted successfully.")
                        st.rerun()
                    else:
                        st.error("Could not delete the entry.")


def render_insights(df):
    st.markdown('<div class="hero-title" style="font-size:2.2rem;">Insights</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-sub">Visualize your mood patterns, track your energy shifts and spot emotional trends over time.</div>',
        unsafe_allow_html=True
    )

    if df.empty:
        st.warning("No entries yet. Add a few reflections first to see analytics.")
        return

    # top metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Entries", get_total_entries(df))
    col2.metric("Average Energy", f"{get_average_energy(df)}/10")
    col3.metric("Most Common Mood", get_most_common_mood(df))

    st.markdown('<div class="spacer-24"></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="section-title">Mood frequency</div>', unsafe_allow_html=True)
        st.plotly_chart(create_mood_frequency_chart(df), use_container_width=True)

    with c2:
        st.markdown('<div class="section-title">Mood distribution</div>', unsafe_allow_html=True)
        donut = create_mood_donut_chart(df)
        if donut:
            st.plotly_chart(donut, use_container_width=True)

    st.markdown('<div class="spacer-16"></div>', unsafe_allow_html=True)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div class="section-title">Energy trend</div>', unsafe_allow_html=True)
        st.plotly_chart(create_energy_trend_chart(df), use_container_width=True)

    with c4:
        st.markdown('<div class="section-title">Mood score trend</div>', unsafe_allow_html=True)
        st.plotly_chart(create_mood_score_trend_chart(df), use_container_width=True)

    weekly = get_weekly_summary(df)
    if weekly:
        st.markdown('<div class="spacer-16"></div>', unsafe_allow_html=True)
        top_mood_emoji = MOOD_OPTIONS.get(weekly["top_mood"], "✨")
        st.markdown(f"""
            <div class="glass-card">
                <p class="muted" style="margin-top:0;">Weekly insight</p>
                <p style="margin-bottom:0.5rem;">You logged <strong>{weekly["entries"]}</strong> entries in your latest 7-day window.</p>
                <p style="margin-bottom:0.5rem;">Your average energy was <strong>{weekly["avg_energy"]}/10</strong>.</p>
                <p style="margin-bottom:0;">Your most common mood was <strong>{top_mood_emoji} {weekly["top_mood"]}</strong>.</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="spacer-16"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Export your mood data</div>', unsafe_allow_html=True)

    export_df = df.copy()
    st.download_button(
        label="Download mood_data.csv",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name="moodmirror_export.csv",
        mime="text/csv"
    )

    st.markdown(
        '<div class="footer-note">Mood score is a simple internal scale used to visualize emotional trend over time — not a clinical measure.</div>',
        unsafe_allow_html=True
    )


# ==========================================
# MAIN APP
# ==========================================
ensure_data_file()
load_css()
df = load_data()

page = render_sidebar()

if page == "Dashboard":
    render_dashboard(df)
elif page == "Log Mood":
    render_log_mood()
elif page == "Mood Journal":
    render_journal(df)
elif page == "Insights":
    render_insights(df)