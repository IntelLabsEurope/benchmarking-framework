__author__ = 'vmriccox'

"""
Setuptools script.
"""

from distutils.core import setup

setup(name='experimental_framework',
      version='1.0',
      description='Framework to automatically run experiments/benchmarks with '
                  'VMs within OpenStack environments',
      author='Intel Research and Development Ireland Ltd',
      author_email='vincenzox.m.riccobene@intel.com',
      license='Apache 2.0',
      url='www.intel.com',
      packages=['experimental_framework',
                'experimental_framework.benchmarks',
                'experimental_framework.packet_generators',
                'experimental_framework.libraries',
                'experimental_framework.constants'])