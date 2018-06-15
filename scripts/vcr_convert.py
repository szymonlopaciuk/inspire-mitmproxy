#!/usr/bin/env python3
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

"""Tool to convert VCRpy casettes to request-response pair files.

Usage: vcr_convert.py [--help] CASETTE_1 [CASETTE_2 ...] DESTINATION_DIR

This will convert an arbitrary number of VCRpy casettes to files with
a single pair of request and response each, structured in folders according
to the pattern: DESTINATION_DIR/<scenario>/<host>/<index in casette>.yaml
"""

import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml


def service_name_for_interaction(interaction: dict) -> str:
    parsed_url = urlparse(interaction['request']['uri'])
    return parsed_url.netloc


if len(sys.argv) < 3 or sys.argv[1] == '--help':
    print(__doc__)
    exit(1)

destination = Path(sys.argv[-1])

for cassette_file in sys.argv[1:-1]:
    cassette_file = Path(cassette_file)
    cassette = yaml.load(cassette_file.read_text())

    for idx, interaction in enumerate(cassette['interactions']):
        output_dir = destination / cassette_file.stem / service_name_for_interaction(interaction)
        output_dir.mkdir(parents=True, exist_ok=True)
        output = output_dir / f'{cassette_file.stem}.{idx}.yaml'
        print(f'Creating {output}')

        # Remove VCR's {'string': ...} wrapper:
        if interaction['response']['body'] is not None:
            interaction['response']['body'] = interaction['response']['body']['string']

        # Rename VCR's 'uri' to 'url'
        interaction['request']['url'] = interaction['request']['uri']
        del interaction['request']['uri']

        output.write_text(yaml.dump(interaction))
