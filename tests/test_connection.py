"""Tests for HeatmiserUH1 connection module across serial and TCP modes."""
import unittest
from unittest.mock import MagicMock, call, patch
import pytest

from heatmiserv3 import connection, constants, heatmiser


class TestHeatmiserUH1(unittest.TestCase):
    """Unit tests for HeatmiserUH1 class."""

    @patch("heatmiserv3.connection.serial.serial_for_url")
    def test_init_string_port(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        assert uh1.ipaddress == "192.168.1.100"
        assert uh1.port == "8068"
        assert uh1.dev is None
        assert uh1.status is True
        mock_serial_for_url.assert_called_with("socket://192.168.1.100:8068")
        mock_port.open.assert_called()

    @patch("heatmiserv3.connection.serial.serial_for_url")
    def test_init_integer_port(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", 8068)
        assert uh1.port == "8068"
        assert uh1.dev is None
        mock_serial_for_url.assert_called_with("socket://192.168.1.100:8068")

    @patch("heatmiserv3.connection.serial.serial_for_url")
    def test_init_serial_device(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1(dev="/dev/ttyACM0")
        assert uh1.dev == "/dev/ttyACM0"
        assert uh1.ipaddress is None
        assert uh1.port is None
        mock_serial_for_url.assert_called_with("/dev/ttyACM0")
        mock_port.open.assert_called()

    @patch("heatmiserv3.connection.serial.serial_for_url")
    def test_open_when_already_open(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        assert uh1.status is True
        # Calling _open when status is already True should return False
        result = uh1._open()
        assert result is False

    @patch("heatmiserv3.connection.serial.serial_for_url")
    def test_reopen(self, mock_serial_for_url):
        initial_port = MagicMock()
        reopened_port = MagicMock()
        mock_serial_for_url.side_effect = [initial_port, reopened_port]

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        uh1.status = False
        assert uh1.reopen() is True
        assert uh1.status is True
        reopened_port.open.assert_called()

    @patch("heatmiserv3.connection.serial.serial_for_url")
    def test_reopen_force_closes_previous_port(self, mock_serial_for_url):
        initial_port = MagicMock()
        reopened_port = MagicMock()
        mock_serial_for_url.side_effect = [initial_port, reopened_port]

        uh1 = connection.HeatmiserUH1(dev="/dev/ttyUSB0")
        assert uh1.status is True

        # Force reopen closes old port and opens new one
        assert uh1.reopen(force=True) is True
        # Close should be called on initial_port (once in _new_serial_port, once on reopen)
        assert initial_port.close.call_count >= 2
        reopened_port.open.assert_called()

    @patch("heatmiserv3.connection.serial.serial_for_url")
    def test_reopen_updates_registered_thermostat_connection(self, mock_serial_for_url):
        initial_port = MagicMock()
        reopened_port = MagicMock()
        mock_serial_for_url.side_effect = [initial_port, reopened_port]

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        thermostat = MagicMock(spec=heatmiser.HeatmiserThermostat)
        thermostat.address = 1
        thermostat.conn = initial_port
        uh1.registerThermostat(thermostat)

        assert uh1.reopen(force=True) is True
        assert thermostat.conn is reopened_port

    @patch("heatmiserv3.connection.serial.serial_for_url")
    def test_reopen_without_force_when_open_returns_none(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        assert uh1.status is True
        assert uh1.reopen(force=False) is None

    @patch("heatmiserv3.connection.serial.serial_for_url")
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

    @patch("heatmiserv3.connection.serial.serial_for_url")
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

    @patch("heatmiserv3.connection.serial.serial_for_url")
    def test_del_destructor(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        uh1.__del__()
        mock_port.close.assert_called()

    @patch("heatmiserv3.connection.serial.serial_for_url")
    def test_del_destructor_exception_safe(self, mock_serial_for_url):
        mock_port = MagicMock()
        mock_serial_for_url.return_value = mock_port

        uh1 = connection.HeatmiserUH1("192.168.1.100", "8068")
        mock_port.close.side_effect = Exception("Port already destroyed")
        # Should catch exceptions cleanly
        uh1.__del__()


# Parametrized tests from PR #117
@pytest.mark.parametrize(
    ("args", "expected_url"),
    [
        (("192.168.1.57", "102"), "socket://192.168.1.57:102"),
        ((), "/dev/ttyACM0"),
    ],
)
def test_connection_uses_selected_endpoint(args, expected_url):
    serial_port = MagicMock()

    with patch(
        "heatmiserv3.connection.serial.serial_for_url",
        return_value=serial_port,
    ) as serial_for_url:
        if args:
            connection.HeatmiserUH1(*args)
        else:
            connection.HeatmiserUH1(dev=expected_url)

    serial_for_url.assert_called_once_with(expected_url)
    assert serial_port.baudrate == constants.COM_BAUD
    assert serial_port.bytesize == constants.COM_SIZE
    assert serial_port.parity == constants.COM_PARITY
    assert serial_port.stopbits == constants.COM_STOP
    assert serial_port.timeout == constants.COM_TIMEOUT
    serial_port.open.assert_called_once_with()


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"ipaddress": "192.168.1.57"},
        {"port": "102"},
        {"ipaddress": "", "port": "102"},
        {"ipaddress": "   ", "port": "102"},
        {"ipaddress": "192.168.1.57", "port": ""},
        {"ipaddress": "192.168.1.57", "port": "   "},
        {"dev": ""},
        {"dev": "   "},
        {"dev": "/dev/ttyACM0", "ipaddress": "192.168.1.57", "port": "102"},
        {"dev": "/dev/ttyACM0", "port": "102"},
        {"dev": "/dev/ttyACM0", "ipaddress": "192.168.1.57"},
    ],
)
def test_connection_rejects_invalid_endpoint_configuration(kwargs):
    with pytest.raises(ValueError):
        connection.HeatmiserUH1(**kwargs)


@pytest.mark.parametrize(
    ("kwargs", "expected_url"),
    [
        (
            {"ipaddress": "192.168.1.57", "port": "102"},
            "socket://192.168.1.57:102",
        ),
        (
            {"ipaddress": "192.168.1.57", "port": 102},
            "socket://192.168.1.57:102",
        ),
        ({"dev": "/dev/ttyACM0"}, "/dev/ttyACM0"),
    ],
)
def test_reopen_reuses_selected_endpoint(kwargs, expected_url):
    initial_port = MagicMock()
    reopened_port = MagicMock()

    with patch(
        "heatmiserv3.connection.serial.serial_for_url",
        side_effect=[initial_port, reopened_port],
    ) as serial_for_url:
        uh1 = connection.HeatmiserUH1(**kwargs)
        assert uh1.reopen(force=True)

    assert serial_for_url.call_args_list == [
        call(expected_url),
        call(expected_url),
    ]
    reopened_port.open.assert_called_once_with()
    assert reopened_port.baudrate == constants.COM_BAUD
    assert reopened_port.timeout == constants.COM_TIMEOUT
