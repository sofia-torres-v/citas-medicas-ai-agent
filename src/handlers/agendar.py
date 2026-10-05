"""Lógica de negocio para agendar una nueva cita."""

import repository as repo
from utils import norm, norm_documento


def ejecutar(p):
    doc = norm_documento(p.get("documento"))
    esp = norm(p.get("especialidad"))
    fecha = str(p.get("fecha", "")).strip()
    hora = str(p.get("hora", "")).strip()

    if not (doc and esp and fecha and hora):
        return {
            "ok": False,
            "mensaje": "Me falta información para agendar: necesito documento, especialidad, fecha y hora.",
        }

    horas = repo.get_horas_especialidad(esp)
    if horas is None:
        return {
            "ok": False,
            "reelicit": "especialidad",
            "mensaje": "Esa especialidad no está disponible. Tenemos: "
            + ", ".join(repo.especialidades_validas()),
        }
    if hora not in horas:
        return {
            "ok": False,
            "reelicit": "hora",
            "mensaje": f"Ese horario no está entre los disponibles para {esp}. Disponibles: {', '.join(horas)}.",
        }

    ocupadas = repo.horas_ocupadas(esp, fecha)
    if hora in ocupadas:
        libres = [h for h in horas if h not in ocupadas]
        libres_txt = ", ".join(libres) if libres else "ninguno por ahora"
        return {
            "ok": False,
            "reelicit": "hora",
            "mensaje": f"Esa hora ya fue reservada. Horarios libres: {libres_txt}.",
        }

    codigo = repo.generar_codigo_unico()
    repo.crear_cita(doc, codigo, p.get("paciente"), esp, fecha, hora)

    return {
        "ok": True,
        "codigo": codigo,
        "mensaje": f"Listo, agendé tu cita de {esp} el {fecha} a las {hora}. Tu código de cita es {codigo}.",
    }
