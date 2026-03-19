import time
import requests
import pandas as pd
from pathlib import Path
from datetime import date, datetime

# ── config ────────────────────────────────────────────────────────────────────
API_URL  = "https://graphql.anilist.co"
OUT_BASE = Path("/home/kaypi/Documents/anilist-analytics-dashboard/user-data")

# ── queries ───────────────────────────────────────────────────────────────────
Q_USER = """
query ($u: String) {
  User(name: $u) {
    id name siteUrl createdAt
    avatar { large }
    statistics {
      anime { count meanScore minutesWatched episodesWatched }
      manga { count meanScore chaptersRead volumesRead }
    }
  }
}"""

Q_LIST = """
query ($u: String, $type: MediaType, $chunk: Int) {
  MediaListCollection(userName: $u, type: $type, chunk: $chunk, perChunk: 500) {
    hasNextChunk
    lists {
      entries {
        score(format: POINT_100) status repeat
        startedAt   { year month day }
        completedAt { year month day }
        media {
          id
          title { romaji english }
          format genres averageScore episodes chapters volumes
          season seasonYear
          studios(isMain: true) { nodes { name } }
          coverImage { large }
          siteUrl
        }
      }
    }
  }
}"""

Q_FAVS = """
query ($u: String) {
  User(name: $u) {
    favourites {
      anime { nodes { id title { romaji } genres averageScore } }
      manga { nodes { id title { romaji } genres averageScore } }
    }
  }
}"""

# ── helpers ───────────────────────────────────────────────────────────────────
def gql(q, **variables):
    """Send a GraphQL request, retry on rate limit."""
    for _ in range(3):
        r = requests.post(API_URL,
                          json={"query": q, "variables": variables},
                          headers={"Content-Type": "application/json"},
                          timeout=30)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 60))
            print(f"  Rate limited — waiting {wait}s...")
            time.sleep(wait)
            continue
        if r.status_code == 404:
            raise ValueError("User not found.")
        r.raise_for_status()
        data = r.json()
        if "errors" in data:
            msg = data["errors"][0].get("message", "")
            if "not found" in msg.lower():
                raise ValueError("User not found.")
            raise RuntimeError(f"API error: {msg}")
        return data["data"]
    raise RuntimeError("Failed after 3 attempts.")


def to_date(d):
    """{ year, month, day } -> '2024-04-15' or None"""
    if not d or not d.get("year"):
        return None
    try:
        return date(d["year"], d.get("month") or 1, d.get("day") or 1).isoformat()
    except ValueError:
        return None


def to_dt(ts):
    """Unix timestamp -> '2024-04-15 19:30' or None"""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else None


# ── fetch functions ───────────────────────────────────────────────────────────
def fetch_list(username, media_type):
    """Fetch completed anime or manga list. media_type = 'ANIME' or 'MANGA'"""
    rows, chunk = [], 1
    while True:
        col = gql(Q_LIST, u=username, type=media_type, chunk=chunk)["MediaListCollection"]
        for lst in col["lists"]:
            for e in lst["entries"]:
                if e["status"] != "COMPLETED":
                    continue
                m = e["media"]
                rows.append({
                    "media_id":      m["id"],
                    "title":         m["title"]["romaji"],
                    "title_english": m["title"].get("english"),
                    "format":        m.get("format"),
                    "genres":        ", ".join(m.get("genres") or []),
                    "avg_score":     m.get("averageScore"),
                    "episodes":      m.get("episodes"),
                    "chapters":      m.get("chapters"),
                    "volumes":       m.get("volumes"),
                    "season":        m.get("season"),
                    "season_year":   m.get("seasonYear"),
                    "studio":        m["studios"]["nodes"][0]["name"] if m.get("studios", {}).get("nodes") else None,
                    "cover_url":     m["coverImage"].get("large"),
                    "anilist_url":   m.get("siteUrl"),
                    "user_score":    e["score"],
                    "repeat":        e["repeat"],
                    "started_at":    to_date(e.get("startedAt")),
                    "completed_at":  to_date(e.get("completedAt")),
                })
        if not col["hasNextChunk"]:
            break
        chunk += 1
    return rows


def fetch_favourites(username):
    favs = gql(Q_FAVS, u=username)["User"]["favourites"]
    rows = []
    for media_type, nodes in [("anime", favs["anime"]["nodes"]),
                               ("manga", favs["manga"]["nodes"])]:
        for n in nodes:
            rows.append({
                "type":      media_type,
                "media_id":  n["id"],
                "title":     n["title"]["romaji"],
                "avg_score": n.get("averageScore"),
                "genres":    ", ".join(n.get("genres") or []),
            })
    return rows


# ── main ──────────────────────────────────────────────────────────────────────
def main(username):
    out = OUT_BASE / username
    out.mkdir(parents=True, exist_ok=True)
    print(f"\nSaving to: {out}/\n")

    print("[1/4] Profile...")
    u = gql(Q_USER, u=username)["User"]
    s = u["statistics"]
    pd.DataFrame([{
        "username":         u["name"],
        "user_id":          u["id"],
        "site_url":         u["siteUrl"],
        "avatar_url":       u["avatar"]["large"],
        "created_at":       to_dt(u["createdAt"]),
        "anime_count":      s["anime"]["count"],
        "anime_mean_score": s["anime"]["meanScore"],
        "hours_watched":    round(s["anime"]["minutesWatched"] / 60, 1),
        "episodes_watched": s["anime"]["episodesWatched"],
        "manga_count":      s["manga"]["count"],
        "manga_mean_score": s["manga"]["meanScore"],
        "chapters_read":    s["manga"]["chaptersRead"],
        "volumes_read":     s["manga"]["volumesRead"],
    }]).to_csv(out / "profile.csv", index=False)
    print("       profile.csv")

    print("[2/4] Anime list...")
    anime = fetch_list(username, "ANIME")
    pd.DataFrame(anime).to_csv(out / "anime_list.csv", index=False)
    print(f"       anime_list.csv  ({len(anime)} rows)")

    print("[3/4] Manga list...")
    manga = fetch_list(username, "MANGA")
    pd.DataFrame(manga).to_csv(out / "manga_list.csv", index=False)
    print(f"       manga_list.csv  ({len(manga)} rows)")

    print("[4/4] Favourites...")
    favs = fetch_favourites(username)
    pd.DataFrame(favs).to_csv(out / "favourites.csv", index=False)
    print(f"       favourites.csv  ({len(favs)} rows)")

    print(f"\n{'─'*40}\nDone! -> {out}\n{'─'*40}\n")


if __name__ == "__main__":
    while True:
        username = input("AniList username: ").strip()
        if not username:
            continue
        try:
            gql("query($u:String){User(name:$u){id}}", u=username)
            print("  Found! Starting download...\n")
            break
        except ValueError:
            print(f"  '{username}' not found on AniList. Try again.\n")
    main(username)