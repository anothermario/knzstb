"""Family Tree Streamlit App."""

from __future__ import annotations

import base64
import html
import inspect
import os
import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.error import URLError

import pandas as pd
import streamlit as st
from streamlit_agraph import Config, Edge, Node, agraph

try:
    from streamlit.errors import StreamlitAPIException
except Exception:  # pragma: no cover - compatibility fallback for older Streamlit versions.
    class StreamlitAPIException(Exception):
        """Fallback Streamlit exception type for runtimes lacking streamlit.errors."""

        pass

CSV_PATH = Path(__file__).with_name("family_data.csv")
LEGACY_CSV_PATH = Path(__file__).with_name("family_tree.csv")
PROFILES_DIR = Path(__file__).parent / "assets" / "profiles"
DEFAULT_DATA_URL = os.getenv("FAMILY_TREE_DATA_URL", "").strip()
APP_TITLE = os.getenv("FAMILY_TREE_TITLE", "Family Tree").strip() or "Family Tree"
REQUIRED_COLUMNS = ["Generation", "Branch", "Birthdate", "Name", "Parent"]
BRANCH_PALETTE = [
    "#0f766e",
    "#2563eb",
    "#7c3aed",
    "#ea580c",
    "#db2777",
    "#0891b2",
    "#65a30d",
]
AVATAR_PALETTE = ["#1d4ed8", "#7c3aed", "#be123c", "#0891b2", "#15803d", "#b45309"]
ROOT_MEMBER_NAME = "Hans Künz"
NULL_LIKE_TEXT_VALUES = {"", "none", "nan", "nat", "null"}
EDITOR_FOOTER_MARKER = "Aktuelles Datum"

st.set_page_config(
    page_title="Family Tree",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background: #f3f4f6;
        color: #000000;
    }
    .stApp {
        background: linear-gradient(180deg, #f9fafb 0%, #eef2f7 100%);
        color: #000000;
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    section[data-testid="stSidebar"] {
        background: #f0f2f6 !important;
        border-right: 1px solid #d1d5db;
    }
    section[data-testid="stSidebar"] * {
        color: #000000 !important;
    }
    [data-testid="stSidebarNav"] {
        background: #f0f2f6 !important;
    }
    .hero-card,
    .tree-panel,
    .profile-card,
    .legend-chip {
        background: #ffffff;
        border: 1px solid #d1d5db;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }
    .hero-card {
        border-radius: 22px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1rem;
    }
    .tree-panel {
        border-radius: 22px;
        padding: 1.25rem;
        margin-bottom: 1.25rem;
    }
    .profile-card {
        border-radius: 24px;
        padding: 1.75rem;
        text-align: center;
    }
    .profile-avatar {
        width: 180px;
        height: 180px;
        object-fit: cover;
        border-radius: 50%;
        border: 3px solid #d1d5db;
        display: block;
        margin: 0 auto 1rem auto;
        background: #e5e7eb;
    }
    .profile-name {
        margin: 0;
        color: #000000;
        font-size: 1.9rem;
        font-weight: 800;
    }
    .profile-subtitle {
        color: #4b5563;
        margin: 0.35rem 0 1.2rem 0;
        font-size: 1rem;
    }
    .profile-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.8rem;
        text-align: left;
    }
    .profile-detail {
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        background: #f9fafb;
        padding: 0.9rem 1rem;
    }
    .profile-detail-label {
        display: block;
        font-size: 0.8rem;
        font-weight: 700;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 0.2rem;
    }
    .profile-detail-value {
        color: #000000;
        font-size: 1rem;
        font-weight: 700;
    }
    .legend-chip {
        border-radius: 999px;
        padding: 0.55rem 0.9rem;
        text-align: center;
        font-weight: 700;
        color: #000000;
    }
    .legend-swatch {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 0.5rem;
        border: 1px solid rgba(17, 24, 39, 0.2);
    }
    .stMetric {
        background: #ffffff;
        border: 1px solid #d1d5db;
        border-radius: 18px;
        padding: 0.4rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: #ffffff;
        border-radius: 999px;
        color: #000000;
        border: 1px solid #d1d5db;
        padding: 0.4rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        background: #dbeafe !important;
        color: #000000 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def to_export_csv_url(url: str) -> str:
    if "/edit" in url:
        return url.split("/edit", 1)[0] + "/export?format=csv"
    return url


def normalize_generation(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if text.isdigit():
        return f"G{int(text)}"
    match = re.search(r"(\d+)", text)
    if match:
        return f"G{int(match.group(1))}"
    return text


def generation_sort_key(value: Any) -> int:
    """Return numeric generation, defaulting to 0 when no digits are present."""
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else 0


def hierarchy_sort_key(name: str, parents: dict[str, str]) -> tuple[int, str]:
    level = 1
    seen = {name}
    parent = parents.get(name, "")
    while parent and parent not in seen:
        seen.add(parent)
        level += 1
        parent = parents.get(parent, "")
    return level, name


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized = normalized.rename(columns={"Partent": "Parent"})
    if "Birthdate" not in normalized.columns and "Geburtsdatum" in normalized.columns:
        normalized = normalized.rename(columns={"Geburtsdatum": "Birthdate"})
    elif "Birthdate" in normalized.columns and "Geburtsdatum" in normalized.columns:
        birthdate_empty = normalized["Birthdate"].isna() | (
            normalized["Birthdate"].astype(str).str.strip() == ""
        )
        normalized.loc[birthdate_empty, "Birthdate"] = normalized.loc[
            birthdate_empty, "Geburtsdatum"
        ]

    for column in REQUIRED_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""

    normalized = normalized[REQUIRED_COLUMNS]
    normalized["Generation"] = normalized["Generation"].apply(normalize_generation)
    normalized["Birthdate"] = pd.to_datetime(normalized["Birthdate"], errors="coerce")

    for column in ("Branch", "Name", "Parent"):
        normalized[column] = normalized[column].apply(
            lambda value: "" if pd.isna(value) else str(value).strip()
        )
    normalized["Parent"] = normalized["Parent"].apply(
        lambda value: ""
        if str(value).strip().lower() in NULL_LIKE_TEXT_VALUES
        else str(value).strip()
    )

    if ROOT_MEMBER_NAME in normalized["Name"].values:
        normalized.loc[normalized["Name"] == ROOT_MEMBER_NAME, "Parent"] = ""
        g2_mask = (normalized["Generation"] == "G2") & (
            normalized["Name"] != ROOT_MEMBER_NAME
        )
        normalized.loc[g2_mask, "Parent"] = ROOT_MEMBER_NAME

    normalized = normalized[normalized["Name"] != ""].drop_duplicates("Name", keep="last")
    parents = dict(zip(normalized["Name"], normalized["Parent"]))
    normalized = normalized.assign(
        _generation_sort=normalized["Generation"].apply(generation_sort_key),
        _hierarchy_sort=normalized["Name"].apply(lambda name: hierarchy_sort_key(name, parents)),
    )
    normalized = normalized.sort_values(
        by=["_generation_sort", "_hierarchy_sort", "Branch", "Birthdate", "Name"],
        na_position="last",
    ).drop(columns=["_generation_sort", "_hierarchy_sort"])
    return normalized.reset_index(drop=True)


def read_remote_data(url: str) -> pd.DataFrame:
    return normalize_dataframe(pd.read_csv(to_export_csv_url(url)))


def bootstrap_local_data() -> None:
    if CSV_PATH.exists() and CSV_PATH.stat().st_size > 0:
        return
    if LEGACY_CSV_PATH.exists() and LEGACY_CSV_PATH.stat().st_size > 0:
        save_data(pd.read_csv(LEGACY_CSV_PATH))
        return
    if not DEFAULT_DATA_URL:
        return
    try:
        df = read_remote_data(DEFAULT_DATA_URL)
    except (URLError, OSError, ValueError, pd.errors.ParserError):
        return
    save_data(df)


@st.cache_data
def load_data() -> pd.DataFrame:
    bootstrap_local_data()
    if CSV_PATH.exists():
        return normalize_dataframe(pd.read_csv(CSV_PATH))
    if not DEFAULT_DATA_URL:
        return normalize_dataframe(pd.DataFrame(columns=REQUIRED_COLUMNS))
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


def average_age(birthdate_series: pd.Series) -> float | None:
    ages = [
        age for age in birthdate_series.apply(compute_age).tolist() if age is not None
    ]
    if not ages:
        return None
    return sum(ages) / len(ages)


def build_initials(name: str) -> str:
    parts = [part for part in re.split(r"[\s-]+", name.strip()) if part]
    initials = "".join(part[0].upper() for part in parts[:2])
    return initials or "?"


def image_file_to_data_uri(path: Path) -> str:
    media_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }.get(path.suffix.lower(), "application/octet-stream")
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{media_type};base64,{encoded}"


def fallback_avatar_data_uri(name: str) -> str:
    initials = html.escape(build_initials(name))
    color = AVATAR_PALETTE[sum(ord(char) for char in name) % len(AVATAR_PALETTE)]
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" width="280" height="280" viewBox="0 0 280 280">
      <circle cx="140" cy="140" r="134" fill="{color}" stroke="#000000" stroke-width="4" />
      <text x="50%" y="53%" dominant-baseline="middle" text-anchor="middle"
            font-family="Inter, Arial, sans-serif" font-size="92" font-weight="800" fill="#ffffff">
        {initials}
      </text>
    </svg>
    """
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def profile_image_data_uri(name: str) -> str:
    for ext in ("jpg", "jpeg", "png"):
        path = PROFILES_DIR / f"{name}.{ext}"
        if path.exists():
            return image_file_to_data_uri(path)
    return fallback_avatar_data_uri(name)


def birth_year_label(birthdate: pd.Timestamp | None) -> str:
    if pd.isna(birthdate):
        return "?"
    return str(birthdate.year)


def get_ancestors(df: pd.DataFrame, names: Iterable[str]) -> set[str]:
    parents = dict(zip(df["Name"], df["Parent"]))
    collected = set(names)
    for name in list(names):
        seen = {name}
        parent = parents.get(name, "")
        while parent and parent not in seen:
            seen.add(parent)
            collected.add(parent)
            parent = parents.get(parent, "")
    return collected


def build_hierarchy_levels(df: pd.DataFrame) -> dict[str, int]:
    parents = dict(zip(df["Name"], df["Parent"]))
    known_names = set(parents)
    levels: dict[str, int] = {}

    def resolve(name: str, trail: set[str]) -> int:
        if name in levels:
            return levels[name]
        parent = parents.get(name, "")
        if not parent or parent == name or parent in trail or parent not in known_names:
            levels[name] = 1
            return 1
        levels[name] = resolve(parent, trail | {name}) + 1
        return levels[name]

    for member_name in df["Name"]:
        resolve(member_name, set())
    return levels


def build_branch_colors(branches: Iterable[str]) -> dict[str, str]:
    cleaned = sorted(
        {
            str(branch).strip()
            for branch in branches
            if pd.notna(branch) and str(branch).strip()
        }
    )
    colors = {
        branch: BRANCH_PALETTE[index % len(BRANCH_PALETTE)]
        for index, branch in enumerate(cleaned)
    }
    colors["Unassigned"] = "#475569"
    return colors


def safe_text(value: Any, default: str = "") -> str:
    if pd.isna(value):
        return default
    text = str(value).strip()
    return text if text else default


def supports_kwarg(function: Any, kwarg_name: str) -> bool:
    try:
        return kwarg_name in inspect.signature(function).parameters
    except (TypeError, ValueError):
        return False


def build_graph(df: pd.DataFrame) -> tuple[list[Node], list[Edge], Config, dict[str, str]]:
    nodes: list[Node] = []
    edges: list[Edge] = []
    levels = build_hierarchy_levels(df)
    branch_colors = build_branch_colors(df["Branch"].tolist())

    for _, row in df.iterrows():
        branch = safe_text(row["Branch"], "Unassigned")
        member_name = safe_text(row["Name"])
        parent_name = safe_text(row["Parent"])
        label = (
            f"<b>{html.escape(member_name)} ({birth_year_label(row['Birthdate'])})</b>"
        )
        nodes.append(
            Node(
                id=member_name,
                label=label,
                title=(
                    f"{member_name} • {format_birthdate(row['Birthdate'])} • "
                    f"{branch}"
                ),
                shape="circularImage",
                image=profile_image_data_uri(member_name),
                size=40,
                level=levels.get(member_name, 1),
                borderWidth=3,
                color={
                    "background": "#ffffff",
                    "border": branch_colors.get(branch, "#475569"),
                    "highlight": {
                        "background": "#ffffff",
                        "border": "#000000",
                    },
                },
                font={
                    "color": "#000000",
                    "face": "Inter",
                    "size": 20,
                    "multi": "html",
                },
                margin={"top": 10, "right": 10, "bottom": 14, "left": 10},
            )
        )
        if parent_name:
            edges.append(
                Edge(
                    source=parent_name,
                    target=member_name,
                    color="#94a3b8",
                    smooth=False,
                    width=2.2,
                )
            )

    config = Config(
        width=1200,
        height=680,
        directed=True,
        physics=False,
        hierarchical=True,
        levelSeparation=180,
        nodeSpacing=210,
        treeSpacing=240,
        direction="UD",
        sortMethod="directed",
        fit=True,
        highlightColor="#111827",
    )
    return nodes, edges, config, branch_colors


def ensure_selected_member(df: pd.DataFrame) -> str | None:
    names = df["Name"].tolist()
    selected = st.session_state.get("selected_member")
    if selected not in names:
        st.session_state["selected_member"] = names[0] if names else None
    return st.session_state.get("selected_member")


def render_profile_card(member: pd.Series | None) -> None:
    st.markdown("### 👤 Profile Card")
    if member is None:
        st.info("Select a family member to open the profile card.")
        return

    age = compute_age(member["Birthdate"])
    name = safe_text(member["Name"], "Unknown")
    generation = safe_text(member["Generation"], "Generation unknown")
    branch = safe_text(member["Branch"], "Unassigned branch")
    parent = safe_text(member["Parent"], "—")
    card_html = f"""
    <div class="profile-card">
      <img
        class="profile-avatar"
        src="{profile_image_data_uri(name)}"
        alt="{html.escape(name)}"
      />
      <h2 class="profile-name">{html.escape(name)}</h2>
      <p class="profile-subtitle">
        {html.escape(generation)} ·
        {html.escape(branch)}
      </p>
      <div class="profile-grid">
        <div class="profile-detail">
          <span class="profile-detail-label">Age</span>
          <span class="profile-detail-value">{age if age is not None else 'Unknown'}</span>
        </div>
        <div class="profile-detail">
          <span class="profile-detail-label">Branch</span>
          <span class="profile-detail-value">{html.escape(branch)}</span>
        </div>
        <div class="profile-detail">
          <span class="profile-detail-label">Birthdate</span>
          <span class="profile-detail-value">{html.escape(format_birthdate(member['Birthdate']))}</span>
        </div>
        <div class="profile-detail">
          <span class="profile-detail-label">Parent</span>
          <span class="profile-detail-value">{html.escape(parent)}</span>
        </div>
      </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_sidebar(df: pd.DataFrame) -> None:
    with st.sidebar:
        st.markdown("## Family Navigator")
        st.caption("Light, high-contrast navigation for quick member selection.")
        names = sorted(df["Name"].tolist())

        if names:
            selected_name = ensure_selected_member(df)
            selected_index = names.index(selected_name) if selected_name in names else 0
            selected = st.selectbox(
                "Choose a family member",
                names,
                index=selected_index,
            )
            st.session_state["selected_member"] = selected
        else:
            st.selectbox(
                "Choose a family member",
                ["No family members available"],
                disabled=True,
            )

        st.markdown("---")
        st.markdown("### Photos")
        st.caption(
            f"Add portraits in `{PROFILES_DIR.as_posix()}` as `[Name].jpg`. "
            "Missing photos automatically render as gray initial badges."
        )

        st.markdown("---")
        st.markdown("### Data source")
        st.caption(
            "The app reads and saves local edits in `family_data.csv` and builds the "
            "tree from each member's `Name` and `Parent` values."
        )


def render_tree_tab(df: pd.DataFrame) -> None:
    st.markdown("### 🌳 Family Tree")
    st.caption(
        "Portrait nodes use bold black labels in the format Name (Birthyear). "
        "Click any node to focus its profile."
    )

    branches = ["All"] + sorted(
        branch for branch in df["Branch"].unique().tolist() if pd.notna(branch) and branch
    )
    generations = sorted(
        [
            generation
            for generation in df["Generation"].unique().tolist()
            if pd.notna(generation) and str(generation).strip()
        ],
        key=generation_sort_key,
    )

    filter_col, generation_col = st.columns(2)
    with filter_col:
        branch_filter = st.selectbox("Filter by branch", branches)
    with generation_col:
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

    nodes, edges, config, branch_colors = build_graph(filtered)

    legend_branches = sorted(
        {branch if branch else "Unassigned" for branch in filtered["Branch"].tolist()}
    )
    legend_cols = st.columns(max(len(legend_branches), 1))
    for index, branch in enumerate(legend_branches):
        legend_cols[index].markdown(
            (
                "<div class='legend-chip'>"
                f"<span class='legend-swatch' style='background:{branch_colors.get(branch, '#475569')};'></span>"
                f"{html.escape(branch)}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    st.markdown("<div class='tree-panel'>", unsafe_allow_html=True)
    clicked = agraph(nodes=nodes, edges=edges, config=config)
    st.markdown("</div>", unsafe_allow_html=True)

    if isinstance(clicked, dict) and clicked.get("id"):
        st.session_state["selected_member"] = clicked["id"]
    elif isinstance(clicked, str):
        st.session_state["selected_member"] = clicked

    selected_name = ensure_selected_member(df)
    selected_member = (
        df.loc[df["Name"] == selected_name].iloc[0]
        if selected_name in df["Name"].values
        else None
    )

    _, profile_col, _ = st.columns([1, 1.8, 1])
    with profile_col:
        render_profile_card(selected_member)


def render_stats_tab(df: pd.DataFrame) -> None:
    st.markdown("### 📊 Family Statistics")

    avg_age = average_age(df["Birthdate"])
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total members", len(df))
    col2.metric("🌿 Generations", int(df["Generation"].replace("", pd.NA).nunique()))
    col3.metric("🌳 Branches", int(df["Branch"].replace("", pd.NA).nunique()))
    col4.metric("🎈 Average age", f"{avg_age:.1f} yrs" if avg_age is not None else "—")

    st.markdown("---")
    left, right = st.columns(2)
    with left:
        st.markdown("**Members per generation**")
        generation_counts = df.groupby("Generation").size().rename("Count")
        generation_counts = generation_counts.reindex(
            sorted(generation_counts.index.tolist(), key=generation_sort_key)
        )
        st.bar_chart(generation_counts)
    with right:
        st.markdown("**Members per branch**")
        branch_counts = (
            df.assign(Branch=df["Branch"].replace("", "Unassigned"))
            .groupby("Branch")
            .size()
            .sort_index()
            .rename("Count")
        )
        st.bar_chart(branch_counts)


def refresh_from_sheet() -> None:
    if not DEFAULT_DATA_URL:
        st.warning("Set `FAMILY_TREE_DATA_URL` to enable Google Sheet refresh.")
        return
    try:
        remote_df = read_remote_data(DEFAULT_DATA_URL)
    except URLError:
        st.error(
            f"Could not reach the Google Sheet at {DEFAULT_DATA_URL}. "
            "Check network access and try again."
        )
        return
    except pd.errors.ParserError:
        st.error("The Google Sheet data could not be parsed as CSV.")
        return
    except ValueError:
        st.error("The configured Google Sheet URL is invalid.")
        return
    except OSError:
        st.error("A local file error prevented saving data from the Google Sheet.")
        return
    save_data(remote_df)
    st.success("Reloaded local data from the provided Google Sheet.")
    st.rerun()


def normalize_nullable_text_series(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .apply(
            lambda value: ""
            if value.lower() in NULL_LIKE_TEXT_VALUES
            else value
        )
    )


def sanitize_editor_rows(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    footer_mask = (
        cleaned.apply(
            lambda row: row.astype(str).str.contains(EDITOR_FOOTER_MARKER, case=False, na=False).any(),
            axis=1,
        )
        if not cleaned.empty
        else pd.Series(False, index=cleaned.index)
    )
    cleaned = cleaned.loc[~footer_mask].copy()

    required_present = [column for column in REQUIRED_COLUMNS if column in cleaned.columns]
    if required_present:
        non_empty_mask = cleaned[required_present].apply(
            lambda row: any(
                str(value).strip().lower() not in NULL_LIKE_TEXT_VALUES
                for value in row
            ),
            axis=1,
        )
        cleaned = cleaned.loc[non_empty_mask].copy()

    return cleaned.reset_index(drop=True)


def render_editor_tab(df: pd.DataFrame) -> None:
    st.markdown("### ✏️ Edit Family Data")
    st.caption("Edit the provided dataset and save updates back to `family_data.csv`.")

    action_col, info_col = st.columns([1, 3])
    with action_col:
        if st.button("Reload from Google Sheet"):
            refresh_from_sheet()
    with info_col:
        st.caption(
            "Uses the Google Sheet from `FAMILY_TREE_DATA_URL` as a reset source, "
            "then writes the result to `family_data.csv` for local editing."
        )

    def text_column(label: str, required: bool = False):
        try:
            return st.column_config.TextColumn(label, required=required)
        except TypeError:
            # Streamlit compatibility: older versions don't support "required".
            return st.column_config.TextColumn(label)

    def date_column(label: str):
        try:
            return st.column_config.DateColumn(label, format="YYYY-MM-DD")
        except TypeError:
            # Streamlit compatibility: older versions don't support "format".
            return st.column_config.DateColumn(label)

    column_config = {
        "Generation": text_column("Generation", required=True),
        "Branch": text_column("Branch"),
        "Birthdate": date_column("Birthdate"),
        "Name": text_column("Name", required=True),
        "Parent": text_column("Parent"),
    }
    editor_kwargs: dict[str, Any] = {
        "column_config": column_config,
        "hide_index": True,
        "key": "family_editor",
    }
    if supports_kwarg(st.data_editor, "num_rows"):
        editor_kwargs["num_rows"] = "dynamic"
    if supports_kwarg(st.data_editor, "use_container_width"):
        editor_kwargs["use_container_width"] = True
    editor_input_df = sanitize_editor_rows(df)
    editor_input_df["Generation"] = normalize_nullable_text_series(editor_input_df["Generation"])
    editor_input_df["Parent"] = normalize_nullable_text_series(editor_input_df["Parent"])
    try:
        editor_df = st.data_editor(editor_input_df, **editor_kwargs)
    except (StreamlitAPIException, TypeError, ValueError) as exc:
        st.error(
            "The data editor could not render the current values. "
            f"Please review Generation and Parent fields, then try again. ({type(exc).__name__})"
        )
        st.exception(exc)
        editor_df = editor_input_df

    save_col, reset_col = st.columns([1, 5])
    with save_col:
        save_button_kwargs = {"type": "primary"} if supports_kwarg(st.button, "type") else {}
        if st.button("💾 Save changes", **save_button_kwargs):
            save_df = sanitize_editor_rows(editor_df)
            save_df["Generation"] = normalize_nullable_text_series(save_df["Generation"])
            save_df["Parent"] = normalize_nullable_text_series(save_df["Parent"])
            save_df["Generation"] = save_df["Generation"].apply(normalize_generation)
            save_df["Parent"] = save_df["Parent"].apply(
                lambda value: ""
                if str(value).strip().lower() in NULL_LIKE_TEXT_VALUES
                else str(value).strip()
            )
            save_data(save_df)
            st.success("Saved updates to family_data.csv.")
            st.rerun()
    with reset_col:
        if st.button("↩️ Discard changes"):
            st.rerun()


def main() -> None:
    df = load_data()
    before_count = len(df)
    df = df.dropna(subset=["Name", "Generation"])
    removed_count = before_count - len(df)
    if removed_count > 0:
        st.warning(
            f"Filtered out {removed_count} rows with missing Name or Generation values."
        )
    ensure_selected_member(df)
    render_sidebar(df)

    st.markdown(
        f"""
        <div class="hero-card">
          <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
            <span style="font-size:2.8rem;">🌳</span>
            <div>
              <h1 style="margin:0;font-size:2.3rem;font-weight:800;color:#111827;">{html.escape(APP_TITLE)}</h1>
              <p style="margin:0.35rem 0 0 0;color:#4b5563;font-size:1rem;">
                High-contrast, data-driven family profiles built directly from <strong>family_data.csv</strong>.
              </p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
