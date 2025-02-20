import sys

from ui import QueryUI
from PySide6.QtCore import QLoggingCategory
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

if __name__ == "__main__":
    # Suppress Qt debug/info messages
    QLoggingCategory.setFilterRules("*.debug=false\nqt.*.info=false")

    app = QApplication(sys.argv)
    # Create a QFont object with desired font family and size
    font = QFont("Unifont", 12)

    # Set the application-wide font
    app.setFont(font)  
    window = QueryUI()
    window.show()
    sys.exit(app.exec())
