from dataclasses import dataclass

@dataclass
class Evento:
    tipo: str
    fecha: str      # "dd/MM/yyyy"
    hora: str       # "HH:mm"
    ubicacion: str
    organizadores: str = ""  # NUEVO
    mesas: int = 1           # NUEVO
