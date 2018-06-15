# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE-MITMPROXY.
# Copyright (C) 2018 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""INSPIRE MITMProxy for E2E Tests."""

from typing import List

from setuptools import setup


readme = open('README.rst').read()

setup_requires = [
    'autosemver~=0.0,>=0.5.3',
]

install_requires = [
    'autosemver~=0.0,>=0.5.3',
    'mitmproxy~=3.0,>=3.0.4',
    'pathlib~=1.0,>=1.0.1',
    'pyyaml~=3.0,>=3.12',
    'requests~=2.0,>=2.18.4',
]

tests_require = [
    'flake8~=3.0,>=3.5.0',
    'isort~=4.0,>=4.3.4',
    'mypy~=0.0,>=0.590',
    'mock~=2.0,>=2.0.0',
    'pytest~=3.0,>=3.5.0',
    'pytest-cov~=2.0,>=2.5.1',
]

docs_require: List[str] = [
    'Sphinx',
    'sphinx-automodapi',
    'sphinx_rtd_theme',
]

extras_require = {
    'docs': docs_require,
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    extras_require['all'].extend(reqs)

setup(
    description=__doc__,
    long_description=readme,
    url='https://github.com/inspirehep/inspire-mitmproxy',
    install_requires=install_requires,
    tests_require=tests_require,
    setup_requires=setup_requires,
    extras_require=extras_require,
    autosemver={'bugtracker_url': '/issues'}
)
