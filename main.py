# main.py
import sys, json, os
from PyQt5.QtWidgets import QApplication, QMessageBox
from VPantallaPrincipal import VPantallaPrincipal
from VPantallaInvitados import VPantallaInvitados

RUTA_EVENTOS = "eventos.json"   # usa el tuyo si es otro

def cargar_eventos():
    try:
        if os.path.exists(RUTA_EVENTOS):
            with open(RUTA_EVENTOS, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Esperamos una lista de dicts con claves tipo/fecha/hora/ubicacion
                return data if isinstance(data, list) else []
    except Exception as e:
        print("[JSON] Error cargando eventos:", e)
    return []

class AppShim:
    """Pequeño ‘router’ en memoria sin archivo extra."""
    def __init__(self):
        self.eventos = cargar_eventos()
        self._ventanas = []  # evita GC de las ventanas secundarias

    # ---- Navegación que la principal espera ----
    def abrir_pantalla2(self, evento):
        win = VPantallaInvitados()
        # Muestra el tipo/nombre del evento en el título de invitados
        nombre = evento.get("tipo") or evento.get("nombre") or "Evento"
        win.set_evento(nombre)
        win.show()
        self._ventanas.append(win)  # mantener referencia

    # ---- Diálogos que la principal invoca (placeholders no destructivos) ----
    def dialog_anadir_evento(self):
        QMessageBox.information(None, "Añadir evento", "Aquí abrirías tu diálogo real de alta.\n(Shim no modifica el JSON)")

    def dialog_editar_evento(self, idx=None):
        QMessageBox.information(None, "Editar evento", f"Aquí editarías el evento índice: {idx}\n(Shim no modifica el JSON)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("")  # sin QSS global para evitar conflictos

    shim = AppShim()
    win = VPantallaPrincipal(router=shim)   # tu controlador principal tal cual
    win.show()

    sys.exit(app.exec_())
