from plover import log
from PySide6.QtCore import QFile, QIODevice, QTextStream


def load_qt_text(text_path: str) -> str:
    try:
        file = QFile(text_path)
        text = ""
        if file.open(QIODevice.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            text_stream = QTextStream(file)
            text_stream.setAutoDetectUnicode(True)

            text = text_stream.readAll()
            file.close()
        return text
    except Exception as e:
        log.error("Failed to load Qt text from %s: %s", text_path, e, exc_info=True)
        return ""
