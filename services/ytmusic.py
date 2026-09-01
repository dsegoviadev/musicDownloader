import re
import unicodedata

from difflib import SequenceMatcher

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

    # ============================================================
    # BUSCAR CANCIÓN
    # ============================================================

    def search_song(
        self,
        artist,
        title,
        album=None,
        duration=None,
    ):
        """
        Busca una canción en YouTube Music.

        MusicBrainz es nuestra fuente de verdad.

        Se utiliza un sistema de scoring para elegir
        el candidato más probable.

        Parámetros:

            artist
                Artista esperado.

            title
                Título esperado.

            album
                Álbum esperado.

            duration
                Duración esperada en segundos.

        Retorna:

            {
                "title": ...,
                "artist": [...],
                "album": ...,
                "duration": ...,
                "video_id": ...
            }

        o None si no existe un candidato suficientemente confiable.
        """

        # ========================================================
        # NORMALIZACIÓN
        # ========================================================

        normalized_artist = (
            self._normalize_text(
                artist
            )
        )

        normalized_title = (
            self._normalize_text(
                title
            )
        )

        normalized_album = (
            self._normalize_text(
                album
            )
            if album
            else ""
        )

        # ========================================================
        # BÚSQUEDA
        # ========================================================

        query = (
            f"{normalized_artist} - "
            f"{normalized_title}"
        )

        print()
        print(
            "=" * 60
        )

        print(
            "Buscando en YouTube Music:"
        )

        print(
            query
        )

        if album:
            print(
                f"Álbum esperado: {album}"
            )

        if duration is not None:

            print(
                "Duración esperada: "
                f"{self._format_duration(duration)}"
            )

        print(
            "=" * 60
        )

        try:

            results = self.ytmusic.search(
                query,
                filter="songs",
            )

        except Exception as error:

            print()
            print(
                "ERROR buscando en "
                "YouTube Music:"
            )

            print(error)

            return None

        if not results:

            print(
                "No se encontraron resultados."
            )

            return None

        print()
        print(
            f"Resultados encontrados: "
            f"{len(results)}"
        )

        # ========================================================
        # EVALUAR CANDIDATOS
        # ========================================================

        candidates = []

        for result in results:

            candidate = (
                self._score_result(
                    result=result,
                    artist=artist,
                    title=title,
                    album=album,
                    duration=duration,
                )
            )

            candidates.append(
                candidate
            )

        # ========================================================
        # ORDENAR
        # ========================================================

        candidates.sort(
            key=lambda item: item["score"],
            reverse=True,
        )

        # ========================================================
        # MOSTRAR DEBUG
        # ========================================================

        print()
        print(
            "=" * 60
        )

        print(
            "CANDIDATOS ORDENADOS POR SCORE"
        )

        print(
            "=" * 60
        )

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):

            self._print_candidate(
                index,
                candidate,
            )

        # ========================================================
        # FILTRAR TÍTULO
        # ========================================================

        compatible_candidates = [
            candidate
            for candidate in candidates
            if candidate[
                "details"
            ][
                "title_compatible"
            ]
        ]

        print()
        print(
            f"Candidatos con título compatible: "
            f"{len(compatible_candidates)}"
        )

        if not compatible_candidates:

            print()
            print(
                "NINGÚN RESULTADO TIENE "
                "UN TÍTULO COMPATIBLE."
            )

            print(
                f"No se descargará "
                f"{artist} - {title}"
            )

            print()
            print(
                "Resultados rechazados:"
            )

            for index, candidate in enumerate(
                candidates,
                start=1,
            ):

                self._print_candidate(
                    index,
                    candidate,
                )

            return None

        # ========================================================
        # SEGURIDAD:
        # ARTISTA DEBE COINCIDIR
        # ========================================================

        compatible_artist_candidates = [
            candidate
            for candidate in compatible_candidates
            if candidate[
                "details"
            ][
                "artist_exact"
            ]
        ]

        print()
        print(
            f"Candidatos con artista exacto: "
            f"{len(compatible_artist_candidates)}"
        )

        if not compatible_artist_candidates:

            print()
            print(
                "NINGÚN RESULTADO TIENE "
                "EL ARTISTA CORRECTO."
            )

            print(
                f"No se descargará "
                f"{artist} - {title}"
            )

            return None

        # ========================================================
        # ELEGIR MEJOR RESULTADO
        # ========================================================

        best_result = (
            compatible_artist_candidates[0]
        )

        print()
        print(
            "=" * 60
        )

        print(
            "MEJOR RESULTADO"
        )

        print(
            "=" * 60
        )

        self._print_candidate(
            1,
            best_result,
        )

        # ========================================================
        # SCORE MÍNIMO
        # ========================================================

        if best_result["score"] < 350:

            print()
            print(
                "ADVERTENCIA:"
            )

            print(
                "El score del mejor resultado "
                "es demasiado bajo."
            )

            print(
                f"Score: "
                f"{best_result['score']}"
            )

            print(
                "No se descargará."
            )

            return None

        # ========================================================
        # RETORNAR
        # ========================================================

        result = best_result[
            "result"
        ]

        artists = result.get(
            "artists",
            [],
        )

        artist_names = [
            item.get(
                "name",
                "",
            )
            for item in artists
        ]

        album_data = result.get(
            "album"
        )

        album_name = ""

        if album_data:

            album_name = album_data.get(
                "name",
                "",
            )

        return {
            "title": result.get(
                "title",
                title,
            ),

            "artist": artist_names,

            "album": album_name,

            "duration": self._get_duration(
                result
            ),

            "video_id": result.get(
                "videoId"
            ),
        }

    # ============================================================
    # SCORE
    # ============================================================

    def _score_result(
        self,
        result,
        artist,
        title,
        album,
        duration,
    ):

        result_title = result.get(
            "title",
            "",
        )

        result_artists = result.get(
            "artists",
            [],
        )

        album_data = result.get(
            "album"
        )

        result_album = ""

        if album_data:

            result_album = album_data.get(
                "name",
                "",
            )

        result_duration = (
            self._get_duration(
                result
            )
        )

        # ========================================================
        # NORMALIZAR
        # ========================================================

        normalized_artist = (
            self._normalize_text(
                artist
            )
        )

        normalized_title = (
            self._normalize_text(
                title
            )
        )

        normalized_album = (
            self._normalize_text(
                album
            )
            if album
            else ""
        )

        normalized_result_title = (
            self._normalize_text(
                result_title
            )
        )

        normalized_result_album = (
            self._normalize_text(
                result_album
            )
        )

        artist_names = [
            self._normalize_text(
                item.get(
                    "name",
                    "",
                )
            )
            for item in result_artists
        ]

        # ========================================================
        # ARTISTA
        # ========================================================

        artist_exact = (
            normalized_artist
            in artist_names
        )

        artist_similar = 0.0

        for name in artist_names:

            similarity = (
                SequenceMatcher(
                    None,
                    normalized_artist,
                    name,
                ).ratio()
            )

            if similarity > artist_similar:

                artist_similar = similarity

        # ========================================================
        # TÍTULO
        # ========================================================

        title_exact = (
            normalized_result_title
            == normalized_title
        )

        title_similar = (
            SequenceMatcher(
                None,
                normalized_title,
                normalized_result_title,
            ).ratio()
        )

        title_compatible = (
            self._title_is_compatible(
                normalized_title,
                normalized_result_title,
            )
        )

        # ========================================================
        # ÁLBUM
        # ========================================================

        album_exact = False
        album_similar = 0.0

        if normalized_album:

            album_exact = (
                normalized_result_album
                == normalized_album
            )

            album_similar = (
                SequenceMatcher(
                    None,
                    normalized_album,
                    normalized_result_album,
                ).ratio()
            )

        # ========================================================
        # DURACIÓN
        # ========================================================

        duration_difference = None

        if (
            duration is not None
            and result_duration is not None
        ):

            expected_duration = (
                self._duration_to_seconds(
                    duration
                )
            )

            actual_duration = (
                self._duration_to_seconds(
                    result_duration
                )
            )

            if (
                expected_duration is not None
                and actual_duration is not None
            ):

                duration_difference = abs(
                    expected_duration
                    - actual_duration
                )

        # ========================================================
        # TEXTO COMPLETO
        # ========================================================

        text_to_check = (
            f"{result_title} "
            f"{result_album}"
        )

        normalized_text = (
            self._normalize_text(
                text_to_check
            )
        )

        # ========================================================
        # SCORE
        # ========================================================

        score = 0

        # --------------------------------------------------------
        # ARTISTA
        # --------------------------------------------------------

        if artist_exact:

            score += 300

        elif artist_similar >= 0.90:

            score += 150

        elif artist_similar >= 0.75:

            score += 50

        else:

            score -= 500

        # --------------------------------------------------------
        # TÍTULO
        # --------------------------------------------------------

        if title_exact:

            score += 400

        elif title_compatible:

            score += 250

        elif title_similar >= 0.85:

            score += 120

        elif title_similar >= 0.65:

            score += 30

        else:

            score -= 200

        # --------------------------------------------------------
        # ÁLBUM
        # --------------------------------------------------------

        if normalized_album:

            if album_exact:

                score += 250

            elif album_similar >= 0.85:

                score += 120

            elif album_similar >= 0.65:

                score += 40

        # --------------------------------------------------------
        # DURACIÓN
        # --------------------------------------------------------

        duration_bonus = 0

        if duration_difference is not None:

            if duration_difference <= 2:

                duration_bonus = 150

            elif duration_difference <= 5:

                duration_bonus = 120

            elif duration_difference <= 10:

                duration_bonus = 80

            elif duration_difference <= 20:

                duration_bonus = 30

            elif duration_difference <= 40:

                duration_bonus = -50

            else:

                duration_bonus = -150

            score += duration_bonus

        # ========================================================
        # AUDIO
        # ========================================================

        audio_bonus = 0

        audio_terms = [
            "audio",
            "official audio",
        ]

        for term in audio_terms:

            if term in normalized_text:

                audio_bonus = 60

                break

        score += audio_bonus

        # ========================================================
        # PENALIZACIÓN DE VERSIONES
        # ========================================================

        version_penalty = 0

        version_terms = {

            "live": 180,

            "concert": 180,

            "festival": 180,

            "performance": 180,

            "bootleg": 200,

            "remix": 180,

            "remixed": 180,

            "instrumental": 180,

            "karaoke": 250,

            "cover": 250,

            "tribute": 250,

            "sped up": 200,

            "slowed": 200,

            "slowed + reverb": 220,

            "nightcore": 220,

            "acoustic": 150,

            "demo": 150,

            "radio edit": 120,

            "extended": 100,

            "edit": 80,

        }

        for term, penalty in (
            version_terms.items()
        ):

            if term in normalized_text:

                version_penalty += penalty

        score -= version_penalty

        # ========================================================
        # RESULTADO
        # ========================================================

        details = {

            "artist_exact":
                artist_exact,

            "artist_similar":
                round(
                    artist_similar,
                    2,
                ),

            "title_exact":
                title_exact,

            "title_compatible":
                title_compatible,

            "title_similar":
                round(
                    title_similar,
                    2,
                ),

            "album_exact":
                album_exact,

            "album_similar":
                round(
                    album_similar,
                    2,
                ),

            "duration_difference":
                duration_difference,

            "duration_bonus":
                duration_bonus,

            "audio_bonus":
                audio_bonus,

            "version_penalty":
                version_penalty,
        }

        return {

            "score":
                score,

            "result":
                result,

            "details":
                details,
        }

    # ============================================================
    # TÍTULO COMPATIBLE
    # ============================================================

    def _title_is_compatible(
        self,
        expected,
        actual,
    ):
        """
        Determina si dos títulos representan
        probablemente la misma canción.

        Además de la comparación normal,
        soporta títulos donde YouTube Music
        agrega una traducción, transliteración
        o título alternativo entre paréntesis.

        Ejemplos:

            BONAMANA
            보나마나 (BONAMANA)

        y:

            BULLSHIT
            개소리 (BULLSHIT)

        y:

            CRAYON
            크레용(Crayon)

        La comparación se realiza sobre textos
        previamente normalizados.
        """

        if not expected or not actual:

            return False

        # --------------------------------------------------------
        # EXACTO
        # --------------------------------------------------------

        if expected == actual:

            return True

        # --------------------------------------------------------
        # LIMPIEZA NORMAL
        # --------------------------------------------------------

        expected_clean = (
            self._clean_title_for_matching(
                expected
            )
        )

        actual_clean = (
            self._clean_title_for_matching(
                actual
            )
        )

        if expected_clean == actual_clean:

            return True

        # --------------------------------------------------------
        # CONTENCIÓN
        # --------------------------------------------------------

        if (
            expected_clean in actual_clean
            or actual_clean in expected_clean
        ):

            return True

        # --------------------------------------------------------
        # ALIAS DENTRO DE PARÉNTESIS / CORCHETES
        #
        # Ejemplo:
        #
        # 보나마나 (BONAMANA)
        #
        # Extraemos:
        #
        # BONAMANA
        # --------------------------------------------------------

        actual_aliases = (
            self._extract_title_aliases(
                actual
            )
        )

        expected_aliases = (
            self._extract_title_aliases(
                expected
            )
        )

        # El título esperado coincide con
        # alguno de los aliases del resultado.

        for alias in actual_aliases:

            alias_clean = (
                self._clean_title_for_matching(
                    alias
                )
            )

            if not alias_clean:
                continue

            if (
                alias_clean
                == expected_clean
            ):

                return True

            if (
                expected_clean
                in alias_clean
                or alias_clean
                in expected_clean
            ):

                return True

            similarity = (
                SequenceMatcher(
                    None,
                    expected_clean,
                    alias_clean,
                ).ratio()
            )

            if similarity >= 0.90:

                return True

        # --------------------------------------------------------
        # También comprobamos aliases del título esperado
        # contra el título real.
        # --------------------------------------------------------

        for alias in expected_aliases:

            alias_clean = (
                self._clean_title_for_matching(
                    alias
                )
            )

            if not alias_clean:
                continue

            if (
                alias_clean
                == actual_clean
            ):

                return True

            if (
                alias_clean
                in actual_clean
                or actual_clean
                in alias_clean
            ):

                return True

            similarity = (
                SequenceMatcher(
                    None,
                    alias_clean,
                    actual_clean,
                ).ratio()
            )

            if similarity >= 0.90:

                return True

        # --------------------------------------------------------
        # COMPARAR ÚNICAMENTE LAS PARTES ASCII
        #
        # Esto permite detectar:
        #
        # 보나마나 (BONAMANA)
        #
        # como:
        #
        # bonamana
        #
        # sin necesitar traducir coreano.
        # --------------------------------------------------------

        expected_ascii = (
            self._extract_ascii_title(
                expected_clean
            )
        )

        actual_ascii = (
            self._extract_ascii_title(
                actual_clean
            )
        )

        if expected_ascii and actual_ascii:

            if (
                expected_ascii
                == actual_ascii
            ):

                return True

            if (
                expected_ascii
                in actual_ascii
                or actual_ascii
                in expected_ascii
            ):

                return True

        # --------------------------------------------------------
        # SIMILITUD FINAL
        # --------------------------------------------------------

        similarity = (
            SequenceMatcher(
                None,
                expected_clean,
                actual_clean,
            ).ratio()
        )

        return similarity >= 0.82

    # ============================================================
    # EXTRAER ALIASES
    # ============================================================

    @staticmethod
    def _extract_title_aliases(
        text
    ):
        """
        Extrae contenido que aparece entre:

            (...)
            [...]

        Ejemplo:

            보나마나 (BONAMANA)

        retorna:

            ["BONAMANA"]
        """

        if not text:

            return []

        aliases = []

        # --------------------------------------------------------
        # Paréntesis
        # --------------------------------------------------------

        parenthesis_matches = re.findall(
            r"\(([^()]*)\)",
            text,
        )

        aliases.extend(
            parenthesis_matches
        )

        # --------------------------------------------------------
        # Corchetes
        # --------------------------------------------------------

        bracket_matches = re.findall(
            r"\[([^\[\]]*)\]",
            text,
        )

        aliases.extend(
            bracket_matches
        )

        return aliases

    # ============================================================
    # EXTRAER TEXTO ASCII
    # ============================================================

    @staticmethod
    def _extract_ascii_title(
        text
    ):
        """
        Extrae las partes ASCII alfanuméricas
        de un título.

        Ejemplo:

            보나마나 (BONAMANA)

        produce:

            bonamana

        Esto permite hacer matching cuando
        MusicBrainz utiliza el título latino
        y YouTube Music muestra primero
        el título coreano.
        """

        if not text:

            return ""

        # --------------------------------------------------------
        # Unicode -> ASCII cuando sea posible
        # --------------------------------------------------------

        normalized = (
            unicodedata.normalize(
                "NFKD",
                text,
            )
        )

        ascii_text = (
            normalized.encode(
                "ascii",
                "ignore",
            )
            .decode(
                "ascii"
            )
        )

        # --------------------------------------------------------
        # Solo letras y números
        # --------------------------------------------------------

        ascii_text = re.sub(
            r"[^a-zA-Z0-9]+",
            "",
            ascii_text,
        )

        return ascii_text.lower()

    # ============================================================
    # LIMPIAR TÍTULO PARA MATCHING
    # ============================================================

    @staticmethod
    def _clean_title_for_matching(
        text
    ):
        """
        Elimina información secundaria del título
        que puede variar entre MusicBrainz y
        YouTube Music.

        Ejemplo:

            POWER (feat. X)

        se compara principalmente como:

            POWER
        """

        text = text.lower()

        # --------------------------------------------------------
        # feat / featuring
        # --------------------------------------------------------

        text = re.sub(
            r"\s*[\(\[]?\s*"
            r"(feat\.?|featuring)"
            r".*?$",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # --------------------------------------------------------
        # Información entre paréntesis
        # --------------------------------------------------------

        text = re.sub(
            r"\([^)]*\)",
            "",
            text,
        )

        # --------------------------------------------------------
        # Información entre corchetes
        # --------------------------------------------------------

        text = re.sub(
            r"\[[^\]]*\]",
            "",
            text,
        )

        # --------------------------------------------------------
        # Espacios
        # --------------------------------------------------------

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ============================================================
    # NORMALIZACIÓN
    # ============================================================

    @staticmethod
    def _normalize_text(
        text
    ):
        """
        Normaliza texto únicamente para comparación.

        NO modifica el texto original utilizado
        posteriormente para metadata.

        Corrige casos como:

            G‐DRAGON
            G-DRAGON

        y:

            PO￦ER
            POWER

        También normaliza:

            comillas Unicode
            guiones Unicode
            espacios especiales
            caracteres full-width
            mayúsculas/minúsculas
        """

        if text is None:

            return ""

        text = str(text)

        # --------------------------------------------------------
        # Unicode compatibility normalization
        # --------------------------------------------------------

        text = unicodedata.normalize(
            "NFKC",
            text,
        )

        # --------------------------------------------------------
        # Símbolos utilizados como W
        # --------------------------------------------------------

        text = (
            text
            .replace("￦", "W")
            .replace("₩", "W")
        )

        # --------------------------------------------------------
        # Guiones Unicode
        # --------------------------------------------------------

        dash_chars = (
            "‐",
            "-",
            "‒",
            "–",
            "—",
            "―",
            "−",
        )

        for char in dash_chars:

            text = text.replace(
                char,
                "-",
            )

        # --------------------------------------------------------
        # Comillas Unicode
        # --------------------------------------------------------

        quote_chars = (
            "‘",
            "’",
            "‚",
            "‛",
            "“",
            "”",
            "„",
            "‟",
            "´",
            "`",
        )

        for char in quote_chars:

            text = text.replace(
                char,
                "'",
            )

        # --------------------------------------------------------
        # Espacios Unicode
        # --------------------------------------------------------

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        # --------------------------------------------------------
        # Lowercase
        # --------------------------------------------------------

        text = text.lower()

        # --------------------------------------------------------
        # Eliminar espacios alrededor de puntuación
        # --------------------------------------------------------

        text = re.sub(
            r"\s*-\s*",
            "-",
            text,
        )

        # --------------------------------------------------------
        # Eliminar espacios duplicados
        # --------------------------------------------------------

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ============================================================
    # OBTENER DURACIÓN
    # ============================================================

    @staticmethod
    def _get_duration(
        result
    ):
        """
        Obtiene la duración de un resultado
        de YouTube Music.

        ytmusicapi puede devolver distintos
        formatos dependiendo de la versión.
        """

        duration = result.get(
            "duration"
        )

        if duration is None:

            return None

        if isinstance(
            duration,
            (int, float),
        ):

            return duration

        if isinstance(
            duration,
            str,
        ):

            return duration

        return None

    # ============================================================
    # CONVERTIR DURACIÓN
    # ============================================================

    @staticmethod
    def _duration_to_seconds(
        duration
    ):
        """
        Convierte:

            209
            "209"
            "3:29"
            "1:03:29"

        a segundos.
        """

        if duration is None:

            return None

        # --------------------------------------------------------
        # Número
        # --------------------------------------------------------

        if isinstance(
            duration,
            (int, float),
        ):

            return float(
                duration
            )

        # --------------------------------------------------------
        # String
        # --------------------------------------------------------

        if isinstance(
            duration,
            str,
        ):

            duration = duration.strip()

            if not duration:

                return None

            # Número como string

            try:

                return float(
                    duration
                )

            except ValueError:

                pass

            # Formato HH:MM:SS / MM:SS

            parts = duration.split(":")

            try:

                parts = [
                    int(part)
                    for part in parts
                ]

            except ValueError:

                return None

            if len(parts) == 2:

                minutes, seconds = parts

                return (
                    minutes * 60
                    + seconds
                )

            if len(parts) == 3:

                hours, minutes, seconds = (
                    parts
                )

                return (
                    hours * 3600
                    + minutes * 60
                    + seconds
                )

        return None

    # ============================================================
    # FORMATEAR DURACIÓN
    # ============================================================

    @staticmethod
    def _format_duration(
        duration
    ):
        """
        Convierte una duración a:

            209 -> 3:29
            "209" -> 3:29
            "3:29" -> 3:29
        """

        seconds = (
            YouTubeMusic
            ._duration_to_seconds(
                duration
            )
        )

        if seconds is None:

            return "N/A"

        seconds = int(
            seconds
        )

        minutes = (
            seconds // 60
        )

        remaining_seconds = (
            seconds % 60
        )

        return (
            f"{minutes}:"
            f"{remaining_seconds:02d}"
        )

    # ============================================================
    # IMPRIMIR CANDIDATO
    # ============================================================

    def _print_candidate(
        self,
        index,
        candidate,
    ):

        result = candidate[
            "result"
        ]

        details = candidate[
            "details"
        ]

        title = result.get(
            "title",
            "N/A",
        )

        artists = result.get(
            "artists",
            [],
        )

        artist_names = [
            item.get(
                "name",
                "",
            )
            for item in artists
        ]

        album_data = result.get(
            "album"
        )

        album = ""

        if album_data:

            album = album_data.get(
                "name",
                "",
            )

        duration = (
            self._get_duration(
                result
            )
        )

        print()

        print(
            f"#{index} "
            f"SCORE: "
            f"{candidate['score']}"
        )

        print(
            f"Título: "
            f"{title}"
        )

        print(
            f"Artista: "
            f"{artist_names}"
        )

        print(
            f"Álbum: "
            f"{album or 'N/A'}"
        )

        print(
            f"Duración: "
            f"{self._format_duration(duration)}"
        )

        print(
            f"Video ID: "
            f"{result.get('videoId')}"
        )

        print(
            "Detalles:"
        )

        print(
            "  artista exacto: "
            f"{details['artist_exact']}"
        )

        print(
            "  artista similar: "
            f"{details['artist_similar']:.2f}"
        )

        print(
            "  título exacto: "
            f"{details['title_exact']}"
        )

        print(
            "  título compatible: "
            f"{details['title_compatible']}"
        )

        print(
            "  título similar: "
            f"{details['title_similar']:.2f}"
        )

        print(
            "  álbum exacto: "
            f"{details['album_exact']}"
        )

        print(
            "  álbum similar: "
            f"{details['album_similar']:.2f}"
        )

        print(
            "  duración diferencia: "
            f"{details['duration_difference']}"
        )

        print(
            "  duración bonus: "
            f"{details['duration_bonus']}"
        )

        print(
            "  audio bonus: "
            f"{details['audio_bonus']}"
        )

        print(
            "  penalización versión: "
            f"{details['version_penalty']}"
        )