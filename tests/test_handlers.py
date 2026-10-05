"""
Tests de los handlers de negocio (src/handlers/*.py). Usamos unittest.mock
para simular las respuestas de repository.py, así no necesitamos una
conexión real a DynamoDB ni la librería `moto` para correr estos tests.

Cómo correrlos:
    pytest tests/test_handlers.py -v
"""

import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.handlers import agendar, cancelar, consultar, reagendar


class TestAgendar:
    @patch("src.handlers.agendar.repo")
    def test_agenda_exitosa(self, mock_repo):
        mock_repo.get_horas_especialidad.return_value = ["08:00", "09:30"]
        mock_repo.horas_ocupadas.return_value = set()
        mock_repo.generar_codigo_unico.return_value = "CITA-1234"

        resultado = agendar.ejecutar(
            {
                "documento": "12345678",
                "paciente": "Jose",
                "especialidad": "medicina general",
                "fecha": "2026-09-28",
                "hora": "08:00",
            }
        )

        assert resultado["ok"] is True
        assert resultado["codigo"] == "CITA-1234"
        mock_repo.crear_cita.assert_called_once()

    @patch("src.handlers.agendar.repo")
    def test_especialidad_invalida_pide_reelicit(self, mock_repo):
        mock_repo.get_horas_especialidad.return_value = None
        mock_repo.especialidades_validas.return_value = ["odontologia", "pediatria"]

        resultado = agendar.ejecutar(
            {
                "documento": "12345678",
                "especialidad": "cardiologia",
                "fecha": "2026-09-28",
                "hora": "08:00",
            }
        )

        assert resultado["ok"] is False
        assert resultado["reelicit"] == "especialidad"
        mock_repo.crear_cita.assert_not_called()

    @patch("src.handlers.agendar.repo")
    def test_hora_ocupada_pide_reelicit_hora(self, mock_repo):
        mock_repo.get_horas_especialidad.return_value = ["08:00", "09:30"]
        mock_repo.horas_ocupadas.return_value = {"08:00"}

        resultado = agendar.ejecutar(
            {
                "documento": "12345678",
                "especialidad": "pediatria",
                "fecha": "2026-09-28",
                "hora": "08:00",
            }
        )

        assert resultado["ok"] is False
        assert resultado["reelicit"] == "hora"
        assert "09:30" in resultado["mensaje"]

    def test_datos_incompletos(self):
        resultado = agendar.ejecutar({"documento": "12345678"})
        assert resultado["ok"] is False
        assert "reelicit" not in resultado


class TestCancelar:
    @patch("src.handlers.cancelar.repo")
    def test_cancela_exitosamente(self, mock_repo):
        mock_repo.buscar_cita_por_codigo.return_value = {
            "documento": "12345678",
            "codigo": "CITA-1234",
            "estado": "confirmada",
        }
        resultado = cancelar.ejecutar({"codigo_cita": "CITA-1234"})
        assert resultado["ok"] is True
        mock_repo.actualizar_estado_cita.assert_called_once_with(
            "12345678", "CITA-1234", "cancelada"
        )

    def test_codigo_no_reconocible_pide_reelicit(self):
        # No pasa por repository porque falla antes, en extraer_codigo_cita
        resultado = cancelar.ejecutar({"codigo_cita": "medicina"})
        assert resultado["ok"] is False
        assert resultado["reelicit"] == "codigo_cita"

    @patch("src.handlers.cancelar.repo")
    def test_codigo_no_encontrado(self, mock_repo):
        mock_repo.buscar_cita_por_codigo.return_value = None
        resultado = cancelar.ejecutar({"codigo_cita": "CITA-9999"})
        assert resultado["ok"] is False
        assert "reelicit" not in resultado

    @patch("src.handlers.cancelar.repo")
    def test_cita_ya_cancelada(self, mock_repo):
        mock_repo.buscar_cita_por_codigo.return_value = {
            "documento": "12345678",
            "codigo": "CITA-1234",
            "estado": "cancelada",
        }
        resultado = cancelar.ejecutar({"codigo_cita": "CITA-1234"})
        assert resultado["ok"] is False
        mock_repo.actualizar_estado_cita.assert_not_called()


class TestConsultarCita:
    @patch("src.handlers.consultar.repo")
    def test_encuentra_cita_confirmada(self, mock_repo):
        mock_repo.buscar_citas_por_documento.return_value = [
            {
                "codigo": "CITA-1",
                "especialidad": "pediatria",
                "fecha": "2026-09-28",
                "hora": "08:30",
                "estado": "confirmada",
                "creado_en": "2026-09-27T10:00:00",
            },
        ]
        resultado = consultar.ejecutar_cita({"documento": "12345678"})
        assert resultado["ok"] is True
        assert resultado["codigo"] == "CITA-1"

    @patch("src.handlers.consultar.repo")
    def test_sin_citas(self, mock_repo):
        mock_repo.buscar_citas_por_documento.return_value = []
        resultado = consultar.ejecutar_cita({"documento": "12345678"})
        assert resultado["ok"] is False


class TestConsultarDisponibilidad:
    @patch("src.handlers.consultar.repo")
    def test_muestra_horas_libres(self, mock_repo):
        mock_repo.get_horas_especialidad.return_value = ["08:00", "09:30", "11:00"]
        mock_repo.horas_ocupadas.return_value = {"08:00"}

        resultado = consultar.ejecutar_disponibilidad(
            {"especialidad": "medicina general", "fecha": "2026-09-28"}
        )

        assert resultado["ok"] is True
        assert resultado["horas_disponibles"] == ["09:30", "11:00"]


class TestReagendar:
    @patch("src.handlers.reagendar.repo")
    def test_reagenda_exitosamente(self, mock_repo):
        mock_repo.buscar_cita_por_codigo.return_value = {
            "documento": "12345678",
            "codigo": "CITA-1234",
            "estado": "confirmada",
            "especialidad": "pediatria",
            "fecha": "2026-09-28",
            "hora": "08:30",
        }
        mock_repo.get_horas_especialidad.return_value = ["08:30", "10:00", "15:00"]
        mock_repo.horas_ocupadas.return_value = set()

        resultado = reagendar.ejecutar(
            {"codigo_cita": "CITA-1234", "fecha": "2026-09-29", "hora": "10:00"}
        )

        assert resultado["ok"] is True
        mock_repo.reagendar_cita_en_bd.assert_called_once()

    @patch("src.handlers.reagendar.repo")
    def test_cita_inactiva_no_se_reagenda(self, mock_repo):
        mock_repo.buscar_cita_por_codigo.return_value = {
            "documento": "12345678",
            "codigo": "CITA-1234",
            "estado": "cancelada",
        }
        resultado = reagendar.ejecutar(
            {"codigo_cita": "CITA-1234", "fecha": "2026-09-29", "hora": "10:00"}
        )
        assert resultado["ok"] is False
