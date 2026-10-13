import sys

from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


BASE_DIR = Path(
    "/home/arch_dani/Projects/musicDownloader/ui/styles"
)

STYLESHEET = BASE_DIR / "styles.css"


app = QApplication(
    sys.argv
)

with open(
    STYLESHEET,
    "r",
    encoding="utf-8",
) as file:

    app.setStyleSheet(
        file.read()
    )

window = MainWindow()

window.show()

sys.exit(
    app.exec()
)