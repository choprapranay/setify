import requests

def search_artist_mb(artist: str):
    url = "https://musicbrainz.org/ws/2/artist"
    params = {"query": artist, "fmt": "json", "limit": 5}

    resp = requests.get(url, params=params, headers={
        "User-Agent": "SetifyApp/1.0 (contact@example.com)"
    })
    resp.raise_for_status()

    data = resp.json()
    artists = data.get("artists", [])
    if not artists:
        return None

    best = max(artists, key=lambda a: a.get("score", 0))
    return {"name": best["name"], "mbid": best["id"]}
