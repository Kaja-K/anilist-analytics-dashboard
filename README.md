# AniList Analytics Dashboard

Interactive analytics dashboard for your AniList profile — Spotify Wrapped for anime.
Works for any AniList account — just enter your username when prompted.

---

## What it does

Pulls your completed anime/manga from [AniList](https://anilist.co) and lets you explore them — genre trends, score distributions, watch history over time, and ML-based recommendations.

No API key needed. Public data only.

---

## Usage

```bash
python fetch.py
# AniList username: your_username
```

Saves CSV files to `user-data/<username>/`:

| File | Content |
|------|---------|
| `profile.csv` | Hours watched, mean score, episode count |
| `anime_list.csv` | Completed anime |
| `manga_list.csv` | Completed manga |
| `favourites.csv` | Favourite anime and manga |

---

## Stack

`requests` · `pandas`  · `plotly` · `dash` · `scikit-learn`

---

## Roadmap

- [x] Data fetching — AniList GraphQL API → CSV
- [ ] Data cleaning — pandas pipeline
- [ ] Dashboard — interactive Dash app with time slider
- [ ] ML — anime recommendations based on user profiles