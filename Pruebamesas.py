import sys, math, json
from PyQt5 import QtWidgets, QtGui, QtCore

import ui_mesa
try:
    import resources_rc  # si has compilado resources.qrc
except Exception:
    pass

ICON_SIZE = 56
MARGIN = 24

# Busca el icono en recursos o disco
def qrc_or_disk(path_qrc: str, path_disk: str) -> str:
    pm = QtGui.QPixmap(path_qrc)
    return path_qrc if not pm.isNull() else path_disk

# Devuelve la ruta del icono según el estado
def icon_for_state(estado: str, is_empty: bool) -> str:
    if is_empty:
        return qrc_or_disk(":/newPrefix/Resources/Icons/gris_transparente.png",
                           "Resources/Icons/gris_transparente.png")
    e = (estado or "").strip().lower()
    if e in ("ok", "verde"):
        fn = "Verde.png"
    elif e in ("conflicto", "rojo"):
        fn = "Rojo.png"
    elif e in ("advertencia", "amarillo", "naranja"):
        fn = "Naranja.png"
    elif e in ("manual", "azul"):
        fn = "Azul.png"
    else:
        fn = "Verde.png"
    return qrc_or_disk(f":/newPrefix/Resources/Icons/{fn}",
                       f"Resources/Icons/{fn}")

# Clase para representar un asiento con icono
class SeatIcon(QtWidgets.QLabel):
    dropped = QtCore.pyqtSignal(int, dict)  # señal: asiento, invitado

    def __init__(self, parent, seat_idx: int):
        super().__init__(parent)
        self.seat_idx = seat_idx
        self.setAcceptDrops(True)
        self.setMinimumSize(ICON_SIZE, ICON_SIZE)
        self.setMaximumSize(ICON_SIZE, ICON_SIZE)
        self.setScaledContents(True)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("QLabel{background:transparent;}")

    # Permitir arrastrar invitados sobre el asiento
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-guest"):
            event.acceptProposedAction()
        else:
            event.ignore()

    # Al soltar un invitado, emite la señal con los datos
    def dropEvent(self, event: QtGui.QDropEvent):
        md = event.mimeData()
        if md.hasFormat("application/x-guest"):
            payload = md.data("application/x-guest").data()
            try:
                info = json.loads(payload.decode("utf-8"))
            except Exception:
                info = {}
            guest = {
                "nombre": info.get("nombre", ""),
                "estado": "manual",  # al colocar manualmente -> azul
            }
            self.dropped.emit(self.seat_idx, guest)
            event.acceptProposedAction()
        else:
            event.ignore()

# Tabla que permite arrastrar los invitados
class DraggableInvitadosTable(QtWidgets.QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.viewport().setAcceptDrops(False)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)

    # Configura el arrastre sin icono molesto
    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if not (event.buttons() & QtCore.Qt.LeftButton):
            return super().mouseMoveEvent(event)
        idxs = self.selectionModel().selectedRows()
        if not idxs:
            return super().mouseMoveEvent(event)

        row = idxs[0].row()
        nombre = self.item(row, 0).text() if self.item(row, 0) else ""
        estado = self.item(row, 1).text() if self.item(row, 1) else ""

        drag = QtGui.QDrag(self)
        mime = QtCore.QMimeData()
        payload = json.dumps({"nombre": nombre, "estado": estado}).encode("utf-8")
        mime.setData("application/x-guest", payload)
        drag.setMimeData(mime)

        pm = QtGui.QPixmap(ICON_SIZE, ICON_SIZE)
        pm.fill(QtCore.Qt.transparent)
        drag.setPixmap(pm)
        drag.setHotSpot(QtCore.QPoint(ICON_SIZE // 2, ICON_SIZE // 2))
        drag.exec_(QtCore.Qt.CopyAction)

# Clase principal de la ventana
class Main(QtWidgets.QMainWindow, ui_mesa.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self._kill_arena_layout_once()

        # Reemplaza la tabla por una versión arrastrable
        parent = self.tblInvitados.parent()
        layout = parent.layout()
        layout.removeWidget(self.tblInvitados)
        self.tblInvitados.deleteLater()
        self.tblInvitados = DraggableInvitadosTable(parent)
        layout.addWidget(self.tblInvitados)

        # Configuración de tablas
        self.tblMesas.setColumnCount(2)
        self.tblMesas.setHorizontalHeaderLabels(["Mesa", "Capacidad"])
        self.tblMesas.horizontalHeader().setStretchLastSection(True)

        self.tblInvitados.setColumnCount(2)
        self.tblInvitados.setHorizontalHeaderLabels(["Nombre", "Estado"])
        self.tblInvitados.horizontalHeader().setStretchLastSection(True)

        # Datos iniciales
        self.mesas = self._crear_mesas_demo()
        self.mesa_keys = list(self.mesas.keys())
        self.current_mesa_key = self.mesa_keys[0]

        # Invitados disponibles
        self.pool = self._demo_pool()
        self._reload_pool_table()

        # Cargar las mesas
        self._reload_tbl_mesas()

        # Zona de asientos
        self.seat_widgets = []
        self.arena.installEventFilter(self)
        self._render_seats()

        # Conexión de botones
        self.tblMesas.selectionModel().selectionChanged.connect(self._on_select_mesa)
        self.btnAnadir.clicked.connect(self._anadir_demo)
        self.btnEliminar.clicked.connect(self._eliminar_demo)
        self.btnConfirmar.clicked.connect(self._confirmar_demo)

    # Datos de ejemplo
    def _crear_mesas_demo(self):
        return {
            "Mesa 1": {
                "capacidad": 10,
                "invitados": [
                    {"nombre": "María", "estado": "ok"},
                    {"nombre": "Pablo", "estado": "advertencia"},
                    {"nombre": "José",  "estado": "ok"},
                    {"nombre": "Lucía", "estado": "ok"},
                    {"nombre": "Laura", "estado": "manual"},
                    {"nombre": "Pepe",  "estado": "conflicto"},
                    {"nombre": "Sara",  "estado": "ok"},
                    {"nombre": "", "estado": "vacio"},
                    {"nombre": "", "estado": "vacio"},
                    {"nombre": "", "estado": "vacio"},
                ],
            },
            "Mesa 2": {
                "capacidad": 8,
                "invitados": [
                    {"nombre": "Alba",  "estado": "ok"},
                    {"nombre": "Nico",  "estado": "ok"},
                    {"nombre": "", "estado": "vacio"},
                    {"nombre": "Raúl",  "estado": "conflicto"},
                    {"nombre": "", "estado": "vacio"},
                    {"nombre": "Iris",  "estado": "advertencia"},
                    {"nombre": "", "estado": "vacio"},
                    {"nombre": "", "estado": "vacio"},
                ],
            },
            "Mesa 3": {
                "capacidad": 6,
                "invitados": [
                    {"nombre": "", "estado": "vacio"},
                    {"nombre": "", "estado": "vacio"},
                    {"nombre": "Lola",  "estado": "ok"},
                    {"nombre": "Dani",  "estado": "ok"},
                    {"nombre": "", "estado": "vacio"},
                    {"nombre": "Óscar", "estado": "ok"},
                ],
            },
        }

    def _demo_pool(self):
        return [
            {"nombre": "Álvaro", "estado": "ok"},
            {"nombre": "Irene",  "estado": "advertencia"},
            {"nombre": "David",  "estado": "ok"},
            {"nombre": "Noa",    "estado": "conflicto"},
            {"nombre": "Vera",   "estado": "ok"},
            {"nombre": "Yago",   "estado": "ok"},
        ]

    # Recarga la tabla de invitados
    def _reload_pool_table(self):
        self.tblInvitados.setRowCount(len(self.pool))
        for r, g in enumerate(self.pool):
            self.tblInvitados.setItem(r, 0, QtWidgets.QTableWidgetItem(g["nombre"]))
            self.tblInvitados.setItem(r, 1, QtWidgets.QTableWidgetItem(g.get("estado", "")))

    # Carga la tabla de mesas
    def _reload_tbl_mesas(self):
        self.tblMesas.setRowCount(len(self.mesa_keys))
        for r, key in enumerate(self.mesa_keys):
            cap = self.mesas[key]["capacidad"]
            self.tblMesas.setItem(r, 0, QtWidgets.QTableWidgetItem(key))
            self.tblMesas.setItem(r, 1, QtWidgets.QTableWidgetItem(str(cap)))
        for r, k in enumerate(self.mesa_keys):
            if k == self.current_mesa_key:
                self.tblMesas.selectRow(r)
                break

    # Cambia la mesa seleccionada
    def _on_select_mesa(self, *_):
        idxs = self.tblMesas.selectionModel().selectedRows()
        if not idxs:
            return
        row = idxs[0].row()
        self.current_mesa_key = self.mesa_keys[row]
        self._render_seats()

    # Busca el primer asiento vacío
    def _first_empty_index(self, invitados):
        for i, it in enumerate(invitados):
            if not (it.get("nombre") or "").strip():
                return i
        return None

    # Elimina un invitado de la lista general (pool)
    def _remove_guest_from_pool_by_name(self, nombre: str):
        nombre = (nombre or "").strip()
        if not nombre:
            return
        for i, g in enumerate(self.pool):
            if (g.get("nombre") or "").strip() == nombre:
                self.pool.pop(i)
                break
        self._reload_pool_table()

    # Limpia la zona de asientos
    def _kill_arena_layout_once(self):
        lay = self.arena.layout()
        if lay:
            while lay.count():
                item = lay.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()
            self.arena.setLayout(None)
            try:
                lay.deleteLater()
            except Exception:
                pass

    def _clear_arena(self):
        self._kill_arena_layout_once()
        for w in self.arena.findChildren(QtWidgets.QWidget):
            w.setParent(None)
            w.deleteLater()
        self.seat_widgets.clear()

    # Dibuja los asientos de la mesa
    def _render_seats(self):
        self._clear_arena()

        mesa = self.mesas[self.current_mesa_key]
        capacidad = mesa["capacidad"]
        invitados = list(mesa["invitados"])

        ocupados = sum(1 for i in invitados if (i.get("nombre") or "").strip())
        if hasattr(self, "lblAsientos"):
            self.lblAsientos.setText(f"Asientos: {ocupados}/{capacidad}")
        if hasattr(self, "lblTituloMesa"):
            self.lblTituloMesa.setText(self.current_mesa_key)

        arena_w, arena_h = self.arena.width(), self.arena.height()
        cx, cy = arena_w // 2, arena_h // 2
        r = min(arena_w, arena_h) // 2 - MARGIN - ICON_SIZE // 2
        if r < 40:
            r = 40

        n_slots = max(capacidad, 1)
        start = -math.pi / 2
        step = 2 * math.pi / n_slots

        if len(invitados) < capacidad:
            invitados += [{"nombre": "", "estado": "vacio"}] * (capacidad - len(invitados))

        for idx in range(n_slots):
            info = invitados[idx]
            ang = start + idx * step
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)

            seat = SeatIcon(self.arena, idx)
            seat.dropped.connect(self._handle_drop_guest)
            path = icon_for_state(info.get("estado"), is_empty=(not (info.get("nombre") or "").strip()))
            seat.setPixmap(QtGui.QPixmap(path))
            seat.move(int(x - ICON_SIZE / 2), int(y - ICON_SIZE / 2))
            seat.show()

            nombre = (info.get("nombre") or "").strip()
            name_lbl = None
            if nombre:
                name_lbl = QtWidgets.QLabel(self.arena)
                name_lbl.setText(nombre)
                name_lbl.adjustSize()
                name_lbl.setAlignment(QtCore.Qt.AlignCenter)
                name_lbl.move(int(x - name_lbl.width() / 2), int(y + ICON_SIZE / 2 + 4))
                name_lbl.show()

            self.seat_widgets.append((seat, name_lbl))

    # Maneja el arrastre de invitados
    def _handle_drop_guest(self, seat_idx: int, guest: dict):
        mesa = self.mesas[self.current_mesa_key]
        invitados = mesa["invitados"]

        if seat_idx >= len(invitados):
            invitados += [{"nombre": "", "estado": "vacio"}] * (seat_idx - len(invitados) + 1)

        prev = invitados[seat_idx]
        if (prev.get("nombre") or "").strip():
            self.pool.append({"nombre": prev["nombre"], "estado": prev.get("estado", "ok")})

        self._remove_guest_from_pool_by_name(guest.get("nombre", ""))
        invitados[seat_idx] = {"nombre": guest.get("nombre", ""), "estado": "manual"}
        mesa["invitados"] = invitados

        self._reload_pool_table()
        self._render_seats()

    # Añadir invitado a la mesa actual
    def _anadir_demo(self):
        idxs = self.tblInvitados.selectionModel().selectedRows()
        if not idxs:
            QtWidgets.QMessageBox.warning(self, "Añadir invitado",
                                          "Selecciona un invitado de la lista para añadirlo a la mesa.")
            return

        row = idxs[0].row()
        nombre_item = self.tblInvitados.item(row, 0)
        estado_item = self.tblInvitados.item(row, 1)
        nombre = nombre_item.text() if nombre_item else ""
        _estado = estado_item.text() if estado_item else "ok"

        mesa = self.mesas[self.current_mesa_key]
        invitados = mesa["invitados"]
        idx_libre = self._first_empty_index(invitados)
        if idx_libre is None:
            QtWidgets.QMessageBox.information(self, "Mesa completa",
                                              f"{self.current_mesa_key} no tiene asientos libres.")
            return

        invitados[idx_libre] = {"nombre": nombre, "estado": "manual"}
        mesa["invitados"] = invitados
        self._remove_guest_from_pool_by_name(nombre)
        self._render_seats()

    # Eliminar último invitado de la mesa actual
    def _eliminar_demo(self):
        mesa = self.mesas[self.current_mesa_key]
        invitados = mesa["invitados"]
        for i in range(len(invitados) - 1, -1, -1):
            if (invitados[i].get("nombre") or "").strip():
                self.pool.append({"nombre": invitados[i]["nombre"],
                                  "estado": invitados[i].get("estado", "ok")})
                invitados[i] = {"nombre": "", "estado": "vacio"}
                self._reload_pool_table()
                break
        self._render_seats()

    # Confirmar ocupación
    def _confirmar_demo(self):
        mesa = self.mesas[self.current_mesa_key]
        ocupados = [i for i in mesa["invitados"] if (i.get("nombre") or "").strip()]
        QtWidgets.QMessageBox.information(
            self, "Confirmado",
            f"{self.current_mesa_key}: {len(ocupados)} / {mesa['capacidad']} ocupados."
        )

# Ejecución principal
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = Main()
    w.show()
    sys.exit(app.exec_())
