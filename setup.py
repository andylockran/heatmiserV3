"""Setuptools file for the repo"""
from setuptools import setup

setup(
    name='heatmiserV3',
    packages=['heatmiserV3'],  # this must be the same as the name above
    version='1.1.13',
    description='A library to interact with Heatmiser Themostats using V3',
    author='Andy Loughran',
    author_email='andy@zrmt.com',
    tests_require=['pytest', 'pylint', 'flake8'],
    data_files = [('config', ['heatmiserV3/config.yml'])],
    include_package_data=True ,
    url='https://github.com/andylockran/heatmiserV3',
    download_url='https://github.com/andylockran/heatmiserV3/tarball/1.1.0',
    keywords=[
        'v3',
        'thermostat',
        'heatmiser',
        'prt',
        'serial',
        'uh1'
    ],
    test_suite='tests.test_heatmiser',
    classifiers=[],
    install_requires=['pyserial', 'pyserial-asyncio', 'pyyaml', 'mock'],
    extras_require={
        'testing': ['pytest'],
    }
)
