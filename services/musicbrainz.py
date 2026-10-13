import time

import requests


BASE_URL = "https://musicbrainz.org/ws/2"

HEADERS = {
    "User-Agent": "MusicDownloader/0.1"
}


def _request(url, params):
    for intento in range(3):

        try:

            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=10,
            )

            if response.status_code == 200:

                time.sleep(1)

                return response.json()

            if response.status_code in (
                429,
                502,
                503,
                504,
            ):

                espera = 2 ** intento

                time.sleep(espera)

                continue

            print(
                "Error de MusicBrainz:"
            )

            print(
                response.text
            )

            return None

        except requests.RequestException as error:

            print(
                f"Error de conexión: {error}"
            )

            espera = 2 ** intento

            time.sleep(espera)

    print(
        "No se pudo obtener respuesta "
        "de MusicBrainz."
    )

    return None


# ============================================================
# NORMALIZACIÓN
# ============================================================

def _normalize_title(value):

    if not value:
        return ""

    return " ".join(
        value.lower()
        .strip()
        .split()
    )


# ============================================================
# BUSCAR ARTISTA + ÁLBUMES
# ============================================================

def search_artist(
    artist_name,
    include_types=None,
):

    if include_types is None:

        include_types = [
            "album"
        ]

    url = f"{BASE_URL}/artist"

    params = {
        "query": artist_name,
        "fmt": "json",
        "limit": 5,
    }

    result = _request(
        url,
        params,
    )

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

    artist = artists[0]

    artist_mbid = artist["id"]

    artist_name = artist["name"]

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

    blocked_secondary_types = {
        "compilation",
        "demo",
        "remix",
        "dj-mix",
        "mixtape",
        "soundtrack",
        "spokenword",
        "audio drama",
    }

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
        "mix",
    ]

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

        album_name = (
            release_group.get(
                "title",
                ""
            )
        )

        album_name_lower = (
            album_name.lower()
        )

        # ====================================================
        # LIVE
        # ====================================================

        is_live = (
            "live"
            in secondary_types
        )

        if is_live:

            if "live" not in include_types:
                continue

            albums.append(
                {
                    "name": album_name,
                    "release_group_mbid":
                        release_group["id"],
                    "type": "live",
                }
            )

            continue

        # ====================================================
        # SINGLE
        # ====================================================

        if primary_type == "Single":

            if "single" not in include_types:
                continue

            albums.append(
                {
                    "name": album_name,
                    "release_group_mbid":
                        release_group["id"],
                    "type": "single",
                }
            )

            continue

        # ====================================================
        # EP
        # ====================================================

        if primary_type == "EP":

            if "ep" not in include_types:
                continue

            albums.append(
                {
                    "name": album_name,
                    "release_group_mbid":
                        release_group["id"],
                    "type": "ep",
                }
            )

            continue

        # ====================================================
        # ÁLBUM
        # ====================================================

        if primary_type != "Album":
            continue

        if "album" not in include_types:
            continue

        if any(
            value in blocked_secondary_types
            for value in secondary_types
        ):
            continue

        if any(
            term in album_name_lower
            for term in blocked_terms
        ):
            continue

        albums.append(
            {
                "name": album_name,
                "release_group_mbid":
                    release_group["id"],
                "type": "album",
            }
        )

    return {
        "artist": artist_name,
        "albums": albums,
    }


# ============================================================
# OBTENER ÁLBUMES DEL ARTISTA
# ============================================================

def get_artist_albums(
    artist_mbid
):

    url = f"{BASE_URL}/release-group"

    params = {
        "artist": artist_mbid,
        "fmt": "json",
        "limit": 100,
    }

    return _request(
        url,
        params,
    )


# ============================================================
# OBTENER RELEASES DE UN ÁLBUM
# ============================================================

def get_release_group_releases(
    release_group_mbid
):

    url = f"{BASE_URL}/release"

    params = {
        "release-group":
            release_group_mbid,
        "fmt": "json",
        "limit": 100,
    }

    return _request(
        url,
        params,
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
        params,
    )


# ============================================================
# SCORE DE RELEASE
# ============================================================

def _release_score(
    release,
    release_group_title,
):

    score = 0

    release_title = release.get(
        "title",
        ""
    )

    normalized_release_title = (
        _normalize_title(
            release_title
        )
    )

    normalized_group_title = (
        _normalize_title(
            release_group_title
        )
    )

    # ========================================================
    # TÍTULO
    # ========================================================

    if (
        normalized_release_title
        == normalized_group_title
    ):

        score += 1000

    else:

        score -= 100

    # ========================================================
    # STATUS
    # ========================================================

    status = (
        release.get(
            "status",
            ""
        )
        or ""
    ).lower()

    if status == "official":

        score += 500

    elif status == "promotion":

        score -= 200

    elif status == "pseudo-release":

        score -= 300

    elif status == "bootleg":

        score -= 500

    # ========================================================
    # TÍTULOS DE EDICIONES ESPECIALES
    # ========================================================

    special_terms = [
        "deluxe",
        "bonus",
        "anniversary",
        "expanded",
        "special edition",
        "limited edition",
        "remastered",
        "reissue",
        "edition",
        "collector",
        "in his own words",
        "instrumental",
        "karaoke",
    ]

    title_lower = normalized_release_title

    for term in special_terms:

        if term in title_lower:

            score -= 400

    # ========================================================
    # FECHA
    #
    # Releases más antiguos tienen prioridad.
    # ========================================================

    date = (
        release.get(
            "date",
            ""
        )
        or ""
    )

    if date:

        try:

            year = int(
                date[:4]
            )

            score += max(
                0,
                2100 - year
            )

        except (
            ValueError,
            TypeError,
        ):

            pass

    # ========================================================
    # PAÍS
    #
    # No usamos país como criterio fuerte porque queremos
    # permitir diferentes ediciones oficiales equivalentes.
    # ========================================================

    country = (
        release.get(
            "country"
        )
    )

    if country == "XW":

        score += 10

    return score


# ============================================================
# ELEGIR RELEASE PRINCIPAL
# ============================================================

def _select_best_release(
    releases,
    release_group_title,
):

    if not releases:

        return None

    candidates = []

    for release in releases:

        release_score = (
            _release_score(
                release,
                release_group_title,
            )
        )

        candidates.append(
            (
                release_score,
                release
            )
        )

    candidates.sort(
        key=lambda value: (
            value[0],
            value[1].get(
                "date",
                ""
            ),
        ),
        reverse=True,
    )

    return candidates[0][1]


# ============================================================
# OBTENER CANCIONES DE UN ÁLBUM
# ============================================================

def get_album_tracks(
    release_group_mbid
):

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

    # ========================================================
    # OBTENER TÍTULO DEL RELEASE GROUP
    # ========================================================

    release_group_url = (
        f"{BASE_URL}/release-group/"
        f"{release_group_mbid}"
    )

    release_group_result = _request(
        release_group_url,
        {
            "fmt": "json",
        },
    )

    if release_group_result:

        release_group_title = (
            release_group_result.get(
                "title",
                ""
            )
        )

    else:

        release_group_title = (
            releases[0].get(
                "title",
                ""
            )
        )

    # ========================================================
    # ELEGIR UNA SOLA EDICIÓN
    # ========================================================

    release = _select_best_release(
        releases,
        release_group_title,
    )

    if not release:

        return []

    release_mbid = release.get(
        "id"
    )

    if not release_mbid:
        return []

    # ========================================================
    # OBTENER TRACKLIST
    # ========================================================

    tracks_result = (
        get_release_tracks(
            release_mbid
        )
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

            if not title:
                continue

            songs.append(
                title
            )

    return songs