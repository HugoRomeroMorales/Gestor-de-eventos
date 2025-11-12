from PyQt5.QtCore import QDate, QTime
from PyQt5.QtWidgets import QMainWindow
from Vistas.emergente_anadir_evento_ui import Ui_EmergenteAnadirEvento
from GestorDeEventos import connect_btn  # tu helper

class WAnadirEvento(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_EmergenteAnadirEvento()
        self.ui.setupUi(self)

        # Fecha/hora por defecto (editables)
        if hasattr(self.ui, "dateFecha"): self.ui.dateFecha.setDate(QDate.currentDate())
        if hasattr(self.ui, "timeHora"):  self.ui.timeHora.setTime(QTime.currentTime())

        connect_btn(self, "btnAnadir", self._guardar)
        connect_btn(self, "btnCancelar", self.close)

    def _guardar(self):
        main = self.parent()
        if not main: return

        nuevo = {
            "tipo":        self.ui.txtTipoEvento.text().strip() if hasattr(self.ui, "txtTipoEvento") else "",
            "fecha":       self.ui.dateFecha.date().toString("dd/MM/yyyy") if hasattr(self.ui, "dateFecha") else "",
            "hora":        self.ui.timeHora.time().toString("HH:mm") if hasattr(self.ui, "timeHora") else "",
            "ubicacion":   self.ui.txtUbicacion.text().strip() if hasattr(self.ui, "txtUbicacion") else "",
            "organizadores": self.ui.txtOrganizadores.text().strip() if hasattr(self.ui, "txtOrganizadores") else "",
            "mesas":       self.ui.spinMesas.value() if hasattr(self.ui, "spinMesas") else 1,
        }

        main.router.eventos.append(nuevo)
        main.router.guardar_eventos()
        main.refrescar_lista()
        self.close()
