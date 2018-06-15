#!/bin/bash -ev
# This file is part of INSPIRE-MITMPROXY.
# Copyright (C) 2018 CERN.
#
# INSPIRE-MITMPROXY is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# INSPIRE-MITMPROXY is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE-MITMPROXY; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

if [[ "$1" == "do_sort" ]]; then
    echo "Sorting imports"
    isort --recursive .
else
    echo "Dry-running isort to check for import ordering"
    isort --check-only --recursive --diff .
fi

echo "Running FLAKE8"
flake8 .

echo "Running MyPy"
export MYPYPATH="${VIRTUAL_ENV}/lib/python3.6/site-packages/"
mypy --follow-imports=silent .

echo "Runnning PyTest"
pytest --cov=inspire_mitmproxy \
    --cov-report=term-missing \
    --capture=sys \
    -vv \
    tests \
    inspire_mitmproxy
