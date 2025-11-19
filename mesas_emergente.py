from typing import List, Dict, Optional
import math, re, os

from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5 import QtCore

from Vistas.Emergente_mesas_ui import Ui_EmergenteMesas

from algoritmo import (
    Invitado,
    Mesa,
    Evento,
    crear_invitado,
    crear_mesa,
    crear_evento,
    asignar_mesas,
    Main,
    cargar_evento_desde_csv_mesas,
)


class EmergenteMesas(QMainWindow, Ui_EmergenteMesas):
    def __init__(
        self,
        invitados_csv: List[Dict],
        evento_dict: Optional[Dict] = None,
        parent=None,
        tamano_mesa_defecto: int = 8,
    ):
        super().__init__(parent)
        self.setupUi(self)

        self.invitados_csv = invitados_csv or []
        self.evento_dict = evento_dict or {}

        total = len(self.invitados_csv)
        num_mesas_cfg = int(self.evento_dict.get("mesas", 0) or 0)
        self.num_mesas_cfg = num_mesas_cfg if num_mesas_cfg > 0 else None

        if total > 0 and self.num_mesas_cfg:
            base = math.ceil(total / self.num_mesas_cfg)
            self.tamano_mesa_defecto = max(8, base)
        else:
            self.tamano_mesa_defecto = max(8, tamano_mesa_defecto)

        nombre_base = self.evento_dict.get("tipo", self.evento_dict.get("nombre", "evento"))
        nombre_base = (nombre_base or "evento").strip() or "evento"
        safe = nombre_base.replace(" ", "_")
        self.csv_mesas_path = os.path.abspath(f"mesas_{safe}.csv")

        self.btnAutomatico.clicked.connect(self.on_generar_mesas_auto)
        self.btnManual.clicked.connect(self.on_generar_mesas_manual)

    def _split_pref_str(self, s: str) -> List[str]:
        if not s:
            return []
        partes = re.split(r"[|,;/]", s)
        return [p.strip() for p in partes if p.strip()]

    def _invitados_csv_a_modelo(self) -> List[Invitado]:
        participantes: List[Invitado] = []

        for d in self.invitados_csv:
            nombre = (d.get("nombre") or "").strip()
            apellido = (d.get("apellido") or "").strip()
            rol = (d.get("rol") or "").strip()

            if not nombre:
                continue

            prefs = []

            pref_con = (d.get("pref_con") or "").strip()
            for amigo in self._split_pref_str(pref_con):
                partes = amigo.split()
                if not partes:
                    continue
                base = partes[0]
                prefs.append(f"amigo:{base}")

            pref_sin = (d.get("pref_sin") or "").strip()
            for enemigo in self._split_pref_str(pref_sin):
                partes = enemigo.split()
                if not partes:
                    continue
                base = partes[0]
                prefs.append(f"enemigo:{base}")

            participantes.append(
                crear_invitado(
                    rol=rol,
                    nombre=nombre,
                    apellido=apellido,
                    preferencias=prefs
                )
            )

        return participantes

    def on_generar_mesas_auto(self):
        try:
            import main

            nombre_evento = self.evento_dict.get("tipo", self.evento_dict.get("nombre", "Evento"))
            fecha = self.evento_dict.get("fecha", "")
            ubic = self.evento_dict.get("ubicacion", "")

            if os.path.exists(self.csv_mesas_path):
                evento = cargar_evento_desde_csv_mesas(
                    nombre_evento=nombre_evento,
                    fecha=fecha,
                    ubicacion=ubic,
                    ruta=self.csv_mesas_path
                )

                main.ventana_mesas_global = Main(evento, self.invitados_csv)
                main.ventana_mesas_global.show()
                self.hide()
                return

            participantes = self._invitados_csv_a_modelo()

            if not participantes:
                QMessageBox.warning(self, "Mesas", "No hay invitados para asignar.")
                return

            tamano = self.tamano_mesa_defecto
            num_mesas_cfg = getattr(self, "num_mesas_cfg", None)

            evento, mapping = asignar_mesas(
                participantes,
                tamano_mesa=tamano,
                nombre_evento=nombre_evento,
                fecha=fecha,
                ubicacion=ubic,
                num_mesas=num_mesas_cfg
            )

            main.ventana_mesas_global = Main(evento, self.invitados_csv)
            main.ventana_mesas_global.show()
            self.hide()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error generando mesas automáticas:\n\n{e}"
            )

    def _crear_evento_vacio(self, tamano_mesa: int) -> Evento:
        total = len(self.invitados_csv)
        num_mesas = getattr(self, "num_mesas_cfg", None) or max(1, math.ceil(total / tamano_mesa))
        cap = max(8, tamano_mesa)

        mesas = []
        for i in range(num_mesas):
            mesas.append(crear_mesa(i + 1, cap, f"Mesa {i+1}"))

        nombre = self.evento_dict.get("tipo", self.evento_dict.get("nombre", "Evento sin nombre"))
        fecha = self.evento_dict.get("fecha", "")
        ubic = self.evento_dict.get("ubicacion", "")

        return crear_evento(nombre, fecha, ubic, mesas)

    def on_generar_mesas_manual(self):
        try:
            import main
            tamano = self.tamano_mesa_defecto
            evento = self._crear_evento_vacio(tamano)

            main.ventana_mesas_global = Main(evento, self.invitados_csv)
            main.ventana_mesas_global.show()
            self.hide()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Ha ocurrido un error en modo manual:\n\n{e}"
            )
