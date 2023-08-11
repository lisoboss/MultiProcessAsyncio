import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 10):
    raise RuntimeError("requires Python 3.10+")

setup(name='multi_process_asyncio',
      version='1.3.0.uncertainty-task',
      description='_',
      author='_',
      author_email='_',
      url='_',
      packages=find_packages(),
      )
