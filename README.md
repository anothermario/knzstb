# 🌳 knzstb — Family Tree App

A modern, interactive family tree built with **Python + Streamlit**.

---

## Project Structure

```
knzstb/
├── app.py                  # Main Streamlit application
├── family_data.csv         # Local editable family data
├── .local_state/           # Auto-created local backup for data/photos (pull/merge-safe)
├── requirements.txt        # Python dependencies
└── assets/
     └── profiles/
         ├── Walter Künz.jpg # (optional) Real photo for "Walter Künz"
         ├── Lisa Schuch.jpg # (optional) Real photo for "Lisa Schuch"
         └── ...             # One file per family member: [Name].jpg
```

---

## Features

| Feature | Details |
|---|---|
| **Interactive Tree** | Clickable, high-contrast `streamlit-agraph` tree with circular portraits and bold `Name (Birthyear)` labels |
| **Sidebar Profile** | Selecting a node updates the sidebar profile panel with portrait, generation, branch, birthdate, and parent |
| **Login Gate** | App access is unlocked only after entering the configured username and password at launch |
| **Mobile Access Link** | The login screen and sidebar surface the current app URL with open/copy/share controls so the same link is easy to use on phones or send to approved external users |
| **Image Handling** | Loads persisted portraits (prefers `.local_state/profiles/`, then `assets/profiles/[Name].jpg`/`.jpeg`/`.png`); falls back to a gray initials avatar |
| **Dynamic Age** | Calculates current age from `Birthdate` using today’s date |
| **Data Editor** | `st.data_editor` table — edit and save changes back to `family_data.csv` and `.local_state/family_data.csv`, set/save a Google Sheet URL, reload from it, and export the current CSV |
| **Statistics** | Member counts per generation and per branch, with bar charts |
| **Modern UI** | Custom CSS: light sidebar, high-contrast cards, rounded avatars, and dark readable text |

---

## Quick Start

### 1 — Install dependencies

```bash
pip install -r requirements.txt
```

Requires Python 3.9+.

### 2 — Add your data

Edit `family_data.csv` (or use the in-app editor).  
The required columns are:

| Column | Description |
|---|---|
| `Generation` | Generation label such as `G2`, `G3`, `G4` |
| `Branch` | Family branch name (e.g. Müller, Schmidt) |
| `Name` | Full name (unique) |
| `Birthdate` | `YYYY-MM-DD` format |
| `Parent` | Name of the direct parent (leave blank for root nodes) |

### 3 — Optional: connect a Google Sheet reset source

In the **Data Editor** tab, paste your Google Sheet URL into **Google Sheet / CSV URL** and click **Save URL**.  
The app stores it in `family_data_url.txt` and uses it for **Reload from Google Sheet**.

You can still preconfigure a default URL via environment variable:

```bash
export FAMILY_TREE_DATA_URL="https://docs.google.com/spreadsheets/d/.../edit?usp=sharing"
```

The app converts Google Sheet edit URLs to CSV export format automatically.

### 4 — Add profile photos *(optional)*

Drop JPEG/PNG files into `assets/profiles/` named exactly after the person:

```
assets/profiles/Heinrich.jpg
assets/profiles/Anna.png
```

Any member without a photo will display a gray circular avatar with their initials automatically.

Uploads done inside the app are automatically persisted to:
- `.local_state/profiles/` (used first; protects against pull/merge overwrites)
- `assets/profiles/` (repository-visible copy)

### 5 — Run the app

```bash
streamlit run app.py
```

Open your browser at **http://localhost:8501**

The login screen and sidebar now also show the current app URL with mobile-friendly **Open**, **Copy**, and **Share** actions so the same link is easier to reuse on a phone or send to external users who already have the login details.

The login screen requires:
- Username: `knzstb`
- Password: `hanskuenz`

Optional: override these defaults with environment variables before launch:

```bash
export FAMILY_TREE_USERNAME="myuser"
export FAMILY_TREE_PASSWORD_SALT_HEX="4c6f67696e53616c7432303236"
export FAMILY_TREE_PASSWORD_ITERATIONS="390000"
export FAMILY_TREE_PASSWORD_HASH="$(python - <<'PY'
import hashlib
salt = bytes.fromhex('4c6f67696e53616c7432303236')
iterations = 390000
print(hashlib.pbkdf2_hmac('sha256', 'your_password_here'.encode(), salt, iterations).hex())
PY
)"
```

---

## Iterative Improvement Loop

1. **Edit data** — use the *Edit Data* tab in the app or edit `family_data.csv` directly.
2. **Add photos** — drop `[Name].jpg` files into `assets/profiles/`.
3. **Click profiles** — select a node in the tree to review the sidebar profile panel.
4. **Review hierarchy** — confirm `Parent` values are correct because the tree layout is built from `Name` → `Parent`.
5. **Save & reload** — click *Save Changes* in the editor; Streamlit hot-reloads automatically.
6. **Reset if needed** — save a URL in *Google Sheet / CSV URL*, then use *Reload from Google Sheet* to re-initialize local CSV data.
7. **Log changes** — commit your edits with a descriptive message so nothing is forgotten.

---

## Lessons Learned / Change Log

| Date | Change | Lesson |
|---|---|---|
| 2026-05-18 | Switched to a clickable `streamlit-agraph` tree | Click-driven profiles are a better fit than static Graphviz charts for this UI |
