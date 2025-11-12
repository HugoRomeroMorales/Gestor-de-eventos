import json, os
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox

from VPantallaPrincipal import VPantallaPrincipal
from VPantalla2 import VPantalla2
from WAnadirEvento import WAnadirEvento
from WEditarEvento import WEditarEvento

class Router:
    def __init__(self):
        self._stack = []
        self._json_path = "eventos.json"
        self.eventos = []
        self._cargar_eventos()

    def _cargar_eventos(self):
        if not os.path.exists(self._json_path):
            self.eventos = []
            return
        try:
            with open(self._json_path, "r", encoding="utf-8") as f:
                self.eventos = json.load(f)
        except Exception:
            self.eventos = []

        # Normaliza campos faltantes para compatibilidad
        changed = False
        for ev in self.eventos:
            if "organizadores" not in ev:
                ev["organizadores"] = ""
                changed = True
            if "mesas" not in ev:
                ev["mesas"] = 1
                changed = True
        if changed:
            self.guardar_eventos()

    def guardar_eventos(self):
        with open(self._json_path, "w", encoding="utf-8") as f:
            json.dump(self.eventos, f, indent=4, ensure_ascii=False)

    # ---------- Pantallas ----------
    def abrir_pantalla_principal(self):
        win = VPantallaPrincipal(self)
        win.show()
        self._stack.append(win)

    def abrir_pantalla2(self, evento: dict):
        win = VPantalla2(self, evento)
        win.show()
        if self._stack:
            self._stack[-1].hide()
        self._stack.append(win)

    # ---------- Diálogos ----------
    def dialog_anadir_evento(self):
        if not self._stack: return
        main = self._stack[-1]
        win = WAnadirEvento(main)
        win.setWindowModality(Qt.ApplicationModal)
        win.show()

    def dialog_editar_evento(self, idx: int):
        if not self._stack: return
        main = self._stack[-1]
        if idx < 0 or idx >= len(self.eventos):
            QMessageBox.information(main, "Editar", "Selecciona un evento válido.")
            return
        win = WEditarEvento(main, idx)
        win.setWindowModality(Qt.ApplicationModal)
        win.show()
