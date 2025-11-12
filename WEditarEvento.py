from PyQt5.QtCore import QDate, QTime
from PyQt5.QtWidgets import QMainWindow
from Vistas.emergente_editar_evento_ui import Ui_EmergenteEditarEvento
from GestorDeEventos import connect_btn

class WEditarEvento(QMainWindow):
    def __init__(self, parent=None, idx: int = -1):
        super().__init__(parent)
        self.ui = Ui_EmergenteEditarEvento()
        self.ui.setupUi(self)
        self._idx = idx

        main = self.parent()
        if main and 0 <= idx < len(main.router.eventos):
            ev = main.router.eventos[idx]

            # Textos
            if hasattr(self.ui, "txtTipoEvento"):    self.ui.txtTipoEvento.setText(ev.get("tipo", ""))
            if hasattr(self.ui, "txtUbicacion"):     self.ui.txtUbicacion.setText(ev.get("ubicacion", ""))
            if hasattr(self.ui, "txtOrganizadores"): self.ui.txtOrganizadores.setText(ev.get("organizadores", ""))
            if hasattr(self.ui, "spinMesas"):        self.ui.spinMesas.setValue(ev.get("mesas", 1))

            # Fecha
            if hasattr(self.ui, "dateFecha"):
                try:
                    d, m, y = map(int, ev.get("fecha", "01/01/2025").split("/"))
                    self.ui.dateFecha.setDate(QDate(y, m, d))
                except Exception:
                    self.ui.dateFecha.setDate(QDate.currentDate())

            # Hora
            if hasattr(self.ui, "timeHora"):
                try:
                    h, mi = map(int, ev.get("hora", "00:00").split(":"))
                    self.ui.timeHora.setTime(QTime(h, mi))
                except Exception:
                    self.ui.timeHora.setTime(QTime.currentTime())

        # Botones
        if hasattr(self.ui, "btnGuardar"):
            self.ui.btnGuardar.clicked.connect(self._guardar)
        else:
            # fallback por si el botón se llama btnAnadir en ese .ui
            connect_btn(self, "btnAnadir", self._guardar)
        connect_btn(self, "btnCancelar", self.close)

    def _guardar(self):
        main = self.parent()
        if not main: return
        ev = main.router.eventos[self._idx]

        if hasattr(self.ui, "txtTipoEvento"): ev["tipo"] = self.ui.txtTipoEvento.text()
        if hasattr(self.ui, "dateFecha"):     ev["fecha"] = self.ui.dateFecha.date().toString("dd/MM/yyyy")
        if hasattr(self.ui, "timeHora"):      ev["hora"]  = self.ui.timeHora.time().toString("HH:mm")
        if hasattr(self.ui, "txtUbicacion"):  ev["ubicacion"] = self.ui.txtUbicacion.text()
        if hasattr(self.ui, "txtOrganizadores"): ev["organizadores"] = self.ui.txtOrganizadores.text()
        if hasattr(self.ui, "spinMesas"):        ev["mesas"] = self.ui.spinMesas.value()

        main.router.guardar_eventos()
        main.refrescar_lista()
        self.close()
