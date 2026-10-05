"""Lógica de negocio para consultar una cita existente y consultar disponibilidad."""

import repository as repo
from utils import norm, norm_documento


def ejecutar_cita(p):
    doc = norm_documento(p.get("documento"))
    if not doc:
        return {
            "ok": False,
            "mensaje": "Necesito tu número de documento para buscar tu cita.",
        }

    items = repo.buscar_citas_por_documento(doc)
    if not items:
        return {
            "ok": False,
            "mensaje": "No encontré citas agendadas con ese número de documento.",
        }

    items.sort(key=lambda it: it.get("creado_en", ""), reverse=True)
    c = next((it for it in items if it.get("estado") == "confirmada"), items[0])

    return {
        "ok": True,
        "codigo": c["codigo"],
        "especialidad": c["especialidad"],
        "fecha": c["fecha"],
        "hora": c["hora"],
        "estado": c["estado"],
        "mensaje": f"Tienes una cita de {c['especialidad']} para el {c['fecha']} a las {c['hora']}. Estado: {c['estado']}. Código: {c['codigo']}.",
    }


def ejecutar_disponibilidad(p):
    esp = norm(p.get("especialidad"))
    fecha = str(p.get("fecha", "")).strip()

    horas = repo.get_horas_especialidad(esp)
    if horas is None:
        return {
            "ok": False,
            "reelicit": "especialidad",
            "mensaje": "No atendemos esa especialidad. Tenemos: "
            + ", ".join(repo.especialidades_validas()),
        }
    if not fecha:
        return {
            "ok": False,
            "mensaje": "Necesito la fecha que prefieres para revisar disponibilidad.",
        }

    ocupadas = repo.horas_ocupadas(esp, fecha)
    horas_libres = [h for h in horas if h not in ocupadas]

    if not horas_libres:
        return {
            "ok": False,
            "mensaje": f"No quedan horarios libres para {esp} el {fecha}. Prueba otra fecha.",
        }

    return {
        "ok": True,
        "especialidad": esp,
        "fecha": fecha,
        "horas_disponibles": horas_libres,
        "mensaje": f"Para {esp} el {fecha} tengo disponible: {', '.join(horas_libres)}.",
    }
