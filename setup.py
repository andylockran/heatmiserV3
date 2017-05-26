from setuptools import setup
# from setuptools.command.test import test as TestCommand
#
# class PyTest(TestCommand):
#     def finalize_options(self):
#         TestCommand.finalize_options(self)
#         self.test_args = []
#         self.test_suite = True
#
#     def run_tests(self):
#         import pytest
#         errcode = pytest.main(self.test_args)
#         sys.exit(errcode)

setup(
  name = 'heatmiserV3',
  packages = ['heatmiserV3'], # this must be the same as the name above
  version = '1.0.0',
  description = 'A library to interact with Heatmiser Themostats using the v3 protocol',
  author = 'Andy Loughran',
  author_email = 'andy@zrmt.com',
  tests_require=['pytest'],
  setup_requires = ['pytest-runner'],
  url = 'https://github.com/andylockran/heatmiserV3', # use the URL to the github repo
  download_url = 'https://github.com/andylockran/heatmiserV3/tarball/1.0.0',
  keywords = ['v3', 'thermostat', 'heatmiser'], # arbitrary keywords
  test_suite='heatmiserV3.test',
  license = 'Apache 2 License',
  classifiers = [
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 4 - Beta',

    # Indicate who your project is intended for
    'Intended Audience :: Developers',
    'Topic :: System :: Hardware :: Hardware Drivers',

    # Pick your license as you wish (should match "license" above)
    'License :: OSI Approved :: Apache Software License',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
  install_requires = ['pyserial'],
  extras_require= {
    'testing': ['pytest'],
  }
)
