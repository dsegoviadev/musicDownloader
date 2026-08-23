from pathlib import Path

import yt_dlp

from mutagen.flac import FLAC, Picture
from mutagen.id3 import (
    APIC,
    TALB,
    TIT2,
    TPE1,
)
from mutagen.mp3 import MP3


class Downloader:

    def __init__(
        self,
        output_folder="downloads",
    ):
        self.output_folder = Path(
            output_folder
        )

        self.output_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ==================================================
    # DESCARGAR
    # ==================================================

    def download(
        self,
        video_id,
        title,
        artist,
        album,
        format_name="mp3",
    ):

        # ---------------------------------------------
        # LIMPIAR DATOS
        # ---------------------------------------------

        artist = self._sanitize_filename(
            artist
        )

        album = self._sanitize_filename(
            album
        )

        title = self._sanitize_filename(
            title
        )

        format_name = format_name.lower()

        # ---------------------------------------------
        # CARPETA:
        #
        # downloads/
        # └── artista/
        #     └── album/
        #         └── canción.ext
        # ---------------------------------------------

        album_folder = (
            self.output_folder
            / artist
            / album
        )

        album_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ---------------------------------------------
        # ARCHIVO FINAL
        # ---------------------------------------------

        file_path = (
            album_folder
            / f"{title}.{format_name}"
        )

        # ---------------------------------------------
        # EVITAR DESCARGAR DUPLICADOS
        # ---------------------------------------------

        if file_path.exists():

            print()
            print(
                "La canción ya existe:"
            )

            print(
                file_path
            )

            print(
                "Saltando descarga."
            )

            return file_path

        # ---------------------------------------------
        # URL YOUTUBE MUSIC
        # ---------------------------------------------

        url = (
            "https://music.youtube.com/watch"
            f"?v={video_id}"
        )

        # ---------------------------------------------
        # TEMPLATE DE YT-DLP
        # ---------------------------------------------

        output_template = str(
            album_folder
            / f"{title}.%(ext)s"
        )

        # ---------------------------------------------
        # POSTPROCESSORS
        # ---------------------------------------------

        if format_name == "mp3":

            postprocessors = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ]

        elif format_name == "flac":

            postprocessors = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "flac",
                }
            ]

        else:

            raise ValueError(
                f"Formato no soportado: "
                f"{format_name}"
            )

        # ---------------------------------------------
        # OPCIONES YT-DLP
        # ---------------------------------------------

        options = {

            "format": "bestaudio/best",

            "outtmpl": output_template,

            "postprocessors": postprocessors,

            # Descargar portada
            "writethumbnail": True,

            # No seguir playlists
            "noplaylist": True,

            "quiet": False,

            "no_warnings": False,
        }

        # ---------------------------------------------
        # DESCARGAR
        # ---------------------------------------------

        print()
        print(
            "Descargando:"
        )

        print(
            f"{artist} - "
            f"{title}"
        )

        print(
            f"Álbum: {album}"
        )

        print(
            f"Formato: "
            f"{format_name.upper()}"
        )

        print(
            f"Destino: "
            f"{file_path}"
        )

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download(
                [url]
            )

        # ---------------------------------------------
        # BUSCAR PORTADA
        # ---------------------------------------------

        thumbnail_path = (
            self._find_thumbnail(
                album_folder,
                title,
            )
        )

        # ---------------------------------------------
        # METADATA
        # ---------------------------------------------

        self._add_metadata(
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            title=title,
            artist=artist,
            album=album,
            format_name=format_name,
        )

        # ---------------------------------------------
        # ELIMINAR PORTADA TEMPORAL
        # ---------------------------------------------

        if (
            thumbnail_path
            and thumbnail_path.exists()
        ):

            thumbnail_path.unlink()

        return file_path

    # ==================================================
    # BUSCAR PORTADA
    # ==================================================

    def _find_thumbnail(
        self,
        album_folder,
        title,
    ):

        base_name = (
            album_folder
            / title
        )

        extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        ]

        for extension in extensions:

            path = (
                base_name.with_suffix(
                    extension
                )
            )

            if path.exists():

                return path

        return None

    # ==================================================
    # METADATA
    # ==================================================

    def _add_metadata(
        self,
        file_path,
        thumbnail_path,
        title,
        artist,
        album,
        format_name,
    ):

        if not file_path.exists():

            raise FileNotFoundError(
                f"No se encontró: "
                f"{file_path}"
            )

        if format_name == "mp3":

            self._add_mp3_metadata(
                file_path,
                thumbnail_path,
                title,
                artist,
                album,
            )

        elif format_name == "flac":

            self._add_flac_metadata(
                file_path,
                thumbnail_path,
                title,
                artist,
                album,
            )

    # ==================================================
    # MP3 METADATA
    # ==================================================

    def _add_mp3_metadata(
        self,
        file_path,
        thumbnail_path,
        title,
        artist,
        album,
    ):

        audio = MP3(
            file_path
        )

        if audio.tags is None:

            audio.add_tags()

        # ---------------------------------------------
        # TÍTULO
        # ---------------------------------------------

        audio.tags.add(
            TIT2(
                encoding=3,
                text=title,
            )
        )

        # ---------------------------------------------
        # ARTISTA
        # ---------------------------------------------

        audio.tags.add(
            TPE1(
                encoding=3,
                text=artist,
            )
        )

        # ---------------------------------------------
        # ÁLBUM
        # ---------------------------------------------

        audio.tags.add(
            TALB(
                encoding=3,
                text=album,
            )
        )

        # ---------------------------------------------
        # PORTADA
        # ---------------------------------------------

        if thumbnail_path:

            with open(
                thumbnail_path,
                "rb",
            ) as image:

                image_data = (
                    image.read()
                )

            audio.tags.add(
                APIC(
                    encoding=3,
                    mime=self._get_mime_type(
                        thumbnail_path
                    ),
                    type=3,
                    desc="Cover",
                    data=image_data,
                )
            )

        audio.save()

    # ==================================================
    # FLAC METADATA
    # ==================================================

    def _add_flac_metadata(
        self,
        file_path,
        thumbnail_path,
        title,
        artist,
        album,
    ):

        audio = FLAC(
            file_path
        )

        # ---------------------------------------------
        # METADATA
        # ---------------------------------------------

        audio["title"] = title

        audio["artist"] = artist

        audio["album"] = album

        # ---------------------------------------------
        # PORTADA
        # ---------------------------------------------

        if thumbnail_path:

            with open(
                thumbnail_path,
                "rb",
            ) as image:

                image_data = (
                    image.read()
                )

            picture = Picture()

            picture.type = 3

            picture.mime = (
                self._get_mime_type(
                    thumbnail_path
                )
            )

            picture.desc = "Cover"

            picture.data = image_data

            # Eliminar portadas anteriores
            audio.clear_pictures()

            audio.add_picture(
                picture
            )

        audio.save()

    # ==================================================
    # MIME TYPE
    # ==================================================

    @staticmethod
    def _get_mime_type(
        path
    ):

        suffix = (
            path.suffix.lower()
        )

        if suffix in (
            ".jpg",
            ".jpeg",
        ):

            return "image/jpeg"

        if suffix == ".png":

            return "image/png"

        if suffix == ".webp":

            return "image/webp"

        return "image/jpeg"

    # ==================================================
    # SANITIZAR NOMBRES
    # ==================================================

    @staticmethod
    def _sanitize_filename(
        name
    ):

        if not name:
            return "Unknown"

        invalid_chars = (
            '<>:"/\\|?*'
        )

        for char in invalid_chars:

            name = name.replace(
                char,
                "_",
            )

        return name.strip()

