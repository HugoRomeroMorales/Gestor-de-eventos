# VPantallaPrincipal.py
# Controlador de la pantalla principal (CRUD y navegación a Pantalla2)

from PyQt5.QtWidgets import QMainWindow, QListWidget, QMessageBox
from Vistas.pantalla_principal_ui import Ui_MainWindow as Ui_PantallaPrincipal


class VPantallaPrincipal(QMainWindow):

    def __init__(self, router):
        super().__init__()
        self.ui = Ui_PantallaPrincipal()
        self.ui.setupUi(self)
        self.router = router

        # --- Conexiones de botones ---
        self.ui.btnAnadir.clicked.connect(self.on_add)
        self.ui.btnEditar.clicked.connect(self.on_edit)
        self.ui.btnEliminar.clicked.connect(self.on_delete)

        # --- Abrir Pantalla2 con doble click ---
        self.ui.lstEventos.itemDoubleClicked.connect(self.on_open_selected)

        # --- Cambios de selección: habilitar/deshabilitar ---
        self.ui.lstEventos.itemSelectionChanged.connect(self._update_buttons_state)

        # --- Estado inicial ---
        self.refrescar_lista()
        self._update_buttons_state()
        
        with open("stylePantallaPrin.qss", "r", encoding="utf-8") as f:
            estilo = f.read()
            self.setStyleSheet(estilo)

    # ------------------ RENDER / SELECCIÓN ------------------

    def refrescar_lista(self):
        """Repinta la lista de eventos desde router.eventos."""
        lista: QListWidget = self.ui.lstEventos
        lista.clear()
        for ev in self.router.eventos:
            # Formato visible en la lista
            texto = f"{ev['tipo']} — {ev['fecha']} {ev['hora']} — {ev['ubicacion']}"
            lista.addItem(texto)
        self._update_buttons_state()

    def get_selected_index(self) -> int:
        """Devuelve el índice seleccionado en router.eventos (o -1 si no hay selección)."""
        fila = self.ui.lstEventos.currentRow()
        return fila if 0 <= fila < len(self.router.eventos) else -1

    def _update_buttons_state(self):
        """Activa/Desactiva Editar y Eliminar según haya selección."""
        has_sel = self.get_selected_index() != -1
        self.ui.btnEditar.setEnabled(has_sel)
        self.ui.btnEliminar.setEnabled(has_sel)

    # ------------------ ACCIONES CRUD ------------------

    def on_add(self):
        """Abrir diálogo de añadir evento y refrescar lista al cerrar."""
        self.router.dialog_anadir_evento()
        self.refrescar_lista()

    def on_edit(self):
        """Abrir diálogo de edición sobre el evento seleccionado."""
        idx = self.get_selected_index()
        if idx == -1:
            QMessageBox.information(self, "Editar", "Selecciona un evento para editarlo.")
            return

        # Soporta routers que aceptan idx o ninguno (por compatibilidad con tu versión previa)
        try:
            self.router.dialog_editar_evento(idx)
        except TypeError:
            self.router.dialog_editar_evento()

        self.refrescar_lista()

    def on_delete(self):
        """Eliminar el evento seleccionado con confirmación."""
        idx = self.get_selected_index()
        if idx == -1:
            QMessageBox.information(self, "Eliminar", "Selecciona un evento para eliminarlo.")
            return

        if QMessageBox.question(
            self, "Confirmar eliminación",
            "¿Seguro que quieres eliminar este evento?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        ) == QMessageBox.Yes:
            del self.router.eventos[idx]
            self.refrescar_lista()

    # ------------------ NAVEGACIÓN ------------------

    def on_open_selected(self):
        """Abrir Pantalla2 con el evento seleccionado (doble-click)."""
        idx = self.get_selected_index()
        if idx == -1:
            return
        evento = self.router.eventos[idx]
        self.router.abrir_pantalla2(evento)
