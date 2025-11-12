# -*- coding: utf-8 -*-
import sys, json, os
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QDialog, QPushButton, QListWidget, QMessageBox
)
from PyQt5.QtCore import Qt, QDate, QTime

# ==== IMPORTAR LAS UI ====
from Vistas.pantalla_principal_ui import Ui_MainWindow as Ui_PantallaPrincipal
from Vistas.pantalla2_ui import Ui_MainWindow as Ui_Pantalla2
from Vistas.mesas_ui import Ui_MainWindow as Ui_Mesas
from Vistas.emergente_alerta_ui import Ui_EmergenteConflicto as Ui_EmergenteAlerta
from Vistas.emergente_alerta_conflicto_ui import Ui_EmergenteConflicto as Ui_EmergenteAlertaConflicto

from Vistas.emergente_anadir_evento_ui import Ui_EmergenteAnadirEvento as Ui_AnadirEvento
from Vistas.emergente_editar_evento_ui import Ui_EmergenteEditarEvento as Ui_EditarEvento


# ==== FUNCIONES AUXILIARES ====

def connect_btn(win, object_name, slot):
    btn = win.findChild(QPushButton, object_name)
    if btn:
        btn.clicked.connect(slot)


# ==== VENTANAS ====

class VPantallaPrincipal(QMainWindow):
    """Pantalla principal con CRUD y lista de eventos"""
    def __init__(self, router):
        super().__init__()
        self.ui = Ui_PantallaPrincipal()
        self.ui.setupUi(self)
        self.router = router

        # Botones
        connect_btn(self, "btnAnadir", self.router.dialog_anadir_evento)
        connect_btn(self, "btnEditar", self.router.dialog_editar_evento)
        connect_btn(self, "btnEliminar", self.eliminar_evento)

        # Doble click -> abrir Pantalla2
        self.ui.lstEventos.itemDoubleClicked.connect(self._abrir_evento)

        # Mostrar eventos iniciales
        self.refrescar_lista()

    def refrescar_lista(self):
        """Recarga la lista con los eventos desde el router"""
        lista: QListWidget = self.ui.lstEventos
        lista.clear()
        for ev in self.router.eventos:
            texto = f"{ev['tipo']} — {ev['fecha']} {ev['hora']} — {ev['ubicacion']}"
            lista.addItem(texto)

    def get_selected_index(self):
        fila = self.ui.lstEventos.currentRow()
        return fila if 0 <= fila < len(self.router.eventos) else -1

    def eliminar_evento(self):
        idx = self.get_selected_index()
        if idx == -1:
            QMessageBox.information(self, "Eliminar", "Selecciona un evento para eliminarlo.")
            return

        if QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Seguro que quieres eliminar este evento?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes:
            del self.router.eventos[idx]
            self.router.guardar_eventos()
            self.refrescar_lista()

    def _abrir_evento(self):
        idx = self.get_selected_index()
        if idx == -1:
            return
        evento = self.router.eventos[idx]
        self.router.abrir_pantalla2(evento)


class WAnadirEvento(QMainWindow):
    """Ventana para añadir eventos"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AnadirEvento()
        self.ui.setupUi(self)

        # ✅ Establecer fecha y hora actual por defecto
        ahora = datetime.now()
        if hasattr(self.ui, "dateFecha"):
            self.ui.dateFecha.setDate(QDate.currentDate())
        if hasattr(self.ui, "timeHora"):
            self.ui.timeHora.setTime(QTime.currentTime())

        connect_btn(self, "btnAnadir", self._guardar_evento)
        connect_btn(self, "btnCancelar", self.close)

    def _guardar_evento(self):
        main = self.parent()
        if not main:
            self.close()
            return

        tipo = self.ui.txtTipoEvento.text()
        fecha = self.ui.dateFecha.date().toString("dd/MM/yyyy")
        hora = self.ui.timeHora.time().toString("HH:mm")
        ubic = self.ui.txtUbicacion.text()

        nuevo = {"tipo": tipo, "fecha": fecha, "hora": hora, "ubicacion": ubic}
        main.router.eventos.append(nuevo)
        main.router.guardar_eventos()

        main.refrescar_lista()
        self.close()


class WEditarEvento(QMainWindow):
    """Ventana para editar un evento existente"""
    def __init__(self, parent=None, idx: int = -1):
        super().__init__(parent)
        self.ui = Ui_EditarEvento()
        self.ui.setupUi(self)
        self._idx = idx

        main = self.parent()
        if main and 0 <= idx < len(main.router.eventos):
            ev = main.router.eventos[idx]
            self.ui.txtTipoEvento.setText(ev["tipo"])
            self.ui.txtUbicacion.setText(ev["ubicacion"])

            # ✅ Si tiene campos de fecha y hora, pon la actual o la guardada
            if hasattr(self.ui, "dateFecha"):
                self.ui.dateFecha.setDate(QDate.currentDate())
            if hasattr(self.ui, "timeHora"):
                self.ui.timeHora.setTime(QTime.currentTime())

        btn_save = self.findChild(QPushButton, "btnAnadir")
        if btn_save:
            btn_save.setText("Guardar")
            btn_save.clicked.connect(self._guardar_cambios)
        connect_btn(self, "btnCancelar", self.close)

    def _guardar_cambios(self):
        main = self.parent()
        if not main:
            self.close()
            return

        ev = main.router.eventos[self._idx]
        ev["tipo"] = self.ui.txtTipoEvento.text()
        ev["fecha"] = self.ui.dateFecha.date().toString("dd/MM/yyyy")
        ev["hora"] = self.ui.timeHora.time().toString("HH:mm")
        ev["ubicacion"] = self.ui.txtUbicacion.text()

        main.router.guardar_eventos()
        main.refrescar_lista()
        self.close()


class VPantalla2(QMainWindow):
    """Pantalla secundaria para ver un evento"""
    def __init__(self, router, evento):
        super().__init__()
        self.ui = Ui_Pantalla2()
        self.ui.setupUi(self)
        self.router = router
        self.evento = evento

        if hasattr(self.ui, "lblTitulo"):
            self.ui.lblTitulo.setText(evento["tipo"])
        if hasattr(self.ui, "lblFecha"):
            self.ui.lblFecha.setText(f"{evento['fecha']} {evento['hora']}")
        if hasattr(self.ui, "lblUbicacion"):
            self.ui.lblUbicacion.setText(evento["ubicacion"])


# ==== ROUTER ====

class Router:
    def __init__(self):
        self.path_json = "eventos.json"
        self.eventos = self.cargar_eventos()
        self._stack = []

    def cargar_eventos(self):
        if os.path.exists(self.path_json):
            with open(self.path_json, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def guardar_eventos(self):
        with open(self.path_json, "w", encoding="utf-8") as f:
            json.dump(self.eventos, f, indent=4, ensure_ascii=False)

    def abrir_pantalla_principal(self):
        win = VPantallaPrincipal(self)
        win.show()
        self._stack.append(win)

    def abrir_pantalla2(self, evento):
        win = VPantalla2(self, evento)
        win.show()
        if self._stack:
            self._stack[-1].hide()
        self._stack.append(win)

    def dialog_anadir_evento(self):
        win = WAnadirEvento(self._stack[-1])
        win.setWindowModality(Qt.ApplicationModal)
        win.show()

    def dialog_editar_evento(self):
        main = self._stack[-1]
        if isinstance(main, VPantallaPrincipal):
            idx = main.get_selected_index()
            if idx == -1:
                QMessageBox.information(main, "Editar", "Selecciona un evento para editarlo.")
                return
            win = WEditarEvento(main, idx)
            win.setWindowModality(Qt.ApplicationModal)
            win.show()


# ==== MAIN ====

if __name__ == "__main__":
    app = QApplication(sys.argv)
    router = Router()
    router.abrir_pantalla_principal()
    sys.exit(app.exec_())
