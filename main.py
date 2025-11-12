import sys
from PyQt5.QtWidgets import QApplication
from Router import Router

if __name__ == "__main__":
    app = QApplication(sys.argv)
    router = Router()
    router.abrir_pantalla_principal()
    sys.exit(app.exec_())
