from services.ytmusic import YouTubeMusic
from services.downloader import Downloader


# --------------------------------------------------
# CANCIÓN
# --------------------------------------------------

ARTIST = "Limp bizkit"
TITLE = "Hot dog"
ALBUM = "Chocolate starfish"


# --------------------------------------------------
# FORMATO
# --------------------------------------------------

FORMAT = "mp3"


# --------------------------------------------------
# BUSCAR EN YOUTUBE MUSIC
# --------------------------------------------------

print("Inicializando YouTube Music...")

ytmusic = YouTubeMusic()

print("Conectado.")
print()

print(
    f"Buscando: {ARTIST} - {TITLE}"
)

print()


result = ytmusic.search_song(
    artist=ARTIST,
    title=TITLE,
    album=ALBUM,
)


if result is None:

    print(
        "No encontramos una "
        "coincidencia exacta."
    )

    exit()


print("Canción encontrada:")
print()

print(
    f"Título: {result['title']}"
)

print(
    f"Artista: {result['artist']}"
)

print(
    f"Álbum: {result['album']}"
)

print(
    f"Duración: {result['duration']}"
)

print(
    f"Video ID: {result['video_id']}"
)

print()


# --------------------------------------------------
# DESCARGAR
# --------------------------------------------------

print(
    f"Formato seleccionado: {FORMAT.upper()}"
)

print()

print("Iniciando descarga...")


downloader = Downloader(
    output_folder="downloads"
)


artist_name = result["artist"][0]


file_path = downloader.download(
    video_id=result["video_id"],
    title=result["title"],
    artist=artist_name,
    album=result["album"],
    format_name=FORMAT,
)


print()
print("Descarga terminada.")
print()
print(f"Archivo: {file_path}")