"""Family Tree Streamlit App."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.error import URLError

import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_agraph import Config, Edge, Node, agraph

CSV_PATH = Path(__file__).with_name("family_tree.csv")
PROFILES_DIR = Path(__file__).parent / "assets" / "profiles"
PLACEHOLDER_IMG = PROFILES_DIR / "placeholder.png"
DEFAULT_DATA_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "10jJ9WtKPP6onZhnHN6AK5WSgLbKirzD2qODFOPDvgu4/edit?usp=sharing"
)
REQUIRED_COLUMNS = ["Generation", "Branch", "Name", "Birthdate", "Parent"]
BRANCH_COLORS = {
    "Root": "#ff6b6b",
    "Müller": "#4f8ef7",
    "Schmidt": "#43b89c",
}

st.set_page_config(
    page_title="Family Tree",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] {
        background: linear-gradient(160deg, #1a1a2e 0%, #16213e 100%);
        color: #f0f0f0;
    }
    section[data-testid="stSidebar"] * { color: #f0f0f0 !important; }
    .profile-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 4px solid #4f8ef7;
    }
    .badge {
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
    .editor-header {
        background: linear-gradient(90deg, #4f8ef7, #7b5ea7);
        border-radius: 10px;
        padding: 10px 18px;
        color: white;
        font-weight: 600;
        margin-bottom: 12px;
    }
    .main .block-container {
        background: #f5f7fb;
        border-radius: 16px;
        padding-top: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def to_export_csv_url(url: str) -> str:
    if "/edit" in url:
        return url.split("/edit", 1)[0] + "/export?format=csv"
    return url


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for column in REQUIRED_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""

    normalized = normalized[REQUIRED_COLUMNS]
    normalized["Generation"] = (
        pd.to_numeric(normalized["Generation"], errors="coerce").fillna(0).astype(int)
    )
    normalized["Birthdate"] = pd.to_datetime(normalized["Birthdate"], errors="coerce")

    for column in ("Branch", "Name", "Parent"):
        normalized[column] = normalized[column].apply(
            lambda value: "" if pd.isna(value) else str(value).strip()
        )

    normalized = normalized[normalized["Name"] != ""]
    normalized = normalized.sort_values(
        by=["Generation", "Branch", "Birthdate", "Name"],
        na_position="last",
    ).reset_index(drop=True)
    return normalized


def read_remote_data(url: str) -> pd.DataFrame:
    return normalize_dataframe(pd.read_csv(to_export_csv_url(url)))


def bootstrap_local_data() -> None:
    if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
        return
    try:
        df = read_remote_data(DEFAULT_DATA_URL)
    except Exception:
        return
    save_data(df)


@st.cache_data
def load_data() -> pd.DataFrame:
    bootstrap_local_data()
    if CSV_PATH.exists():
        return normalize_dataframe(pd.read_csv(CSV_PATH))
    return read_remote_data(DEFAULT_DATA_URL)


def save_data(df: pd.DataFrame) -> None:
    output = normalize_dataframe(df)
    output["Birthdate"] = output["Birthdate"].apply(
        lambda value: value.strftime("%Y-%m-%d") if pd.notna(value) else ""
    )
    output.to_csv(CSV_PATH, index=False)
    st.cache_data.clear()


def compute_age(birthdate: pd.Timestamp | date | None) -> int | None:
    if pd.isna(birthdate) or birthdate in ("", None):
        return None
    birthday = birthdate.date() if hasattr(birthdate, "date") else birthdate
    today = date.today()
    return today.year - birthday.year - (
        (today.month, today.day) < (birthday.month, birthday.day)
    )


def format_birthdate(birthdate: pd.Timestamp | None) -> str:
    if pd.isna(birthdate):
        return "Unknown"
    return birthdate.strftime("%d %B %Y")


def get_profile_image(name: str):
    for ext in ("jpg", "jpeg", "png"):
        path = PROFILES_DIR / f"{name}.{ext}"
        if path.exists():
            return Image.open(path)
    if PLACEHOLDER_IMG.exists():
        return Image.open(PLACEHOLDER_IMG)
    return None


def get_ancestors(df: pd.DataFrame, names: Iterable[str]) -> set[str]:
    parents = dict(zip(df["Name"], df["Parent"]))
    collected = set(names)
    for name in list(names):
        parent = parents.get(name, "")
        while parent:
            collected.add(parent)
            parent = parents.get(parent, "")
    return collected


def build_graph(df: pd.DataFrame) -> tuple[list[Node], list[Edge], Config]:
    nodes: list[Node] = []
    edges: list[Edge] = []

    for _, row in df.iterrows():
        age = compute_age(row["Birthdate"])
        age_label = f"{age} yrs" if age is not None else "Age unknown"
        branch_color = BRANCH_COLORS.get(row["Branch"], "#7b8794")
        nodes.append(
            Node(
                id=row["Name"],
                label=row["Name"],
                title=f"{row['Name']} • {age_label} • {row['Branch'] or 'No branch'}",
                shape="box",
                size=24,
                color=branch_color,
                level=max(int(row["Generation"]), 1),
                borderWidth=2,
                font={"color": "#ffffff", "face": "Inter", "size": 18},
                margin=14,
            )
        )
        if row["Parent"]:
            edges.append(
                Edge(
                    source=row["Parent"],
                    target=row["Name"],
                    color="#cbd5e1",
                    smooth=False,
                    width=2,
                )
            )

    config = Config(
        width=1100,
        height=560,
        directed=True,
        physics=False,
        hierarchical=True,
        levelSeparation=150,
        nodeSpacing=180,
        treeSpacing=220,
        direction="UD",
        sortMethod="directed",
        fit=True,
        highlightColor="#1d4ed8",
    )
    return nodes, edges, config


def ensure_selected_member(df: pd.DataFrame) -> str | None:
    names = df["Name"].tolist()
    selected = st.session_state.get("selected_member")
    if selected not in names:
        st.session_state["selected_member"] = names[0] if names else None
    return st.session_state.get("selected_member")


def render_profile_card(member: pd.Series | None) -> None:
    st.markdown("### 👤 Profile")
    if member is None:
        st.info("Click a node in the tree to open a family member profile.")
        return

    image = get_profile_image(member["Name"])
    age = compute_age(member["Birthdate"])

    with st.container():
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        if image:
            st.image(image, use_container_width=True)
        st.markdown(f"## {member['Name']}")
        st.markdown(
            "".join(
                [
                    f'<span class="badge">Generation {int(member["Generation"])}</span>',
                    f'<span class="badge">{member["Branch"] or "No branch"}</span>',
                ]
            ),
            unsafe_allow_html=True,
        )
        st.write(f"**Birthdate:** {format_birthdate(member['Birthdate'])}")
        st.write(f"**Current Age:** {age if age is not None else 'Unknown'}")
        st.write(f"**Parent:** {member['Parent'] or '—'}")
        st.markdown("</div>", unsafe_allow_html=True)


def render_sidebar(df: pd.DataFrame) -> None:
    with st.sidebar:
        st.markdown("## 👨‍👩‍👧‍👦 Family Tree")
        st.caption("Click any node in the graph or jump to a member here.")
        names = sorted(df["Name"].tolist())
        selected = st.selectbox(
            "Quick member lookup",
            names,
            index=names.index(ensure_selected_member(df)) if names else None,
        )
        st.session_state["selected_member"] = selected

        st.markdown("---")
        st.markdown("### 📁 Photos")
        st.caption(f"Store portraits in `{PROFILES_DIR.as_posix()}` as `[Name].jpg`.")

        st.markdown("---")
        st.markdown("### 🔄 Data source")
        st.caption("Local edits save to `family_tree.csv`. You can also refresh from the provided Google Sheet in the editor tab.")


def render_tree_tab(df: pd.DataFrame) -> None:
    st.markdown("### 🌳 Interactive Family Tree")
    st.caption("Click a node to open the profile card.")

    branches = ["All"] + sorted(branch for branch in df["Branch"].unique().tolist() if branch)
    col_filter, col_gen = st.columns(2)

    with col_filter:
        branch_filter = st.selectbox("Filter by branch", branches)
    with col_gen:
        generations = sorted(int(gen) for gen in df["Generation"].unique().tolist() if gen)
        generation_filter = st.multiselect(
            "Filter by generation",
            generations,
            default=generations,
        )

    filtered = df.copy()
    if branch_filter != "All":
        names = filtered.loc[filtered["Branch"] == branch_filter, "Name"].tolist()
        filtered = filtered[filtered["Name"].isin(get_ancestors(df, names))]
    if generation_filter:
        filtered = filtered[filtered["Generation"].isin(generation_filter)]

    if filtered.empty:
        st.info("No members match the current filters.")
        return

    tree_col, profile_col = st.columns([2.1, 1], gap="large")
    with tree_col:
        legend_cols = st.columns(max(len(BRANCH_COLORS), 1))
        for index, (branch, color) in enumerate(BRANCH_COLORS.items()):
            legend_cols[index].markdown(
                (
                    f"<div style='background:{color};color:white;border-radius:8px;"
                    "padding:6px 10px;text-align:center;font-weight:600;'>"
                    f"{branch}</div>"
                ),
                unsafe_allow_html=True,
            )

        nodes, edges, config = build_graph(filtered)
        clicked = agraph(nodes=nodes, edges=edges, config=config)
        if clicked:
            st.session_state["selected_member"] = (
                clicked.get("id") if isinstance(clicked, dict) else clicked
            )

    with profile_col:
        selected_name = ensure_selected_member(df)
        selected_member = (
            df.loc[df["Name"] == selected_name].iloc[0]
            if selected_name in df["Name"].values
            else None
        )
        render_profile_card(selected_member)


def render_stats_tab(df: pd.DataFrame) -> None:
    st.markdown("### 📊 Family Statistics")

    ages = [age for age in df["Birthdate"].apply(compute_age).tolist() if age is not None]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total members", len(df))
    col2.metric("🌿 Generations", int(df["Generation"].nunique()))
    col3.metric("🌳 Branches", int(df["Branch"].replace("", pd.NA).nunique()))
    col4.metric("🎈 Average age", f"{(sum(ages) / len(ages)):.1f} yrs" if ages else "—")

    st.markdown("---")
    left, right = st.columns(2)
    with left:
        st.markdown("**Members per generation**")
        st.bar_chart(df.groupby("Generation").size().rename("Count"))
    with right:
        st.markdown("**Members per branch**")
        branch_counts = (
            df.assign(Branch=df["Branch"].replace("", "Unassigned"))
            .groupby("Branch")
            .size()
            .rename("Count")
        )
        st.bar_chart(branch_counts)


def refresh_from_sheet() -> None:
    try:
        remote_df = read_remote_data(DEFAULT_DATA_URL)
    except (URLError, OSError, ValueError, pd.errors.ParserError):
        st.error(
            "Could not refresh from the Google Sheet. Check the URL or network access "
            "and try again."
        )
        return
    save_data(remote_df)
    st.success("Reloaded local data from the provided Google Sheet.")
    st.rerun()


def render_editor_tab(df: pd.DataFrame) -> None:
    st.markdown('<div class="editor-header">✏️ Edit Family Data</div>', unsafe_allow_html=True)
    st.caption("Add new members, fix dates, then save back to the local CSV.")

    action_col, info_col = st.columns([1, 3])
    with action_col:
        if st.button("Reload from Google Sheet"):
            refresh_from_sheet()
    with info_col:
        st.caption(
            "Uses the provided spreadsheet as a reset source, then writes the result to "
            "`family_tree.csv` for local editing."
        )

    editor_df = st.data_editor(
        df,
        column_config={
            "Generation": st.column_config.NumberColumn(
                "Generation", min_value=1, max_value=20, step=1, required=True
            ),
            "Branch": st.column_config.TextColumn("Branch"),
            "Name": st.column_config.TextColumn("Name", required=True),
            "Birthdate": st.column_config.DateColumn("Birthdate", format="YYYY-MM-DD"),
            "Parent": st.column_config.TextColumn("Parent"),
        },
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key="family_editor",
    )

    save_col, reset_col = st.columns([1, 5])
    with save_col:
        if st.button("💾 Save changes", type="primary"):
            save_data(editor_df)
            st.success("Saved updates to family_tree.csv.")
            st.rerun()
    with reset_col:
        if st.button("↩️ Discard changes"):
            st.rerun()


def main() -> None:
    df = load_data()
    ensure_selected_member(df)
    render_sidebar(df)

    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
          <span style="font-size:2.8rem;">🌳</span>
          <div>
            <h1 style="margin:0;font-size:2rem;font-weight:700;color:#1a1a2e;">Family Tree</h1>
            <p style="margin:0;color:#666;font-size:0.9rem;">
              Interactive genealogy explorer with dynamic ages and editable data
            </p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    tab_tree, tab_stats, tab_editor = st.tabs(
        ["🌳 Family Tree", "📊 Statistics", "✏️ Data Editor"]
    )
    with tab_tree:
        render_tree_tab(df)
    with tab_stats:
        render_stats_tab(df)
    with tab_editor:
        render_editor_tab(df)


if __name__ == "__main__":
    main()
