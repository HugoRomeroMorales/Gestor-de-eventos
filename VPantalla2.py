from PyQt5.QtWidgets import QMainWindow
from Vistas.pantalla2_ui import Ui_MainWindow as Ui_Pantalla2


class VPantalla2(QMainWindow):
    def __init__(self, router, evento: dict):
        super().__init__()
        self.ui = Ui_Pantalla2()
        self.ui.setupUi(self)
        self.router = router
        self.evento = evento

        # Muestra los datos del evento
        if hasattr(self.ui, "lblTitulo"):
            self.ui.lblTitulo.setText(evento.get("tipo", ""))
        if hasattr(self.ui, "lblFecha"):
            self.ui.lblFecha.setText(f"{evento.get('fecha', '')} {evento.get('hora', '')}")
        if hasattr(self.ui, "lblUbicacion"):
            self.ui.lblUbicacion.setText(evento.get("ubicacion", ""))
