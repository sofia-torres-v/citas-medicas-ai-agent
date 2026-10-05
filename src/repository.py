"""
Toda la comunicación con DynamoDB vive aquí, y solo aquí. Los handlers
(agendar, cancelar, etc.) nunca llaman a boto3 directamente — solo usan
las funciones de este módulo. Si el día de mañana se cambias de base de
datos, esta es la única capa que se toca.
"""

import os
import random
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")

ESPECIALIDADES_TABLE = os.environ.get(
    "ESPECIALIDADES_TABLE", "citas-medicas-especialidades"
)
CITAS_TABLE = os.environ.get("CITAS_TABLE", "citas-medicas-citas")

tabla_especialidades = dynamodb.Table(ESPECIALIDADES_TABLE)
tabla_citas = dynamodb.Table(CITAS_TABLE)


def get_horas_especialidad(esp):
    """Devuelve la lista de horarios configurados para una especialidad,
    o None si la especialidad no existe en la tabla."""
    resp = tabla_especialidades.get_item(Key={"especialidad": esp})
    item = resp.get("Item")
    if not item:
        return None
    return list(item.get("horas_disponibles", []))


def especialidades_validas():
    """Lista ordenada de todas las especialidades configuradas, usada
    para armar mensajes de error tipo 'no atendemos esa especialidad,
    tenemos: ...'."""
    items = tabla_especialidades.scan().get("Items", [])
    return sorted(it["especialidad"] for it in items)


def horas_ocupadas(esp, fecha):
    """Horas con una cita CONFIRMADA para esa especialidad y fecha
    (evita dobles reservas)."""
    key = f"{esp}#{fecha}"
    resp = tabla_citas.query(
        IndexName="especialidad-fecha-index",
        KeyConditionExpression=Key("especialidad_fecha").eq(key),
    )
    return {
        item.get("hora")
        for item in resp.get("Items", [])
        if item.get("estado") == "confirmada"
    }


def generar_codigo_unico():
    """Genera un código CITA-9999 que no choque con uno ya existente."""
    codigo = f"CITA-{random.randint(9000, 9999)}"
    for _ in range(5):
        resp = tabla_citas.query(
            IndexName="codigo-index", KeyConditionExpression=Key("codigo").eq(codigo)
        )
        if not resp.get("Items"):
            break
        codigo = f"CITA-{random.randint(9000, 9999)}"
    return codigo


def crear_cita(documento, codigo, paciente, especialidad, fecha, hora):
    tabla_citas.put_item(
        Item={
            "documento": documento,
            "codigo": codigo,
            "paciente": paciente or "Paciente",
            "especialidad": especialidad,
            "fecha": fecha,
            "hora": hora,
            "estado": "confirmada",
            "especialidad_fecha": f"{especialidad}#{fecha}",
            "creado_en": datetime.now(timezone.utc).isoformat(),
        }
    )


def buscar_citas_por_documento(documento):
    resp = tabla_citas.query(KeyConditionExpression=Key("documento").eq(documento))
    return resp.get("Items", [])


def buscar_cita_por_codigo(codigo):
    """Devuelve la primera cita que coincide con ese código, o None."""
    resp = tabla_citas.query(
        IndexName="codigo-index", KeyConditionExpression=Key("codigo").eq(codigo)
    )
    items = resp.get("Items", [])
    return items[0] if items else None


def actualizar_estado_cita(documento, codigo, nuevo_estado):
    tabla_citas.update_item(
        Key={"documento": documento, "codigo": codigo},
        UpdateExpression="SET estado = :e",
        ExpressionAttributeValues={":e": nuevo_estado},
    )


def reagendar_cita_en_bd(documento, codigo, especialidad, nueva_fecha, nueva_hora):
    tabla_citas.update_item(
        Key={"documento": documento, "codigo": codigo},
        UpdateExpression="SET fecha = :f, hora = :h, especialidad_fecha = :ef",
        ExpressionAttributeValues={
            ":f": nueva_fecha,
            ":h": nueva_hora,
            ":ef": f"{especialidad}#{nueva_fecha}",
        },
    )
