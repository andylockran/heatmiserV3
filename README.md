# heatmiserv3

[![Build Status](https://github.com/andylockran/heatmiserv3/actions/workflows/python-package.yml/badge.svg)](https://github.com/andylockran/heatmiserv3/actions/workflows/python-package.yml)

This library has been created from the work carried out by 
Neil Trimboy in 2011 here:
[https://code.google.com/p/heatmiser-monitor-control/]

The library uses the Heatmiser V3 Protocol to communicate 
with a number of thermostats

As the DCB Structures are different on each thermostat, this
module doesn't yet cover all their intricacies, but with the
connection in place, it provides a raw method of interfacing
directly with the thermostat.

I hope to add specific model support as it gets requested.

## Supported Thermostats

DT/DT-E/PRT/PRT-E/PRT-HW

## Supported Timing Switches

The timing switches have a smaller DCB, but it is possible with
this module to still send raw comamnds to them.

TM1/TM1-N

## Other sensors

Heatmiser have used their V3 protocol in a number of sensors.
Your mileage may vary in attempting to use this library
to communicate with them, but please open a pull request if 
you get something working.

# Requirements

Python needs to be version 3.

# Packaging and publishing

This library fell out of a little bit of love as I moved out of
the home that had the thermostats.  However, it appears to have
quite a significant following on home-assistant, with a number
of users wanting to benefit from it.  I've therefore tried to 
improve the resilience by upgrading the packaging, building and
publishing process to poetry.  This should make the project 
easier to contribute to, and align with the latest standards in
the python ecosystem.