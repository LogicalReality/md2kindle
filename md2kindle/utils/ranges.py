"""Utilities for parsing manga volume/chapter ranges."""


def parse_range(start, end):
    """Convierte un rango de strings en una lista.

    Soporta decimales (25.5) y alfanuméricos (S1).
    """
    try:
        s = float(start)
        e = float(end)
        if s == e:
            return [start]

        # Generamos lista de enteros si son exactos; si no, retornamos extremos.
        if s.is_integer() and e.is_integer():
            return [str(i) for i in range(int(s), int(e) + 1)]
        return [start, end]
    except ValueError:
        # Si no es un número (ej. "S1", "Extra"), devolvemos como literal.
        if start == end:
            return [start]
        return [start]
