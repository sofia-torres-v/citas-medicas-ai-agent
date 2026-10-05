"""
Configuración compartida de pytest. Se ejecuta automáticamente antes de
cualquier test en esta carpeta.

boto3.resource("dynamodb") necesita saber la región de AWS incluso para
crear el objeto en memoria (sin hacer ninguna llamada real). En Lambda
esto ya viene configurado por el runtime; en tu máquina local no, así
que lo fijamos aquí solo para que los tests puedan importar los módulos
sin fallar. No hace ninguna llamada real a AWS.
"""

import os

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("ESPECIALIDADES_TABLE", "citas-medicas-especialidades")
os.environ.setdefault("CITAS_TABLE", "citas-medicas-citas")
