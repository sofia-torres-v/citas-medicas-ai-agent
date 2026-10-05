"""Lógica de negocio para reagendar (cambiar fecha/hora de) una cita existente."""

import repository as repo
from utils import extraer_codigo_cita


def ejecutar(p):
    codigo = extraer_codigo_cita(p.get("codigo_cita"))
    nueva_fecha = str(p.get("fecha", "")).strip()
    nueva_hora = str(p.get("hora", "")).strip()

    if not codigo:
        return {
            "ok": False,
            "reelicit": "codigo_cita",
            "mensaje": "No logré identificar un código de cita (necesito 4 dígitos, ej. CITA-1234). ¿Me lo confirmas?",
        }
    if not (nueva_fecha and nueva_hora):
        return {
            "ok": False,
            "mensaje": "Necesito el código de la cita, la nueva fecha y la nueva hora.",
        }

    c = repo.buscar_cita_por_codigo(codigo)
    if not c:
        return {"ok": False, "mensaje": "No encontré una cita con ese código."}

    if c.get("estado") != "confirmada":
        return {
            "ok": False,
            "mensaje": "Esa cita ya no está activa, no se puede reagendar.",
        }

    esp = c["especialidad"]
    horas = repo.get_horas_especialidad(esp)
    if horas is None or nueva_hora not in horas:
        horas_txt = ", ".join(horas) if horas else "sin horarios configurados"
        return {
            "ok": False,
            "reelicit": "hora",
            "mensaje": f"Ese horario no está disponible para {esp}. Horarios: {horas_txt}.",
        }

    ocupadas = repo.horas_ocupadas(esp, nueva_fecha)
    if c.get("fecha") == nueva_fecha and c.get("hora") == nueva_hora:
        ocupadas.discard(nueva_hora)
    if nueva_hora in ocupadas:
        libres = [h for h in horas if h not in ocupadas]
        libres_txt = ", ".join(libres) if libres else "ninguno por ahora"
        return {
            "ok": False,
            "reelicit": "hora",
            "mensaje": f"Esa hora ya está ocupada. Horarios libres: {libres_txt}.",
        }

    repo.reagendar_cita_en_bd(c["documento"], c["codigo"], esp, nueva_fecha, nueva_hora)
    return {
        "ok": True,
        "codigo": codigo,
        "mensaje": f"Listo, reagendé tu cita {codigo} de {esp} para el {nueva_fecha} a las {nueva_hora}.",
    }
