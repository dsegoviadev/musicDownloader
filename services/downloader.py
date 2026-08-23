from pathlib import Path

import yt_dlp
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, TALB, TIT2, TPE1
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

        extension = format_name.lower()

        output_template = str(
            self.output_folder
            / f"{artist} - {title}.%(ext)s"
        )

        if extension == "mp3":

            postprocessors = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ]

        elif extension == "flac":

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

        options = {
            "format": "bestaudio/best",

            "outtmpl": output_template,

            "postprocessors": postprocessors,

            "writethumbnail": True,

            "noplaylist": True,

            "quiet": False,

            "no_warnings": False,
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])

        file_path = (
            self.output_folder
            / f"{artist} - {title}.{extension}"
        )

        thumbnail_path = (
            self._find_thumbnail(
                artist,
                title,
            )
        )

        self._add_metadata(
            file_path=file_path,
            thumbnail_path=thumbnail_path,
            title=title,
            artist=artist,
            album=album,
            format_name=extension,
        )

        if (
            thumbnail_path
            and thumbnail_path.exists()
        ):
            thumbnail_path.unlink()

        return file_path

    def _find_thumbnail(
        self,
        artist,
        title,
    ):

        base_name = (
            self.output_folder
            / f"{artist} - {title}"
        )

        extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        ]

        for extension in extensions:

            path = base_name.with_suffix(
                extension
            )

            if path.exists():
                return path

        return None

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

    def _add_mp3_metadata(
        self,
        file_path,
        thumbnail_path,
        title,
        artist,
        album,
    ):

        audio = MP3(file_path)

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

                image_data = image.read()

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

    def _add_flac_metadata(
        self,
        file_path,
        thumbnail_path,
        title,
        artist,
        album,
    ):

        audio = FLAC(file_path)

        audio["title"] = title
        audio["artist"] = artist
        audio["album"] = album

        if thumbnail_path:

            with open(
                thumbnail_path,
                "rb",
            ) as image:

                image_data = image.read()

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

    @staticmethod
    def _get_mime_type(path):

        suffix = path.suffix.lower()

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