# main.py
import sys, json, os
from PyQt5.QtWidgets import QApplication, QMessageBox
from VPantallaPrincipal import VPantallaPrincipal
from VPantallaInvitados import VPantallaInvitados

RUTA_EVENTOS = "eventos.json"

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
    """Pequeño ‘router’ en memoria sin archivo extra."""
    def __init__(self):
        self.eventos = cargar_eventos()
        self._ventanas = []  # evita GC de las ventanas secundarias

    # ---- Persistencia requerida por WAnadirEvento ----
    def guardar_eventos(self):
        try:
            os.makedirs(os.path.dirname(RUTA_EVENTOS) or ".", exist_ok=True)
            with open(RUTA_EVENTOS, "w", encoding="utf-8") as f:
                json.dump(self.eventos, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("[JSON] Error guardando eventos:", e)

    # ---- Navegación que la principal espera ----
    def abrir_pantalla2(self, evento):
        win = VPantallaInvitados()
        nombre = evento.get("tipo") or evento.get("nombre") or "Evento"
        try:
            win.set_evento(nombre)  # si tu clase lo tiene
        except AttributeError:
            win.setWindowTitle(nombre)
        win.show()
        self._ventanas.append(win)

    # ---- (Opcional) Stubs de edición si los usas ----
    def dialog_anadir_evento(self):
        # Ya no se usa: la principal abre WAnadirEvento directamente.
        pass

    def dialog_editar_evento(self, idx=None):
        QMessageBox.information(None, "Editar evento",
                                f"Edición no implementada (idx={idx}).")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("")  # sin QSS global para evitar conflictos

    shim = AppShim()
    win = VPantallaPrincipal(router=shim)
    win.show()

    sys.exit(app.exec_())
