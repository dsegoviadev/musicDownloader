from pathlib import Path

from PySide6.QtCore import (
    QSignalBlocker,
    Qt,
)

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.musicbrainz import (
    search_artist as fetch_artist,
    get_album_tracks,
)

from services.ytmusic import (
    YouTubeMusic,
)

from services.downloader import (
    Downloader,
)


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "Music Downloader"
        )

        self.resize(
            900,
            650,
        )

        # ==================================================
        # SERVICIOS
        # ==================================================

        self.youtube_music = (
            YouTubeMusic()
        )

        self.downloader = Downloader(
            output_folder="downloads"
        )

        self.current_artist_name = ""

        self.setup_ui()

    # ==================================================
    # UI
    # ==================================================

    def setup_ui(self):

        central_widget = QWidget()

        main_layout = QVBoxLayout()

        central_widget.setLayout(
            main_layout
        )

        self.setCentralWidget(
            central_widget
        )

        # ==================================================
        # TÍTULO
        # ==================================================

        title = QLabel(
            "Music Downloader"
        )

        main_layout.addWidget(
            title
        )

        # ==================================================
        # BUSCADOR
        # ==================================================

        search_layout = QHBoxLayout()

        self.artist_input = QLineEdit()

        self.artist_input.setPlaceholderText(
            "Escribe un artista..."
        )

        self.search_button = QPushButton(
            "Buscar"
        )

        self.search_button.clicked.connect(
            self.search_artist
        )

        search_layout.addWidget(
            self.artist_input
        )

        search_layout.addWidget(
            self.search_button
        )

        main_layout.addLayout(
            search_layout
        )

        # ==================================================
        # FORMATO
        # ==================================================

        format_layout = QHBoxLayout()

        format_label = QLabel(
            "Formato:"
        )

        self.format_selector = (
            QComboBox()
        )

        self.format_selector.addItem(
            "MP3 320 kbps",
            "mp3",
        )

        self.format_selector.addItem(
            "FLAC",
            "flac",
        )

        format_layout.addWidget(
            format_label
        )

        format_layout.addWidget(
            self.format_selector
        )

        format_layout.addStretch()

        main_layout.addLayout(
            format_layout
        )

        # ==================================================
        # TIPOS DE RELEASE
        # ==================================================

        release_type_label = QLabel(
            "Incluir:"
        )

        main_layout.addWidget(
            release_type_label
        )

        release_type_layout = QHBoxLayout()

        self.album_checkbox = QCheckBox(
            "Álbumes"
        )

        self.single_checkbox = QCheckBox(
            "Singles"
        )

        self.ep_checkbox = QCheckBox(
            "EPs"
        )

        self.live_checkbox = QCheckBox(
            "Lives"
        )

        # ==================================================
        # DEFAULTS
        # ==================================================

        self.album_checkbox.setChecked(
            True
        )

        self.single_checkbox.setChecked(
            False
        )

        self.ep_checkbox.setChecked(
            False
        )

        self.live_checkbox.setChecked(
            False
        )

        release_type_layout.addWidget(
            self.album_checkbox
        )

        release_type_layout.addWidget(
            self.single_checkbox
        )

        release_type_layout.addWidget(
            self.ep_checkbox
        )

        release_type_layout.addWidget(
            self.live_checkbox
        )

        release_type_layout.addStretch()

        main_layout.addLayout(
            release_type_layout
        )

        # ==================================================
        # RESULTADOS
        # ==================================================

        self.results_tree = (
            QTreeWidget()
        )

        self.results_tree.setHeaderLabels(
            ["Álbumes / Canciones"]
        )

        self.results_tree.itemChanged.connect(
            self.handle_item_changed
        )

        self.results_tree.itemExpanded.connect(
            self.handle_item_expanded
        )

        main_layout.addWidget(
            self.results_tree
        )

        # ==================================================
        # DESCARGAR
        # ==================================================

        self.download_button = (
            QPushButton(
                "Descargar seleccionadas"
            )
        )

        self.download_button.clicked.connect(
            self.download_selected_songs
        )

        main_layout.addWidget(
            self.download_button
        )

        # ==================================================
        # ESTADO
        # ==================================================

        self.status_label = QLabel(
            "Listo."
        )

        main_layout.addWidget(
            self.status_label
        )

    # ==================================================
    # BUSCAR ARTISTA
    # ==================================================

    def search_artist(self):

        artist = (
            self.artist_input
            .text()
            .strip()
        )

        if not artist:
            return

        include_types = []

        if self.album_checkbox.isChecked():

            include_types.append(
                "album"
            )

        if self.single_checkbox.isChecked():

            include_types.append(
                "single"
            )

        if self.ep_checkbox.isChecked():

            include_types.append(
                "ep"
            )

        if self.live_checkbox.isChecked():

            include_types.append(
                "live"
            )

        if not include_types:

            self.status_label.setText(
                "Selecciona al menos "
                "un tipo de release."
            )

            return

        self.status_label.setText(
            "Cargando álbumes..."
        )

        QApplication.processEvents()

        self.search_button.setEnabled(
            False
        )

        self.download_button.setEnabled(
            False
        )

        try:

            result = fetch_artist(
                artist,
                include_types=include_types,
            )

            self.results_tree.clear()

            # ==================================================
            # ARTISTA REAL DE MUSICBRAINZ
            # ==================================================

            self.current_artist_name = (
                result.get(
                    "artist",
                    artist,
                )
            )

            # ==================================================
            # ÁLBUMES
            # ==================================================

            for album_data in result.get(
                "albums",
                []
            ):

                album = QTreeWidgetItem(
                    self.results_tree,
                    [
                        album_data["name"]
                    ],
                )

                # Tipo de nodo

                album.setData(
                    0,
                    Qt.UserRole,
                    "album",
                )

                # MBID

                album.setData(
                    0,
                    Qt.UserRole + 1,
                    album_data[
                        "release_group_mbid"
                    ],
                )

                # Tipo de release

                album.setData(
                    0,
                    Qt.UserRole + 3,
                    album_data.get(
                        "type",
                        "album",
                    ),
                )

                # Canciones aún no cargadas

                album.setData(
                    0,
                    Qt.UserRole + 2,
                    False,
                )

                # Checkbox

                album.setCheckState(
                    0,
                    Qt.Unchecked,
                )

                # Placeholder

                placeholder = QTreeWidgetItem(
                    album,
                    [
                        "Expandir para "
                        "cargar canciones..."
                    ],
                )

                placeholder.setData(
                    0,
                    Qt.UserRole,
                    "placeholder",
                )

            self.status_label.setText(
                "Álbumes cargados."
            )

        except Exception as error:

            print()
            print(
                "ERROR buscando artista:"
            )

            print(error)

            self.status_label.setText(
                "Error al cargar álbumes."
            )

        finally:

            self.search_button.setEnabled(
                True
            )

            self.download_button.setEnabled(
                True
            )

    # ==================================================
    # EXPANDIR ÁLBUM
    # ==================================================

    def handle_item_expanded(
        self,
        item,
    ):

        item_type = item.data(
            0,
            Qt.UserRole,
        )

        if item_type != "album":
            return

        loaded = item.data(
            0,
            Qt.UserRole + 2,
        )

        if loaded:
            return

        self.load_album_songs(
            item
        )

    # ==================================================
    # CARGAR CANCIONES
    # ==================================================

    def load_album_songs(
        self,
        album,
    ):

        loaded = album.data(
            0,
            Qt.UserRole + 2,
        )

        if loaded:
            return True

        release_group_mbid = album.data(
            0,
            Qt.UserRole + 1,
        )

        if not release_group_mbid:
            return False

        album_name = album.text(0)

        self.status_label.setText(
            f"Cargando canciones: "
            f"{album_name}..."
        )

        QApplication.processEvents()

        try:

            songs = get_album_tracks(
                release_group_mbid
            )

        except Exception as error:

            print()
            print(
                "ERROR cargando canciones:"
            )

            print(error)

            self.status_label.setText(
                f"Error cargando canciones "
                f"de {album_name}."
            )

            return False

        if not songs:

            self.status_label.setText(
                f"No se encontraron "
                f"canciones en {album_name}."
            )

            return False

        blocker = QSignalBlocker(
            self.results_tree
        )

        while album.childCount() > 0:

            child = album.takeChild(0)

            del child

        # ==================================================
        # CANCIONES
        # ==================================================

        for song_data in songs:

            if isinstance(
                song_data,
                dict,
            ):

                song_name = song_data.get(
                    "title",
                    "",
                )

            else:

                song_name = song_data

            if not song_name:
                continue

            song = QTreeWidgetItem(
                album,
                [song_name],
            )

            song.setData(
                0,
                Qt.UserRole,
                "song",
            )

            song.setCheckState(
                0,
                Qt.Unchecked,
            )

        album.setData(
            0,
            Qt.UserRole + 2,
            True,
        )

        self.status_label.setText(
            f"Canciones cargadas: "
            f"{album_name}"
        )

        print(
            f"Canciones encontradas: "
            f"{album.childCount()}"
        )

        return True

    # ==================================================
    # CHECKBOXES
    # ==================================================

    def handle_item_changed(
        self,
        item,
        column,
    ):

        if column != 0:
            return

        item_type = item.data(
            0,
            Qt.UserRole,
        )

        state = item.checkState(0)

        if item_type == "placeholder":
            return

        # ==================================================
        # ÁLBUM
        # ==================================================

        if item_type == "album":

            loaded = item.data(
                0,
                Qt.UserRole + 2,
            )

            if not loaded:

                blocker = QSignalBlocker(
                    self.results_tree
                )

                item.setCheckState(
                    0,
                    Qt.Unchecked,
                )

                self.status_label.setText(
                    "Abre el álbum para "
                    "cargar sus canciones."
                )

                return

            if state == Qt.PartiallyChecked:
                return

            blocker = QSignalBlocker(
                self.results_tree
            )

            for index in range(
                item.childCount()
            ):

                child = item.child(
                    index
                )

                child.setCheckState(
                    0,
                    state
                )

            return

        # ==================================================
        # CANCIÓN
        # ==================================================

        if item_type != "song":
            return

        parent = item.parent()

        if parent is None:
            return

        checked_children = 0

        total_children = (
            parent.childCount()
        )

        for index in range(
            total_children
        ):

            child = parent.child(
                index
            )

            if (
                child.checkState(0)
                == Qt.Checked
            ):

                checked_children += 1

        if (
            checked_children
            == total_children
        ):

            parent_state = Qt.Checked

        elif checked_children == 0:

            parent_state = Qt.Unchecked

        else:

            parent_state = (
                Qt.PartiallyChecked
            )

        blocker = QSignalBlocker(
            self.results_tree
        )

        parent.setCheckState(
            0,
            parent_state
        )

    # ==================================================
    # CANCIONES SELECCIONADAS
    # ==================================================

    def get_selected_songs(self):

        selected_songs = []

        # ==================================================
        # MUSICBRAINZ ES LA FUENTE DE VERDAD
        # ==================================================

        artist = getattr(
            self,
            "current_artist_name",
            self.artist_input.text().strip(),
        )

        for index in range(
            self.results_tree.topLevelItemCount()
        ):

            album = (
                self.results_tree
                .topLevelItem(index)
            )

            album_name = album.text(0)

            for child_index in range(
                album.childCount()
            ):

                song = album.child(
                    child_index
                )

                if (
                    song.data(
                        0,
                        Qt.UserRole,
                    )
                    != "song"
                ):
                    continue

                if (
                    song.checkState(0)
                    == Qt.Checked
                ):

                    selected_songs.append(
                        {
                            "artist": artist,
                            "album": album_name,
                            "title": song.text(0),
                        }
                    )

        return selected_songs

    # ==================================================
    # DESCARGAR
    # ==================================================

    def download_selected_songs(
        self
    ):

        songs = (
            self.get_selected_songs()
        )

        if not songs:

            self.status_label.setText(
                "Selecciona al menos "
                "una canción."
            )

            return

        format_name = (
            self.format_selector
            .currentData()
        )

        self.download_button.setEnabled(
            False
        )

        self.search_button.setEnabled(
            False
        )

        self.format_selector.setEnabled(
            False
        )

        self.album_checkbox.setEnabled(
            False
        )

        self.single_checkbox.setEnabled(
            False
        )

        self.ep_checkbox.setEnabled(
            False
        )

        self.live_checkbox.setEnabled(
            False
        )

        total = len(songs)

        try:

            for index, song in enumerate(
                songs,
                start=1,
            ):

                self.status_label.setText(
                    f"Cargando canción "
                    f"{index}/{total}..."
                )

                QApplication.processEvents()

                print()
                print(
                    "=" * 60
                )

                print(
                    f"Procesando "
                    f"{index}/{total}"
                )

                print(
                    f"{song['artist']} - "
                    f"{song['title']}"
                )

                print(
                    f"Álbum: "
                    f"{song['album']}"
                )

                print(
                    f"Formato: "
                    f"{format_name.upper()}"
                )

                # ==================================================
                # YOUTUBE MUSIC
                #
                # IMPORTANTE:
                #
                # YouTube Music solamente decide qué VIDEO
                # descargar.
                #
                # NO decide el artista ni el álbum donde
                # se guardará.
                # ==================================================

                result = (
                    self.youtube_music
                    .search_song(
                        artist=song["artist"],
                        title=song["title"],
                        album=song["album"],
                    )
                )

                if result is None:

                    print(
                        "No se encontró "
                        "la canción."
                    )

                    continue

                # ==================================================
                # INFORMACIÓN ENCONTRADA
                # ==================================================

                print()
                print(
                    "Resultado seleccionado:"
                )

                print(
                    f"Título YT: "
                    f"{result['title']}"
                )

                print(
                    f"Artista YT: "
                    f"{result['artist']}"
                )

                print(
                    f"Álbum YT: "
                    f"{result['album']}"
                )

                print(
                    f"Video ID: "
                    f"{result['video_id']}"
                )

                # ==================================================
                # IMPORTANTE
                #
                # Para el Downloader usamos:
                #
                # artist = MusicBrainz
                # album  = MusicBrainz
                # title  = MusicBrainz
                #
                # y únicamente:
                #
                # video_id = YouTube Music
                #
                # Esto evita que un resultado de YouTube que
                # aparezca como "Single" cambie nuestra estructura.
                # ==================================================

                download_artist = song[
                    "artist"
                ]

                download_album = song[
                    "album"
                ]

                download_title = song[
                    "title"
                ]

                print()
                print(
                    "Metadata final:"
                )

                print(
                    f"Artista: "
                    f"{download_artist}"
                )

                print(
                    f"Álbum: "
                    f"{download_album}"
                )

                print(
                    f"Título: "
                    f"{download_title}"
                )

                # ==================================================
                # DESCARGAR
                # ==================================================

                self.status_label.setText(
                    f"Descargando "
                    f"{index}/{total}: "
                    f"{download_title}..."
                )

                QApplication.processEvents()

                try:

                    file_path = (
                        self.downloader.download(
                            video_id=result[
                                "video_id"
                            ],

                            # -----------------------------
                            # MUSICBRAINZ
                            # -----------------------------

                            title=download_title,

                            artist=download_artist,

                            album=download_album,

                            format_name=format_name,
                        )
                    )

                    print()
                    print(
                        "Descarga completada:"
                    )

                    print(
                        file_path
                    )

                except Exception as error:

                    print()
                    print(
                        "ERROR:"
                    )

                    print(error)

            # ==================================================
            # LIMPIEZA FINAL
            # ==================================================

            self.status_label.setText(
                "Limpiando archivos temporales..."
            )

            QApplication.processEvents()

            removed = (
                self.downloader
                .cleanup_webp()
            )

            print()
            print(
                f"WebP eliminados: {removed}"
            )

            self.status_label.setText(
                "Descargas terminadas."
            )

        finally:

            self.download_button.setEnabled(
                True
            )

            self.search_button.setEnabled(
                True
            )

            self.format_selector.setEnabled(
                True
            )

            self.album_checkbox.setEnabled(
                True
            )

            self.single_checkbox.setEnabled(
                True
            )

            self.ep_checkbox.setEnabled(
                True
            )

            self.live_checkbox.setEnabled(
                True
            )