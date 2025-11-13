# main.py
import sys
import json
import os

# 🔥 DEBUG PARA VER ERRORES REALES DE QT
os.environ["QT_DEBUG_PLUGINS"] = "1"
os.environ["QT_LOGGING_RULES"] = "*.debug=true"

from PyQt5.QtWidgets import QApplication, QMessageBox
from VPantallaPrincipal import VPantallaPrincipal
from VPantallaInvitados import VPantallaInvitados

RUTA_EVENTOS = "eventos.json"

# 🔥 Aquí guardaremos la ventana de mesas para evitar que PyQt la destruya
ventana_mesas_global = None


def cargar_eventos():
    try:
        if os.path.exists(RUTA_EVENTOS):
            with open(RUTA_EVENTOS, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        print("[JSON] Error cargando eventos:", e)
    return []


class AppShim:
    """Router simple que gestiona las ventanas."""
    def __init__(self):
        self.eventos = cargar_eventos()
        self._ventanas = []  # Mantiene vivas las ventanas secundarias

    # ---- Guardar eventos ----
    def guardar_eventos(self):
        try:
            with open(RUTA_EVENTOS, "w", encoding="utf-8") as f:
                json.dump(self.eventos, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("[JSON] Error guardando eventos:", e)

    # ---- Abrir pantalla de invitados ----
    def abrir_pantalla2(self, evento):
        win = VPantallaInvitados(evento=evento, router=self)

        nombre = evento.get("tipo") or evento.get("nombre") or "Evento"
        try:
            win.set_evento(nombre)
        except AttributeError:
            win.setWindowTitle(nombre)

        win.show()
        self._ventanas.append(win)  # evitar destrucción

    def dialog_anadir_evento(self):
        pass

    def dialog_editar_evento(self, idx=None):
        QMessageBox.information(None, "Editar evento",
                                f"Edición no implementada (idx={idx}).")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Sin QSS global para evitar conflictos
    app.setStyleSheet("")

    shim = AppShim()

    win = VPantallaPrincipal(router=shim)
    win.show()

    sys.exit(app.exec_())
