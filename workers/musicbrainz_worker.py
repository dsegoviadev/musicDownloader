from PySide6.QtCore import QObject, Signal, Slot

from services.musicbrainz import (
    search_artist,
    get_artist_albums,
    get_release_group_releases,
    get_release_tracks,
)


class AlbumWorker(QObject):

    finished = Signal(object)
    error = Signal(str)

    def __init__(self, artist_name):
        super().__init__()

        self.artist_name = artist_name

    @Slot()
    def run(self):

        try:
            # -----------------------------
            # Buscar artista
            # -----------------------------

            result = search_artist(
                self.artist_name
            )

            if result is None:
                self.error.emit(
                    "No se pudo conectar con MusicBrainz."
                )
                return

            artists = result.get(
                "artists",
                []
            )

            if not artists:
                self.error.emit(
                    "No se encontró el artista."
                )
                return

            # Por ahora usamos el primer resultado
            artist = artists[0]

            artist_mbid = artist["id"]

            # -----------------------------
            # Obtener álbumes
            # -----------------------------

            albums_result = get_artist_albums(
                artist_mbid
            )

            if albums_result is None:
                self.error.emit(
                    "No se pudieron obtener los álbumes."
                )
                return

            release_groups = albums_result.get(
                "release-groups",
                []
            )

            self.finished.emit(
                release_groups
            )

        except Exception as error:

            self.error.emit(
                str(error)
            )


class TracksWorker(QObject):

    finished = Signal(object)
    error = Signal(str)

    def __init__(self, release_group_mbid):
        super().__init__()

        self.release_group_mbid = (
            release_group_mbid
        )

        self.album_item = None

    @Slot()
    def run(self):

        try:
            # -----------------------------
            # Buscar releases
            # -----------------------------

            releases_result = (
                get_release_group_releases(
                    self.release_group_mbid
                )
            )

            if releases_result is None:
                self.error.emit(
                    "No se pudieron obtener las releases."
                )
                return

            releases = releases_result.get(
                "releases",
                []
            )

            if not releases:
                self.error.emit(
                    "Este álbum no tiene releases."
                )
                return

            # -----------------------------
            # Primera release
            # -----------------------------

            first_release = releases[0]

            release_mbid = first_release["id"]

            # -----------------------------
            # Obtener canciones
            # -----------------------------

            tracks_result = get_release_tracks(
                release_mbid
            )

            if tracks_result is None:
                self.error.emit(
                    "No se pudieron obtener las canciones."
                )
                return

            self.finished.emit(
                tracks_result
            )

        except Exception as error:

            self.error.emit(
                str(error)
            )