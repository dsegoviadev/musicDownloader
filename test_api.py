from services.musicbrainz import (
    search_artist,
    get_artist_albums,
)


# --------------------------------
# 1. Buscar artista
# --------------------------------

result = search_artist("Mayhem")

if result is None:
    print("No se pudo buscar el artista.")
    exit()


artists = result["artists"]

if not artists:
    print("No se encontraron artistas.")
    exit()


# --------------------------------
# 2. Seleccionar artista
# --------------------------------

artist = artists[0]

print("Artista:")
print(artist["name"])

print("MBID:")
print(artist["id"])

print()


# --------------------------------
# 3. Obtener discografía
# --------------------------------

albums_result = get_artist_albums(
    artist["id"]
)

if albums_result is None:
    print("No se pudieron obtener los álbumes.")
    exit()


release_groups = albums_result["release-groups"]


# --------------------------------
# 4. Mostrar álbumes
# --------------------------------

print("Álbumes:")
print()


for album in release_groups:

    title = album["title"]

    # Ignorar Live
    if "live" in title.lower():
        continue

    print(
        title,
        "|",
        album.get("primary-type"),
        "|",
        album.get("first-release-date"),
        "|",
        album["id"],
    )