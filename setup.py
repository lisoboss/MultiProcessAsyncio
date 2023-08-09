import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 8):
    raise RuntimeError("requires Python 3.8+")

setup(name='multi_process_asyncio',
      version='1.3.0',
      description='_',
      author='_',
      author_email='_',
      url='_',
      packages=find_packages(),
      )
