"""Tests for HeatmiserUH1 connection module."""
import unittest
from unittest.mock import MagicMock, patch
from heatmiserv3 import connection, heatmiser


class TestHeatmiserUH1(unittest.TestCase):
    """Unit tests for HeatmiserUH1 class."""

    @patch("serial.serial_for_url")
    def test_init_string_port(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        assert uh1.ipaddress == "192.168.1.100"
        assert uh1.port == "8068"
        assert uh1.status is True
        mock_serial_for_url.assert_called_with("socket://192.168.1.100:8068")
        mock_port.open.assert_called()

    @patch("serial.serial_for_url")
    def test_init_integer_port(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        # Passing integer port should not raise TypeError
        uh1 = connection.HeatmiserUH1("192.168.1.100", 8068)
        assert uh1.port == "8068"
        mock_serial_for_url.assert_called_with("socket://192.168.1.100:8068")

    @patch("serial.serial_for_url")
    def test_open_when_already_open(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        assert uh1.status is True
        # Calling _open when status is already True should return False
        result = uh1._open()
        assert result is False

    @patch("serial.serial_for_url")
    def test_reopen(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        uh1.status = False
        assert uh1.reopen() is True
        assert uh1.status is True

        # Reopen with force=True even when status is True
        assert uh1.reopen(force=True) is True

        # Reopen without force when status is True returns None
        uh1.status = True
        assert uh1.reopen(force=False) is None

    @patch("serial.serial_for_url")
    def test_register_thermostat(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")

        mock_thermo = MagicMock(spec=heatmiser.HeatmiserThermostat)
        mock_thermo.address = 1

        # Register valid thermostat
        ser = uh1.registerThermostat(mock_thermo)
        assert ser is mock_port
        assert 1 in uh1.thermostats

        # Registering duplicate thermostat address should not raise uncaught error
        uh1.registerThermostat(mock_thermo)
        assert len(uh1.thermostats) == 1

        # Registering non-HeatmiserThermostat should not crash on Python 3 (no e.message bug)
        uh1.registerThermostat("invalid-object")
        assert len(uh1.thermostats) == 1

    @patch("serial.serial_for_url")
    def test_list_thermostats(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        assert uh1.listThermostats() is None

        mock_thermo = MagicMock(spec=heatmiser.HeatmiserThermostat)
        mock_thermo.address = 5
        uh1.registerThermostat(mock_thermo)

        thermostats = uh1.listThermostats()
        assert thermostats is not None
        assert 5 in thermostats

    @patch("serial.serial_for_url")
    def test_del_destructor(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        # Should execute cleanly without error
        uh1.__del__()
        mock_port.close.assert_called()

    @patch("serial.serial_for_url")
    def test_del_destructor_exception_safe(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        # Now set close to raise an exception
        mock_port.close.side_effect = Exception("Port already destroyed")
        # Should swallow exceptions cleanly
        uh1.__del__()
