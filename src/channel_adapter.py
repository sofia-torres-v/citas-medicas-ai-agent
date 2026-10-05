"""
Capa adaptadora para Amazon Connect / AI Agent.

Recibe el evento que Connect entrega al Lambda (Details.Parameters),
extrae la acción y sus parámetros, y convierte la respuesta a un
diccionario plano donde todos los valores son strings (STRING_MAP).

Es la única capa que conoce el formato de Connect.
"""

# Claves internas de los handlers que no deben viajar de vuelta a Connect.
_CLAVES_INTERNAS = {"reelicit"}


def extraer_parametros(event):
    """Devuelve (accion, parametros) desde el evento de Connect."""
    event = event or {}

    # Formato de Amazon Connect: Details.Parameters.
    if "Details" in event:
        params = event.get("Details", {}).get("Parameters", {}) or {}
        return params.get("action", ""), params

    # Formato utilizado para pruebas manuales en AWS Lambda.
    return event.get("action", ""), event


def construir_respuesta(resultado):
    """Convierte el resultado a un diccionario plano de strings para Connect."""
    out = {}

    for k, v in resultado.items():
        if k in _CLAVES_INTERNAS:
            continue

        if isinstance(v, bool):
            out[k] = "true" if v else "false"
        elif isinstance(v, (list, tuple)):
            out[k] = ", ".join(str(x) for x in v)
        elif v is None:
            out[k] = ""
        else:
            out[k] = str(v)

    return out
