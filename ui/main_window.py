from PySide6.QtCore import (
    QObject,
    QSignalBlocker,
    QThread,
    Qt,
    Signal,
)

from PySide6.QtWidgets import (
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


class AlbumTracksWorker(QObject):

    finished = Signal(object, object)
    failed = Signal(object, object, str)

    def __init__(
        self,
        album_mbid,
        album_name,
    ):
        super().__init__()

        self.album_mbid = album_mbid
        self.album_name = album_name

    def run(self):

        try:
            songs = get_album_tracks(
                self.album_mbid
            )

            self.finished.emit(
                self.album_mbid,
                songs,
            )

        except Exception as error:

            self.failed.emit(
                self.album_mbid,
                self.album_name,
                str(error),
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

        self.youtube_music = (
            YouTubeMusic()
        )

        self.downloader = Downloader(
            output_folder="downloads"
        )

        self.current_artist_name = ""

        self.album_threads = {}
        self.album_workers = {}
        self.pending_album_states = {}

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

        title = QLabel(
            "Music Downloader"
        )

        main_layout.addWidget(
            title
        )

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

        self.results_tree = QTreeWidget()

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

        self.download_button = QPushButton(
            "Descargar seleccionadas"
        )

        self.download_button.clicked.connect(
            self.download_selected_songs
        )

        main_layout.addWidget(
            self.download_button
        )

        self.status_label = QLabel(
            "Listo."
        )

        main_layout.addWidget(
            self.status_label
        )

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

            self.pending_album_states.clear()

            self.current_artist_name = (
                result.get(
                    "artist",
                    artist,
                )
            )

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

                album.setData(
                    0,
                    Qt.UserRole,
                    "album",
                )

                album.setData(
                    0,
                    Qt.UserRole + 1,
                    album_data[
                        "release_group_mbid"
                    ],
                )

                album.setData(
                    0,
                    Qt.UserRole + 3,
                    album_data.get(
                        "type",
                        "album",
                    ),
                )

                album.setData(
                    0,
                    Qt.UserRole + 2,
                    False,
                )

                album.setCheckState(
                    0,
                    Qt.Unchecked,
                )

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

        if release_group_mbid in self.album_threads:
            return True

        album_name = album.text(0)

        self.status_label.setText(
            f"Cargando canciones: "
            f"{album_name}..."
        )

        self.pending_album_states[
            release_group_mbid
        ] = (
            album.checkState(0)
            == Qt.Checked
        )

        thread = QThread(
            self
        )

        worker = AlbumTracksWorker(
            release_group_mbid,
            album_name,
        )

        worker.moveToThread(
            thread
        )

        thread.started.connect(
            worker.run
        )

        worker.finished.connect(
            self.album_tracks_loaded
        )

        worker.failed.connect(
            self.album_tracks_failed
        )

        worker.finished.connect(
            thread.quit
        )

        worker.failed.connect(
            thread.quit
        )

        worker.finished.connect(
            worker.deleteLater
        )

        worker.failed.connect(
            worker.deleteLater
        )

        thread.finished.connect(
            thread.deleteLater
        )

        thread.finished.connect(
            lambda mbid=release_group_mbid:
            self.cleanup_album_worker(
                mbid
            )
        )

        self.album_threads[
            release_group_mbid
        ] = thread

        self.album_workers[
            release_group_mbid
        ] = worker

        thread.start()

        return True

    def album_tracks_loaded(
        self,
        release_group_mbid,
        songs,
    ):

        album = self.find_album_by_mbid(
            release_group_mbid
        )

        if album is None:
            return

        album_name = album.text(0)

        if not songs:

            self.status_label.setText(
                f"No se encontraron "
                f"canciones en {album_name}."
            )

            return

        should_check = (
            self.pending_album_states.get(
                release_group_mbid,
                False,
            )
        )

        blocker = QSignalBlocker(
            self.results_tree
        )

        while album.childCount() > 0:

            child = album.takeChild(0)

            del child

        valid_song_count = 0

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
                Qt.Checked
                if should_check
                else Qt.Unchecked,
            )

            valid_song_count += 1

        album.setData(
            0,
            Qt.UserRole + 2,
            True,
        )

        album.setCheckState(
            0,
            Qt.Checked
            if should_check
            else Qt.Unchecked,
        )

        del blocker

        self.status_label.setText(
            f"Canciones cargadas: "
            f"{album_name}"
        )

        print()
        print(
            f"Canciones encontradas: "
            f"{valid_song_count}"
        )

    def album_tracks_failed(
        self,
        release_group_mbid,
        album_name,
        error,
    ):

        print()
        print(
            "ERROR cargando canciones:"
        )

        print(error)

        self.status_label.setText(
            f"Error cargando canciones "
            f"de {album_name}."
        )

    def cleanup_album_worker(
        self,
        release_group_mbid,
    ):

        thread = self.album_threads.pop(
            release_group_mbid,
            None,
        )

        self.album_workers.pop(
            release_group_mbid,
            None,
        )

        self.pending_album_states.pop(
            release_group_mbid,
            None,
        )

        if thread is not None:

            thread.deleteLater()

    def find_album_by_mbid(
        self,
        release_group_mbid,
    ):

        for index in range(
            self.results_tree.topLevelItemCount()
        ):

            album = (
                self.results_tree
                .topLevelItem(index)
            )

            album_mbid = album.data(
                0,
                Qt.UserRole + 1,
            )

            if album_mbid == release_group_mbid:

                return album

        return None

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

        if item_type == "album":

            release_group_mbid = item.data(
                0,
                Qt.UserRole + 1,
            )

            loaded = item.data(
                0,
                Qt.UserRole + 2,
            )

            if not loaded:

                self.pending_album_states[
                    release_group_mbid
                ] = (
                    state == Qt.Checked
                )

                if state == Qt.Checked:

                    self.load_album_songs(
                        item
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

                if (
                    child.data(
                        0,
                        Qt.UserRole,
                    )
                    != "song"
                ):
                    continue

                child.setCheckState(
                    0,
                    state
                )

            del blocker

            return

        if item_type != "song":
            return

        parent = item.parent()

        if parent is None:
            return

        checked_children = 0
        total_children = 0

        for index in range(
            parent.childCount()
        ):

            child = parent.child(
                index
            )

            if (
                child.data(
                    0,
                    Qt.UserRole,
                )
                != "song"
            ):
                continue

            total_children += 1

            if (
                child.checkState(0)
                == Qt.Checked
            ):

                checked_children += 1

        if total_children == 0:
            return

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

        del blocker

    def get_selected_songs(
        self
    ):

        selected_songs = []

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

                self.status_label.setText(
                    f"Descargando "
                    f"{index}/{total}: "
                    f"{download_title}..."
                )

                try:

                    file_path = (
                        self.downloader.download(
                            video_id=result[
                                "video_id"
                            ],
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

            self.status_label.setText(
                "Limpiando archivos temporales..."
            )

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

    def closeEvent(
        self,
        event,
    ):

        threads = list(
            self.album_threads.values()
        )

        for thread in threads:

            if thread.isRunning():

                thread.quit()

        for thread in threads:

            if thread.isRunning():

                thread.wait()

        self.album_threads.clear()
        self.album_workers.clear()
        self.pending_album_states.clear()

        super().closeEvent(
            event
        )