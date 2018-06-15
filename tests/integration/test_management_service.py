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

"""Tests for the ManagementService"""

from json import loads as json_loads
from os import environ
from typing import List, Type

from mock import patch
from pytest import fixture

from inspire_mitmproxy.dispatcher import Dispatcher
from inspire_mitmproxy.http import MITMHeaders, MITMRequest
from inspire_mitmproxy.services import BaseService


@fixture(scope='function')
def dispatcher() -> Dispatcher:
    class TestService(BaseService):
        SERVICE_HOSTS = ['test-service.local']

    services: List[Type[BaseService]] = [TestService]

    with patch.object(Dispatcher, 'SERVICE_LIST', services):
        return Dispatcher()


@fixture
def fake_scenarios_dir(tmpdir) -> str:
    scenarios = tmpdir.mkdir('scenarios')

    scenario1 = scenarios.mkdir('scenario1')
    scenario2 = scenarios.mkdir('scenario2')

    scenario1_serviceA = scenario1.mkdir('A')
    scenario2_serviceA = scenario2.mkdir('A')
    scenario2_serviceB = scenario2.mkdir('B')

    scenario1_serviceA.join('1.yaml').ensure()
    scenario1_serviceA.join('2.yaml').ensure()

    scenario2_serviceA.join('1.yaml').ensure()
    scenario2_serviceB.join('1.yaml').ensure()
    scenario2_serviceB.join('2.yaml').ensure()
    scenario2_serviceB.join('3.yaml').ensure()

    with patch.dict(environ, {'SCENARIOS_PATH': scenarios.strpath}):
        yield


def test_management_service_get_services(dispatcher):
    result = dispatcher.process_request(
        MITMRequest(
            method='GET',
            url='http://mitm-manager.local/services',
            headers=MITMHeaders({
                'Host': ['mitm-manager.local'],
                'Accept': ['application/json'],
            })
        )
    )

    expected = {
        '0': {
            'class': 'ManagementService',
            'service_hosts': ['mitm-manager.local'],
        },
        '1': {
            'class': 'TestService',
            'service_hosts': ['test-service.local'],
        },
    }

    assert result.status_code == 200
    assert json_loads(result.body) == expected


def test_management_service_get_scenarios(fake_scenarios_dir, dispatcher):
    result = dispatcher.process_request(
        MITMRequest(
            method='GET',
            url='http://mitm-manager.local/scenarios',
            headers=MITMHeaders({
                'Host': ['mitm-manager.local'],
                'Accept': ['application/json'],
            })
        )
    )

    expected = {
        'scenario1': {
            'responses': {
                'A': ['1.yaml', '2.yaml'],
            }
        },
        'scenario2': {
            'responses': {
                'A': ['1.yaml'],
                'B': ['1.yaml', '2.yaml', '3.yaml'],
            }
        },
    }

    assert result.status_code == 200
    assert json_loads(result.body) == expected


def test_management_service_get_config(dispatcher):
    result = dispatcher.process_request(
        MITMRequest(
            method='GET',
            url='http://mitm-manager.local/config',
            headers=MITMHeaders({
                'Host': ['mitm-manager.local'],
                'Accept': ['application/json'],
            })
        )
    )

    expected = {
        'active_scenario': 'default',
    }

    assert result.status_code == 200
    assert json_loads(result.body) == expected


def test_management_service_post_and_put_config(dispatcher):
    post_config_request = MITMRequest(
        method='POST',
        url='http://mitm-manager.local/config',
        body='{"active_scenario": "a scenario", "another": "value"}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    put_config_request = MITMRequest(
        method='PUT',
        url='http://mitm-manager.local/config',
        body='{"active_scenario": "another scenario"}',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    get_config_request = MITMRequest(
        method='GET',
        url='http://mitm-manager.local/config',
        headers=MITMHeaders({
            'Host': ['mitm-manager.local'],
            'Accept': ['application/json'],
        })
    )

    expected_config = {
        'active_scenario': 'another scenario',
        'another': 'value',
    }

    post_req = dispatcher.process_request(post_config_request)
    assert post_req.status_code == 201

    put_req = dispatcher.process_request(put_config_request)
    assert put_req.status_code == 204

    result = dispatcher.process_request(get_config_request)
    assert result.status_code == 200

    assert json_loads(result.body) == expected_config
