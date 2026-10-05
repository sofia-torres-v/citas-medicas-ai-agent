"""
Funciones puras de normalización de texto, sin dependencias de AWS.
No importan boto3 ni nada externo — por eso se pueden testear directo,
sin mockear DynamoDB ni Lex.
"""

import re
import unicodedata


def norm(t):
    """Minúsculas, sin espacios extra, sin tildes. Usado para comparar
    especialidades contra las claves guardadas en DynamoDB."""
    t = str(t or "").strip().lower()
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t


def norm_documento(doc):
    """AMAZON.Number puede devolver espacios o el valor tal cual lo dijo
    el usuario. Nos quedamos solo con dígitos para evitar desajustes
    al comparar/guardar en DynamoDB."""
    doc = str(doc or "").strip()
    solo_digitos = re.sub(r"\D", "", doc)
    return solo_digitos or doc


def extraer_codigo_cita(raw):
    """AMAZON.AlphaNumeric a veces pierde el prefijo 'CITA-' cuando el
    usuario escribe una frase completa (ej: 'es esta CITA-9487' -> Lex
    solo captura '-9487'). En vez de exigir el texto exacto, buscamos
    4 dígitos seguidos en cualquier parte del texto y reconstruimos
    el código nosotros mismos."""
    raw = str(raw or "").strip().upper()
    m = re.search(r"(\d{4})", raw)
    if not m:
        return None
    return f"CITA-{m.group(1)}"
