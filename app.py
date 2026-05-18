"""Family Tree Streamlit App — app.py"""

import os
from datetime import date, datetime

import graphviz
import pandas as pd
import streamlit as st
from PIL import Image

# ── Constants ──────────────────────────────────────────────────────────────────
CSV_PATH = "family_tree.csv"
PROFILES_DIR = os.path.join("assets", "profiles")
PLACEHOLDER_IMG = os.path.join(PROFILES_DIR, "placeholder.png")

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Family Tree",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(160deg, #1a1a2e 0%, #16213e 100%);
        color: #f0f0f0;
    }
    section[data-testid="stSidebar"] * { color: #f0f0f0 !important; }
    section[data-testid="stSidebar"] .stSelectbox label { color: #a0c4ff !important; }

    /* Profile card */
    .profile-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 16px;
        border-left: 4px solid #4f8ef7;
    }
    .profile-card h2 {
        margin: 0 0 4px 0;
        font-size: 1.4rem;
        font-weight: 700;
        color: #1a1a2e;
    }
    .profile-card .meta {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 12px;
    }
    .profile-card .badge {
        display: inline-block;
        background: #eef3ff;
        color: #4f8ef7;
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 4px;
    }

    /* Stat tiles */
    .stat-row {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-top: 12px;
    }
    .stat-tile {
        flex: 1;
        min-width: 100px;
        background: #f8faff;
        border-radius: 12px;
        padding: 12px 16px;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    .stat-tile .value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #4f8ef7;
    }
    .stat-tile .label {
        font-size: 0.75rem;
        color: #888;
        margin-top: 2px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 600;
    }

    /* Editor section */
    .editor-header {
        background: linear-gradient(90deg, #4f8ef7, #7b5ea7);
        border-radius: 10px;
        padding: 10px 18px;
        color: white;
        font-weight: 600;
        margin-bottom: 12px;
    }

    /* Main background */
    .main .block-container {
        background: #f5f7fb;
        border-radius: 16px;
        padding-top: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Data helpers ───────────────────────────────────────────────────────────────

@st.cache_data
def load_data() -> pd.DataFrame:
    """Load CSV and parse dates."""
    df = pd.read_csv(CSV_PATH)
    df["Birthdate"] = pd.to_datetime(df["Birthdate"], errors="coerce")
    df["Parent"] = df["Parent"].fillna("")
    return df


def save_data(df: pd.DataFrame) -> None:
    """Persist DataFrame back to CSV."""
    out = df.copy()
    out["Birthdate"] = out["Birthdate"].apply(
        lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) and x != "" else ""
    )
    out.to_csv(CSV_PATH, index=False)
    st.cache_data.clear()


def compute_age(birthdate) -> str:
    """Return a human-readable age string."""
    if pd.isna(birthdate) or birthdate == "":
        return "Unknown"
    today = date.today()
    bd = birthdate.date() if hasattr(birthdate, "date") else birthdate
    age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
    return str(age)


def get_profile_image(name: str):
    """Return a PIL Image for the member, falling back to placeholder."""
    for ext in ("jpg", "jpeg", "png"):
        path = os.path.join(PROFILES_DIR, f"{name}.{ext}")
        if os.path.exists(path):
            return Image.open(path)
    if os.path.exists(PLACEHOLDER_IMG):
        return Image.open(PLACEHOLDER_IMG)
    return None


# ── Tree builder ───────────────────────────────────────────────────────────────

BRANCH_COLORS = {
    "Root": "#ff6b6b",
    "Müller": "#4f8ef7",
    "Schmidt": "#43b89c",
}


def build_tree(df: pd.DataFrame) -> graphviz.Digraph:
    """Build a Graphviz directed graph from the DataFrame."""
    dot = graphviz.Digraph(
        comment="Family Tree",
        graph_attr={
            "rankdir": "TB",
            "bgcolor": "#f5f7fb",
            "splines": "ortho",
            "nodesep": "0.6",
            "ranksep": "0.8",
        },
        node_attr={
            "shape": "box",
            "style": "filled,rounded",
            "fontname": "Inter",
            "fontsize": "11",
            "margin": "0.15,0.08",
        },
        edge_attr={
            "color": "#cccccc",
            "arrowsize": "0.7",
        },
    )

    for _, row in df.iterrows():
        color = BRANCH_COLORS.get(row["Branch"], "#aaaaaa")
        age_str = compute_age(row["Birthdate"])
        label = f'{row["Name"]}\n({age_str} yrs)'
        dot.node(
            str(row["Name"]),
            label=label,
            fillcolor=color,
            fontcolor="white" if row["Branch"] != "" else "#333",
        )

    for _, row in df.iterrows():
        if row["Parent"]:
            dot.edge(str(row["Parent"]), str(row["Name"]))

    return dot


# ── Sidebar: Profile Gallery ───────────────────────────────────────────────────

def render_sidebar(df: pd.DataFrame) -> None:
    with st.sidebar:
        st.markdown("## 👨‍👩‍👧‍👦 Family Tree")
        st.markdown("---")
        st.markdown("### 🔍 Profile Gallery")

        names = sorted(df["Name"].dropna().tolist())
        selected = st.selectbox("Select a family member", names)

        if selected:
            row = df[df["Name"] == selected].iloc[0]
            img = get_profile_image(selected)

            st.markdown("<br>", unsafe_allow_html=True)
            if img:
                st.image(img, use_container_width=True, caption=selected)
            else:
                st.markdown(
                    f'<div style="text-align:center;font-size:4rem;">👤</div>',
                    unsafe_allow_html=True,
                )

            age_str = compute_age(row["Birthdate"])
            bd_str = (
                row["Birthdate"].strftime("%d %B %Y")
                if pd.notna(row["Birthdate"])
                else "Unknown"
            )

            st.markdown(
                f"""
                <div style="margin-top:12px;">
                  <p style="margin:4px 0;"><strong>🎂 Born:</strong> {bd_str}</p>
                  <p style="margin:4px 0;"><strong>🎈 Age:</strong> {age_str} years</p>
                  <p style="margin:4px 0;"><strong>🌿 Branch:</strong> {row['Branch']}</p>
                  <p style="margin:4px 0;"><strong>👶 Generation:</strong> {int(row['Generation'])}</p>
                  <p style="margin:4px 0;"><strong>👤 Parent:</strong> {row['Parent'] or '—'}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown(
            '<p style="font-size:0.72rem;color:#aaa;text-align:center;">'
            "Family Tree App · Built with Streamlit</p>",
            unsafe_allow_html=True,
        )


# ── Tab 1: Interactive Tree ────────────────────────────────────────────────────

def render_tree_tab(df: pd.DataFrame) -> None:
    st.markdown("### 🌳 Interactive Family Tree")

    branches = ["All"] + sorted(df["Branch"].unique().tolist())
    col_filter, col_gen = st.columns([2, 2])
    with col_filter:
        branch_filter = st.selectbox("Filter by Branch", branches)
    with col_gen:
        generations = sorted(df["Generation"].unique().tolist())
        gen_filter = st.multiselect(
            "Filter by Generation",
            generations,
            default=generations,
        )

    filtered = df.copy()
    if branch_filter != "All":
        # Keep selected branch + their ancestors to preserve connectivity
        branch_names = set(df[df["Branch"] == branch_filter]["Name"].tolist())
        # Walk up the parent chain
        all_names = set(branch_names)
        for name in branch_names:
            parent = df[df["Name"] == name]["Parent"].values
            while parent.size > 0 and parent[0]:
                all_names.add(parent[0])
                parent = df[df["Name"] == parent[0]]["Parent"].values
        filtered = filtered[filtered["Name"].isin(all_names)]

    if gen_filter:
        filtered = filtered[filtered["Generation"].isin(gen_filter)]

    if filtered.empty:
        st.info("No members match the current filters.")
        return

    dot = build_tree(filtered)

    # Legend
    legend_html = "<div style='display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;'>"
    for branch, color in BRANCH_COLORS.items():
        legend_html += (
            f"<span style='background:{color};color:white;border-radius:6px;"
            f"padding:3px 10px;font-size:0.8rem;font-weight:600;'>{branch}</span>"
        )
    legend_html += "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)

    st.graphviz_chart(dot, use_container_width=True)


# ── Tab 2: Statistics ──────────────────────────────────────────────────────────

def render_stats_tab(df: pd.DataFrame) -> None:
    st.markdown("### 📊 Family Statistics")

    total = len(df)
    generations = df["Generation"].nunique()
    branches = df["Branch"].nunique()
    avg_age = (
        df["Age"].mean() if "Age" in df.columns else 0
    )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Total Members", total)
    with col2:
        st.metric("🌿 Generations", generations)
    with col3:
        st.metric("🌳 Branches", branches)
    with col4:
        st.metric("🎈 Avg Age", f"{avg_age:.1f} yrs")

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Members per Generation**")
        gen_counts = df.groupby("Generation").size().reset_index(name="Count")
        st.bar_chart(gen_counts.set_index("Generation"))

    with col_b:
        st.markdown("**Members per Branch**")
        branch_counts = df.groupby("Branch").size().reset_index(name="Count")
        st.bar_chart(branch_counts.set_index("Branch"))


# ── Tab 3: Data Editor ─────────────────────────────────────────────────────────

def render_editor_tab(df: pd.DataFrame) -> None:
    st.markdown(
        '<div class="editor-header">✏️ Edit Family Data</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Edit names, birthdates, branches, or parent relationships below. "
        "Click **Save Changes** to write back to the CSV."
    )

    # Configure column types for the data editor
    column_config = {
        "Name": st.column_config.TextColumn("Name", required=True),
        "Birthdate": st.column_config.DateColumn(
            "Birthdate", format="YYYY-MM-DD", help="Date of birth"
        ),
        "Age": st.column_config.NumberColumn("Age", min_value=0, max_value=150),
        "Generation": st.column_config.NumberColumn(
            "Generation", min_value=1, max_value=20, step=1
        ),
        "Branch": st.column_config.TextColumn("Branch"),
        "Parent": st.column_config.TextColumn("Parent"),
    }

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        key="family_editor",
    )

    col_save, col_reset = st.columns([1, 5])
    with col_save:
        if st.button("💾 Save Changes", type="primary"):
            save_data(edited_df)
            st.success("✅ Changes saved to family_tree.csv!")
            st.rerun()
    with col_reset:
        if st.button("↩️ Discard Changes"):
            st.rerun()


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    df = load_data()

    render_sidebar(df)

    # Header
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
          <span style="font-size:2.8rem;">🌳</span>
          <div>
            <h1 style="margin:0;font-size:2rem;font-weight:700;color:#1a1a2e;">Family Tree</h1>
            <p style="margin:0;color:#666;font-size:0.9rem;">Interactive genealogy explorer</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    tab_tree, tab_stats, tab_editor = st.tabs(
        ["🌳 Family Tree", "📊 Statistics", "✏️ Edit Data"]
    )

    with tab_tree:
        render_tree_tab(df)

    with tab_stats:
        render_stats_tab(df)

    with tab_editor:
        render_editor_tab(df)


if __name__ == "__main__":
    main()
