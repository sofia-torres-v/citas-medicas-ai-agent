"""
Tests de las funciones puras en src/utils.py. No necesitan AWS ni mocks:
solo importan las funciones y verifican entradas/salidas conocidas.

Cómo correrlos (desde la raíz del proyecto):
    pytest tests/test_utils.py -v
"""

import sys
import os

# Permite importar "src.utils" sin instalar el paquete
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils import norm, norm_documento, extraer_codigo_cita


class TestNorm:
    def test_quita_tildes(self):
        assert norm("odontología") == "odontologia"
        assert norm("dermatólogo") == "dermatologo"

    def test_minusculas(self):
        assert norm("MEDICINA GENERAL") == "medicina general"

    def test_espacios_extra(self):
        assert norm("  pediatria  ") == "pediatria"

    def test_valor_vacio(self):
        assert norm(None) == ""
        assert norm("") == ""


class TestNormDocumento:
    def test_solo_digitos(self):
        assert norm_documento("12345678") == "12345678"

    def test_quita_espacios(self):
        assert norm_documento(" 12345678 ") == "12345678"

    def test_quita_caracteres_no_numericos(self):
        assert norm_documento("12.345.678") == "12345678"

    def test_valor_vacio_devuelve_vacio(self):
        assert norm_documento("") == ""
        assert norm_documento(None) == ""


class TestExtraerCodigoCita:
    def test_codigo_exacto(self):
        assert extraer_codigo_cita("CITA-9487") == "CITA-9487"

    def test_minuscula_se_normaliza(self):
        assert extraer_codigo_cita("cita-9487") == "CITA-9487"

    def test_frase_con_texto_alrededor(self):
        # El bug real que encontramos en las pruebas de Lex:
        assert extraer_codigo_cita("es esta CITA-9487") == "CITA-9487"

    def test_solo_numero_sin_prefijo(self):
        assert extraer_codigo_cita("9487") == "CITA-9487"

    def test_codigo_roto_sin_prefijo(self):
        # Lo que Lex realmente entregó en el bug documentado:
        assert extraer_codigo_cita("-9487") == "CITA-9487"

    def test_texto_sin_digitos_devuelve_none(self):
        assert extraer_codigo_cita("medicina") is None
        assert extraer_codigo_cita("no tengo codigo") is None

    def test_menos_de_4_digitos_devuelve_none(self):
        assert extraer_codigo_cita("CITA-948") is None
