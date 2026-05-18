# 🌳 knzstb — Family Tree App

A modern, interactive family tree built with **Python + Streamlit**.

---

## Project Structure

```
knzstb/
├── app.py                  # Main Streamlit application
├── family_tree.csv         # Family data (edit or replace with your own)
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
| **Interactive Tree** | Graphviz diagram with branch colour-coding and generation/branch filters |
| **Profile Gallery** | Sidebar shows birthdate, age, branch, generation, and a profile photo |
| **Image Handling** | Loads `assets/profiles/[Name].jpg` (or `.jpeg`/`.png`); falls back to placeholder |
| **Data Editor** | `st.data_editor` table — edit and save changes back to `family_tree.csv` |
| **Statistics** | Member counts per generation and per branch, with bar charts |
| **Modern UI** | Custom CSS: Inter font, gradient sidebar, rounded cards, coloured badges |

---

## Quick Start

### 1 — Install dependencies

```bash
pip install -r requirements.txt
```

> Requires Python 3.9+ and the **Graphviz system package**:
> - macOS: `brew install graphviz`
> - Ubuntu/Debian: `sudo apt-get install graphviz`
> - Windows: download from https://graphviz.org/download/

### 2 — Add your data

Edit `family_tree.csv` (or use the in-app editor).  
The required columns are:

| Column | Description |
|---|---|
| `Generation` | Integer — 1 = oldest generation |
| `Branch` | Family branch name (e.g. Müller, Schmidt) |
| `Birthdate` | `YYYY-MM-DD` format |
| `Name` | Full name (unique) |
| `Age` | Integer age (auto-displayed; re-compute after edits) |
| `Parent` | Name of the direct parent (leave blank for root nodes) |

### 3 — Add profile photos *(optional)*

Drop JPEG/PNG files into `assets/profiles/` named exactly after the person:

```
assets/profiles/Heinrich.jpg
assets/profiles/Anna.png
```

Any member without a photo will display the placeholder avatar automatically.

### 4 — Run the app

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

---

## Iterative Improvement Loop

1. **Edit data** — use the *Edit Data* tab in the app or edit `family_tree.csv` directly.
2. **Add photos** — drop `[Name].jpg` files into `assets/profiles/`.
3. **Customise branches** — update the `BRANCH_COLORS` dict in `app.py` to match your family branches.
4. **Save & reload** — click *Save Changes* in the editor; Streamlit hot-reloads automatically.
5. **Log changes** — commit your edits with a descriptive message so nothing is forgotten.

---

## Lessons Learned / Change Log

| Date | Change | Lesson |
|---|---|---|
| 2026-05-18 | Initial app created | Graphviz `rankdir=TB` + `splines=ortho` gives the cleanest top-down tree layout |
