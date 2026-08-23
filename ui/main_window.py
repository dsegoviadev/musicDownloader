from PySide6.QtCore import (
    QSignalBlocker,
    Qt,
)

from PySide6.QtWidgets import (
    QApplication,
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
            600,
        )

        # -----------------------------
        # SERVICIOS
        # -----------------------------

        self.youtube_music = (
            YouTubeMusic()
        )

        self.downloader = Downloader(
            output_folder="downloads"
        )

        self.setup_ui()

    def setup_ui(self):

        central_widget = QWidget()

        main_layout = QVBoxLayout()

        central_widget.setLayout(
            main_layout
        )

        self.setCentralWidget(
            central_widget
        )

        # -----------------------------
        # TÍTULO
        # -----------------------------

        title = QLabel(
            "Music Downloader"
        )

        main_layout.addWidget(
            title
        )

        # -----------------------------
        # BUSCADOR
        # -----------------------------

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

        # -----------------------------
        # FORMATO
        # -----------------------------

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

        # -----------------------------
        # RESULTADOS
        # -----------------------------

        self.results_tree = (
            QTreeWidget()
        )

        self.results_tree.setHeaderLabels(
            ["Álbumes / Canciones"]
        )

        # Checkbox
        self.results_tree.itemChanged.connect(
            self.handle_item_changed
        )

        # Flecha / expansión
        self.results_tree.itemExpanded.connect(
            self.handle_item_expanded
        )

        main_layout.addWidget(
            self.results_tree
        )

        # -----------------------------
        # DESCARGAR
        # -----------------------------

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

        # -----------------------------
        # ESTADO
        # -----------------------------

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
                artist
            )

            self.results_tree.clear()

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

                # --------------------------------
                # Identificar como ÁLBUM
                # --------------------------------

                album.setData(
                    0,
                    Qt.UserRole,
                    "album",
                )

                # --------------------------------
                # Guardar MBID
                # --------------------------------

                album.setData(
                    0,
                    Qt.UserRole + 1,
                    album_data[
                        "release_group_mbid"
                    ],
                )

                # --------------------------------
                # Todavía no cargamos canciones
                # --------------------------------

                album.setData(
                    0,
                    Qt.UserRole + 2,
                    False,
                )

                # --------------------------------
                # Checkbox
                # --------------------------------

                album.setCheckState(
                    0,
                    Qt.Unchecked,
                )

                # --------------------------------
                # CHILD DUMMY
                #
                # Esto hace que Qt muestre
                # la flecha de expansión.
                # --------------------------------

                placeholder = QTreeWidgetItem(
                    album,
                    [
                        "Cargando canciones..."
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

        # Solo nos interesan álbumes
        if item_type != "album":
            return

        loaded = item.data(
            0,
            Qt.UserRole + 2,
        )

        # Ya cargado -> no hacemos otro request
        if loaded:
            return

        self.load_album_songs(
            item
        )

    # ==================================================
    # CARGAR CANCIONES DE UN ÁLBUM
    # ==================================================

    def load_album_songs(
        self,
        album,
    ):

        # --------------------------------
        # Ya cargado
        # --------------------------------

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

        print()
        print("=" * 60)

        print(
            f"Cargando canciones: "
            f"{album_name}"
        )

        print(
            f"Release Group: "
            f"{release_group_mbid}"
        )

        # --------------------------------
        # Mostrar estado
        # --------------------------------

        self.status_label.setText(
            f"Cargando canciones: "
            f"{album_name}..."
        )

        QApplication.processEvents()

        # --------------------------------
        # Request
        # --------------------------------

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

        # --------------------------------
        # No encontramos canciones
        # --------------------------------

        if not songs:

            print(
                "No se encontraron canciones."
            )

            self.status_label.setText(
                f"No se encontraron "
                f"canciones en {album_name}."
            )

            return False

        # --------------------------------
        # Eliminar placeholder
        # --------------------------------

        blocker = QSignalBlocker(
            self.results_tree
        )

        while album.childCount() > 0:

            child = album.takeChild(0)

            del child

        # --------------------------------
        # Crear canciones
        # --------------------------------

        for song_name in songs:

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

        # --------------------------------
        # Marcar como cargado
        # --------------------------------

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
            f"{len(songs)}"
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

        # ==================================================
        # PLACEHOLDER
        # ==================================================

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

            # --------------------------------
            # Si todavía no se expandió,
            # no hay canciones que seleccionar.
            #
            # Importante:
            # NO hacemos request aquí.
            # El request solamente ocurre
            # al abrir la flecha.
            # --------------------------------

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

            # --------------------------------
            # Estado parcial
            # --------------------------------

            if state == Qt.PartiallyChecked:
                return

            # --------------------------------
            # Propagar estado
            # a las canciones
            # --------------------------------

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
                    state,
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

        # --------------------------------
        # Determinar estado del álbum
        # --------------------------------

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

        # --------------------------------
        # Cambiar álbum sin disparar
        # nuevamente el evento
        # --------------------------------

        blocker = QSignalBlocker(
            self.results_tree
        )

        parent.setCheckState(
            0,
            parent_state,
        )

    # ==================================================
    # CANCIONES SELECCIONADAS
    # ==================================================

    def get_selected_songs(self):

        selected_songs = []

        artist = (
            self.artist_input
            .text()
            .strip()
        )

        for index in range(
            self.results_tree.topLevelItemCount()
        ):

            album = (
                self.results_tree
                .topLevelItem(index)
            )

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
                            "album": album.text(0),
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

        total = len(songs)

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
            print("=" * 60)

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

            # --------------------------------
            # YOUTUBE MUSIC
            # --------------------------------

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

            # --------------------------------
            # ARTISTA
            # --------------------------------

            result_artist = (
                result["artist"][0]
                if result["artist"]
                else song["artist"]
            )

            # --------------------------------
            # DESCARGA
            # --------------------------------

            self.status_label.setText(
                f"Descargando "
                f"{index}/{total}: "
                f"{result['title']}..."
            )

            QApplication.processEvents()

            try:

                file_path = (
                    self.downloader.download(
                        video_id=result[
                            "video_id"
                        ],
                        title=result[
                            "title"
                        ],
                        artist=result_artist,
                        album=result[
                            "album"
                        ],
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

        # --------------------------------
        # TERMINADO
        # --------------------------------

        self.download_button.setEnabled(
            True
        )

        self.search_button.setEnabled(
            True
        )

        self.format_selector.setEnabled(
            True
        )

        self.status_label.setText(
            "Descargas terminadas."
        )