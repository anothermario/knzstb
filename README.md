# 🌳 knzstb — Family Tree App

A modern, interactive family tree built with **Python + Streamlit**.

---

## Project Structure

```
knzstb/
├── app.py                  # Main Streamlit application
├── family_tree.csv         # Local editable family data
├── requirements.txt        # Python dependencies
└── assets/
    └── profiles/
        ├── placeholder.png # Fallback avatar shown when no photo exists
        ├── Heinrich.jpg    # (optional) Real photo for "Heinrich"
        ├── Klaus.jpg       # (optional) Real photo for "Klaus"
        └── ...             # One file per family member: [Name].jpg
```

---

## Features

| Feature | Details |
|---|---|
| **Interactive Tree** | Clickable `streamlit-agraph` tree with branch colour-coding and generation/branch filters |
| **Profile Card** | Clicking a node opens an in-page profile card with photo, branch, generation, and parent |
| **Image Handling** | Loads `assets/profiles/[Name].jpg` (or `.jpeg`/`.png`); falls back to placeholder |
| **Dynamic Age** | Calculates current age from `Birthdate` using today’s date |
| **Data Editor** | `st.data_editor` table — edit and save changes back to `family_tree.csv`, or reset from the provided Google Sheet |
| **Statistics** | Member counts per generation and per branch, with bar charts |
| **Modern UI** | Custom CSS: Inter font, gradient sidebar, rounded cards, coloured badges |

---

## Quick Start

### 1 — Install dependencies

```bash
pip install -r requirements.txt
```

Requires Python 3.9+.

### 2 — Add your data

Edit `family_tree.csv` (or use the in-app editor).  
The required columns are:

| Column | Description |
|---|---|
| `Generation` | Integer — 1 = oldest generation |
| `Branch` | Family branch name (e.g. Müller, Schmidt) |
| `Name` | Full name (unique) |
| `Birthdate` | `YYYY-MM-DD` format |
| `Parent` | Name of the direct parent (leave blank for root nodes) |

### 3 — Optional: connect a Google Sheet reset source

If you want the **Reload from Google Sheet** button to work, set:

```bash
export FAMILY_TREE_DATA_URL="https://docs.google.com/spreadsheets/d/.../edit?usp=sharing"
```

The app will convert the edit URL to CSV export format automatically.

### 4 — Add profile photos *(optional)*

Drop JPEG/PNG files into `assets/profiles/` named exactly after the person:

```
assets/profiles/Heinrich.jpg
assets/profiles/Anna.png
```

Any member without a photo will display the placeholder avatar automatically.

### 5 — Run the app

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## Iterative Improvement Loop

1. **Edit data** — use the *Edit Data* tab in the app or edit `family_tree.csv` directly.
2. **Add photos** — drop `[Name].jpg` files into `assets/profiles/`.
3. **Click profiles** — select a node in the tree to review the current profile card.
4. **Customise branches** — update the `BRANCH_COLORS` dict in `app.py` to match your family branches.
5. **Save & reload** — click *Save Changes* in the editor; Streamlit hot-reloads automatically.
6. **Reset if needed** — use *Reload from Google Sheet* to re-initialize the local CSV from `FAMILY_TREE_DATA_URL`.
7. **Log changes** — commit your edits with a descriptive message so nothing is forgotten.

---

## Lessons Learned / Change Log

| Date | Change | Lesson |
|---|---|---|
| 2026-05-18 | Switched to a clickable `streamlit-agraph` tree | Click-driven profiles are a better fit than static Graphviz charts for this UI |
