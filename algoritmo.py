import sys
from math import ceil
from typing import List, Optional, Dict

from ortools.sat.python import cp_model
from PyQt5 import QtWidgets


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


class VentanaMesas(QtWidgets.QMainWindow):
    def __init__(self, evento: Evento):
        super().__init__()
        self.evento = evento
        self.setWindowTitle(f"Mesas - {evento.nombre}")
        central = QtWidgets.QWidget(self)
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        self.tblMesas = QtWidgets.QTableWidget()
        self.tblMesas.setColumnCount(3)
        self.tblMesas.setHorizontalHeaderLabels(["Mesa", "Asiento", "Invitado"])
        self.tblMesas.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tblMesas)
        self._cargar_datos()

    def _cargar_datos(self):
        total_filas = sum(m.numAsientos for m in self.evento.mesas)
        self.tblMesas.setRowCount(total_filas)
        row = 0
        for mesa in self.evento.mesas:
            nombre_mesa = mesa.nombMesa or f"Mesa {mesa.mesa_id}"
            for i, inv in enumerate(mesa.invitados):
                self.tblMesas.setItem(row, 0, QtWidgets.QTableWidgetItem(nombre_mesa))
                self.tblMesas.setItem(row, 1, QtWidgets.QTableWidgetItem(str(i + 1)))
                nombre_inv = inv.nombre if (inv and inv.nombre) else ""
                self.tblMesas.setItem(row, 2, QtWidgets.QTableWidgetItem(nombre_inv))
                row += 1
        self.tblMesas.resizeColumnsToContents()


def _mostrar_ventana_mesas(evento: Evento):
    app = QtWidgets.QApplication.instance()
    propio = False
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        propio = True
    w = VentanaMesas(evento)
    w.show()
    if propio:
        app.exec_()


def asignar_mesas(participantes: List[Invitado], tamano_mesa: int,
                  nombre_evento: str = "Evento", fecha: str = "", ubicacion: str = ""):
    nombres = [i.nombre for i in participantes]
    n = len(participantes)
    num_mesas = max(1, ceil(n / tamano_mesa))
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
        evento_vacio = crear_evento(nombre_evento, fecha, ubicacion, [])
        _mostrar_ventana_mesas(evento_vacio)
        return evento_vacio, {}
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
    _mostrar_ventana_mesas(evento)
    return evento, mapping
