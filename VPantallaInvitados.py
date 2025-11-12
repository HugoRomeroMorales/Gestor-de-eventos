# VPantallaInvitados.py
# Pantalla de Invitados sin checkbox: selección por fila + QSS styleInvitados.qss

import os
import csv
import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox, QMenu,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QComboBox,
    QToolButton
)

from Vistas.pantalla2_ui import Ui_MainWindow  # <-- ajusta si tu .ui usa otro nombre

# ------------------ Configuración ------------------
CAMPOS = ["nombre", "apellido", "pref_con", "pref_sin", "rol"]

# Tolerancia de cabeceras "bonitas" al importar CSV
CSV_MAP = {
    "nombre": "nombre",
    "apellido": "apellido",
    "prefiere con": "pref_con",
    "preferencias de con quien estar": "pref_con",
    "preferencias de con quién estar": "pref_con",
    "prefiere sin": "pref_sin",
    "preferencias de con quien no estar": "pref_sin",
    "preferencias de con quién no estar": "pref_sin",
    "rol": "rol",
}

def invitado_vacio():
    """Crea un dict base para un invitado."""
    return {k: "" for k in CAMPOS}

def slug(texto: str) -> str:
    """Convierte un texto a un nombre de archivo seguro."""
    s = re.sub(r"[^\w\s-]", "", texto, flags=re.UNICODE)
    s = re.sub(r"\s+", "_", s.strip())
    return s.lower() or "archivo"

def buscar_qss(nombre="styleInvitados.qss", desde_ruta=__file__, max_up=2):
    """Busca un QSS subiendo hasta 'max_up' niveles desde 'desde_ruta'."""
    ruta = os.path.abspath(os.path.dirname(desde_ruta))
    for _ in range(max_up + 1):
        candidato = os.path.join(ruta, nombre)
        if os.path.exists(candidato):
            return candidato
        ruta = os.path.abspath(os.path.join(ruta, ".."))
    return None

# ------------------ Diálogo añadir/editar ------------------
class InvitadoDialog(QDialog):
    """Formulario modal sencillo para crear/editar un invitado."""
    def __init__(self, invitado=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Invitado")
        self.setModal(True)

        self.edtNombre   = QLineEdit()
        self.edtApellido = QLineEdit()
        self.cmbPrefCon  = QComboBox(); self.cmbPrefCon.addItems(["", "A", "B", "C"])
        self.cmbPrefSin  = QComboBox(); self.cmbPrefSin.addItems(["", "X", "Y", "Z"])
        self.cmbRol      = QComboBox(); self.cmbRol.addItems(["", "Novio/a", "Familia", "Amigo/a", "Trabajo"])

        form = QFormLayout(self)
        form.addRow("Nombre:",   self.edtNombre)
        form.addRow("Apellido:", self.edtApellido)
        form.addRow("Preferencias de con quién estar:", self.cmbPrefCon)
        form.addRow("Preferencias de con quién no estar:", self.cmbPrefSin)
        form.addRow("Rol:", self.cmbRol)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

        if invitado:
            self.edtNombre.setText(invitado.get("nombre", ""))
            self.edtApellido.setText(invitado.get("apellido", ""))
            self.cmbPrefCon.setCurrentText(invitado.get("pref_con", ""))
            self.cmbPrefSin.setCurrentText(invitado.get("pref_sin", ""))
            self.cmbRol.setCurrentText(invitado.get("rol", ""))

    def datos(self):
        """Devuelve los datos del formulario como dict."""
        return {
            "nombre":   self.edtNombre.text().strip(),
            "apellido": self.edtApellido.text().strip(),
            "pref_con": self.cmbPrefCon.currentText(),
            "pref_sin": self.cmbPrefSin.currentText(),
            "rol":      self.cmbRol.currentText(),
        }

# ------------------ Controlador ------------------
class VPantallaInvitados(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Datos en memoria
        self.invitados = []
        self.nombre_evento = "Nombre del Evento"

        # Estilos y UI
        self._cargar_qss()
        self._config_labels()
        self._config_tabla()
        self._conectar_senales()

        # Estado inicial
        self.refrescar_tabla()

    # ---------- QSS ----------
    def _cargar_qss(self):
        try:
            ruta = buscar_qss()
            print("[QSS] cargando:", ruta)  # <--- ayuda a detectar qué archivo da warnings
            if ruta:
                with open(ruta, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            else:
                print("[QSS] styleInvitados.qss no encontrado (no rompe).")
        except Exception as e:
            print(f"[QSS] Error: {e}")

    # ---------- Título / sección ----------
    def _config_labels(self):
        if hasattr(self.ui, "lblSeccion"):
            self.ui.lblSeccion.setText("Invitados")
        self._pintar_titulo()

    def set_evento(self, nombre: str):
        """Actualiza el nombre del evento mostrado en el título."""
        self.nombre_evento = nombre or "Nombre del Evento"
        self._pintar_titulo()

    def _pintar_titulo(self):
        if hasattr(self.ui, "lblTitulo"):
            self.ui.lblTitulo.setText(f"LISTA DE PARTICIPANTES: [{self.nombre_evento}]")

    # ---------- Tabla ----------
    def _config_tabla(self):
        tbl = self.ui.tblInvitados
        tbl.setColumnCount(5)
        tbl.setHorizontalHeaderLabels([
            "Nombre",
            "Apellido",
            "Preferencias de con quién estar",
            "Preferencias de con quién no estar",
            "Rol",
        ])
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.setSelectionBehavior(tbl.SelectRows)           # filas completas
        tbl.setSelectionMode(tbl.ExtendedSelection)        # múltiple (Eliminar)
        tbl.setEditTriggers(tbl.NoEditTriggers)
        tbl.setAlternatingRowColors(True)                  # activa alternate-background-color del QSS
        tbl.doubleClicked.connect(self._on_double_click_editar)

    def refrescar_tabla(self, filtro: str = ""):
        datos = self._filtrar(filtro)
        tbl = self.ui.tblInvitados
        tbl.setRowCount(len(datos))
        for r, inv in enumerate(datos):
            valores = [
                inv.get("nombre", ""),
                inv.get("apellido", ""),
                inv.get("pref_con", ""),
                inv.get("pref_sin", ""),
                inv.get("rol", "")
            ]
            for c, val in enumerate(valores):
                tbl.setItem(r, c, QTableWidgetItem(str(val)))

    def _filtrar(self, texto: str):
        if not texto:
            return self.invitados
        f = texto.lower().strip()
        return [
            d for d in self.invitados
            if f in (d.get("nombre", "") + " " + d.get("apellido", "")).lower()
        ]

    def _fila_seleccionada(self):
        idxs = self.ui.tblInvitados.selectionModel().selectedRows()
        return idxs[0].row() if idxs else -1

    def _filas_seleccionadas(self):
        return sorted([i.row() for i in self.ui.tblInvitados.selectionModel().selectedRows()])

    # ---------- Señales ----------
    def _conectar_senales(self):
        if hasattr(self.ui, "btnAnadir"):
            self.ui.btnAnadir.clicked.connect(self.on_add)
        if hasattr(self.ui, "btnEditar"):
            self.ui.btnEditar.clicked.connect(self.on_edit)
        if hasattr(self.ui, "btnEliminar"):
            self.ui.btnEliminar.clicked.connect(self.on_delete)
        if hasattr(self.ui, "btnSubirCSV"):
            self.ui.btnSubirCSV.clicked.connect(self.on_import_csv)
        if hasattr(self.ui, "btnGenerarMesas"):
            self.ui.btnGenerarMesas.clicked.connect(self.on_generar_mesas)

        if hasattr(self.ui, "txtBuscar"):
            self.ui.txtBuscar.textChanged.connect(lambda t: self.refrescar_tabla(t))
        if hasattr(self.ui, "btnBuscar"):
            self.ui.btnBuscar.clicked.connect(lambda: self.refrescar_tabla(self.ui.txtBuscar.text()))

        if hasattr(self.ui, "btnMenuTabla"):
            # usar el enum de QToolButton, no del propio botón (más fiable)
            self.ui.btnMenuTabla.setPopupMode(QToolButton.MenuButtonPopup)
            menu = QMenu(self)
            act_export = menu.addAction("Exportar CSV")
            act_sel_all = menu.addAction("Seleccionar todo")
            act_unsel   = menu.addAction("Deseleccionar todo")
            act_invsel  = menu.addAction("Invertir selección")
            act_export.triggered.connect(self.on_export_csv)
            act_sel_all.triggered.connect(lambda: self.ui.tblInvitados.selectAll())
            act_unsel.triggered.connect(lambda: self.ui.tblInvitados.clearSelection())
            act_invsel.triggered.connect(self._invertir_seleccion)
            self.ui.btnMenuTabla.setMenu(menu)

    def _invertir_seleccion(self):
        tbl = self.ui.tblInvitados
        total = tbl.rowCount()
        actuales = {idx.row() for idx in tbl.selectionModel().selectedRows()}
        tbl.clearSelection()
        for r in range(total):
            if r not in actuales:
                tbl.selectRow(r)

    # ---------- Doble click = editar ----------
    def _on_double_click_editar(self, *args):
        self.on_edit()

    # ---------- CRUD ----------
    def on_add(self):
        dlg = InvitadoDialog(parent=self)
        if dlg.exec_() == QDialog.Accepted:
            datos = dlg.datos()
            if not datos["nombre"]:
                QMessageBox.warning(self, "Validación", "El nombre es obligatorio.")
                return
            self.invitados.append(datos)
            self.refrescar_tabla(self.ui.txtBuscar.text() if hasattr(self.ui, "txtBuscar") else "")

    def on_edit(self):
        fila = self._fila_seleccionada()
        if fila < 0:
            QMessageBox.information(self, "Editar", "Selecciona un invitado (clic en la fila).")
            return
        actual = self._datos_por_fila(fila)
        dlg = InvitadoDialog(actual, self)
        if dlg.exec_() == QDialog.Accepted:
            self.invitados[fila] = dlg.datos()
            self.refrescar_tabla(self.ui.txtBuscar.text() if hasattr(self.ui, "txtBuscar") else "")

    def on_delete(self):
        filas = self._filas_seleccionadas()
        if not filas:
            QMessageBox.information(self, "Eliminar", "Selecciona uno o varios invitados (clic en las filas).")
            return
        if QMessageBox.question(self, "Eliminar", f"¿Eliminar {len(filas)} invitado(s)?") != QMessageBox.Yes:
            return
        for f in sorted(filas, reverse=True):
            del self.invitados[f]
        self.refrescar_tabla(self.ui.txtBuscar.text() if hasattr(self.ui, "txtBuscar") else "")

    def _datos_por_fila(self, fila: int):
        d = {}
        for c, k in enumerate(CAMPOS):
            it = self.ui.tblInvitados.item(fila, c)
            d[k] = it.text() if it else ""
        return d

    # ---------- CSV ----------
    def _normaliza_headers(self, headers):
        """Mapea cabeceras del CSV a claves internas."""
        norm = []
        for h in headers:
            norm.append(CSV_MAP.get(h.strip().lower(), None))
        return norm

    def on_import_csv(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Importar CSV", "", "CSV (*.csv)")
        if not ruta:
            return
        try:
            with open(ruta, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
            if not rows:
                QMessageBox.warning(self, "Importación", "El CSV está vacío.")
                return

            headers = self._normaliza_headers(rows[0])
            if any(h is None for h in headers):
                raise ValueError("Cabeceras no reconocidas. Usa: nombre, apellido, (prefiere con), (prefiere sin), rol")

            nuevos = []
            for row in rows[1:]:
                if not any(cell.strip() for cell in row):
                    continue
                inv = invitado_vacio()
                for idx, key in enumerate(headers):
                    if key and idx < len(row):
                        inv[key] = row[idx].strip()
                nuevos.append(inv)

            self.invitados.extend(nuevos)
            self.refrescar_tabla(self.ui.txtBuscar.text() if hasattr(self.ui, "txtBuscar") else "")
            QMessageBox.information(self, "Importación", f"Importados {len(nuevos)} invitados.")
        except Exception as e:
            QMessageBox.critical(self, "Error CSV", str(e))

    def on_export_csv(self):
        if not self.invitados:
            QMessageBox.information(self, "Exportar", "No hay datos para exportar.")
            return
        nombre = slug(f"invitados_{self.nombre_evento}") + ".csv"
        ruta, _ = QFileDialog.getSaveFileName(self, "Exportar CSV", nombre, "CSV (*.csv)")
        if not ruta:
            return
        try:
            with open(ruta, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CAMPOS)
                writer.writeheader()
                writer.writerows(self.invitados)
            QMessageBox.information(self, "Exportación", "CSV guardado correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error CSV", str(e))

    # ---------- Generar mesas (stub) ----------
    def on_generar_mesas(self):
        QMessageBox.information(
            self, "Generar mesas",
            "Aquí irá tu lógica de asignación de mesas.\nDe momento es un placeholder."
        )
