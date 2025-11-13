# VPantallaInvitados.py
# Pantalla de Invitados sin columna ROL + guardado automático por evento

import os
import csv
import re
from PyQt5.QtWidgets import QDialog

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QFileDialog, QTableWidgetItem, QMessageBox, QMenu,
    QToolButton
)

from Vistas.pantalla2_ui import Ui_MainWindow
from WAnadirPersona import WAnadirPersona 

# ------------------ Configuración ------------------
CAMPOS = ["nombre", "apellido", "pref_con", "pref_sin"]

CSV_MAP = {
    "nombre": "nombre",
    "apellido": "apellido",
    "prefiere con": "pref_con",
    "preferencias de con quien estar": "pref_con",
    "preferencias de con quién estar": "pref_con",
    "prefiere sin": "pref_sin",
    "preferencias de con quien no estar": "pref_sin",
    "preferencias de con quién no estar": "pref_sin",
}


def invitado_vacio():
    return {k: "" for k in CAMPOS}


def slug(texto: str) -> str:
    s = re.sub(r"[^\w\s-]", "", texto, flags=re.UNICODE)
    s = re.sub(r"\s+", "_", s.strip())
    return s.lower() or "archivo"


def buscar_qss(nombre="styleInvitados.qss", desde_ruta=__file__, max_up=2):
    ruta = os.path.abspath(os.path.dirname(desde_ruta))
    for _ in range(max_up + 1):
        candidato = os.path.join(ruta, nombre)
        if os.path.exists(candidato):
            return candidato
        ruta = os.path.abspath(os.path.join(ruta, ".."))
    return None


# ------------------ Controlador ------------------
class VPantallaInvitados(QMainWindow):
    def __init__(self, evento=None, router=None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.router = router
        self.evento = evento or {}

        self.nombre_evento = (
            self.evento.get("tipo")
            or self.evento.get("nombre")
            or "Nombre del Evento"
        )

        # Lista interna de invitados (dicts con claves CAMPOS)
        self.invitados = []

        self._cargar_qss()
        self._config_labels()
        self._config_tabla()
        self._conectar_senales()

        # Cargar CSV propio del evento (si existe)
        self._cargar_csv_evento()

        # Pintar tabla
        self.refrescar_tabla()

    # ---------- QSS ----------
    def _cargar_qss(self):
        try:
            ruta = buscar_qss()
            if ruta:
                with open(ruta, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"[QSS] Error: {e}")

    # ---------- Título y cabeceras ----------
    def _config_labels(self):
        if hasattr(self.ui, "lblSeccion"):
            self.ui.lblSeccion.setText("Invitados")
        self._pintar_titulo()

    def set_evento(self, nombre: str):
        self.nombre_evento = nombre
        self._pintar_titulo()

    def _pintar_titulo(self):
        self.ui.lblTitulo.setText(f"LISTA DE PARTICIPANTES: [{self.nombre_evento}]")

    # ---------- Tabla ----------
    def _config_tabla(self):
        tbl = self.ui.tblInvitados
        tbl.setColumnCount(4)
        tbl.setHorizontalHeaderLabels(
            [
                "Nombre",
                "Apellido",
                "Pref de estar",
                "Preferencias de con quien no estar",
            ]
        )
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.setSelectionBehavior(tbl.SelectRows)
        tbl.setSelectionMode(tbl.ExtendedSelection)
        tbl.setEditTriggers(tbl.NoEditTriggers)
        tbl.setAlternatingRowColors(True)
        tbl.doubleClicked.connect(self._on_double_click_editar)

    def refrescar_tabla(self, filtro=""):
        datos = self._filtrar(filtro)
        tbl = self.ui.tblInvitados
        tbl.setRowCount(len(datos))

        for r, inv in enumerate(datos):
            valores = [
                inv.get("nombre", ""),
                inv.get("apellido", ""),
                inv.get("pref_con", ""),
                inv.get("pref_sin", ""),
            ]
            for c, val in enumerate(valores):
                tbl.setItem(r, c, QTableWidgetItem(str(val)))

    def _filtrar(self, texto):
        if not texto:
            return self.invitados
        f = texto.lower().strip()
        return [
            d
            for d in self.invitados
            if f in (d.get("nombre", "") + " " + d.get("apellido", "")).lower()
        ]

    # ---------- Selección ----------
    def _fila_seleccionada(self):
        idxs = self.ui.tblInvitados.selectionModel().selectedRows()
        return idxs[0].row() if idxs else -1

    def _filas_seleccionadas(self):
        return sorted(
            [i.row() for i in self.ui.tblInvitados.selectionModel().selectedRows()]
        )

    # ---------- Señales ----------
    def _conectar_senales(self):
        ui = self.ui

        if hasattr(ui, "btnAnadir"):
            ui.btnAnadir.clicked.connect(self.on_add)
        if hasattr(ui, "btnEditar"):
            ui.btnEditar.clicked.connect(self.on_edit)
        if hasattr(ui, "btnEliminar"):
            ui.btnEliminar.clicked.connect(self.on_delete)
        if hasattr(ui, "btnSubirCSV"):
            ui.btnSubirCSV.clicked.connect(self.on_import_csv)
        if hasattr(ui, "btnGenerarMesas"):
            ui.btnGenerarMesas.clicked.connect(self.on_generar_mesas)

        if hasattr(ui, "txtBuscar"):
            ui.txtBuscar.textChanged.connect(lambda t: self.refrescar_tabla(t))

        if hasattr(ui, "btnBuscar"):
            ui.btnBuscar.clicked.connect(
                lambda: self.refrescar_tabla(ui.txtBuscar.text())
            )

        if hasattr(ui, "btnMenuTabla"):
            ui.btnMenuTabla.setPopupMode(QToolButton.MenuButtonPopup)
            menu = QMenu(self)
            act_export = menu.addAction("Exportar CSV")
            act_sel_all = menu.addAction("Seleccionar todo")
            act_unsel = menu.addAction("Deseleccionar todo")
            act_invsel = menu.addAction("Invertir selección")

            act_export.triggered.connect(self.on_export_csv)
            act_sel_all.triggered.connect(lambda: ui.tblInvitados.selectAll())
            act_unsel.triggered.connect(lambda: ui.tblInvitados.clearSelection())
            act_invsel.triggered.connect(self._invertir_seleccion)

            ui.btnMenuTabla.setMenu(menu)

    # ---------- Menú tabla ----------
    def _invertir_seleccion(self):
        tbl = self.ui.tblInvitados
        total = tbl.rowCount()
        actuales = {idx.row() for idx in tbl.selectionModel().selectedRows()}
        tbl.clearSelection()
        for r in range(total):
            if r not in actuales:
                tbl.selectRow(r)

    # ---------- CRUD ----------
    def _on_double_click_editar(self, *_):
        self.on_edit()

    def on_add(self):
        """Añadir invitado usando la ventana azul WAnadirPersona."""
        dlg = WAnadirPersona(self)   # solo pasamos la ventana como parent

        if dlg.exec_() == QDialog.Accepted:
            datos = dlg.datos()  # dict con nombre, apellido, pref_con, pref_sin

            if not datos.get("nombre"):
                QMessageBox.warning(self, "Validación", "El nombre es obligatorio.")
                return

            # Añadimos a la lista interna y refrescamos la tabla
            self.invitados.append(datos)
            self.refrescar_tabla()


    def on_edit(self):
        """Abrir ventana WAñadirPersona en modo EDICIÓN."""
        fila = self._fila_seleccionada()
        if fila < 0:
            QMessageBox.information(self, "Editar", "Selecciona un invitado.")
            return

        invitado = self.invitados[fila]
        dlg = WAnadirPersona(self, invitado=invitado, indice=fila)
        dlg.exec_()   # la ventana actualiza y refresca

    def on_delete(self):
        filas = self._filas_seleccionadas()
        if not filas:
            QMessageBox.information(self, "Eliminar", "Selecciona invitado(s).")
            return

        if (
            QMessageBox.question(
                self, "Eliminar", f"¿Eliminar {len(filas)} invitado(s)?"
            )
            != QMessageBox.Yes
        ):
            return

        for f in reversed(filas):
            del self.invitados[f]

        self.refrescar_tabla()

    def _datos_por_fila(self, fila):
        return {
            k: (
                self.ui.tblInvitados.item(fila, i).text()
                if self.ui.tblInvitados.item(fila, i)
                else ""
            )
            for i, k in enumerate(CAMPOS)
        }

    # ---------- CSV ----------
    def _normaliza_headers(self, headers):
        """Mapea cabeceras del CSV a claves internas, limpiando BOM y símbolos extra."""
        norm = []
        for h in headers:
            base = h.strip().lower()
            base = base.lstrip("\ufeff")
            base = base.strip(" ;:,")
            if base in CAMPOS:
                norm.append(base)
            else:
                norm.append(CSV_MAP.get(base, None))
        return norm

    def on_import_csv(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Importar CSV", "", "CSV (*.csv)"
        )
        if not ruta:
            return

        try:
            with open(ruta, newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))

            if not rows:
                QMessageBox.warning(self, "CSV vacío", "El archivo está vacío.")
                return

            headers = self._normaliza_headers(rows[0])
            nuevos = []

            for row in rows[1:]:
                if not any(cell.strip() for cell in row):
                    continue

                inv = invitado_vacio()
                for i, key in enumerate(headers):
                    if key and key in CAMPOS and i < len(row):
                        inv[key] = row[i].strip()

                nuevos.append(inv)

            self.invitados.extend(nuevos)
            self.refrescar_tabla()
            QMessageBox.information(self, "Importado", "CSV cargado correctamente.")

        except Exception as e:
            QMessageBox.critical(self, "Error CSV", str(e))

    def on_export_csv(self):
        if not self.invitados:
            QMessageBox.information(
                self, "Exportar", "No hay datos para exportar."
            )
            return

        nombre = slug(f"invitados_{self.nombre_evento}") + ".csv"
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar CSV", nombre, "CSV (*.csv)"
        )
        if not ruta:
            return

        try:
            with open(ruta, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CAMPOS)
                writer.writeheader()
                writer.writerows(self.invitados)

            QMessageBox.information(
                self, "Exportado", "CSV guardado correctamente."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error CSV", str(e))

    # ---------- CSV Automático por evento ----------
    def _cargar_csv_evento(self):
        ruta = self.evento.get("csv_invitados")
        if not ruta or not os.path.exists(ruta):
            return

        try:
            with open(ruta, newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))
            headers = self._normaliza_headers(rows[0])

            invitados = []
            for row in rows[1:]:
                inv = invitado_vacio()
                for i, key in enumerate(headers):
                    if key and i < len(row):
                        inv[key] = row[i].strip()
                invitados.append(inv)

            self.invitados = invitados

        except Exception as e:
            print(f"[CSV] Error al cargar CSV del evento: {e}")

    def _guardar_csv_evento(self):
        if not self.invitados:
            return

        nombre_archivo = slug(f"invitados_{self.nombre_evento}") + ".csv"
        ruta = os.path.abspath(nombre_archivo)

        try:
            with open(ruta, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CAMPOS)
                writer.writeheader()
                writer.writerows(self.invitados)

            self.evento["csv_invitados"] = ruta

            if self.router:
                self.router.guardar_eventos()

            print(f"[CSV] Guardado automático: {ruta}")

        except Exception as e:
            print(f"[CSV] Error guardando: {e}")

    # ---------- Hook de cierre ----------
    def closeEvent(self, event):
        try:
            self._guardar_csv_evento()
        except Exception as e:
            print(f"[CLOSE] Error guardando CSV: {e}")

        super().closeEvent(event)

    # ---------- Mesas (placeholder) ----------
    def on_generar_mesas(self):
        QMessageBox.information(self, "Generar mesas", "FALTA TU MÉTODO AQUÍ")
