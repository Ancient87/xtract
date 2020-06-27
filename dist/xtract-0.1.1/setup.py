# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['xtract',
 'xtract.api',
 'xtract.financial_api',
 'xtract.model',
 'xtract.stockdata_service']

package_data = \
{'': ['*']}

install_requires = \
['ConfigParser>=4.0.2,<5.0.0',
 'Flask-Migrate>=2.5.3,<3.0.0',
 'Flask-Script>=2.0.6,<3.0.0',
 'bs4>=0.0.1,<0.0.2',
 'connexion>=2.6.0,<3.0.0',
 'flask-bcrypt>=0.7.1,<0.8.0',
 'flask-restplus>=0.13.0,<0.14.0',
 'flask>=1.1.1,<2.0.0',
 'flask_cors>=3.0.8,<4.0.0',
 'flask_sqlalchemy>=2.4.1,<3.0.0',
 'gunicorn>=20.0.4,<21.0.0',
 'mysql-connector>=2.2.9,<3.0.0',
 'numpy>=1.18.2,<2.0.0',
 'pandas>=1.0.3,<2.0.0',
 'pyjwt>=1.7.1,<2.0.0',
 'pymysql>=0.9.3,<0.10.0',
 'selenium>=3.141.0,<4.0.0',
 'sqlalchemy>=1.3.15,<2.0.0',
 'sqlalchemy_utils>=0.36.3,<0.37.0']

setup_kwargs = {
    'name': 'xtract',
    'version': '0.1.1',
    'description': 'Stock extractor',
    'long_description': None,
    'author': 'Sev Gassauer-Fleissner',
    'author_email': 'severin.gassauer@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.7,<4.0',
}


setup(**setup_kwargs)
