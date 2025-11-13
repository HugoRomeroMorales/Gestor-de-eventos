"""Compatibilidad: reexporta el pequeño modelo desde
`ObjetosParaElProyecto.py` para mantener las importaciones
existentes que usan `modelos.Evento`.
"""
from ObjetosParaElProyecto import EventoSimple as Evento

__all__ = ["Evento"]
