# VPantallaPrincipal.py
import os
from PyQt5.QtWidgets import QMainWindow, QListWidget, QMessageBox
from PyQt5.QtCore import Qt
from Vistas.pantalla_principal_ui import Ui_MainWindow as Ui_PantallaPrincipal
from WAnadirEvento import WAnadirEvento
from WEditarEvento import WEditarEvento


class VPantallaPrincipal(QMainWindow):

    def __init__(self, router):
        super().__init__()
        self.ui = Ui_PantallaPrincipal()
        self.ui.setupUi(self)
        self.router = router

        self._dlg_add = None
        self._dlg_edit = None

        # --- Conexiones de botones ---
        self.ui.btnAnadir.clicked.connect(self.on_add)
        self.ui.btnEditar.clicked.connect(self.on_edit)
        self.ui.btnEliminar.clicked.connect(self.on_delete)

        # --- Abrir Pantalla2 con doble click ---
        self.ui.lstEventos.itemDoubleClicked.connect(self.on_open_selected)

        # --- Cambios de selección ---
        self.ui.lstEventos.itemSelectionChanged.connect(self._update_buttons_state)

        # --- Estado inicial ---
        self.refrescar_lista()
        self._update_buttons_state()

        # -------------------------
        # 🔥 CARGA DE QSS ROBUSTA
        # -------------------------
        ruta_qss = os.path.join(os.path.dirname(__file__), "stylePantallaPrin.qss")

        if os.path.exists(ruta_qss):
            try:
                with open(ruta_qss, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception as e:
                print("[QSS] Error cargando stylePantallaPrin.qss:", e)
        else:
            print("[QSS] stylePantallaPrin.qss no encontrado en:", ruta_qss)

    # ------------------ SELECCIÓN ------------------

    def refrescar_lista(self):
        lista: QListWidget = self.ui.lstEventos
        lista.clear()
        for ev in self.router.eventos:
            texto = (
                f"{ev.get('tipo', '(sin tipo)')} — "
                f"{ev.get('fecha', '??/??/????')} {ev.get('hora', '--:--')} — "
                f"{ev.get('ubicacion', '(sin ubicación)')}"
            )
            lista.addItem(texto)
        self._update_buttons_state()

    def get_selected_index(self) -> int:
        fila = self.ui.lstEventos.currentRow()
        return fila if 0 <= fila < len(self.router.eventos) else -1

    def _update_buttons_state(self):
        has_sel = self.get_selected_index() != -1
        self.ui.btnEditar.setEnabled(has_sel)
        self.ui.btnEliminar.setEnabled(has_sel)

    # ------------------ CRUD ------------------

    def on_add(self):
        self._dlg_add = WAnadirEvento(parent=self)
        self._dlg_add.setAttribute(Qt.WA_DeleteOnClose, True)
        self._dlg_add.show()

    def on_edit(self):
        idx = self.get_selected_index()
        if idx == -1:
            QMessageBox.information(self, "Editar", "Selecciona un evento para editarlo.")
            return

        self._dlg_edit = WEditarEvento(parent=self, idx=idx)
        self._dlg_edit.setAttribute(Qt.WA_DeleteOnClose, True)
        self._dlg_edit.show()

    def on_delete(self):
        idx = self.get_selected_index()
        if idx == -1:
            QMessageBox.information(self, "Eliminar", "Selecciona un evento para eliminarlo.")
            return

        if QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Seguro que quieres eliminar este evento?",
            QMessageBox.Si | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Si:
            del self.router.eventos[idx]
            if hasattr(self.router, "guardar_eventos"):
                self.router.guardar_eventos()
            self.refrescar_lista()

    # ------------------ NAVEGACIÓN ------------------

    def on_open_selected(self):
        idx = self.get_selected_index()
        if idx == -1:
            return

        evento = self.router.eventos[idx]
        self.router.abrir_pantalla2(evento)
