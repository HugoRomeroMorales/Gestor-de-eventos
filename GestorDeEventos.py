# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QPushButton, QListWidget, QMessageBox
from PyQt5 import QtCore
from PyQt5.QtCore import Qt

# ==== IMPORTAR LAS UI ====
from Vistas.pantalla_principal_ui import Ui_MainWindow as Ui_PantallaPrincipal
from Vistas.pantalla2_ui import Ui_MainWindow as Ui_Pantalla2
from Vistas.mesas_ui import Ui_MainWindow as Ui_Mesas
from Vistas.emergente_alerta_ui import Ui_EmergenteConflicto as Ui_EmergenteAlerta
from Vistas.emergente_alerta_conflicto_ui import Ui_EmergenteConflicto as Ui_EmergenteAlertaConflicto
from Vistas.emergente_anadir_evento_ui import Ui_EmergenteAnadirEvento as Ui_AnadirEvento
from Vistas.emergente_anadir_persona_ui import Ui_EmergenteAnadirEvento as Ui_AnadirPersona
from Vistas.emergente_editar_evento_ui import Ui_EmergenteAnadirEvento as Ui_EditarEvento
from Vistas.emergente_editar_persona_ui import Ui_EmergenteAnadirEvento as Ui_EditarPersona


# ==== FUNCIONES AUXILIARES ====

def connect_btn(win, object_name, slot):
    """Conecta un botón por su objectName si existe"""
    btn = win.findChild(QPushButton, object_name)
    if btn:
        btn.clicked.connect(slot)

def abrir_modal_seguro(win):
    """Si es QDialog -> exec_; si es QMainWindow -> show con modalidad de aplicación."""
    if isinstance(win, QDialog):
        win.exec_()
    else:
        win.setWindowModality(Qt.ApplicationModal)
        win.show()


# ==== CLASES DE VENTANAS ====

class VPantallaPrincipal(QMainWindow):
    def __init__(self, router):
        super().__init__()
        self.ui = Ui_PantallaPrincipal()
        self.ui.setupUi(self)
        self.router = router

        # Conexiones de botones
        connect_btn(self, "btnAnadir", self.router.dialog_anadir_evento)
        connect_btn(self, "btnEditar", self.router.dialog_editar_evento)
        connect_btn(self, "btnEliminar", self.eliminar_evento)

        # Refrescar lista al iniciar
        self.refrescar_lista()

    def refrescar_lista(self):
        """Recarga la lista de eventos"""
        lista = self.findChild(QListWidget, "lstEventos")
        if not lista:
            return
        lista.clear()
        for ev in self.router.eventos:
            texto = f"{ev['tipo']} — {ev['fecha']} {ev['hora']} — {ev['ubicacion']}"
            lista.addItem(texto)


class VPantalla2(QMainWindow):
    def __init__(self, router):
        super().__init__()
        self.ui = Ui_Pantalla2()
        self.ui.setupUi(self)
        self.router = router


class VMesas(QMainWindow):
    def __init__(self, router):
        super().__init__()
        self.ui = Ui_Mesas()
        self.ui.setupUi(self)
        self.router = router


# ==== EMERGENTES ====

class DAlertaConflicto(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_EmergenteAlertaConflicto()
        self.ui.setupUi(self)
        connect_btn(self, "btnConfirmar", self.close)
        connect_btn(self, "btnCancelar", self.close)


class DAlerta(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_EmergenteAlerta()
        self.ui.setupUi(self)
        connect_btn(self, "btnConfirmar", self.close)
        connect_btn(self, "btnCancelar", self.close)


# ==== EMERGENTES DE AÑADIR / EDITAR ====

class WAnadirEvento(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AnadirEvento()
        self.ui.setupUi(self)

        btn_add = self.findChild(QPushButton, "btnAnadir")
        if btn_add:
            btn_add.clicked.connect(self._guardar_evento)

        connect_btn(self, "btnCancelar", self.close)

    def _guardar_evento(self):
        """Guarda el evento y actualiza la lista de la pantalla principal"""
        main = self.parent()
        if not main:
            self.close()
            return

        tipo = self.ui.txtTipoEvento.text() if hasattr(self.ui, "txtTipoEvento") else ""
        fecha = self.ui.dateFecha.date().toString("dd/MM/yyyy") if hasattr(self.ui, "dateFecha") else ""
        hora = self.ui.timeHora.time().toString("HH:mm") if hasattr(self.ui, "timeHora") else ""
        ubic = self.ui.txtUbicacion.text() if hasattr(self.ui, "txtUbicacion") else ""

        main.router.eventos.append({
            "tipo": tipo,
            "fecha": fecha,
            "hora": hora,
            "ubicacion": ubic
        })

        if hasattr(main, "refrescar_lista"):
            main.refrescar_lista()

        self.close()


class WAnadirPersona(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_AnadirPersona()
        self.ui.setupUi(self)
        connect_btn(self, "btnCancelar", self.close)


class WEditarEvento(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_EditarEvento()
        self.ui.setupUi(self)
        connect_btn(self, "btnCancelar", self.close)


class WEditarPersona(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_EditarPersona()
        self.ui.setupUi(self)
        connect_btn(self, "btnCancelar", self.close)


# ==== ROUTER PRINCIPAL ====

class Router:
    def __init__(self):
        self.eventos = []  # lista de eventos en memoria
        self._stack = []

    def abrir_pantalla_principal(self):
        win = VPantallaPrincipal(self)
        win.show()
        self._stack.append(win)

    def abrir_pantalla2(self):
        win = VPantalla2(self)
        win.show()
        self._stack.append(win)

    def abrir_mesas(self):
        win = VMesas(self)
        win.show()
        self._stack.append(win)

    # --- diálogos ---
    def dialog_anadir_evento(self):
        abrir_modal_seguro(WAnadirEvento(self._stack[-1]))

    def dialog_editar_evento(self):
        abrir_modal_seguro(WEditarEvento(self._stack[-1]))

    def dialog_anadir_persona(self):
        abrir_modal_seguro(WAnadirPersona(self._stack[-1]))

    def dialog_editar_persona(self):
        abrir_modal_seguro(WEditarPersona(self._stack[-1]))

    def dialog_alerta(self):
        abrir_modal_seguro(DAlerta(self._stack[-1]))

    def dialog_alerta_conflicto(self):
        abrir_modal_seguro(DAlertaConflicto(self._stack[-1]))


# ==== MAIN ====

if __name__ == "__main__":
    app = QApplication(sys.argv)
    router = Router()
    router.abrir_pantalla_principal()
    sys.exit(app.exec_())
