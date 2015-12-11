from setuptools import setup
from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
  name = 'heatmiserV3',
  packages = ['heatmiserV3'], # this must be the same as the name above
  version = '0.9.3',
  description = 'A library to interact with Heatmiser Themostats using the v3 protocol',
  author = 'Andy Loughran',
  author_email = 'andy@zrmt.com',
  tests_require=['pytest'],
  url = 'https://github.com/andylockran/heatmiserV3', # use the URL to the github repo
  download_url = 'https://github.com/andylockran/heatmiserV3/tarball/0.9.3', 
  keywords = ['v3', 'thermostat', 'heatmiser'], # arbitrary keywords
  test_suite='heatmiserV3.test.test_heatmiser',
  classifiers = [],
  install_requires = ['pyserial'],
  extras_require= {
    'testing': ['pytest'],
  }
)
