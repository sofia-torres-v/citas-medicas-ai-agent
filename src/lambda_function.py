"""
Router de entrada para Amazon Connect / AI Agent.

Recibe el evento de Amazon Connect, identifica la acción solicitada,
ejecuta el handler correspondiente y devuelve la respuesta en formato
compatible con Connect.

No contiene reglas de negocio. Estas viven en src/handlers/.
"""

from channel_adapter import extraer_parametros, construir_respuesta
from handlers import agendar, consultar, cancelar, reagendar

_ACCIONES = {
    "agendar_cita": agendar.ejecutar,
    "consultar_cita": consultar.ejecutar_cita,
    "consultar_disponibilidad": consultar.ejecutar_disponibilidad,
    "cancelar_cita": cancelar.ejecutar,
    "reagendar_cita": reagendar.ejecutar,
}


def lambda_handler(event, context=None):
    accion, params = extraer_parametros(event)

    # Se registra únicamente la acción, evitando exponer los parámetros
    # que podrían contener datos personales.
    print(f"Acción recibida: {accion}")

    handler = _ACCIONES.get(accion)

    try:
        if handler:
            resultado = handler(params)
        else:
            resultado = {
                "ok": False,
                "mensaje": (
                    "No logré identificar qué necesitas. ¿Quieres agendar, "
                    "consultar, reagendar, cancelar una cita o ver disponibilidad?"
                ),
                "accion_recibida": accion,
            }

    except Exception:
        print("Error interno procesando la solicitud.")

        resultado = {
            "ok": False,
            "mensaje": (
                "Tuve un problema interno procesando tu solicitud. "
                "Intentemos de nuevo en un momento."
            ),
        }

    respuesta = construir_respuesta(resultado)

    print(f"Solicitud procesada. Acción: {accion}")

    return respuesta
