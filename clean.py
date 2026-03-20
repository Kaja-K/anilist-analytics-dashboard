"""
clean.py  —  Load user CSV data into pandas DataFrames.

Usage:
    python clean.py
"""

import pandas as pd
from pathlib import Path

# ── config ────────────────────────────────────────────────────────────────────
DATA_DIR = Path(__file__).parent / "user-data"

FILES = {
    "profile":    "profile.csv",
    "anime_list": "anime_list.csv",
    "manga_list": "manga_list.csv",
    "favourites": "favourites.csv",
}


# ── load ──────────────────────────────────────────────────────────────────────
def load_data(username: str) -> dict[str, pd.DataFrame]:
    """Load all CSV files for a given username into DataFrames."""
    user_dir = DATA_DIR / username

    if not user_dir.exists():
        raise FileNotFoundError(
            f"No data found for '{username}'.\n"
            f"Run fetch.py first to download the data."
        )

    dfs = {}
    for name, filename in FILES.items():
        path = user_dir / filename
        if path.exists():
            dfs[name] = pd.read_csv(path)
        else:
            print(f"  Warning: {filename} not found, skipping.")

    return dfs


def print_overview(dfs: dict[str, pd.DataFrame]) -> None:
    """Print shape and column names for each DataFrame."""
    for name, df in dfs.items():
        print(f"\n── {name}  ({df.shape[0]} rows × {df.shape[1]} cols)")
        print(f"   {list(df.columns)}")


# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    while True:
        username = input("AniList username: ").strip()
        if not username:
            continue
        try:
            dfs = load_data(username)
            break
        except FileNotFoundError as e:
            print(f"  {e}\n")

    print(f"\nLoaded data for: {username}")
    print_overview(dfs)