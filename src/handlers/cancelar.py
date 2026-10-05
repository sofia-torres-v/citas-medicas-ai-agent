"""Lógica de negocio para cancelar una cita existente."""

import repository as repo
from utils import extraer_codigo_cita


def ejecutar(p):
    codigo = extraer_codigo_cita(p.get("codigo_cita"))
    if not codigo:
        return {
            "ok": False,
            "reelicit": "codigo_cita",
            "mensaje": "No logré identificar un código de cita (necesito 4 dígitos, ej. CITA-1234). ¿Me lo confirmas?",
        }

    c = repo.buscar_cita_por_codigo(codigo)
    if not c:
        return {"ok": False, "mensaje": "No encontré ninguna cita con ese código."}

    if c.get("estado") != "confirmada":
        return {
            "ok": False,
            "mensaje": f"La cita {codigo} ya está en estado '{c.get('estado')}', no se puede cancelar de nuevo.",
        }

    repo.actualizar_estado_cita(c["documento"], c["codigo"], "cancelada")
    return {
        "ok": True,
        "codigo": codigo,
        "mensaje": f"Cancelé exitosamente tu cita {codigo}.",
    }
