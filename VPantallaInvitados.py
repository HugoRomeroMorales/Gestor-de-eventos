import os
import json
import csv

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QFileDialog,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox
)


from Vistas.pantalla2_ui import Ui_MainWindow


# ------------------ Modelo de datos ------------------
CAMPOS = ["nombre", "apellido", "pref_con", "rol", "pref_sin"]

def invitado_vacio():
    """Crea un dict con todas las claves vacías."""
    return {k: "" for k in CAMPOS}


# ------------------ Diálogo añadir/editar ------------------
class InvitadoDialog(QDialog):
    """Formulario modal sencillo para crear/editar un invitado."""
    def __init__(self, invitado=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Invitado")
        self.setModal(True)

        self.edtNombre   = QLineEdit()
        self.edtApellido = QLineEdit()
        self.edtPrefCon  = QLineEdit()
        self.cmbRol      = QComboBox()
        self.cmbRol.addItems(["", "Invitado", "VIP", "Organizador", "Ponente"])
        self.edtPrefSin  = QLineEdit()

        layout = QFormLayout(self)
        layout.addRow("Nombre:", self.edtNombre)
        layout.addRow("Apellido:", self.edtApellido)
        layout.addRow("Pref. con quién estar:", self.edtPrefCon)
        layout.addRow("Rol:", self.cmbRol)
        layout.addRow("Pref. con quién NO estar:", self.edtPrefSin)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addRow(btns)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        if invitado:
            self.edtNombre.setText(invitado.get("nombre", ""))
            self.edtApellido.setText(invitado.get("apellido", ""))
            self.edtPrefCon.setText(invitado.get("pref_con", ""))
            self.cmbRol.setCurrentText(invitado.get("rol", ""))
            self.edtPrefSin.setText(invitado.get("pref_sin", ""))

    def datos(self):
        """Devuelve los datos del formulario como dict."""
        return {
            "nombre": self.edtNombre.text().strip(),
            "apellido": self.edtApellido.text().strip(),
            "pref_con": self.edtPrefCon.text().strip(),
            "rol": self.cmbRol.currentText().strip(),
            "pref_sin": self.edtPrefSin.text().strip(),
        }

    def accept(self):
        if not self.edtNombre.text().strip():
            QMessageBox.warning(self, "Faltan datos", "El nombre es obligatorio.")
            return
        super().accept()


# ------------------ Ventana principal (Controlador) ------------------
class MainWindow(QMainWindow, Ui_MainWindow):
    RUTA_JSON = os.path.join("data", "participantes.json")
    
   

    def __init__(self):
        super().__init__()
        self.setupUi(self)   # Construye la UI creada en Qt Designer
            
        with open("styleInvitados.qss","r",encoding="utf-8") as f:
            self.setStyleSheet(f.read())  
            
        # Estado en memoria
        self.participantes = []

        # Configuramos la tabla:
        # - Añadimos una columna 0 para checkboxes
        # - Dejas las 5 columnas de datos: Nombre, Apellido, Pref de estar, Rol, Pref no estar
        self.tblInvitados.setColumnCount(6)
        headers = ["", "Nombre", "Apellido", "Pref de estar", "Rol",
                   "Preferencias de con quien no estar"]
        for i, t in enumerate(headers):
            self.tblInvitados.setHorizontalHeaderItem(i, QtWidgets.QTableWidgetItem(t))

        self.tblInvitados.setSortingEnabled(True)
        self.tblInvitados.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tblInvitados.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tblInvitados.verticalHeader().setVisible(False)
        self.tblInvitados.horizontalHeader().setStretchLastSection(True)
        self.tblInvitados.doubleClicked.connect(self.on_editar)  # doble clic = editar

        # Conectar señales de botones
        self.btnAnadir.clicked.connect(self.on_anadir)
        self.btnEditar.clicked.connect(self.on_editar)
        self.btnEliminar.clicked.connect(self.on_eliminar)
        self.btnSubirCSV.clicked.connect(self.on_subir_csv)
        self.btnBuscar.clicked.connect(self.on_buscar)
        self.txtBuscar.textChanged.connect(self.on_buscar)

        # Cargar persistencia y pintar
        self.cargar_desde_json()
        self.refrescar_tabla()

    # ---------- Persistencia ----------
    def _asegurar_directorio(self):
        os.makedirs(os.path.dirname(self.RUTA_JSON), exist_ok=True)

    def cargar_desde_json(self):
        """Carga lista de participantes desde JSON si existe."""
        self._asegurar_directorio()
        if os.path.exists(self.RUTA_JSON):
            try:
                with open(self.RUTA_JSON, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                self.participantes = [
                    {k: str(item.get(k, "")).strip() for k in CAMPOS}
                    for item in datos if isinstance(item, dict)
                ]
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo leer JSON:\n{e}")
                self.participantes = []
        else:
            self.participantes = []

    def guardar_a_json(self):
        """Guarda la lista actual a JSON con sangría."""
        self._asegurar_directorio()
        try:
            with open(self.RUTA_JSON, "w", encoding="utf-8") as f:
                json.dump(self.participantes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar JSON:\n{e}")

    # ---------- Pintado de tabla ----------
    def _item_check(self, checked=False):
        it = QtWidgets.QTableWidgetItem()
        it.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        it.setCheckState(QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked)
        return it

    def refrescar_tabla(self, filtrado=None):
        """Vuelca la lista (o su versión filtrada) a la QTableWidget."""
        datos = filtrado if filtrado is not None else self.participantes
        self.tblInvitados.setRowCount(len(datos))
        for fila, invit in enumerate(datos):
            self.tblInvitados.setItem(fila, 0, self._item_check(False))
            self.tblInvitados.setItem(fila, 1, QtWidgets.QTableWidgetItem(invit.get("nombre", "")))
            self.tblInvitados.setItem(fila, 2, QtWidgets.QTableWidgetItem(invit.get("apellido", "")))
            self.tblInvitados.setItem(fila, 3, QtWidgets.QTableWidgetItem(invit.get("pref_con", "")))
            self.tblInvitados.setItem(fila, 4, QtWidgets.QTableWidgetItem(invit.get("rol", "")))
            self.tblInvitados.setItem(fila, 5, QtWidgets.QTableWidgetItem(invit.get("pref_sin", "")))
        self.tblInvitados.resizeColumnsToContents()

    def fila_seleccionada_index(self):
        """Devuelve el índice en la lista base del elemento seleccionado (resistente al sorting)."""
        sel = self.tblInvitados.currentRow()
        if sel < 0:
            return None
        nombre   = self.tblInvitados.item(sel, 1).text() if self.tblInvitados.item(sel, 1) else ""
        apellido = self.tblInvitados.item(sel, 2).text() if self.tblInvitados.item(sel, 2) else ""
        pref_con = self.tblInvitados.item(sel, 3).text() if self.tblInvitados.item(sel, 3) else ""
        rol      = self.tblInvitados.item(sel, 4).text() if self.tblInvitados.item(sel, 4) else ""
        pref_sin = self.tblInvitados.item(sel, 5).text() if self.tblInvitados.item(sel, 5) else ""
        for i, it in enumerate(self.participantes):
            if (it["nombre"] == nombre and it["apellido"] == apellido and
                it["pref_con"] == pref_con and it["rol"] == rol and it["pref_sin"] == pref_sin):
                return i
        return None

    # ---------- Acciones ----------
    def on_anadir(self):
        dlg = InvitadoDialog(invitado_vacio(), self)
        if dlg.exec_() == QDialog.Accepted:
            self.participantes.append(dlg.datos())
            self.guardar_a_json()
            self.refrescar_tabla()
            self.statusbar.showMessage("Invitado añadido", 2500)

    def on_editar(self):
        idx = self.fila_seleccionada_index()
        if idx is None:
            QMessageBox.information(self, "Editar", "Selecciona un invitado (clic en una fila).")
            return
        dlg = InvitadoDialog(self.participantes[idx], self)
        if dlg.exec_() == QDialog.Accepted:
            self.participantes[idx] = dlg.datos()
            self.guardar_a_json()
            self.refrescar_tabla()
            self.statusbar.showMessage("Invitado actualizado", 2500)

    def on_eliminar(self):
        # Primero intentamos borrado múltiple si hay checkboxes marcados
        marcados = []
        for fila in range(self.tblInvitados.rowCount()):
            it = self.tblInvitados.item(fila, 0)
            if it and it.checkState() == QtCore.Qt.Checked:
                nombre   = self.tblInvitados.item(fila, 1).text()
                apellido = self.tblInvitados.item(fila, 2).text()
                pref_con = self.tblInvitados.item(fila, 3).text()
                rol      = self.tblInvitados.item(fila, 4).text()
                pref_sin = self.tblInvitados.item(fila, 5).text()
                marcados.append((nombre, apellido, pref_con, rol, pref_sin))

        if marcados:
            if QMessageBox.question(self, "Confirmar",
                                    f"¿Eliminar {len(marcados)} invitado(s) marcados?") != QMessageBox.Yes:
                return
            def tupla(it): return (it["nombre"], it["apellido"], it["pref_con"], it["rol"], it["pref_sin"])
            self.participantes = [it for it in self.participantes if tupla(it) not in marcados]
            self.guardar_a_json()
            self.refrescar_tabla()
            self.statusbar.showMessage("Invitados eliminados", 2500)
            return

        # Si no hay checks, borramos la fila seleccionada
        idx = self.fila_seleccionada_index()
        if idx is None:
            QMessageBox.information(self, "Eliminar", "Marca casillas o selecciona una fila.")
            return
        nom = f'{self.participantes[idx]["nombre"]} {self.participantes[idx]["apellido"]}'.strip()
        if QMessageBox.question(self, "Confirmar", f"¿Eliminar a '{nom}'?") == QMessageBox.Yes:
            self.participantes.pop(idx)
            self.guardar_a_json()
            self.refrescar_tabla()
            self.statusbar.showMessage("Invitado eliminado", 2500)

    def on_buscar(self):
        texto = self.txtBuscar.text().strip().lower()
        if not texto:
            self.refrescar_tabla()
            return
        filtrado = [
            it for it in self.participantes
            if texto in it["nombre"].lower() or texto in it["apellido"].lower()
        ]
        self.refrescar_tabla(filtrado)

    def on_subir_csv(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Seleccionar CSV", "", "CSV (*.csv)")
        if not ruta:
            return
        try:
            with open(ruta, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)

                # Mapeo laxo de cabeceras
                mapa = {
                    "nombre":   ["nombre", "name", "first_name"],
                    "apellido": ["apellido", "apellidos", "surname", "last_name"],
                    "pref_con": ["pref_con", "preferencias_con", "pref_estar", "with"],
                    "rol":      ["rol", "role", "papel"],
                    "pref_sin": ["pref_sin", "preferencias_sin", "pref_no_estar", "without"],
                }
                def take(row, clave):
                    for alias in mapa[clave]:
                        if alias in row and row[alias] is not None:
                            return str(row[alias]).strip()
                    return ""

                added = 0
                for row in reader:
                    nuevo = {
                        "nombre":   take(row, "nombre"),
                        "apellido": take(row, "apellido"),
                        "pref_con": take(row, "pref_con"),
                        "rol":      take(row, "rol"),
                        "pref_sin": take(row, "pref_sin"),
                    }
                    if not nuevo["nombre"]:
                        continue
                    existe = any(
                        it["nombre"].lower() == nuevo["nombre"].lower() and
                        it["apellido"].lower() == nuevo["apellido"].lower()
                        for it in self.participantes
                    )
                    if not existe:
                        self.participantes.append(nuevo)
                        added += 1

                self.guardar_a_json()
                self.refrescar_tabla()
                self.statusbar.showMessage(f"CSV importado: {added} nuevo(s)", 2500)

        except Exception as e:
            QMessageBox.critical(self, "Error CSV", f"No se pudo leer el CSV:\n{e}")


# ------------------ Arranque ------------------
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())