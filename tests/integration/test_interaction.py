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

from pathlib import Path
from time import sleep

from mock import call, patch
from pytest import fixture

from inspire_mitmproxy.interaction import Interaction


@fixture(scope='module')
def interaction_callback(request):
    with patch.dict('os.environ', {'TEST_ENVAR_INTERPOLATION': 'interpolated'}):
        yield Interaction.from_file(
            Path(request.fspath.join('../fixtures/test_interaction_callback.yaml'))
        )


def test_interaction_execute_callbacks(interaction_callback: Interaction):
    with patch('requests.request') as request:
        interaction_callback.execute_callbacks()

        sleep(1)

        first_expected = call(
            method='GET',
            url='http://callback.local',
            data=b'1',
            headers={'Host': 'callback.local'},
            timeout=10,
        )

        second_expected = call(
            method='GET',
            url='http://interpolated.local',
            data=b'2',
            headers={'Host': 'interpolated.local'},
            timeout=10,
        )

        assert request.mock_calls.count(first_expected) == 1
        assert request.mock_calls.count(second_expected) == 1
