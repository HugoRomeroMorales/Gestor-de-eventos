import sys, math, json
from typing import List, Optional, Dict
from ortools.sat.python import cp_model
from PyQt5 import QtWidgets, QtGui, QtCore

import ui_mesa

ICON_SIZE = 56
MARGIN = 24

class Invitado:
    def __init__(self, rol: str, nombre: str, apellido: str = "", preferencias: Optional[List[str]] = None):
        self.rol = rol
        self.nombre = nombre
        self.apellido = apellido
        self.preferencias = preferencias or []

class Mesa:
    def __init__(self, mesa_id: int, numAsientos: int, nombMesa: Optional[str] = None,
                 invitados: Optional[List[Optional[Invitado]]] = None):
        self.mesa_id = mesa_id
        self.numAsientos = numAsientos
        self.nombMesa = nombMesa
        self.invitados = invitados or []

class Evento:
    def __init__(self, nombre: str, fecha: str, ubicacion: str, mesas: Optional[List[Mesa]] = None):
        self.nombre = nombre
        self.fecha = fecha
        self.ubicacion = ubicacion
        self.mesas = mesas or []

def crear_invitado(rol: str, nombre: str, apellido: str = "", preferencias: Optional[List[str]] = None):
    return Invitado(rol, nombre, apellido, preferencias)

def crear_mesa(mesa_id: int, numAsientos: int, nombMesa: Optional[str] = None,
               invitados: Optional[List[Optional[Invitado]]] = None):
    inv = invitados or []
    if len(inv) < numAsientos:
        inv += [None] * (numAsientos - len(inv))
    return Mesa(mesa_id, numAsientos, nombMesa, inv)

def crear_evento(nombre: str, fecha: str, ubicacion: str, mesas: Optional[List[Mesa]] = None):
    return Evento(nombre, fecha, ubicacion, mesas)

def _split_pref(pref: str):
    p = (pref or "").strip()
    lower = p.lower()
    if lower.startswith("amigo:"):
        return "amigo", p.split(":", 1)[1].strip()
    if lower.startswith("enemigo:"):
        return "enemigo", p.split(":", 1)[1].strip()
    return None, ""

def _es_enemigo(inv: Invitado, nombre_otro: str) -> bool:
    if not inv or not nombre_otro:
        return False
    for pref in inv.preferencias or []:
        t, who = _split_pref(pref)
        if t == "enemigo" and who == nombre_otro:
            return True
    return False

def calcular_estados_conflicto(mesa: Mesa) -> List[str]:
    estados: List[str] = []
    invitados = mesa.invitados or []
    for i, inv in enumerate(invitados):
        if not inv or not (inv.nombre or "").strip():
            estados.append("vacio")
            continue
        estado = "ok"
        for j, otro in enumerate(invitados):
            if i == j:
                continue
            if not otro or not (otro.nombre or "").strip():
                continue
            if _es_enemigo(inv, otro.nombre) or _es_enemigo(otro, inv.nombre):
                estado = "conflicto"
                break
        estados.append(estado)
    return estados

def asignar_mesas(participantes: List[Invitado], tamano_mesa: int,
                  nombre_evento: str = "Evento", fecha: str = "", ubicacion: str = ""):
    nombres = [i.nombre for i in participantes]
    n = len(participantes)
    num_mesas = max(1, math.ceil(n / tamano_mesa))
    model = cp_model.CpModel()
    mesa_var: Dict[str, cp_model.IntVar] = {nom: model.NewIntVar(0, num_mesas - 1, nom) for nom in nombres}
    nombre_set = set(nombres)
    for inv in participantes:
        amigos, enemigos = [], []
        for pref in inv.preferencias or []:
            t, who = _split_pref(pref)
            if t == "amigo" and who:
                amigos.append(who)
            elif t == "enemigo" and who:
                enemigos.append(who)
        for a in amigos:
            if a in nombre_set:
                model.Add(mesa_var[inv.nombre] == mesa_var[a])
        for e in enemigos:
            if e in nombre_set:
                model.Add(mesa_var[inv.nombre] != mesa_var[e])
    for m in range(num_mesas):
        indicadores = []
        for nom in nombres:
            b = model.NewBoolVar(f"{nom}_en_mesa_{m}")
            model.Add(mesa_var[nom] == m).OnlyEnforceIf(b)
            model.Add(mesa_var[nom] != m).OnlyEnforceIf(b.Not())
            indicadores.append(b)
        model.Add(sum(indicadores) <= tamano_mesa)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return crear_evento(nombre_evento, fecha, ubicacion, []), {}
    mapping = {nom: solver.Value(mesa_var[nom]) for nom in nombres}
    mesas = [crear_mesa(i + 1, tamano_mesa, f"Mesa {i+1}") for i in range(num_mesas)]
    colocados = [0] * num_mesas
    for inv in participantes:
        m_idx = mapping.get(inv.nombre, 0)
        pos = colocados[m_idx]
        if pos < tamano_mesa:
            mesas[m_idx].invitados[pos] = inv
            colocados[m_idx] += 1
    evento = crear_evento(nombre_evento, fecha, ubicacion, mesas)
    return evento, mapping

def icon_for_state(estado: str, is_empty: bool) -> str:
    base = "Resources/Icons"
    if is_empty:
        return f"{base}/gris_transparente.png"
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
    return f"{base}/{fn}"

class SeatIcon(QtWidgets.QLabel):
    dropped = QtCore.pyqtSignal(int, dict)

    def __init__(self, parent, seat_idx: int):
        super().__init__(parent)
        self.seat_idx = seat_idx
        self.setAcceptDrops(True)
        self.setMinimumSize(ICON_SIZE, ICON_SIZE)
        self.setMaximumSize(ICON_SIZE, ICON_SIZE)
        self.setScaledContents(True)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("QLabel{background:transparent;}")

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-guest"):
            event.acceptProposedAction()
        else:
            event.ignore()

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
                "estado": "manual",
            }
            self.dropped.emit(self.seat_idx, guest)
            event.acceptProposedAction()
        else:
            event.ignore()

class DraggableInvitadosTable(QtWidgets.QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
        self.viewport().setAcceptDrops(False)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)

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

class Main(QtWidgets.QMainWindow, ui_mesa.Ui_MainWindow):
    def __init__(self, evento: Evento, invitados_csv: Optional[List[Dict]] = None):
        super().__init__()
        self.setupUi(self)

        self.evento = evento
        self.current_mesa_idx = 0
        self.pool: List[Dict[str, str]] = []

       
        if invitados_csv:
            for d in invitados_csv:
                nombre = (d.get("nombre") or "").strip()
                if not nombre:
                    continue
                self.pool.append({"nombre": nombre, "estado": "ok"})

  
        self.inv_por_nombre: Dict[str, Invitado] = {}
        for mesa in self.evento.mesas:
            for inv in mesa.mesas if False else mesa.invitados:  
                if inv and (inv.nombre or "").strip():
                    self.inv_por_nombre[inv.nombre] = inv

        self._kill_arena_layout_once()
        parent = self.tblInvitados.parent()
        layout = parent.layout()
        layout.removeWidget(self.tblInvitados)
        self.tblInvitados.deleteLater()
        self.tblInvitados = DraggableInvitadosTable(parent)
        layout.addWidget(self.tblInvitados)

        self.tblMesas.setColumnCount(2)
        self.tblMesas.setHorizontalHeaderLabels(["Mesa", "Capacidad"])
        self.tblMesas.horizontalHeader().setStretchLastSection(True)

        self.tblInvitados.setColumnCount(2)
        self.tblInvitados.setHorizontalHeaderLabels(["Nombre", "Estado"])
        self.tblInvitados.horizontalHeader().setStretchLastSection(True)

        self.seat_widgets = []
        self.arena.installEventFilter(self)

        self._reload_pool_table()
        self._reload_tbl_mesas()
        self._render_seats()

        self.tblMesas.selectionModel().selectionChanged.connect(self._on_select_mesa)
        self.btnAnadir.clicked.connect(self._anadir_demo)
        self.btnEliminar.clicked.connect(self._eliminar_demo)
        self.btnConfirmar.clicked.connect(self._confirmar_demo)

    def _get_invitado_by_name(self, nombre: str) -> Optional[Invitado]:
        nombre = (nombre or "").strip()
        if not nombre:
            return None
        inv = self.inv_por_nombre.get(nombre)
        if inv is None:
            inv = crear_invitado("invitado", nombre)
            self.inv_por_nombre[nombre] = inv
        return inv

    def _reload_pool_table(self):
        self.tblInvitados.setRowCount(len(self.pool))
        for r, g in enumerate(self.pool):
            self.tblInvitados.setItem(r, 0, QtWidgets.QTableWidgetItem(g["nombre"]))
            self.tblInvitados.setItem(r, 1, QtWidgets.QTableWidgetItem(g.get("estado", "")))

    def _reload_tbl_mesas(self):
        self.tblMesas.setRowCount(len(self.evento.mesas))
        for r, mesa in enumerate(self.evento.mesas):
            nombre_mesa = mesa.nombMesa or f"Mesa {mesa.mesa_id}"
            self.tblMesas.setItem(r, 0, QtWidgets.QTableWidgetItem(nombre_mesa))
            self.tblMesas.setItem(r, 1, QtWidgets.QTableWidgetItem(str(mesa.numAsientos)))
        if self.evento.mesas:
            self.tblMesas.selectRow(self.current_mesa_idx)

    def _on_select_mesa(self, *_):
        idxs = self.tblMesas.selectionModel().selectedRows()
        if not idxs:
            return
        row = idxs[0].row()
        if 0 <= row < len(self.evento.mesas):
            self.current_mesa_idx = row
            self._render_seats()

    def _first_empty_index(self, mesa_idx: int):
        mesa = self.evento.mesas[mesa_idx]
        for i, inv in enumerate(mesa.invitados):
            if not inv or not (inv.nombre or "").strip():
                return i
        return None

    def _remove_guest_from_pool_by_name(self, nombre: str):
        nombre = (nombre or "").strip()
        if not nombre:
            return
        for i, g in enumerate(self.pool):
            if (g.get("nombre") or "").strip() == nombre:
                self.pool.pop(i)
                break
        self._reload_pool_table()

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

    def _render_seats(self):
        self._clear_arena()

        mesa = self.evento.mesas[self.current_mesa_idx]
        capacidad = mesa.numAsientos
        invitados = mesa.invitados or []

        if len(invitados) < capacidad:
            diff = capacidad - len(invitados)
            invitados += [None] * diff
            mesa.invitados = invitados

        estados = calcular_estados_conflicto(mesa)
        if len(estados) < capacidad:
            estados += ["vacio"] * (capacidad - len(estados))

        ocupados = sum(
            1 for inv in invitados
            if inv and (inv.nombre or "").strip()
        )

        if hasattr(self, "lblAsientos"):
            self.lblAsientos.setText(f"Asientos: {ocupados}/{capacidad}")

        if hasattr(self, "lblTituloMesa"):
            nombre_mesa = mesa.nombMesa or f"Mesa {mesa.mesa_id}"
            self.lblTituloMesa.setText(nombre_mesa)

        arena_w, arena_h = self.arena.width(), self.arena.height()
        cx, cy = arena_w // 2, arena_h // 2
        r = min(arena_w, arena_h) // 2 - MARGIN - ICON_SIZE // 2
        if r < 40:
            r = 40

        n_slots = max(capacidad, 1)
        start = -math.pi / 2
        step = 2 * math.pi / n_slots

        for idx in range(capacidad):
            inv = invitados[idx]
            estado = estados[idx]
            ang = start + idx * step
            x = cx + r * math.cos(ang)
            y = cy + r * math.sin(ang)

            is_empty = not (inv and (inv.nombre or "").strip())

            seat = SeatIcon(self.arena, idx)
            seat.dropped.connect(self._handle_drop_guest)

            path = icon_for_state(estado, is_empty=is_empty)
            seat.setPixmap(QtGui.QPixmap(path))
            seat.move(int(x - ICON_SIZE / 2), int(y - ICON_SIZE / 2))
            seat.show()

            nombre = inv.nombre if inv and inv.nombre else ""
            name_lbl = None
            if nombre:
                name_lbl = QtWidgets.QLabel(self.arena)
                name_lbl.setText(nombre)
                name_lbl.adjustSize()
                name_lbl.setAlignment(QtCore.Qt.AlignCenter)
                name_lbl.move(int(x - name_lbl.width() / 2), int(y + ICON_SIZE / 2 + 4))
                name_lbl.show()

            self.seat_widgets.append((seat, name_lbl))

    def _handle_drop_guest(self, seat_idx: int, guest: dict):
        mesa = self.evento.mesas[self.current_mesa_idx]
        invitados = mesa.invitados

        if seat_idx >= len(invitados):
            invitados += [None] * (seat_idx - len(invitados) + 1)

        prev = invitados[seat_idx]
        if prev and (prev.nombre or "").strip():
            self.pool.append({"nombre": prev.nombre, "estado": "ok"})

        self._remove_guest_from_pool_by_name(guest.get("nombre", ""))

        inv_obj = self._get_invitado_by_name(guest.get("nombre", ""))
        invitados[seat_idx] = inv_obj
        mesa.invitados = invitados

        self._reload_pool_table()
        self._render_seats()

    def _anadir_demo(self):
        idxs = self.tblInvitados.selectionModel().selectedRows()
        if not idxs:
            QtWidgets.QMessageBox.warning(self, "Añadir invitado",
                                          "Selecciona un invitado de la lista para añadirlo a la mesa.")
            return
        row = idxs[0].row()
        nombre_item = self.tblInvitados.item(row, 0)
        nombre = nombre_item.text() if nombre_item else ""
        mesa = self.evento.mesas[self.current_mesa_idx]
        idx_libre = self._first_empty_index(self.current_mesa_idx)
        if idx_libre is None:
            QtWidgets.QMessageBox.information(self, "Mesa completa",
                                              "La mesa seleccionada no tiene asientos libres.")
            return
        inv_obj = self._get_invitado_by_name(nombre)
        mesa.invitados[idx_libre] = inv_obj
        self._remove_guest_from_pool_by_name(nombre)
        self._render_seats()

    def _eliminar_demo(self):
        mesa = self.evento.mesas[self.current_mesa_idx]
        for i in range(len(mesa.invitados) - 1, -1, -1):
            inv = mesa.invitados[i]
            if inv and (inv.nombre or "").strip():
                self.pool.append({"nombre": inv.nombre, "estado": "ok"})
                mesa.invitados[i] = None
                self._reload_pool_table()
                break
        self._render_seats()

    def _confirmar_demo(self):
        mesa = self.evento.mesas[self.current_mesa_idx]
        ocupados = [inv for inv in mesa.invitados if inv and (inv.nombre or "").strip()]
        QtWidgets.QMessageBox.information(
            self, "Confirmado",
            f"{mesa.nombMesa or 'Mesa ' + str(mesa.mesa_id)}: {len(ocupados)} / {mesa.numAsientos} ocupados."
        )

if __name__ == "__main__":
    invitados_demo = [
        crear_invitado("invitado", "Ana", preferencias=["amigo:Luis"]),
        crear_invitado("invitado", "Luis", preferencias=["amigo:Ana", "amigo:Sofía"]),
        crear_invitado("invitado", "Marta", preferencias=["enemigo:Pedro"]),
        crear_invitado("invitado", "Pedro", preferencias=["enemigo:Marta"]),
        crear_invitado("invitado", "Sofía", preferencias=["amigo:Luis", "enemigo:Marta"]),
        crear_invitado("invitado", "Carlos"),
        crear_invitado("invitado", "Lucía"),
        crear_invitado("invitado", "Raúl"),
    ]

    evento_demo, _ = asignar_mesas(
        invitados_demo,
        tamano_mesa=4,
        nombre_evento="Evento prueba",
        fecha="2025-11-13",
        ubicacion="Murcia"
    )

    app = QtWidgets.QApplication(sys.argv)
    w = Main(evento_demo)
    w.show()
    sys.exit(app.exec_())
