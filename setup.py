"""Setuptools file for the repo"""

from setuptools import setup

setup(
    name="heatmiserv3",
    packages=["heatmiserv3"],  # this must be the same as the name above
    description="A library to interact with Heatmiser Themostats using V3",
    author="Andy Loughran",
    author_email="andy@zrmt.com",
    tests_require=["pytest", "pylint", "flake8"],
    data_files=[("config", ["heatmiserv3/config.yml"])],
    include_package_data=True,
    url="https://github.com/andylockran/heatmiserv3",
    keywords=["v3", "thermostat", "heatmiser", "prt", "serial", "uh1"],
    test_suite="tests.test_heatmiser",
    classifiers=[],
    install_requires=["pyserial", "pyyaml", "mock"],
    extras_require={
        "testing": ["pytest"],
    },
)
