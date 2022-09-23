import sys
from distutils.core import setup

if sys.version_info < (3, 7):
    raise RuntimeError("aiohttp 4.x requires Python 3.7+")

setup(name='multi_process_asyncio',
      version='1.0.0',
      description='_',
      author='_',
      author_email='_',
      url='_',
      # packages=['distutils', 'distutils.command'],
      )
