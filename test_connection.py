import requests

url = "https://musicbrainz.org/ws/2/artist"

params = {
    "query": "Mayhem",
    "fmt": "json",
    "limit": 1,
}

headers = {
    "User-Agent": "MusicDownloader/0.1"
}

response = requests.get(
    url,
    params=params,
    headers=headers,
    timeout=10,
)

print("Status:", response.status_code)
print("URL:", response.url)
print("Respuesta:")
print(response.text[:500])
