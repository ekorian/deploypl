"""
setup.py
   deploypl
@author: K.Edeline
"""

try:
   from setuptools import setup, find_packages
except ImportError:
   from distutils.core import setup, find_packages

config = {
   'description': 'PlanetLab deployer',
   'keywords' : 'planetlab deploy experiment',
   'author': 'korian edeline',
   'url': 'https://github.com/ekorian/deploypl',
   'download_url': 'https://github.com/ekorian/deploypl',
   'author_email': 'korian.edeline@ulg.ac.be',
   'version': '0.1',
   
   #'install_requires': ['nose'],

   'packages': find_packages(),
   
   'scripts': ['scripts/deploypl'],

   'package_data': {
      '': ['nodes/*.txt'],
   },

   'license' : 'PSF',
   'name': 'deploypl'
}

setup(**config)
