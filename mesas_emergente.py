# mesas_emergente.py

from typing import List, Dict, Optional
import math

from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5 import QtCore

from Vistas.Emergente_mesas_ui import Ui_EmergenteMesas

# --- Importamos de tu algoritmo real ---
from algoritmo import (
    Invitado,
    Mesa,
    Evento,
    crear_invitado,
    crear_mesa,
    crear_evento,
    asignar_mesas
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

        # Datos recibidos
        self.invitados_csv = invitados_csv or []
        self.evento_dict = evento_dict or {}
        self.tamano_mesa_defecto = tamano_mesa_defecto

        # Botones
        self.btnAutomatico.clicked.connect(self.on_generar_mesas_auto)
        self.btnManual.clicked.connect(self.on_generar_mesas_manual)

        print("[DEBUG] EmergenteMesas iniciada.")

    # -------------------------------------------------------------------
    # Convertir CSV → Lista de objetos Invitado (con amigos/enemigos)
    # -------------------------------------------------------------------
    def _invitados_csv_a_modelo(self) -> List[Invitado]:
        participantes: List[Invitado] = []

        for d in self.invitados_csv:
            nombre = (d.get("nombre") or "").strip()
            apellido = (d.get("apellido") or "").strip()
            rol = (d.get("rol") or "").strip()

            if not nombre:
                continue

            prefs = []

            # Amigos
            pref_con = (d.get("pref_con") or "").strip()
            if pref_con:
                for amigo in pref_con.split("|"):
                    amigo = amigo.strip()
                    if amigo:
                        prefs.append(f"amigo:{amigo}")

            # Enemigos
            pref_sin = (d.get("pref_sin") or "").strip()
            if pref_sin:
                for enemigo in pref_sin.split("|"):
                    enemigo = enemigo.strip()
                    if enemigo:
                        prefs.append(f"enemigo:{enemigo}")

            participantes.append(
                crear_invitado(
                    rol=rol,
                    nombre=nombre,
                    apellido=apellido,
                    preferencias=prefs
                )
            )

        print(f"[DEBUG] Invitados convertidos: {[p.nombre for p in participantes]}")
        return participantes

    # -------------------------------------------------------------------
    # AUTOMÁTICO → Ejecutar ORTOOLS + abrir ventana mesas
    # -------------------------------------------------------------------
    def on_generar_mesas_auto(self):
        print("[DEBUG] BOTÓN AUTOMÁTICO pulsado")

        try:
            import main  # para acceder a ventana_mesas_global
            print("[DEBUG] Import main correcto")

            # Importamos la clase Main SOLO AQUÍ
            from ui_mesa import Main
            print("[DEBUG] Import Main desde ui_mesa correcto")

            participantes = self._invitados_csv_a_modelo()
            print(f"[DEBUG] Total participantes: {len(participantes)}")

            if not participantes:
                QMessageBox.warning(self, "Mesas", "No hay invitados para asignar.")
                return

            tamano = self.tamano_mesa_defecto
            print("[DEBUG] Ejecutando ORTOOLS…")

            # Ejecutar solver
            evento, mapping = asignar_mesas(
                participantes,
                tamano_mesa=tamano,
                nombre_evento=self.evento_dict.get("nombre", "Evento"),
                fecha=self.evento_dict.get("fecha", ""),
                ubicacion=self.evento_dict.get("ubicacion", "")
            )

            print("[DEBUG] ORTOOLS ha devuelto un evento con "
                  f"{len(evento.mesas)} mesas")

            # Mantener viva la ventana para que no se destruya
            main.ventana_mesas_global = Main(evento, self.invitados_csv)
            main.ventana_mesas_global.show()

            print("[DEBUG] Ventana de mesas abierta correctamente")

            # Cerramos emergente
            self.hide()

        except Exception as e:
            print("[DEBUG] ERROR en automático:", e)
            QMessageBox.critical(
                self,
                "Error",
                f"Error generando mesas automáticas:\n\n{e}"
            )

    # -------------------------------------------------------------------
    # MANUAL → Crear mesas sin invitados
    # -------------------------------------------------------------------
    def _crear_evento_vacio(self, tamano_mesa: int) -> Evento:
        total = len(self.invitados_csv)
        num_mesas = max(1, math.ceil(total / tamano_mesa))

        mesas = []
        for i in range(num_mesas):
            mesas.append(crear_mesa(i + 1, tamano_mesa, f"Mesa {i+1}"))

        nombre = self.evento_dict.get("nombre", "Evento sin nombre")
        fecha = self.evento_dict.get("fecha", "")
        ubic = self.evento_dict.get("ubicacion", "")

        return crear_evento(nombre, fecha, ubic, mesas)

    def on_generar_mesas_manual(self):
        print("[DEBUG] BOTÓN MANUAL pulsado")

        try:
            import main
            from ui_mesa import Main

            tamano = self.tamano_mesa_defecto

            evento = self._crear_evento_vacio(tamano)

            # Guardamos ventana para que PyQt no la destruya
            main.ventana_mesas_global = Main(evento, self.invitados_csv)
            main.ventana_mesas_global.show()

            print("[DEBUG] Ventana manual abierta correctamente")

            self.hide()

        except Exception as e:
            print("[DEBUG] ERROR en manual:", e)
            QMessageBox.critical(
                self,
                "Error",
                f"Ha ocurrido un error en modo manual:\n\n{e}"
            )
