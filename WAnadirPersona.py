# WAnadirPersona.py
import os
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QDialog, QLineEdit, QPushButton, QVBoxLayout, QMessageBox
)


class WAnadirPersona(QDialog):
    """
    Ventana azul para añadir/editar persona.

    Usa el .ui:
        Vistas/emergente_anadir_persona.ui

    En el .ui deben existir estos objectName:
      - txtNombre     (QLineEdit)
      - txtApellidos  (QLineEdit)
      - txtPrefCon    (QLineEdit)
      - txtPrefSin    (QLineEdit)
      - btnAnadir     (QPushButton)
      - btnCancelar   (QPushButton)
    """

    def __init__(self, parent=None, invitado=None, indice=None):
        super().__init__(parent)
        self.setModal(True)
        self.indice = indice  # por si algún día lo quieres usar

        # 1) Cargar el .ui como widget independiente
        ruta_ui = os.path.join(
            os.path.dirname(__file__),
            "Vistas",
            "emergente_anadir_persona.ui"
        )
        ui_widget = uic.loadUi(ruta_ui)   # devuelve el toplevel del .ui

        # 2) Meter ese widget dentro de este QDialog
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(ui_widget)

        # 3) Referencias a los widgets por objectName
        self.txtNombre    = ui_widget.findChild(QLineEdit, "txtNombre")
        self.txtApellidos = ui_widget.findChild(QLineEdit, "txtApellidos")
        self.txtPrefCon   = ui_widget.findChild(QLineEdit, "txtPrefCon")
        self.txtPrefSin   = ui_widget.findChild(QLineEdit, "txtPrefSin")
        self.btnAnadir    = ui_widget.findChild(QPushButton, "btnAnadir")
        self.btnCancelar  = ui_widget.findChild(QPushButton, "btnCancelar")

        # 4) Conectar botones
        if self.btnAnadir is not None:
            self.btnAnadir.clicked.connect(self._on_guardar)
        if self.btnCancelar is not None:
            self.btnCancelar.clicked.connect(self.reject)

        # 5) Si venimos en modo edición, rellenar campos
        if invitado:
            if self.txtNombre:
                self.txtNombre.setText(invitado.get("nombre", ""))
            if self.txtApellidos:
                self.txtApellidos.setText(invitado.get("apellido", ""))
            if self.txtPrefCon:
                self.txtPrefCon.setText(invitado.get("pref_con", ""))
            if self.txtPrefSin:
                self.txtPrefSin.setText(invitado.get("pref_sin", ""))

    # ----------------- Lógica interna -----------------
    def _on_guardar(self):
        """Validación básica y cerrar el diálogo con Accept."""
        if self.txtNombre and not self.txtNombre.text().strip():
            QMessageBox.warning(self, "Validación", "El nombre es obligatorio.")
            return

        self.accept()

    # ----------------- API para VPantallaInvitados -----------------
    def datos(self):
        """Devuelve un dict con las claves EXACTAS que usa la tabla."""
        return {
            "nombre":   self.txtNombre.text().strip()    if self.txtNombre    else "",
            "apellido": self.txtApellidos.text().strip() if self.txtApellidos else "",
            "pref_con": self.txtPrefCon.text().strip()   if self.txtPrefCon   else "",
            "pref_sin": self.txtPrefSin.text().strip()   if self.txtPrefSin   else "",
        }
