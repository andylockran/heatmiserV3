"""Tests for serial and TCP connection setup."""
from unittest.mock import MagicMock, call, patch

import pytest

from heatmiserv3 import connection, constants


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
        {"ipaddress": "192.168.1.57", "port": ""},
        {"dev": ""},
        {"dev": "/dev/ttyACM0", "ipaddress": "192.168.1.57", "port": "102"},
        {"dev": "/dev/ttyACM0", "port": "102"},
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
