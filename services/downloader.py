from pathlib import Path

import yt_dlp

from mutagen.flac import (
    FLAC,
    Picture,
)

from mutagen.id3 import (
    APIC,
    TALB,
    TIT2,
    TPE1,
)

from mutagen.mp3 import (
    MP3,
)


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

        url = (
            "https://music.youtube.com/watch"
            f"?v={video_id}"
        )

        extension = (
            format_name.lower()
        )

        # --------------------------------
        # ESTRUCTURA
        #
        # downloads/
        #   artista/
        #       album/
        #           canción
        # --------------------------------

        album_folder = (
            self.output_folder
            / self._sanitize_name(
                artist
            )
            / self._sanitize_name(
                album
            )
        )

        album_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_template = str(
            album_folder
            / f"{self._sanitize_name(title)}.%(ext)s"
        )

        # ==================================================
        # POSTPROCESSORS
        # ==================================================

        if extension == "mp3":

            postprocessors = [
                {
                    "key":
                        "FFmpegExtractAudio",

                    "preferredcodec":
                        "mp3",

                    "preferredquality":
                        "320",
                }
            ]

        elif extension == "flac":

            postprocessors = [
                {
                    "key":
                        "FFmpegExtractAudio",

                    "preferredcodec":
                        "flac",
                }
            ]

        else:

            raise ValueError(
                f"Formato no soportado: "
                f"{format_name}"
            )

        # ==================================================
        # YT-DLP
        # ==================================================

        options = {

            "format":
                "bestaudio/best",

            "outtmpl":
                output_template,

            "postprocessors":
                postprocessors,

            "writethumbnail":
                True,

            "noplaylist":
                True,

            "quiet":
                False,

            "no_warnings":
                False,
        }

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            ydl.download(
                [url]
            )

        # ==================================================
        # ARCHIVO FINAL
        # ==================================================

        file_path = (
            album_folder
            / f"{self._sanitize_name(title)}.{extension}"
        )

        # ==================================================
        # PORTADA
        # ==================================================

        thumbnail_path = (
            self._find_thumbnail(
                album_folder,
                title,
            )
        )

        # ==================================================
        # METADATA
        # ==================================================

        self._add_metadata(
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            title=title,
            artist=artist,
            album=album,
            format_name=extension,
        )

        # --------------------------------
        # No eliminamos aquí el WebP.
        #
        # La limpieza se hace al final
        # del lote completo.
        # --------------------------------

        return file_path

    # ==================================================
    # BUSCAR THUMBNAIL
    # ==================================================

    def _find_thumbnail(
        self,
        folder,
        title,
    ):

        base_name = (
            folder
            / self._sanitize_name(
                title
            )
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
    # LIMPIAR WEBP
    # ==================================================

    def cleanup_webp(self):
        """
        Elimina todos los archivos .webp
        dentro de la carpeta de descargas.

        Se llama al terminar todo el lote.
        """

        removed = 0

        if not self.output_folder.exists():
            return removed

        for path in self.output_folder.rglob(
            "*.webp"
        ):

            try:

                path.unlink()

                removed += 1

                print(
                    f"WebP eliminado: "
                    f"{path}"
                )

            except OSError as error:

                print(
                    f"No se pudo eliminar "
                    f"{path}: {error}"
                )

        return removed

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

        audio.tags.add(
            TIT2(
                encoding=3,
                text=title,
            )
        )

        audio.tags.add(
            TPE1(
                encoding=3,
                text=artist,
            )
        )

        audio.tags.add(
            TALB(
                encoding=3,
                text=album,
            )
        )

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

        audio["title"] = title

        audio["artist"] = artist

        audio["album"] = album

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
    def _sanitize_name(
        name
    ):
        """
        Limpia caracteres que pueden
        romper nombres de archivos/directorios.
        """

        invalid_chars = (
            '<>:"/\\|?*'
        )

        cleaned = "".join(
            "_"
            if char in invalid_chars
            else char
            for char in name
        )

        cleaned = (
            cleaned
            .strip()
            .rstrip(".")
        )

        return (
            cleaned
            if cleaned
            else "Unknown"
        )