
from ytmusicapi import YTMusic


class YouTubeMusic:

    def __init__(self):

        print(
            "Inicializando YouTube Music..."
        )

        self.ytmusic = YTMusic()

        print(
            "Conectado."
        )

    def search_song(
        self,
        artist,
        title,
        album=None,
    ):

        query = (
            f"{artist} - {title}"
        )

        print()
        print(
            f"Buscando en YouTube Music: "
            f"{query}"
        )

        results = self.ytmusic.search(
            query,
            filter="songs",
        )

        if not results:

            print(
                "No se encontraron resultados."
            )

            return None

        valid_results = []

        for result in results:

            result_title = result.get(
                "title",
                "",
            )

            result_artists = result.get(
                "artists",
                [],
            )

            result_album = result.get(
                "album"
            )

            result_album_name = ""

            if result_album:

                result_album_name = (
                    result_album.get(
                        "name",
                        "",
                    )
                )

            # --------------------------------
            # ARTISTAS
            # --------------------------------

            artist_names = [
                item.get(
                    "name",
                    "",
                )
                for item in result_artists
            ]

            artist_match = any(
                artist.lower()
                in name.lower()
                for name in artist_names
            )

            if not artist_match:
                continue

            # --------------------------------
            # EXCLUIR LIVE
            # --------------------------------

            text_to_check = (
                f"{result_title} "
                f"{result_album_name}"
            ).lower()

            live_terms = [
                "live",
                "concert",
                "festival",
                "performance",
                "bootleg",
                "bischofswerda",
                "leipzig",
                "sarpsborg",
                "zeitz",
            ]

            if any(
                term in text_to_check
                for term in live_terms
            ):
                continue

            # --------------------------------
            # EXCLUIR COVERS
            # --------------------------------

            cover_terms = [
                "cover",
                "tribute",
            ]

            if any(
                term in text_to_check
                for term in cover_terms
            ):
                continue

            valid_results.append(
                result
            )

        if not valid_results:

            print(
                "No se encontraron "
                "resultados válidos."
            )

            return None

        best_result = (
            self._select_best_result(
                valid_results,
                artist,
                title,
                album,
            )
        )

        if best_result is None:
            return None

        artists = best_result.get(
            "artists",
            [],
        )

        artist_names = [
            item.get(
                "name",
                ""
            )
            for item in artists
        ]

        album_data = best_result.get(
            "album"
        )

        album_name = ""

        if album_data:

            album_name = (
                album_data.get(
                    "name",
                    "",
                )
            )

        return {
            "title": best_result.get(
                "title",
                title,
            ),

            "artist": artist_names,

            "album": album_name,

            "duration": best_result.get(
                "duration",
                "",
            ),

            "video_id": best_result.get(
                "videoId"
            ),
        }

    def _select_best_result(
        self,
        results,
        artist,
        title,
        album,
    ):

        title_lower = title.lower()
        artist_lower = artist.lower()

        best_result = None
        best_score = -1

        for result in results:

            score = 0

            result_title = (
                result.get(
                    "title",
                    "",
                ).lower()
            )

            artists = result.get(
                "artists",
                [],
            )

            artist_names = [
                item.get(
                    "name",
                    ""
                ).lower()
                for item in artists
            ]

            result_album = result.get(
                "album"
            )

            album_name = ""

            if result_album:

                album_name = (
                    result_album.get(
                        "name",
                        "",
                    ).lower()
                )

            # --------------------------------
            # TÍTULO
            # --------------------------------

            if result_title == title_lower:

                score += 100

            elif title_lower in result_title:

                score += 50

            # --------------------------------
            # ARTISTA
            # --------------------------------

            if artist_lower in artist_names:

                score += 100

            elif any(
                artist_lower in name
                for name in artist_names
            ):

                score += 50

            # --------------------------------
            # ÁLBUM
            # --------------------------------

            if album:

                album_lower = album.lower()

                if album_name == album_lower:

                    score += 150

                elif album_lower in album_name:

                    score += 75

            # --------------------------------
            # MEJOR RESULTADO
            # --------------------------------

            if score > best_score:

                best_score = score
                best_result = result

        return best_result
