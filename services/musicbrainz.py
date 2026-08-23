import time

import requests


BASE_URL = "https://musicbrainz.org/ws/2"

HEADERS = {
    "User-Agent": "MusicDownloader/0.1"
}


def _request(url, params):
    """
    Hace una petición a MusicBrainz.
    Reintenta automáticamente si el servidor está ocupado.
    """

    for intento in range(3):

        try:
            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=10,
            )

            print(response.url)
            print(response.status_code)

            # -----------------------------
            # ÉXITO
            # -----------------------------

            if response.status_code == 200:

                time.sleep(1)

                return response.json()

            # -----------------------------
            # SERVIDOR OCUPADO
            # -----------------------------

            if response.status_code in (
                429,
                502,
                503,
                504,
            ):

                espera = 2 ** intento

                print(
                    f"MusicBrainz ocupado. "
                    f"Reintentando en {espera} segundos..."
                )

                time.sleep(espera)

                continue

            # -----------------------------
            # OTRO ERROR
            # -----------------------------

            print("Error de MusicBrainz:")
            print(response.text)

            return None

        except requests.RequestException as error:

            print(
                f"Error de conexión: {error}"
            )

            espera = 2 ** intento

            print(
                f"Reintentando en {espera} segundos..."
            )

            time.sleep(espera)

    print(
        "No se pudo obtener respuesta de MusicBrainz."
    )

    return None


# ============================================================
# BUSCAR ARTISTA + ÁLBUMES
# ============================================================

def search_artist(artist_name):
    """
    Busca un artista y devuelve únicamente sus álbumes.

    Las canciones NO se cargan aquí.

    Retorna:

    {
        "artist": "Mayhem",
        "albums": [
            {
                "name": "De Mysteriis Dom Sathanas",
                "release_group_mbid": "..."
            }
        ]
    }
    """

    # -----------------------------
    # BUSCAR ARTISTA
    # -----------------------------

    url = f"{BASE_URL}/artist"

    params = {
        "query": artist_name,
        "fmt": "json",
        "limit": 5,
    }

    result = _request(url, params)

    if not result:
        return {
            "artist": artist_name,
            "albums": [],
        }

    artists = result.get(
        "artists",
        []
    )

    if not artists:
        return {
            "artist": artist_name,
            "albums": [],
        }

    # MusicBrainz coloca normalmente
    # el resultado más relevante primero.

    artist = artists[0]

    artist_mbid = artist["id"]
    artist_name = artist["name"]

    print()
    print("Artista encontrado:")
    print(artist_name)

    print("MBID:")
    print(artist_mbid)

    # -----------------------------
    # OBTENER RELEASE GROUPS
    # -----------------------------

    release_groups_result = (
        get_artist_albums(
            artist_mbid
        )
    )

    if not release_groups_result:

        return {
            "artist": artist_name,
            "albums": [],
        }

    release_groups = (
        release_groups_result.get(
            "release-groups",
            []
        )
    )

    albums = []

    # ========================================================
    # FILTRAR ÁLBUMES
    # ========================================================

    for release_group in release_groups:

        primary_type = (
            release_group.get(
                "primary-type"
            )
        )

        secondary_types = [
            value.lower()
            for value in release_group.get(
                "secondary-types",
                []
            )
        ]

        album_name = release_group.get(
            "title",
            ""
        )

        album_name_lower = (
            album_name.lower()
        )

        # -----------------------------
        # SOLO ALBUM
        # -----------------------------

        if primary_type != "Album":
            continue

        # -----------------------------
        # TIPOS EXCLUIDOS
        # -----------------------------

        blocked_secondary_types = {
            "live",
            "compilation",
            "demo",
            "remix",
            "dj-mix",
            "mixtape",
            "soundtrack",
            "spokenword",
        }

        if any(
            value in blocked_secondary_types
            for value in secondary_types
        ):
            continue

        # -----------------------------
        # EXCLUIR POR NOMBRE
        # -----------------------------

        blocked_terms = [
            "live",
            "concert",
            "bootleg",
            "compilation",
            "greatest hits",
            "best of",
            "remix",
            "remixes",
            "demo",
        ]

        if any(
            term in album_name_lower
            for term in blocked_terms
        ):
            continue

        albums.append(
            {
                "name": album_name,
                "release_group_mbid": (
                    release_group["id"]
                ),
            }
        )

    print()
    print(
        f"Álbumes válidos encontrados: "
        f"{len(albums)}"
    )

    return {
        "artist": artist_name,
        "albums": albums,
    }


# ============================================================
# OBTENER ÁLBUMES DEL ARTISTA
# ============================================================

def get_artist_albums(artist_mbid):

    url = f"{BASE_URL}/release-group"

    params = {
        "artist": artist_mbid,
        "fmt": "json",
        "limit": 100,
    }

    return _request(
        url,
        params
    )


# ============================================================
# OBTENER RELEASES DE UN ÁLBUM
# ============================================================

def get_release_group_releases(
    release_group_mbid
):

    url = f"{BASE_URL}/release"

    params = {
        "release-group": release_group_mbid,
        "fmt": "json",
        "limit": 100,
    }

    return _request(
        url,
        params
    )


# ============================================================
# OBTENER CANCIONES DE UN RELEASE
# ============================================================

def get_release_tracks(
    release_mbid
):

    url = (
        f"{BASE_URL}/release/"
        f"{release_mbid}"
    )

    params = {
        "fmt": "json",
        "inc": "recordings",
    }

    return _request(
        url,
        params
    )


# ============================================================
# OBTENER CANCIONES DE UN ÁLBUM
# ============================================================

def get_album_tracks(
    release_group_mbid
):
    """
    Obtiene las canciones de un álbum
    haciendo requests únicamente cuando
    el álbum es solicitado.
    """

    releases_result = (
        get_release_group_releases(
            release_group_mbid
        )
    )

    if not releases_result:
        return []

    releases = (
        releases_result.get(
            "releases",
            []
        )
    )

    if not releases:
        return []

    # --------------------------------
    # Elegir un release
    # --------------------------------

    release = releases[0]

    release_mbid = release["id"]

    # --------------------------------
    # Obtener tracks
    # --------------------------------

    tracks_result = get_release_tracks(
        release_mbid
    )

    if not tracks_result:
        return []

    songs = []

    media = tracks_result.get(
        "media",
        []
    )

    for medium in media:

        for track in medium.get(
            "tracks",
            []
        ):

            title = track.get(
                "title"
            )

            if title:
                songs.append(title)

    return songs