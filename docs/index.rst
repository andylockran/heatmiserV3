.. heatmiserv3 documentation master file

Welcome to Heatmiser V3's Documentation!
========================================

**heatmiserv3** is a Python library for interacting with Heatmiser Version 3 network thermostats over RS485 serial and UH1 wiring centres.

.. note::
   For the interactive browser-based portal, live frame inspector, and 5-zone multi-thermostat digital twin, visit the `GitHub Pages Live Portal <https://andylockran.github.io/heatmiserv3/>`_ and `Interactive Digital Twin <https://andylockran.github.io/heatmiserv3/twin.html>`_.

Features
--------

* **Full Heatmiser V3 Protocol Support**: Supports DT, DT-E, PRT, PRT-E, PRTHW, TM1, and HC-EN thermostat models.
* **UH1 Wiring Centre Support**: Serial (``/dev/tty*``) and TCP/IP (``socket://``) bridge connectivity.
* **Defensive Serial Layer**: CRC-16 CCITT validation, frame boundary checks, and automatic port reconnection.
* **High-Level Helper Methods**: Grouped convenience setters for on/off state, key lock, temperature formats, differentials, sensor selection, hold periods, and holiday hours.
* **Digital Twin & Simulation**: Built-in logic emulation and interactive browser UI.

Installation
------------

Install via pip:

.. code-block:: bash

   pip install heatmiserv3

Or using ``uv``:

.. code-block:: bash

   uv add heatmiserv3

Quickstart
----------

.. code-block:: python

   from heatmiserv3 import HeatmiserUH1, HeatmiserThermostat, PRTHWThermostat

   # Connect via RS485 serial port or IP socket
   uh1 = HeatmiserUH1(dev="/dev/ttyUSB0")
   # Or via network socket: uh1 = HeatmiserUH1(ipaddress="192.168.1.57", port=102)

   # Register a PRT thermostat at RS485 address 1
   stat = HeatmiserThermostat(1, "prt", uh1)
   uh1.registerThermostat(stat)

   # Read telemetry
   temp = stat.get_temperature()
   target = stat.get_target_temp()
   print(f"Room Temperature: {temp}°C | Target: {target}°C")

   # Convenience setters
   stat.set_target_temp(21)
   stat.set_on_off(True)
   stat.set_temp_hold(hours=2, minutes=30, temp=22)

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   heatmiser-v3-protocol-spec
   api
   adrs/index

.. toctree::
   :maxdepth: 1
   :caption: Interactive Tools

   GitHub Pages Live Portal <https://andylockran.github.io/heatmiserv3/>
   Interactive Digital Twin <https://andylockran.github.io/heatmiserv3/twin.html>
